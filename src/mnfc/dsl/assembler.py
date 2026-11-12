"""MNFC DSL — Fase 4 · Assembler.

Agrupa ResultadoAccion por (fractal, regla). Cada grupo produce un
Asiento tipado. El cuadre se verifica por grupo: el descuadre de una
regla no se compensa con el saldo de otra.

Frontera numérica
-----------------
El assembler acepta int y float (no bool). El tipo Decimal no es
contablemente inválido; queda fuera del contrato numérico de esta
fase porque:
  (a) el kernel (baldor.verificar_cuadre, _validar_finito) opera
      en float;
  (b) mezclar Decimal y float en sumas produce TypeError, lo que
      forzaría conversión implícita — precisamente lo que el kernel
      evita;
  (c) la migración a Decimal es deuda de v0.3.0, no de esta fase.
Aceptar Decimal aquí sin migrar el kernel introduciría una
inconsistencia silenciosa entre capas.

Cada monto individual se valida antes de sumarse:
  - rechaza bool (aunque sea subclase de int);
  - rechaza no numérico (str, Decimal, list, ...);
  - rechaza no finito (NaN, +inf, -inf);
  - rechaza negativo.

Los totales se pre-chequean por overflow (suma de floats finitos
puede desbordar a inf) ANTES de delegar en verificar_cuadre y
ANTES de marcar el asiento como cuadrado.

El mensaje de descuadre calcula la diferencia con un helper que no
propaga inf/nan al texto diagnóstico, incluso si en el futuro se
relajara la restricción de monto no negativo.

Determinismo: el orden de los asientos sigue el orden de primera
aparición de cada par (fractal, regla) en la lista de resultados.

Sin persistencia. Sin fiscal. Sin marcos reales.
"""

import math

from ..baldor import verificar_cuadre
from ..extensiones.modelos import (
    Asiento,
    ContextoContable,
    LineaAsiento,
    PartidaAutorizada,
)
from .evaluator import DSLEvaluationError, ResultadoAccion


class DSLAssemblyError(DSLEvaluationError):
    """Error de ensamblado del DSL.

    Hereda de DSLEvaluationError para que pueda capturarse con un
    except único cuando se recorre el pipeline completo.
    Constructor heredado: DSLAssemblyError(mensaje, contexto="").
    Incluye contexto: 'FRACTAL <f> > REGLA <r>'.
    """


def ensamblar(
    resultados: list[ResultadoAccion],
    contexto: ContextoContable | None = None,
) -> list[Asiento]:
    """Agrupa ResultadoAccion por (fractal, regla) → Asiento por grupo.

    Args:
        resultados: salida de evaluar().
        contexto: ContextoContable opcional, adjuntado a cada Asiento.

    Returns:
        Un Asiento por par (fractal, regla) distinto, en orden de
        primera aparición.

    Raises:
        DSLAssemblyError: si una acción no tiene partidas, si un monto
            individual es inválido, si una ubicación no es DEBE/HABER,
            si un total desborda a inf, o si un asiento no cuadra.
    """
    if not resultados:
        return []

    grupos: dict[tuple[str, str], list[ResultadoAccion]] = {}
    orden: list[tuple[str, str]] = []
    for r in resultados:
        clave = (r.fractal, r.regla)
        if clave not in grupos:
            grupos[clave] = []
            orden.append(clave)
        grupos[clave].append(r)

    asientos: list[Asiento] = []
    for fractal, regla in orden:
        ctx = f"FRACTAL {fractal} > REGLA {regla}"
        partidas: list[PartidaAutorizada] = []
        for r in grupos[(fractal, regla)]:
            if not r.partidas:
                raise DSLAssemblyError(f"acción #{r.indice} sin partidas", ctx)
            partidas.extend(r.partidas)
        asiento = _construir_asiento(partidas, contexto, ctx)
        _verificar_cuadre(asiento, ctx)
        asientos.append(asiento)

    return asientos


def _validar_monto(monto, cuenta: str, ctx: str) -> int:
    """Valida monto individual. Devuelve int (centavos enteros).

    Contrato fase 2 (ADR-005):
      - bool: rechazado (sin sentido contable).
      - no numérico (str, list, dict): rechazado.
      - no finito (NaN, +inf, -inf): rechazado.
      - negativo: rechazado (rompe semántica de partida doble).
      - Decimal/int/float válido: convertido a centavos.
    """
    from decimal import Decimal, InvalidOperation
    from ..money import to_centimos

    if isinstance(monto, bool):
        raise DSLAssemblyError(
            f"monto booleano en cuenta {cuenta}: {monto!r}", ctx
        )
    if not isinstance(monto, (int, float, Decimal)):
        raise DSLAssemblyError(
            f"monto no numérico en cuenta {cuenta}: "
            f"{type(monto).__name__}", ctx
        )

    # Convertir a Decimal para validar finitud y signo
    try:
        dec = monto if isinstance(monto, Decimal) else Decimal(str(monto))
    except (InvalidOperation, ValueError) as e:
        raise DSLAssemblyError(
            f"monto no numérico en cuenta {cuenta}: {monto!r}", ctx
        ) from e

    if not dec.is_finite():
        raise DSLAssemblyError(
            f"monto no finito en cuenta {cuenta}: {monto!r}", ctx
        )
    if dec < 0:
        raise DSLAssemblyError(
            f"monto negativo en cuenta {cuenta}: {monto}", ctx
        )

    try:
        return to_centimos(dec)
    except (InvalidOperation, OverflowError) as e:
        raise DSLAssemblyError(
            f"monto fuera de rango en cuenta {cuenta}: {monto!r} "
            f"(no cabe en centavos)",
            ctx,
        ) from e




def _construir_asiento(
    partidas,
    contexto,
    ctx,
):
    lineas = []
    total_debe_cent = 0
    total_haber_cent = 0

    for pa in partidas:
        monto_cent = _validar_monto(pa.monto, pa.cuenta_codigo, ctx)
        if pa.ubicacion not in ("DEBE", "HABER"):
            raise DSLAssemblyError(
                f"ubicación inválida: {pa.ubicacion!r} "
                f"(cuenta {pa.cuenta_codigo})",
                ctx,
            )
        lineas.append(
            LineaAsiento(
                cuenta=pa.cuenta_codigo,
                ubicacion=pa.ubicacion,
                monto_cent=monto_cent,
                naturaleza=None,
                movimiento=pa.movimiento,
            )
        )
        if pa.ubicacion == "DEBE":
            total_debe_cent += monto_cent
        else:
            total_haber_cent += monto_cent

    return Asiento(
        lineas=lineas,
        total_debe_cent=total_debe_cent,
        total_haber_cent=total_haber_cent,
        cuadrado=False,
        contexto=contexto,
    )




def _describir_diferencia(total_debe: float, total_haber: float) -> str:
    """Diferencia para el mensaje de error, segura ante overflow.

    No altera la decisión de cuadre (esa la toma verificar_cuadre
    antes). Sólo construye el texto diagnóstico.
    """
    try:
        d = total_debe - total_haber
    except (OverflowError, ValueError):
        return "no calculable"
    if not math.isfinite(d):
        return "no calculable (overflow)"
    return f"{abs(d):.6f}"


def _verificar_cuadre(asiento: Asiento, ctx: str) -> None:
    # Pre-check: suma de floats finitos puede desbordar a inf.
    # Se ejecuta ANTES de delegar en baldor y ANTES de fijar cuadrado.
    if not math.isfinite(asiento.total_debe) or not math.isfinite(asiento.total_haber):
        raise DSLAssemblyError(
            f"total no finito (posible overflow): "
            f"DEBE={asiento.total_debe!r} "
            f"HABER={asiento.total_haber!r}",
            ctx,
        )
    try:
        ok = verificar_cuadre(asiento.total_debe, asiento.total_haber)
    except ValueError as e:
        raise DSLAssemblyError(f"cuadre no evaluable: {e}", ctx) from e
    if not ok:
        raise DSLAssemblyError(
            f"asiento descuadrado: DEBE={asiento.total_debe} "
            f"HABER={asiento.total_haber} "
            f"(diferencia="
            f"{_describir_diferencia(asiento.total_debe, asiento.total_haber)}, "
            f"tolerancia=<0.001)",
            ctx,
        )
    asiento.cuadrado = True

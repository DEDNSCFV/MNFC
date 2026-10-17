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
from typing import Dict, List, Optional, Tuple

from .evaluator import ResultadoAccion, DSLEvaluationError
from ..extensiones.modelos import (
    Asiento,
    LineaAsiento,
    PartidaAutorizada,
    ContextoContable,
)
from ..baldor import verificar_cuadre


class DSLAssemblyError(DSLEvaluationError):
    """Error de ensamblado del DSL.

    Hereda de DSLEvaluationError para que pueda capturarse con un
    except único cuando se recorre el pipeline completo.
    Constructor heredado: DSLAssemblyError(mensaje, contexto="").
    Incluye contexto: 'FRACTAL <f> > REGLA <r>'.
    """


def ensamblar(
    resultados: List[ResultadoAccion],
    contexto: Optional[ContextoContable] = None,
) -> List[Asiento]:
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

    grupos: Dict[Tuple[str, str], List[ResultadoAccion]] = {}
    orden: List[Tuple[str, str]] = []
    for r in resultados:
        clave = (r.fractal, r.regla)
        if clave not in grupos:
            grupos[clave] = []
            orden.append(clave)
        grupos[clave].append(r)

    asientos: List[Asiento] = []
    for fractal, regla in orden:
        ctx = f"FRACTAL {fractal} > REGLA {regla}"
        partidas: List[PartidaAutorizada] = []
        for r in grupos[(fractal, regla)]:
            if not r.partidas:
                raise DSLAssemblyError(
                    f"acción #{r.indice} sin partidas", ctx
                )
            partidas.extend(r.partidas)
        asiento = _construir_asiento(partidas, contexto, ctx)
        _verificar_cuadre(asiento, ctx)
        asientos.append(asiento)

    return asientos


def _validar_monto(monto, cuenta: str, ctx: str) -> float:
    """Valida monto individual. Devuelve float normalizado.

    Rechaza explícitamente:
      - bool (aunque es subclase de int): sin sentido contable.
      - no numérico (str, Decimal, list, ...).
      - no finito (NaN, +inf, -inf).
      - negativo (rompe semántica de partida doble).
    """
    if isinstance(monto, bool):
        raise DSLAssemblyError(
            f"monto booleano en cuenta {cuenta}: {monto!r}", ctx
        )
    if not isinstance(monto, (int, float)):
        raise DSLAssemblyError(
            f"monto no numérico en cuenta {cuenta}: "
            f"{type(monto).__name__}", ctx
        )
    if not math.isfinite(monto):
        raise DSLAssemblyError(
            f"monto no finito en cuenta {cuenta}: {monto!r}", ctx
        )
    if monto < 0:
        raise DSLAssemblyError(
            f"monto negativo en cuenta {cuenta}: {monto}", ctx
        )
    return float(monto)


def _construir_asiento(
    partidas: List[PartidaAutorizada],
    contexto: Optional[ContextoContable],
    ctx: str,
) -> Asiento:
    lineas: List[LineaAsiento] = []
    total_debe = 0.0
    total_haber = 0.0

    for pa in partidas:
        monto = _validar_monto(pa.monto, pa.cuenta_codigo, ctx)
        if pa.ubicacion not in ("DEBE", "HABER"):
            raise DSLAssemblyError(
                f"ubicación inválida: {pa.ubicacion!r} "
                f"(cuenta {pa.cuenta_codigo})", ctx,
            )
        lineas.append(LineaAsiento(
            cuenta=pa.cuenta_codigo,
            ubicacion=pa.ubicacion,
            monto=monto,
            naturaleza=None,
            movimiento=pa.movimiento,
        ))
        if pa.ubicacion == "DEBE":
            total_debe += monto
        else:
            total_haber += monto

    return Asiento(
        lineas=lineas,
        total_debe=total_debe,
        total_haber=total_haber,
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
    if not math.isfinite(asiento.total_debe) or \
       not math.isfinite(asiento.total_haber):
        raise DSLAssemblyError(
            f"total no finito (posible overflow): "
            f"DEBE={asiento.total_debe!r} "
            f"HABER={asiento.total_haber!r}",
            ctx,
        )
    try:
        ok = verificar_cuadre(asiento.total_debe, asiento.total_haber)
    except ValueError as e:
        raise DSLAssemblyError(
            f"cuadre no evaluable: {e}", ctx
        ) from e
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

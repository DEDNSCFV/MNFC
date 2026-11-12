"""
MNFC v0.2.0 - Capa 7 - Modelos tipados del dominio contable.

Migrado de SCFV_DSR/scfv_dsr/contable/modelos.py (recortado).
Se eliminaron los modelos relacionados con H2 (ConsecuenciaAutorizada).
Se agregaron Asiento y LineaAsiento como versiones tipadas de los
dicts que devuelve mnfc.procesar_asiento.

Sin dependencias externas. Solo stdlib.
"""

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation


@dataclass
class ContextoContable:
    """Contexto bajo el cual se interpreta un asiento."""

    marco_contable: str
    PCU_version: str
    reglas_version: str
    politica_monetaria_version: str


@dataclass(init=False)
class PartidaAutorizada:
    """Linea de un asiento con todos sus metadatos.

    Fuente de verdad: monto_cent (int, centavos). Field serializable.
    monto es @property derivada (compat hasta 2.6).

    __init__ acepta monto= (pesos: int/float/Decimal/str) o monto_cent= (int).
    Preserva raw para valores inválidos (bool, string, negativo, inf, nan,
    no numérico) para que _validar_monto los rechace con el mensaje correcto.
    """

    cuenta_codigo: str
    cuenta_version: str
    monto_cent: int
    ubicacion: str
    movimiento: str
    moneda: str | None = "VES"
    es_fiscal: bool = False
    norma_id: str | None = None

    def __init__(
        self,
        cuenta_codigo: str,
        cuenta_version: str,
        monto=None,
        ubicacion: str = "DEBE",
        movimiento: str = "AUMENTA",
        moneda: str | None = "VES",
        es_fiscal: bool = False,
        norma_id: str | None = None,
        monto_cent=None,
    ):
        self.cuenta_codigo = cuenta_codigo
        self.cuenta_version = cuenta_version
        self.ubicacion = ubicacion
        self.movimiento = movimiento
        self.moneda = moneda
        self.es_fiscal = es_fiscal
        self.norma_id = norma_id
        self.monto_cent = 0

        if monto is not None and monto_cent is not None:
            raise TypeError(
                "PartidaAutorizada: especificar solo uno de monto o monto_cent"
            )
        if monto is None and monto_cent is None:
            raise TypeError(
                "PartidaAutorizada: se requiere monto o monto_cent"
            )

        if monto_cent is not None:
            if isinstance(monto_cent, bool) or not isinstance(monto_cent, int):
                raise TypeError(
                    f"monto_cent debe ser int, no {type(monto_cent).__name__}"
                )
            self.monto_cent = monto_cent
            return

        # monto: preservar raw para inválidos; convertir a centavos para válidos
        if isinstance(monto, bool):
            self._monto_raw = monto
            return
        if isinstance(monto, str):
            # Fase 2: string no es monto válido (ADR-005 decisión 2)
            self._monto_raw = monto
            return
        if not isinstance(monto, (int, float, Decimal)):
            self._monto_raw = monto
            return
        try:
            dec = Decimal(str(monto))
        except Exception:
            self._monto_raw = monto
            return
        if not dec.is_finite():
            self._monto_raw = monto
            return
        # Preservar raw si es negativo (incluye -0.001 que redondearía a 0)
        if dec < 0:
            self._monto_raw = monto
            return

        from ..money import to_centimos
        try:
            self.monto_cent = to_centimos(dec)
        except (InvalidOperation, OverflowError, ValueError):
            self._monto_raw = monto
            return

    @property
    def monto(self):
        """Compatibilidad. Devuelve raw si inválido; float derivado si no."""
        raw = getattr(self, "_monto_raw", None)
        if raw is not None:
            return raw
        return self.monto_cent / 100.0

@dataclass(init=False)
class LineaAsiento:
    """Linea de un asiento procesado (version tipada).

    Fuente de verdad: monto_cent (int, centavos). Field serializable.
    monto es @property derivada (compat hasta 2.6).

    __init__ acepta:
        LineaAsiento("A", "DEBE", 100.50)                   # posicional (compat)
        LineaAsiento(cuenta="A", ubicacion="DEBE", monto=100.50)
        LineaAsiento(cuenta="A", ubicacion="DEBE", monto_cent=10050)

    Ver ADR-006.
    """

    cuenta: str
    ubicacion: str
    monto_cent: int
    naturaleza: str | None = None
    movimiento: str | None = None

    def __init__(
        self,
        cuenta: str,
        ubicacion: str,
        monto=None,
        monto_cent=None,
        naturaleza: str | None = None,
        movimiento: str | None = None,
    ):
        self.cuenta = cuenta
        self.ubicacion = ubicacion
        self.naturaleza = naturaleza
        self.movimiento = movimiento
        self.monto_cent = 0

        if monto is not None and monto_cent is not None:
            raise TypeError(
                "LineaAsiento: especificar solo uno de monto o monto_cent"
            )
        if monto is None and monto_cent is None:
            raise TypeError(
                "LineaAsiento: se requiere monto o monto_cent"
            )

        if monto_cent is not None:
            if isinstance(monto_cent, bool) or not isinstance(monto_cent, int):
                raise TypeError(
                    f"monto_cent debe ser int, no {type(monto_cent).__name__}"
                )
            self.monto_cent = monto_cent
            return

        # monto: intentar convertir a centavos; si falla, dejar 0 y preservar raw
        if isinstance(monto, bool):
            self._monto_raw = monto
            return
        if not isinstance(monto, (int, float, Decimal, str)):
            self._monto_raw = monto
            return
        try:
            dec = Decimal(str(monto))
        except Exception:
            self._monto_raw = monto
            return
        if not dec.is_finite():
            self._monto_raw = monto
            return

        from ..money import to_centimos
        from decimal import InvalidOperation
        try:
            self.monto_cent = to_centimos(dec)
        except (InvalidOperation, OverflowError):
            self._monto_raw = monto
            return

    @property
    def monto(self) -> float:
        """Compatibilidad. Devuelve raw si inválido; float derivado si no."""
        raw = getattr(self, "_monto_raw", None)
        if raw is not None:
            return raw
        return float(self.monto_cent) / 100.0

@dataclass
class Asiento:
    """Asiento procesado por MNFC (version tipada).

    Fuente de verdad: total_debe_cent / total_haber_cent (int, centavos).
    total_debe / total_haber son @property derivadas (compat hasta 2.6).

    Constructor acepta:
        Asiento(..., total_debe=100.00, total_haber=100.00)          # compat
        Asiento(..., total_debe_cent=10000, total_haber_cent=10000)  # preferido

    Valores inválidos (inf, nan, bool) se preservan en _total_*_raw
    para que _verificar_cuadre los detecte correctamente.
    """

    lineas: list[LineaAsiento] = field(default_factory=list)
    cuadrado: bool = False
    contexto: ContextoContable | None = None

    def __init__(
        self,
        lineas=None,
        cuadrado: bool = False,
        contexto=None,
        total_debe=None,
        total_haber=None,
        total_debe_cent=None,
        total_haber_cent=None,
    ):
        self.lineas = lineas if lineas is not None else []
        self.cuadrado = cuadrado
        self.contexto = contexto
        self._total_debe_raw = None
        self._total_haber_raw = None
        self._total_debe_cent = 0
        self._total_haber_cent = 0

        # Resolver total_debe
        if total_debe is not None and total_debe_cent is not None:
            raise TypeError("Asiento: especificar solo total_debe o total_debe_cent")
        if total_debe_cent is not None:
            if isinstance(total_debe_cent, bool) or not isinstance(total_debe_cent, int):
                raise TypeError(
                    f"total_debe_cent debe ser int, no {type(total_debe_cent).__name__}"
                )
            self._total_debe_cent = total_debe_cent
        elif total_debe is not None:
            self._resolver_total("debe", total_debe)

        # Resolver total_haber
        if total_haber is not None and total_haber_cent is not None:
            raise TypeError("Asiento: especificar solo total_haber o total_haber_cent")
        if total_haber_cent is not None:
            if isinstance(total_haber_cent, bool) or not isinstance(total_haber_cent, int):
                raise TypeError(
                    f"total_haber_cent debe ser int, no {type(total_haber_cent).__name__}"
                )
            self._total_haber_cent = total_haber_cent
        elif total_haber is not None:
            self._resolver_total("haber", total_haber)

    def _resolver_total(self, lado: str, valor) -> None:
        """Convierte total a centavos, o preserva raw si es inválido (inf, nan, bool)."""
        raw_attr = f"_total_{lado}_raw"
        cent_attr = f"_total_{lado}_cent"

        if isinstance(valor, bool):
            setattr(self, raw_attr, valor)
            return
        try:
            dec = Decimal(str(valor))
        except Exception:
            setattr(self, raw_attr, valor)
            return
        if not dec.is_finite():
            setattr(self, raw_attr, valor)
            return

        from ..money import to_centimos
        setattr(self, cent_attr, to_centimos(dec))

    @property
    def total_debe_cent(self) -> int:
        return self._total_debe_cent

    @property
    def total_haber_cent(self) -> int:
        return self._total_haber_cent

    @property
    def total_debe(self):
        """Compatibilidad. Devuelve raw si inf/nan/bool; float derivado si no."""
        if self._total_debe_raw is not None:
            return self._total_debe_raw
        return float(self._total_debe_cent) / 100.0

    @property
    def total_haber(self):
        if self._total_haber_raw is not None:
            return self._total_haber_raw
        return float(self._total_haber_cent) / 100.0

    @property
    def cuadrado_cent(self) -> bool:
        return self.total_debe_cent == self.total_haber_cent

    def __repr__(self) -> str:
        estado = "cuadrado" if self.cuadrado else "DESCUADRADO"
        return "Asiento(n=%d, debe=%s, haber=%s, %s)" % (
            len(self.lineas),
            self.total_debe,
            self.total_haber,
            estado,
        )
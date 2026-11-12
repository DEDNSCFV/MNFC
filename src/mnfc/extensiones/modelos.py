"""
MNFC v0.2.0 - Capa 7 - Modelos tipados del dominio contable.

Migrado de SCFV_DSR/scfv_dsr/contable/modelos.py (recortado).
Se eliminaron los modelos relacionados con H2 (ConsecuenciaAutorizada).
Se agregaron Asiento y LineaAsiento como versiones tipadas de los
dicts que devuelve mnfc.procesar_asiento.

Sin dependencias externas. Solo stdlib.
"""

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class ContextoContable:
    """Contexto bajo el cual se interpreta un asiento."""

    marco_contable: str
    PCU_version: str
    reglas_version: str
    politica_monetaria_version: str


@dataclass
class PartidaAutorizada:
    """Linea de un asiento con todos sus metadatos."""

    cuenta_codigo: str
    cuenta_version: str
    monto: float
    ubicacion: str
    movimiento: str
    moneda: str | None = "VES"
    es_fiscal: bool = False
    norma_id: str | None = None

    @property
    def monto_cent(self) -> int:
        """Derivado. Fuente de verdad sigue siendo monto (float) hasta 2.4."""
        from ..money import to_centimos
        return to_centimos(Decimal(str(self.monto)))


@dataclass
class LineaAsiento:
    """Linea de un asiento procesado por MNFC (version tipada)."""

    cuenta: str
    ubicacion: str
    monto: float
    naturaleza: str | None = None
    movimiento: str | None = None

    @property
    def monto_cent(self) -> int:
        from ..money import to_centimos
        return to_centimos(Decimal(str(self.monto)))


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
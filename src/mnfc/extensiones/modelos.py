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
    """Asiento procesado por MNFC (version tipada)."""

    lineas: list[LineaAsiento] = field(default_factory=list)
    total_debe: float = 0.0
    total_haber: float = 0.0
    cuadrado: bool = False
    contexto: ContextoContable | None = None

    @property
    def total_debe_cent(self) -> int:
        from ..money import to_centimos
        return to_centimos(Decimal(str(self.total_debe)))

    @property
    def total_haber_cent(self) -> int:
        from ..money import to_centimos
        return to_centimos(Decimal(str(self.total_haber)))

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

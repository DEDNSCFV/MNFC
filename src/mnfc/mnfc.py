"""
Capa 4 - Composicion - el PROCESO.

Recibe lineas contables, clasifica DEBE/HABER, acumula, verifica cuadre.
No persiste (eso es capa 6). No reporta.

Estado epistemico:
    N4 - aplicada (dominio contable)

Frontera: el modulo no decide contabilidad por si mismo. Delega en
xnor (capa 0) para clasificar y en baldor (capa 1) para verificar.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from .baldor import verificar_cuadre
from .money import to_centimos, to_decimal
from .xnor import calcular_ubicacion


@dataclass
class Asiento:
    """Asiento contable procesado.

    Fuente de verdad: total_debe_cent / total_haber_cent (int, centavos).
    total_debe / total_haber son @property derivadas (compat hasta 2.6).
    """

    lineas: list[dict[str, Any]] = field(default_factory=list)
    total_debe_cent: int = 0
    total_haber_cent: int = 0
    cuadrado: bool = False

    @property
    def total_debe(self) -> float:
        """Compatibilidad. Se elimina en 2.6."""
        return float(self.total_debe_cent) / 100.0

    @property
    def total_haber(self) -> float:
        """Compatibilidad. Se elimina en 2.6."""
        return float(self.total_haber_cent) / 100.0

    @property
    def cuadrado_cent(self) -> bool:
        return self.total_debe_cent == self.total_haber_cent

    def __repr__(self) -> str:
        estado = "cuadrado" if self.cuadrado else "DESCUADRADO"
        return (
            f"Asiento(n={len(self.lineas)}, "
            f"debe_cent={self.total_debe_cent}, "
            f"haber_cent={self.total_haber_cent}, {estado})"
        )

def procesar_asiento(lineas: list[dict[str, Any]]) -> Asiento:
    """Procesa una lista de lineas contables en centavos exactos.

    Cada linea debe tener:
        naturaleza: "DEUDORA" | "ACREEDORA"
        movimiento: "AUMENTA" | "DISMINUYE"
        monto: pesos (int/float/str/Decimal; se interpreta como PESOS)
        cuenta: str (opcional)

    Devuelve un Asiento cuadrado o lanza ValueError si no cuadra.
    """
    if not lineas:
        raise ValueError("asiento sin lineas")

    asiento = Asiento()
    for i, l in enumerate(lineas):
        for campo in ("naturaleza", "movimiento", "monto"):
            if campo not in l:
                raise ValueError(f"linea {i} sin campo '{campo}'")

        if isinstance(l["monto"], bool):
            raise ValueError(f"linea {i}: monto booleano no válido")

        # Interpretar SIEMPRE como pesos, sin importar el tipo de entrada.
        try:
            monto_dec = Decimal(str(l["monto"]))
        except Exception as e:
            raise ValueError(
                f"linea {i}: monto no convertible a Decimal: {l['monto']!r}"
            ) from e

        monto_cent = to_centimos(monto_dec)

        ubicacion = calcular_ubicacion(l["naturaleza"], l["movimiento"])
        asiento.lineas.append(
            {
                "cuenta": l.get("cuenta", f"linea_{i}"),
                "ubicacion": ubicacion,
                "monto_cent": monto_cent,
            }
        )
        if ubicacion == "DEBE":
            asiento.total_debe_cent += monto_cent
        else:
            asiento.total_haber_cent += monto_cent

    if asiento.total_debe_cent != asiento.total_haber_cent:
        dif = abs(asiento.total_debe_cent - asiento.total_haber_cent)
        raise ValueError(
            f"asiento descuadrado: "
            f"DEBE={to_decimal(asiento.total_debe_cent)} "
            f"HABER={to_decimal(asiento.total_haber_cent)} "
            f"(dif={to_decimal(dif)})"
        )
    asiento.cuadrado = True
    return asiento
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
from typing import List, Dict, Any
from .xnor import calcular_ubicacion
from .baldor import verificar_cuadre


@dataclass
class Asiento:
    """Asiento contable procesado."""
    lineas: List[Dict[str, Any]] = field(default_factory=list)
    total_debe: float = 0.0
    total_haber: float = 0.0
    cuadrado: bool = False

    def __repr__(self) -> str:
        estado = "cuadrado" if self.cuadrado else "DESCUADRADO"
        return (f"Asiento(n={len(self.lineas)}, debe={self.total_debe}, "
                f"haber={self.total_haber}, {estado})")


def procesar_asiento(lineas: List[Dict[str, Any]]) -> Asiento:
    """
    Procesa una lista de lineas contables.

    Cada linea debe tener:
        naturaleza: "DEUDORA" | "ACREEDORA"
        movimiento: "AUMENTA" | "DISMINUYE"
        monto: float
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
        ubicacion = calcular_ubicacion(l["naturaleza"], l["movimiento"])
        monto = float(l["monto"])
        asiento.lineas.append({
            "cuenta": l.get("cuenta", f"linea_{i}"),
            "ubicacion": ubicacion,
            "monto": monto,
        })
        if ubicacion == "DEBE":
            asiento.total_debe += monto
        else:
            asiento.total_haber += monto

    if not verificar_cuadre(asiento.total_debe, asiento.total_haber):
        raise ValueError(
            f"asiento descuadrado: DEBE={asiento.total_debe} "
            f"HABER={asiento.total_haber}"
        )
    asiento.cuadrado = True
    return asiento

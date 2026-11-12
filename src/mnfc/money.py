"""
Módulo único de dinero. Todo monto monetario pasa por aquí.

Reglas duras:
- Almacenamiento: int (centavos).
- Cálculo: Decimal + ROUND_HALF_EVEN (redondeo bancario).
- float: prohibido en la frontera. Se rechaza con TypeError.
"""
from decimal import Decimal, ROUND_HALF_EVEN, InvalidOperation
from typing import Union

CENT = Decimal("0.01")
MontoInput = Union[int, Decimal, str]


def _rechazar_bool(x) -> None:
    if isinstance(x, bool):
        raise TypeError(f"bool no es un monto válido: {x!r}")


def to_centimos(x: MontoInput) -> int:
    """Convierte a centavos enteros. Rechaza float explícitamente."""
    _rechazar_bool(x)
    if isinstance(x, int):
        return x
    if isinstance(x, float):
        raise TypeError(
            f"Prohibido float en montos contables: {x!r}. "
            "Usa Decimal('...'), str, o int en centavos."
        )
    if isinstance(x, str):
        try:
            x = Decimal(x)
        except InvalidOperation as e:
            raise ValueError(f"str no convertible a Decimal: {x!r}") from e
    if not isinstance(x, Decimal):
        raise TypeError(f"Tipo no soportado: {type(x).__name__}")
    return int((x * 100).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))


def to_decimal(centimos: int) -> Decimal:
    """Convierte centavos enteros a Decimal con 2 decimales."""
    if isinstance(centimos, bool) or not isinstance(centimos, int):
        raise TypeError(f"centimos debe ser int, no {type(centimos).__name__}")
    return (Decimal(centimos) / 100).quantize(CENT)


def to_str(centimos: int) -> str:
    return str(to_decimal(centimos))


def sumar(*centimos_list: int) -> int:
    return sum(centimos_list)


def iva(monto_cent: int, tasa) -> tuple:
    """
    Base e IVA a partir de un monto con IVA incluido.
    Garantiza base_cent + iva_cent == monto_cent (exacto).
    """
    monto = Decimal(monto_cent)
    if isinstance(tasa, (int, str)):
        tasa = Decimal(tasa)
    if tasa > 1:
        tasa = tasa / 100
    divisor = Decimal(1) + tasa
    base_cent = int((monto / divisor).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))
    iva_cent = monto_cent - base_cent
    return base_cent, iva_cent

"""Puente de dinero. Rechaza float. Delega en money.py."""
from .money import to_centimos, to_decimal, to_str, iva


def a_centimos(monto) -> int:
    return to_centimos(monto)


def a_decimal(centimos: int):
    return to_decimal(centimos)


def calcular_base_e_iva_centimos(monto_cent: int, tasa) -> tuple:
    return iva(monto_cent, tasa)

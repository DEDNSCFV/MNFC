"""Puente de dinero. Rechaza float. Delega en money.py."""

from .money import iva, to_centimos, to_decimal


def a_centimos(monto) -> int:
    return to_centimos(monto)


def a_decimal(centimos: int):
    return to_decimal(centimos)


def calcular_base_e_iva_centimos(monto_cent: int, tasa) -> tuple:
    return iva(monto_cent, tasa)

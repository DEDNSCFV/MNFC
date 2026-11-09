"""Verificación contable en céntimos enteros. Reemplaza float en Baldor."""
from typing import List

def a_centimos(monto: float) -> int:
    return int(round(monto * 100))

def a_decimal(centimos: int) -> float:
    return centimos / 100.0

def sumar_montos_centimos(montos_cent: List[int]) -> int:
    return sum(montos_cent)  # exacto, sin error

def verificar_cuadre_centimos(debe_cent: int, haber_cent: int) -> bool:
    return debe_cent == haber_cent  # igualdad exacta, no tolerancia

def calcular_base_e_iva_centimos(monto_cent: int, tasa: float) -> tuple:
    base = int(round(monto_cent / (1.0 + tasa)))
    iva = monto_cent - base
    return base, iva  # base + iva == monto_cent, exacto

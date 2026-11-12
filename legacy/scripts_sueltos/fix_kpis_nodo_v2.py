#!/usr/bin/env python3
"""Corrige kpis_nodo_v4.py reescribiendo las secciones problemáticas."""
from pathlib import Path

src = Path.home() / "MNFC" / "kpis_nodo_v4.py"
texto = src.read_text(encoding='utf-8')

# Buscar el bloque donde se calcula valor_inv
# Imprimir las líneas con valor_inv para ver qué hay
lineas = texto.split('\n')
print("=== Líneas con 'valor_inv' ===")
for i, l in enumerate(lineas):
    if 'valor_inv' in l:
        print(f"  {i+1}: {l[:100]}")

print()
print("=== Líneas con 'stock_central' ===")
for i, l in enumerate(lineas):
    if 'stock_central' in l:
        print(f"  {i+1}: {l[:100]}")

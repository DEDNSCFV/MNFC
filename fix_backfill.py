#!/usr/bin/env python3
"""Corrige el bug de fechas en backfill.py"""
from pathlib import Path

src = Path.home() / "MNFC" / "backfill.py"
dst = Path.home() / "MNFC" / "backfill_v2.py"

texto = src.read_text(encoding='utf-8')

# Fix 1: rango de fechas (MIN/MAX cronológico)
texto = texto.replace(
    'SELECT MIN(fecha), MAX(fecha) FROM movimientos_historico WHERE nodo=?',
    "SELECT MIN(SUBSTR(fecha,7,4)||'-'||SUBSTR(fecha,4,2)||'-'||SUBSTR(fecha,1,2)), MAX(SUBSTR(fecha,7,4)||'-'||SUBSTR(fecha,4,2)||'-'||SUBSTR(fecha,1,2)) FROM movimientos_historico WHERE nodo=?"
)

# Fix 2: parsear YYYY-MM-DD
texto = texto.replace("datetime.strptime(rango[0], '%d/%m/%Y')", "datetime.strptime(rango[0], '%Y-%m-%d')")
texto = texto.replace("datetime.strptime(rango[1], '%d/%m/%Y')", "datetime.strptime(rango[1], '%Y-%m-%d')")

# Fix 3: comparar fechas como YYYY-MM-DD en todas las consultas
texto = texto.replace(
    'AND fecha >= ? AND fecha <= ?',
    "AND SUBSTR(fecha,7,4)||'-'||SUBSTR(fecha,4,2)||'-'||SUBSTR(fecha,1,2) >= ? AND SUBSTR(fecha,7,4)||'-'||SUBSTR(fecha,4,2)||'-'||SUBSTR(fecha,1,2) <= ?"
)
texto = texto.replace(
    "fecha_desde.strftime('%d/%m/%Y')",
    "fecha_desde.strftime('%Y-%m-%d')"
)
texto = texto.replace(
    "fecha_hasta.strftime('%d/%m/%Y')",
    "fecha_hasta.strftime('%Y-%m-%d')"
)

dst.write_text(texto, encoding='utf-8')
print(f"Backfill corregido: {dst}")
print()

# Verificar los cambios
print("Verificación:")
for linea in dst.read_text(encoding='utf-8').split('\n'):
    if 'SUBSTR(fecha,7,4)' in linea or "strptime(rango" in linea:
        print(f"  {linea.strip()[:120]}")

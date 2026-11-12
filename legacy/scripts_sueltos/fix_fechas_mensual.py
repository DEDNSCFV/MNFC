#!/usr/bin/env python3
"""Corrige el filtro de fechas en libro_mensual.py usando YYYY-MM-DD."""
from pathlib import Path

src = Path.home() / "MNFC" / "libro_mensual.py"
texto = src.read_text(encoding='utf-8')

# Fix 1: agregar función fecha_iso
texto = texto.replace(
    "def fs(d): return d.strftime('%d/%m/%Y')",
    """def fs(d): return d.strftime('%d/%m/%Y')
def fiso(d): return d.strftime('%Y-%m-%d')
def mes_expr(col='fecha'):
    \"\"\"Expresión SQL que convierte DD/MM/YYYY a YYYY-MM-DD para comparar.\"\"\"
    return f"SUBSTR({col},7,4)||'-'||SUBSTR({col},4,2)||'-'||SUBSTR({col},1,2)\""""
)

# Fix 2: reemplazar todos los filtros de fecha
# Los que usan fs(primer_dia) y fs(ultimo_dia)
texto = texto.replace(
    "AND fecha>=? AND fecha<=?",
    "AND SUBSTR(fecha,7,4)||'-'||SUBSTR(fecha,4,2)||'-'||SUBSTR(fecha,1,2) >= ? AND SUBSTR(fecha,7,4)||'-'||SUBSTR(fecha,4,2)||'-'||SUBSTR(fecha,1,2) <= ?"
)
texto = texto.replace("AND mh.fecha>=? AND mh.fecha<=?", 
    "AND SUBSTR(mh.fecha,7,4)||'-'||SUBSTR(mh.fecha,4,2)||'-'||SUBSTR(mh.fecha,1,2) >= ? AND SUBSTR(mh.fecha,7,4)||'-'||SUBSTR(mh.fecha,4,2)||'-'||SUBSTR(mh.fecha,1,2) <= ?")

# Fix 3: reemplazar las llamadas a fs() por fiso() en los parámetros
texto = texto.replace("(NODO, fs(primer_dia), fs(ultimo_dia))", "(NODO, fiso(primer_dia), fiso(ultimo_dia))")
texto = texto.replace("(NODO, fs(primer_dia_ant), fs(ultimo_dia_ant))", "(NODO, fiso(primer_dia_ant), fiso(ultimo_dia_ant))")

dst = Path.home() / "MNFC" / "libro_mensual_v2.py"
dst.write_text(texto, encoding='utf-8')
print(f"Script corregido: {dst}")
print()
print("Verificando que todos los filtros usen fiso()...")

# Verificación
lineas = dst.read_text(encoding='utf-8').split('\n')
for i, l in enumerate(lineas):
    if 'BETWEEN' in l or ('>=' in l and 'fecha' in l.lower()):
        print(f"  {i+1}: {l.strip()[:100]}")

#!/usr/bin/env python3
"""Detecta qué períodos reales hay en el corpus."""
import sqlite3
from pathlib import Path
from collections import Counter
from datetime import datetime

DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"
conn = sqlite3.connect(DB)

print("=== RANGO DE FECHAS EN movimientos_historico ===")
r = conn.execute("SELECT MIN(fecha), MAX(fecha), COUNT(*) FROM movimientos_historico").fetchone()
print(f"  Min: {r[0]}")
print(f"  Max: {r[1]}")
print(f"  Total: {r[2]:,}")
print()

print("=== MOVIMIENTOS POR MES ===")
rows = conn.execute("""
    SELECT SUBSTR(fecha, 4, 2) || '/' || SUBSTR(fecha, 7, 4) AS mes,
           COUNT(*) AS n
    FROM movimientos_historico
    GROUP BY mes
    ORDER BY SUBSTR(fecha, 7, 4) || SUBSTR(fecha, 4, 2)
""").fetchall()
for mes, n in rows:
    print(f"  {mes}: {n:>8,}")
print()

print("=== ÚLTIMO DÍA CON MOVIMIENTOS ===")
r = conn.execute("""
    SELECT fecha, COUNT(*) FROM movimientos_historico
    GROUP BY fecha ORDER BY SUBSTR(fecha, 7, 4) || SUBSTR(fecha, 4, 2) || SUBSTR(fecha, 1, 2) DESC
    LIMIT 1
""").fetchone()
print(f"  Último día: {r[0]} — {r[1]} movimientos")
print()

print("=== ÚLTIMOS 7 DÍAS CON MOVIMIENTOS ===")
for fecha, n in conn.execute("""
    SELECT fecha, COUNT(*) FROM movimientos_historico
    GROUP BY fecha ORDER BY SUBSTR(fecha, 7, 4) || SUBSTR(fecha, 4, 2) || SUBSTR(fecha, 1, 2) DESC
    LIMIT 7
""").fetchall():
    print(f"  {fecha}: {n:>6,}")
print()

print("=== RANGO EN movimientos_sep (kardex agregado) ===")
r = conn.execute("SELECT COUNT(*), MIN(stock_inicial), MAX(stock_final) FROM movimientos_sep").fetchone()
print(f"  Filas: {r[0]:,}")
print(f"  (Sin fechas: es agregado por SKU, no por día)")
print()

print("=== RANGO EN ajustes_historico ===")
r = conn.execute("SELECT MIN(fecha), MAX(fecha), COUNT(*) FROM ajustes_historico").fetchone()
print(f"  Min: {r[0]}")
print(f"  Max: {r[1]}")
print(f"  Total: {r[2]:,}")
print()

print("=== RESUMEN DE PERÍODOS DISPONIBLES ===")
primer_mes = conn.execute("""
    SELECT SUBSTR(fecha, 4, 2) || '/' || SUBSTR(fecha, 7, 4) FROM movimientos_historico
    ORDER BY SUBSTR(fecha, 7, 4) || SUBSTR(fecha, 4, 2) ASC LIMIT 1
""").fetchone()[0]
ultimo_mes = conn.execute("""
    SELECT SUBSTR(fecha, 4, 2) || '/' || SUBSTR(fecha, 7, 4) FROM movimientos_historico
    ORDER BY SUBSTR(fecha, 7, 4) || SUBSTR(fecha, 4, 2) DESC LIMIT 1
""").fetchone()[0]
ultimo_dia = conn.execute("""
    SELECT fecha FROM movimientos_historico
    ORDER BY SUBSTR(fecha, 7, 4) || SUBSTR(fecha, 4, 2) || SUBSTR(fecha, 1, 2) DESC LIMIT 1
""").fetchone()[0]

print(f"  Histórico completo: {primer_mes} → {ultimo_mes}")
print(f"  Último día con datos: {ultimo_dia}")
print(f"  Última semana: 7 días previos a {ultimo_dia}")
print(f"  Último mes completo: mes anterior a {ultimo_mes}")

conn.close()

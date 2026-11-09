#!/usr/bin/env python3
"""Paso 2: Verifica si hay duplicados reales con la nueva clave."""
import sqlite3
from pathlib import Path

DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"
conn = sqlite3.connect(DB)

print("=" * 70)
print("  PASO 2 — VERIFICAR DUPLICADOS CON NUEVA CLAVE")
print("=" * 70)
print()

# Movimientos con numero_documento
r = conn.execute("""
    SELECT COUNT(*) FROM movimientos_historico
    WHERE numero_documento IS NOT NULL AND numero_documento != ''
""").fetchone()[0]
print(f"Movimientos con numero_documento: {r:,}")

r = conn.execute("SELECT COUNT(*) FROM movimientos_historico").fetchone()[0]
print(f"Total movimientos:                {r:,}")
print(f"Pendientes de poblar:             {r - r if False else 'todos (Paso 3)'}")
print()

# Duplicados por clave amplia (con stock_actual)
print("Duplicados por (sku, fecha, tipo, nodo, cantidad, costo, stock_actual):")
r = conn.execute("""
    SELECT COUNT(*) FROM (
        SELECT sku, fecha, tipo, nodo, cantidad, costo_unitario, stock_actual, COUNT(*) AS n
        FROM movimientos_historico
        GROUP BY sku, fecha, tipo, nodo, cantidad, costo_unitario, stock_actual
        HAVING n > 1
    )
""").fetchone()
print(f"  Grupos duplicados: {r[0]:,}")

# Ids repetidos (deberían ser 0)
r = conn.execute("SELECT COUNT(*) - COUNT(DISTINCT id) FROM movimientos_historico").fetchone()
print(f"  Ids repetidos:     {r[0]:,}")
print()

# Duplicados por nodo
print("Duplicados por nodo (con stock_actual):")
for nodo, n in conn.execute("""
    SELECT nodo, COUNT(*) FROM (
        SELECT nodo, COUNT(*) AS n
        FROM movimientos_historico
        GROUP BY sku, fecha, tipo, nodo, cantidad, costo_unitario, stock_actual
        HAVING n > 1
    ) GROUP BY nodo ORDER BY n DESC
""").fetchall():
    print(f"  {nodo:15s}: {n:,} grupos")
print()

# ¿Cuántos de esos grupos son de meses distintos? (probables transacciones reales)
print("Distribución de los duplicados por mes (top 5 meses):")
for mes, n in conn.execute("""
    SELECT SUBSTR(fecha,4,2)||'/'||SUBSTR(fecha,7,4) AS mes, COUNT(*) FROM (
        SELECT fecha, COUNT(*) AS n
        FROM movimientos_historico
        GROUP BY sku, fecha, tipo, nodo, cantidad, costo_unitario, stock_actual
        HAVING n > 1
    ) GROUP BY mes ORDER BY n DESC LIMIT 5
""").fetchall():
    print(f"  {mes}: {n:,} grupos")

conn.close()

#!/usr/bin/env python3
"""Verifica si hay movimientos duplicados en la BD actual."""
import sqlite3
from pathlib import Path

DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"
conn = sqlite3.connect(DB)

print("=" * 70)
print("  VERIFICACIÓN DE DUPLICADOS EN movimientos_historico")
print("=" * 70)
print()

# Total de movimientos
total = conn.execute("SELECT COUNT(*) FROM movimientos_historico").fetchone()[0]
print(f"Total de movimientos: {total:,}")
print()

# ¿Hay duplicados por (sku, fecha, tipo, nodo, cantidad, costo)?
r = conn.execute("""
    SELECT COUNT(*) FROM (
        SELECT sku, fecha, tipo, nodo, cantidad, costo_unitario, COUNT(*) AS n
        FROM movimientos_historico
        GROUP BY sku, fecha, tipo, nodo, cantidad, costo_unitario
        HAVING n > 1
    )
""").fetchone()
print(f"Grupos con duplicados exactos (sku+fecha+tipo+nodo+cantidad+costo): {r[0]:,}")

# ¿Cuántas filas sobran?
r = conn.execute("""
    SELECT SUM(n - 1) FROM (
        SELECT COUNT(*) AS n
        FROM movimientos_historico
        GROUP BY sku, fecha, tipo, nodo, cantidad, costo_unitario
        HAVING n > 1
    )
""").fetchone()
print(f"Filas duplicadas (sobrantes): {r[0] or 0:,}")
print()

# ¿Hay columnas de identificación única?
cols = conn.execute("PRAGMA table_info(movimientos_historico)").fetchall()
print("Columnas de movimientos_historico:")
for c in cols:
    print(f"  {c[1]:25s} {c[2]}")
print()

# ¿Hay índice único?
indices = conn.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='movimientos_historico'").fetchall()
print("Índices en movimientos_historico:")
for idx in indices:
    print(f"  {idx[0]}: {idx[1] or 'autoindex'}")
print()

# ¿Los duplicados se concentran en algún nodo?
print("Duplicados por nodo:")
for nodo, n in conn.execute("""
    SELECT nodo, COUNT(*) FROM (
        SELECT nodo, COUNT(*) AS n
        FROM movimientos_historico
        GROUP BY sku, fecha, tipo, nodo, cantidad, costo_unitario
        HAVING n > 1
    ) GROUP BY nodo ORDER BY n DESC
""").fetchall():
    print(f"  {nodo:15s}: {n:,} grupos")

conn.close()

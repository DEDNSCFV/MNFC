#!/usr/bin/env python3
"""Diagnóstico del Paso 3: por qué falla el match."""
import sqlite3
from pathlib import Path

DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"
conn = sqlite3.connect(DB)

NODO = "04 La Urbina"

print("=" * 70)
print(f"  DIAGNÓSTICO PASO 3 — {NODO}")
print("=" * 70)
print()

# 1. Tipos en la BD
print("[1/5] Tipos de movimiento en la BD:")
for tipo, total, con_doc in conn.execute("""
    SELECT tipo, COUNT(*) AS n, SUM(CASE WHEN numero_documento IS NOT NULL THEN 1 ELSE 0 END) AS c
    FROM movimientos_historico WHERE nodo = ?
    GROUP BY tipo ORDER BY COUNT(*) DESC
""", (NODO,)).fetchall():
    sin_doc = total - (con_doc or 0)
    print(f"  {tipo:6s}: {total:>7,} total | {(con_doc or 0):>7,} con doc | {sin_doc:>7,} SIN match")
print()

# 2. Meses de los sin match
print("[2/5] Meses de los movimientos SIN match:")
for mes, n in conn.execute("""
    SELECT SUBSTR(fecha,4,2)||'/'||SUBSTR(fecha,7,4) AS mes, COUNT(*) AS n
    FROM movimientos_historico
    WHERE nodo = ? AND numero_documento IS NULL
    GROUP BY mes ORDER BY mes
""", (NODO,)).fetchall():
    print(f"  {mes}: {n:,}")
print()

# 3. Muestra de 10 sin match
print("[3/5] Muestra de 10 movimientos SIN match:")
for row in conn.execute("""
    SELECT id, sku, tipo, fecha, cantidad, costo_unitario, stock_actual
    FROM movimientos_historico
    WHERE nodo = ? AND numero_documento IS NULL
    LIMIT 10
""", (NODO,)).fetchall():
    print(f"  id={row[0]:>6} | sku={row[1]:15s} | tipo={row[2]:5s} | fecha={row[3]} | cant={row[4]} | costo={row[5]} | stock={row[6]}")
print()

# 4. Duplicados entre los sin match
print("[4/5] Duplicados entre los movimientos SIN match:")
r = conn.execute("""
    SELECT COUNT(*) FROM (
        SELECT sku, fecha, tipo, cantidad, costo_unitario, stock_actual, COUNT(*) AS n
        FROM movimientos_historico
        WHERE nodo = ? AND numero_documento IS NULL
        GROUP BY sku, fecha, tipo, cantidad, costo_unitario, stock_actual
        HAVING COUNT(*) > 1
    )
""", (NODO,)).fetchone()[0]
print(f"  Grupos con duplicados entre los sin match: {r:,}")
print()

# 5. Top SKUs con más movimientos sin match
print("[5/5] Top 10 SKUs con más movimientos SIN match:")
for row in conn.execute("""
    SELECT sku, COUNT(*) AS n
    FROM movimientos_historico
    WHERE nodo = ? AND numero_documento IS NULL
    GROUP BY sku ORDER BY COUNT(*) DESC LIMIT 10
""", (NODO,)).fetchall():
    print(f"  {row[0]:20s}: {row[1]:,}")

conn.close()

#!/usr/bin/env python3
"""Verifica si stock_actual es del nodo o del consolidado."""
import sqlite3
from pathlib import Path

DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"
conn = sqlite3.connect(DB)

print("=" * 70)
print("  VERIFICACIÓN DE stock_actual — ¿NODO o CONSOLIDADO?")
print("=" * 70)
print()

# Tomar un SKU que sepamos que tiene stock
skus = conn.execute("""
    SELECT sku, nodo, MAX(id) AS max_id
    FROM movimientos_historico
    GROUP BY sku, nodo
    LIMIT 5
""").fetchall()

for sku, nodo, max_id in skus:
    print(f"SKU: {sku}")
    print(f"  Último movimiento en nodo: {nodo} (id {max_id})")
    
    # Ver stock_actual del último movimiento en cada nodo
    rows = conn.execute("""
        SELECT nodo, stock_actual, tipo, fecha
        FROM movimientos_historico
        WHERE sku = ?
        ORDER BY id DESC LIMIT 5
    """, (sku,)).fetchall()
    
    for n, s, t, f in rows:
        print(f"    {f} | {n:15s} | {t:5s} | stock_actual: {s}")
    
    # Comparar con stock_central
    sc = conn.execute("SELECT stock FROM stock_central WHERE codigo = ?", (sku,)).fetchone()
    if sc:
        print(f"  stock_central: {sc[0]}")
    print()

conn.close()

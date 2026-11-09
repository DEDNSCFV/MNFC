#!/usr/bin/env python3
"""
Verifica si la suma de los valores de los 4 nodos coincide con el global.
Si coincide: el cálculo es correcto.
Si no coincide: hay inflación o desactualización.
"""
import sqlite3
from pathlib import Path

DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"
conn = sqlite3.connect(DB)

NODOS = ["01 Central", "04 La Urbina", "05 Cúa", "06 TERE"]

print("=" * 70)
print("  VERIFICACIÓN: SUMA DE NODOS vs GLOBAL")
print("=" * 70)
print()

# Costos
costos = dict(conn.execute("SELECT codigo, costo_unitario_usd FROM maestro_sku WHERE costo_unitario_usd > 0").fetchall())

# Valor global (del maestro)
global_valor = conn.execute("""
    SELECT SUM(stock_central * costo_unitario_usd) FROM maestro_sku
    WHERE stock_central > 0 AND costo_unitario_usd > 0
""").fetchone()[0] or 0
print(f"Valor global (maestro): ${global_valor:,.2f}")
print()

# Valor por nodo
total_nodos = 0
for nodo in NODOS:
    # Stock del último movimiento por SKU en el nodo
    stock_nodo = {}
    for sku, stock in conn.execute("""
        SELECT mh.sku, mh.stock_actual
        FROM movimientos_historico mh
        INNER JOIN (
            SELECT sku, MAX(id) AS max_id
            FROM movimientos_historico WHERE nodo = ?
            GROUP BY sku
        ) latest ON mh.sku = latest.sku AND mh.id = latest.max_id
        WHERE mh.nodo = ?
    """, (nodo, nodo)).fetchall():
        if stock is not None:
            stock_nodo[sku] = stock

    valor_nodo = sum(max(0, s) * costos.get(sku, 0) for sku, s in stock_nodo.items())
    skus_con_stock = sum(1 for s in stock_nodo.values() if s > 0)
    total_nodos += valor_nodo
    print(f"  {nodo:15s}: ${valor_nodo:>15,.2f} ({skus_con_stock:,} SKUs con stock)")

print()
print(f"Suma de los 4 nodos: ${total_nodos:,.2f}")
print(f"Valor global:        ${global_valor:,.2f}")
print(f"Diferencia:          ${total_nodos - global_valor:,.2f}")
print()

if abs(total_nodos - global_valor) / global_valor < 0.05:
    print("✅ La suma coincide con el global (diferencia < 5%)")
    print("   El cálculo por nodo es correcto.")
else:
    print("⚠️ La suma NO coincide con el global")
    print(f"   Diferencia: {100*(total_nodos-global_valor)/global_valor:.1f}%")
    print("   El cálculo por nodo tiene inflación o desactualización.")

conn.close()

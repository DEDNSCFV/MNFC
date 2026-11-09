#!/usr/bin/env python3
"""Corrige kpis_nodo_v3.py para que use el stock del nodo, no el global."""
from pathlib import Path

src = Path.home() / "MNFC" / "kpis_nodo_v3.py"
texto = src.read_text(encoding='utf-8')

# Reemplazar el cálculo de valor del inventario
texto = texto.replace(
    '''# Valor del inventario: SOLO Central tiene stock desagregado
if NODO == "01 Central":
    r = conn.execute("""
        SELECT SUM(stock_central * costo_unitario_usd) FROM maestro_sku
        WHERE stock_central > 0 AND costo_unitario_usd > 0
    """).fetchone()
    valor_inv = r[0] or 0
    tiene_stock_nodo = True
else:
    # Para los otros nodos, no hay stock desagregado
    valor_inv = 0
    tiene_stock_nodo = False''',
    '''# Valor del inventario: reconstruir desde stock_actual del nodo
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
""", (NODO, NODO)).fetchall():
    if stock is not None:
        stock_nodo[sku] = stock

costos = dict(conn.execute("SELECT codigo, costo_unitario_usd FROM maestro_sku WHERE costo_unitario_usd > 0").fetchall())
valor_inv = sum(max(0, s) * costos.get(sku, 0) for sku, s in stock_nodo.items())
tiene_stock_nodo = True'''
)

dst = Path.home() / "MNFC" / "kpis_nodo_v4.py"
dst.write_text(texto, encoding='utf-8')
print(f"Script corregido: {dst}")

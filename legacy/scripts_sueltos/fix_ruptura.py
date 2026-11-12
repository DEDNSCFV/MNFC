#!/usr/bin/env python3
"""Reemplaza el bucle lento de Tiempo hasta Ruptura por una sola consulta."""
from pathlib import Path

src = Path.home() / "MNFC" / "kpis_nodo_v2.py"
texto = src.read_text(encoding='utf-8')

# Reemplazar el bucle por una consulta única
texto = texto.replace(
    '''# Tiempo hasta Ruptura (ahora con stock_actual real)
dias_ruptura = []
for sku, stock in stock_nodo.items():
    if stock <= 0 or costos.get(sku, 0) <= 0:
        continue
    r = conn.execute("SELECT COUNT(*) FROM movimientos_historico WHERE sku=? AND tipo='FACT' AND nodo=?", (sku, NODO)).fetchone()
    n_fact = r[0] or 0
    if n_fact > 0:
        dias = stock / (n_fact / 240)
        dias_ruptura.append((sku, stock, dias, costos.get(sku, 0) * stock))

if dias_ruptura:
    dias_ruptura.sort(key=lambda x: -x[3])
    top_20 = dias_ruptura[:20]
    prom = sum(d[2] for d in top_20) / len(top_20)
    kpis[18] = K(18, "Tiempo hasta Ruptura", 3, "CALCULADO", round(prom, 1), "días",
        "Stock / Demanda diaria", "> 30 días",
        f"Promedio top 20 SKUs: {prom:.1f} días")
else:
    kpis[18] = K(18, "Tiempo hasta Ruptura", 3, "REQUIERE DATO", None, "días", "Stock / Demanda", "> 30 días", "Sin datos")''',
    '''# Tiempo hasta Ruptura: una sola consulta (no bucle)
facturas_por_sku = dict(conn.execute("""
    SELECT sku, COUNT(*) FROM movimientos_historico
    WHERE tipo='FACT' AND nodo=?
    GROUP BY sku
""", (NODO,)).fetchall())

dias_ruptura = []
for sku, stock in stock_nodo.items():
    if stock <= 0 or costos.get(sku, 0) <= 0:
        continue
    n_fact = facturas_por_sku.get(sku, 0)
    if n_fact > 0:
        dias = stock / (n_fact / 240)
        dias_ruptura.append((sku, stock, dias, costos.get(sku, 0) * stock))

if dias_ruptura:
    dias_ruptura.sort(key=lambda x: -x[3])
    top_20 = dias_ruptura[:20]
    prom = sum(d[2] for d in top_20) / len(top_20)
    kpis[18] = K(18, "Tiempo hasta Ruptura", 3, "CALCULADO", round(prom, 1), "días",
        "Stock / Demanda diaria", "> 30 días",
        f"Promedio top 20 SKUs: {prom:.1f} días")
else:
    kpis[18] = K(18, "Tiempo hasta Ruptura", 3, "REQUIERE DATO", None, "días", "Stock / Demanda", "> 30 días", "Sin datos")'''
)

dst = Path.home() / "MNFC" / "kpis_nodo_v3.py"
dst.write_text(texto, encoding='utf-8')
print(f"Script corregido: {dst}")
print("El bucle se reemplazó por 1 consulta en vez de 7,511.")

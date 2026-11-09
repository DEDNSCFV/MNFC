#!/usr/bin/env python3
"""Corrige los KPIs 10 (Obsolescencia) y 18 (Tiempo hasta Ruptura) en kpis_nodo_v4.py."""
from pathlib import Path

src = Path.home() / "MNFC" / "kpis_nodo_v4.py"
texto = src.read_text(encoding='utf-8')

# Fix KPI 10 (Obsolescencia): usar "sin venta en 3 meses", no "sin venta nunca"
texto = texto.replace(
    '''pct_obs = pct_inm  # mismo cálculo que inmovilizado
kpis[10] = K(10, "Obsolescencia", 2, "CALCULADO", pct_obs, "%",
    "(Costo obsoletos / Costo total) × 100", "< 20%",
    f"{pct_obs}% del valor en SKUs sin venta.")''',
    '''# Obsolescencia: SKUs sin venta en los últimos 3 meses (agosto-octubre 2026)
obsoletos = []
for sku in stock_nodo:
    if stock_nodo[sku] <= 0:
        continue
    # Buscar última venta
    ult = conn.execute("""
        SELECT MAX(fecha) FROM movimientos_historico
        WHERE sku = ? AND tipo = 'FACT' AND nodo = ?
    """, (sku, NODO)).fetchone()
    ultima = ult[0] if ult else None
    if not ultima or (ultima[6:10] + ultima[3:5] < '202607'):
        obsoletos.append(sku)

valor_obs = sum(max(0, stock_nodo.get(s, 0)) * costos.get(s, 0) for s in obsoletos)
pct_obs = round(100.0 * valor_obs / valor_inv, 1) if valor_inv else 0
kpis[10] = K(10, "Obsolescencia", 2, "CALCULADO", pct_obs, "%",
    "(Costo obsoletos / Costo total) × 100", "< 20%",
    f"{pct_obs}% del valor en SKUs sin venta en los últimos 3 meses. {len(obsoletos)} SKUs obsoletos, ${valor_obs:,.2f}.")'''
)

# Fix KPI 18 (Tiempo hasta Ruptura): acotar a 365 días
texto = texto.replace(
    '''if dias_ruptura:
    dias_ruptura.sort(key=lambda x: -x[3])
    top_20 = dias_ruptura[:20]
    prom = sum(d[2] for d in top_20) / len(top_20)
    kpis[18] = K(18, "Tiempo hasta Ruptura", 3, "CALCULADO", round(prom, 1), "días",
        "Stock / Demanda diaria", "> 30 días",
        f"Promedio top 20 SKUs: {prom:.1f} días")
else:
    kpis[18] = K(18, "Tiempo hasta Ruptura", 3, "REQUIERE DATO", None, "días", "Stock / Demanda", "> 30 días", "Sin datos")''',
    '''if dias_ruptura:
    dias_ruptura.sort(key=lambda x: -x[3])
    top_20 = dias_ruptura[:20]
    # Acotar cada uno a 365 días antes de promediar
    dias_acotados = [min(d[2], 365) for d in top_20]
    prom = sum(dias_acotados) / len(dias_acotados)
    kpis[18] = K(18, "Tiempo hasta Ruptura", 3, "CALCULADO", round(prom, 1), "días",
        "Stock / Demanda diaria (acotado a 365 días)", "> 30 días",
        f"Promedio top 20 SKUs: {prom:.1f} días (acotado). Sin acotar: {max(d[2] for d in top_20):.0f} días máx.")
else:
    kpis[18] = K(18, "Tiempo hasta Ruptura", 3, "REQUIERE DATO", None, "días", "Stock / Demanda", "> 30 días", "Sin datos")'''
)

dst = Path.home() / "MNFC" / "kpis_nodo_v5.py"
dst.write_text(texto, encoding='utf-8')
print(f"Script corregido: {dst}")

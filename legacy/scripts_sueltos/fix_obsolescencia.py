#!/usr/bin/env python3
"""Corrige el KPI 10 (Obsolescencia) en kpis_nodo_v5.py por reescritura directa."""
from pathlib import Path

src = Path.home() / "MNFC" / "kpis_nodo_v5.py"
texto = src.read_text(encoding='utf-8')

# Buscar la línea exacta del KPI 10
lineas = texto.split('\n')
nuevas = []
en_kpi10 = False
saltar_hasta = 0

for i, linea in enumerate(lineas):
    if saltar_hasta > 0:
        saltar_hasta -= 1
        continue
    if 'kpis[10]' in linea or ('pct_obs' in linea and 'K(10' not in linea):
        # Encontramos el bloque del KPI 10, reemplazarlo
        nuevas.append('# KPI 10 — Obsolescencia (corregido: sin venta en 3 meses)')
        nuevas.append('obsoletos = []')
        nuevas.append('for sku in stock_nodo:')
        nuevas.append('    if stock_nodo[sku] <= 0:')
        nuevas.append('        continue')
        nuevas.append('    ult = conn.execute("SELECT MAX(fecha) FROM movimientos_historico WHERE sku=? AND tipo=\'FACT\' AND nodo=?", (sku, NODO)).fetchone()')
        nuevas.append('    ultima = ult[0] if ult else None')
        nuevas.append('    if not ultima or (ultima[6:10] + ultima[3:5] < \'202607\'):')
        nuevas.append('        obsoletos.append(sku)')
        nuevas.append('valor_obs = sum(max(0, stock_nodo.get(s, 0)) * costos.get(s, 0) for s in obsoletos)')
        nuevas.append('pct_obs = round(100.0 * valor_obs / valor_inv, 1) if valor_inv else 0')
        nuevas.append('kpis[10] = K(10, "Obsolescencia", 2, "CALCULADO", pct_obs, "%",')
        nuevas.append('    "(Costo obsoletos / Costo total) × 100", "< 20%",')
        nuevas.append('    f"{pct_obs}% en SKUs sin venta 3 meses ({len(obsoletos)} SKUs, ${valor_obs:,.2f})")')
        # Saltar las líneas del bloque original (hasta encontrar kpis[10] cerrado o siguiente KPI)
        saltar_hasta = 3
        en_kpi10 = True
    else:
        nuevas.append(linea)

dst = Path.home() / "MNFC" / "kpis_nodo_v6.py"
dst.write_text('\n'.join(nuevas), encoding='utf-8')
print(f"Script corregido: {dst}")

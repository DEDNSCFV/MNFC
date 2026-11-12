#!/usr/bin/env python3
"""
24 KPIs por nodo usando stock_actual de la última transacción.
Uso: python kpis_nodo_v2.py "<nodo_db>" "<nodo_tecnico>"
"""
import sys, json
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

if len(sys.argv) < 2:
    print("Uso: python kpis_nodo_v2.py '<nodo_db>' ['<nodo_tecnico>']")
    sys.exit(1)

NODO = sys.argv[1]
NODO_TEC = sys.argv[2] if len(sys.argv) > 2 else NODO.replace(" ", "_")
DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"
BASE = Path.home() / "DARTONY_CONTROL" / NODO_TEC / "control" / "kpis"
FECHA = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
BASE.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(DB)

kpis = {}

def K(id, nombre, nivel, estado, valor, unidad, formula, benchmark, nota, donde=None, accion=None):
    return {'id': id, 'nombre': nombre, 'nivel': nivel, 'estado': estado,
            'valor': valor, 'unidad': unidad, 'formula': formula,
            'benchmark': benchmark, 'nota': nota,
            'donde_buscar': donde, 'accion': accion,
            'nodo': NODO, 'fecha': FECHA}

# ============================================================
# STOCK CORRECTO: stock_actual de la última transacción por SKU
# ============================================================
stock_nodo = {}
for sku, stock in conn.execute("""
    SELECT mh.sku, mh.stock_actual
    FROM movimientos_historico mh
    INNER JOIN (
        SELECT sku, MAX(id) AS max_id
        FROM movimientos_historico
        WHERE nodo = ?
        GROUP BY sku
    ) latest ON mh.sku = latest.sku AND mh.id = latest.max_id
    WHERE mh.nodo = ?
""", (NODO, NODO)).fetchall():
    if stock is not None:
        stock_nodo[sku] = stock

costos = dict(conn.execute("SELECT codigo, costo_unitario_usd FROM maestro_sku WHERE costo_unitario_usd > 0").fetchall())

valor_inv = sum(max(0, s) * costos.get(sku, 0) for sku, s in stock_nodo.items())
skus_con_stock = sum(1 for s in stock_nodo.values() if s > 0)

# Costo de ventas del nodo (8 meses)
r = conn.execute("""
    SELECT SUM(ABS(mh.cantidad) * ms.costo_unitario_usd)
    FROM movimientos_historico mh
    JOIN maestro_sku ms ON ms.codigo = mh.sku
    WHERE mh.tipo = 'FACT' AND mh.cantidad < 0 AND ms.costo_unitario_usd > 0 AND mh.nodo = ?
""", (NODO,)).fetchone()
costo_ven = r[0] or 0

print("=" * 70)
print(f"KPI POR NODO — {NODO} (v2)")
print("=" * 70)
print()
print(f"Stock desde última transacción: {len(stock_nodo)} SKUs")
print(f"SKUs con stock > 0: {skus_con_stock}")
print(f"Valor del inventario: ${valor_inv:,.2f}")
print(f"Costo de ventas (8 meses): ${costo_ven:,.2f}")
print()

# ============================================================
# NIVEL 1
# ============================================================

# KPI 1 — Rotación
rot = round((costo_ven / 8.0 * 12) / valor_inv, 2) if valor_inv else 0
kpis[1] = K(1, "Rotación de Inventario", 1, "CALCULADO", rot, "veces/año",
    "Costo Ventas Anual / Valor Inventario", "4-6x",
    f"Valor inv: ${valor_inv:,.2f} | Costo ven anualizado: ${costo_ven/8*12:,.2f} | Rotación: {rot}x")

# KPI 2 — DOH
doh = round(365 / rot, 0) if rot else 0
kpis[2] = K(2, "Días de Inventario (DOH)", 1, "CALCULADO", doh, "días",
    "365 / Rotación", "60-90 días", f"DOH: {doh} días.")

# KPI 3 — Fill Rate
r = conn.execute("SELECT COUNT(*), SUM(CASE WHEN stock_actual > 0 THEN 1 ELSE 0 END) FROM movimientos_historico WHERE tipo='FACT' AND nodo = ?", (NODO,)).fetchone()
tf, cs = r[0] or 0, r[1] or 0
fr = round(100.0 * cs / tf, 1) if tf else 0
kpis[3] = K(3, "Fill Rate", 1, "CALCULADO", fr, "%", "(Surtidos / Total) × 100", "> 95%", f"{cs:,}/{tf:,}")

# KPI 4 — Exactitud
if NODO == "01 Central":
    r = conn.execute("SELECT COUNT(*), SUM(CASE WHEN ABS((stock_inicial+compras+entradas-ventas-salidas)-stock_final) <= 0.01 THEN 1 ELSE 0 END) FROM movimientos_sep").fetchone()
    tk, ok = r[0] or 0, r[1] or 0
    ex = round(100.0 * ok / tk, 1) if tk else 0
    kpis[4] = K(4, "Exactitud de Inventario", 1, "CALCULADO", ex, "%", "Kardex cuadrado", "> 95%", f"{ex}%")
else:
    kpis[4] = K(4, "Exactitud de Inventario", 1, "REQUIERE DATO", None, "%",
        "Conteo físico", "> 95%",
        "No hay conteo físico de este nodo. Solo Central tiene kardex validado.",
        "NIA 501", "Ejecutar conteo físico")

# KPI 5 — Stockout
kpis[5] = K(5, "Stockout Rate", 1, "CALCULADO", round(100-fr,1), "%", "100 - Fill Rate", "< 5%", f"{tf-cs:,} sin stock")

# KPI 6 — Inmovilizado
skus_fact = set(r[0] for r in conn.execute("SELECT DISTINCT sku FROM movimientos_historico WHERE tipo='FACT' AND nodo=?", (NODO,)).fetchall())
skus_sin_venta = set(stock_nodo.keys()) - skus_fact
valor_inm = sum(max(0, stock_nodo.get(s, 0)) * costos.get(s, 0) for s in skus_sin_venta)
pct_inm = round(100.0 * valor_inm / valor_inv, 1) if valor_inv else 0
kpis[6] = K(6, "Valor Inmovilizado", 1, "CALCULADO", pct_inm, "%", "(Sin venta / Total) × 100", "< 20%",
    f"{len(skus_sin_venta)} SKUs sin venta. Valor: ${valor_inm:,.2f}")

# KPI 7 — ROP
kpis[7] = K(7, "Punto de Reorden (ROP)", 1, "REQUIERE DATO", None, "unidades",
    "(Demanda diaria × Lead Time) + SS", "Depende", "Falta lead time.",
    "Módulo Compras", "Solicitar lead time")

# ============================================================
# NIVEL 2
# ============================================================
kpis[8] = K(8, "GMROI", 2, "PARCIAL", None, "ratio", "Margen / Costo Promedio", "> 2.0x",
    "Margen no válido por bimonetarismo.", "Corregir márgenes", "Corregir escalas")

r = conn.execute("""
    SELECT COUNT(*), SUM(ms.precio_unitario_usd)
    FROM movimientos_historico mh
    JOIN maestro_sku ms ON ms.codigo = mh.sku
    WHERE mh.tipo = 'FACT' AND mh.stock_actual <= 0 AND mh.nodo = ?
""", (NODO,)).fetchone()
kpis[9] = K(9, "Lost Sales", 2, "PARCIAL", round(r[1] or 0, 2), "USD", "N° × Precio", "0",
    f"{r[0]:,} facturas. Estimado: ${r[1] or 0:,.2f}")

# KPI 10 — Obsolescencia (corregido: sin venta en 3 meses)
obsoletos = []
for sku in stock_nodo:
    if stock_nodo[sku] <= 0:
        continue
    ult = conn.execute("SELECT MAX(fecha) FROM movimientos_historico WHERE sku=? AND tipo='FACT' AND nodo=?", (sku, NODO)).fetchone()
    ultima = ult[0] if ult else None
    if not ultima or (ultima[6:10] + ultima[3:5] < '202607'):
        obsoletos.append(sku)
valor_obs = sum(max(0, stock_nodo.get(s, 0)) * costos.get(s, 0) for s in obsoletos)
pct_obs = round(100.0 * valor_obs / valor_inv, 1) if valor_inv else 0
kpis[10] = K(10, "Obsolescencia", 2, "CALCULADO", pct_obs, "%",
    "(Costo obsoletos / Costo total) × 100", "< 20%",
    f"{pct_obs}% en SKUs sin venta 3 meses ({len(obsoletos)} SKUs, ${valor_obs:,.2f})")

kpis[12] = K(12, "Canibalización", 2, "REQUIERE DATO", None, "%", "(Repuestos motos nuevas / Ventas)", "< 5%",
    "Dato físico, no en Profit.", "Taller", "Marcado manual")

kpis[13] = K(13, "Rentabilidad por Categoría", 2, "REQUIERE DATO", None, "ratio", "Margen / Costo", "> 2.0x",
    "No hay campo categoría.", "Catálogo", "Mapear familias")

kpis[14] = K(14, "TIC", 2, "REQUIERE DATO", None, "USD", "Suma de costos", "Minimizar",
    "Falta costo ordenar y mantener.", "Contabilidad", "Solicitar costos")

kpis[15] = K(15, "EOQ", 2, "REQUIERE DATO", None, "unidades", "√(2DS/H)", "Depende",
    "Falta S y H.", "Compras + Contabilidad", "Mismos datos que TIC")

# ============================================================
# NIVEL 3
# ============================================================
kpis[16] = K(16, "MAPE", 3, "REQUIERE DATO", None, "%", "100% - MAPE", "> 80%",
    "Sin pronóstico previo.", "Modelo predictivo", "Construir pronóstico")

kpis[17] = K(17, "Stock Seguridad Dinámico", 3, "REQUIERE DATO", None, "unidades", "Z × Desv × √LT", "Depende",
    "Falta lead time.", "Compras", "Solicitar lead time")

# Tiempo hasta Ruptura: una sola consulta (no bucle)
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
    # Acotar cada uno a 365 días antes de promediar
    dias_acotados = [min(d[2], 365) for d in top_20]
    prom = sum(dias_acotados) / len(dias_acotados)
    kpis[18] = K(18, "Tiempo hasta Ruptura", 3, "CALCULADO", round(prom, 1), "días",
        "Stock / Demanda diaria (acotado a 365 días)", "> 30 días",
        f"Promedio top 20 SKUs: {prom:.1f} días (acotado). Sin acotar: {max(d[2] for d in top_20):.0f} días máx.")
else:
    kpis[18] = K(18, "Tiempo hasta Ruptura", 3, "REQUIERE DATO", None, "días", "Stock / Demanda", "> 30 días", "Sin datos")

kpis[19] = K(19, "IML", 3, "REQUIERE DATO", None, "días", "Cobertura - LT", "> 0",
    "Falta lead time.", "Compras", "Solicitar lead time")

kpis[20] = K(20, "Demanda Perdida", 3, "REQUIERE DATO", None, "USD", "Prob × Demanda × Margen", "0",
    "Falta modelo y margen.", "No en Profit", "Modelo predictivo")

kpis[21] = K(21, "Participación Segmento", 3, "PARCIAL", None, "%", "(Ventas segmento / Total) × 100", "Depende",
    "ventas_segmento_central corrupta.", "Ventas", "Pedir data limpia")

# Novedad: SKUs con primera aparición en los últimos 3 meses / total
r = conn.execute("""
    SELECT COUNT(DISTINCT sku) FROM movimientos_historico
    WHERE tipo='FACT' AND nodo=?
      AND SUBSTR(fecha,7,4)||SUBSTR(fecha,4,2) >= '202608'
      AND sku NOT IN (
        SELECT DISTINCT sku FROM movimientos_historico WHERE tipo='FACT' AND nodo=?
          AND SUBSTR(fecha,7,4)||SUBSTR(fecha,4,2) < '202608'
      )
""", (NODO, NODO)).fetchone()
nuevos = r[0] or 0
r = conn.execute("SELECT COUNT(DISTINCT sku) FROM movimientos_historico WHERE tipo='FACT' AND nodo=?", (NODO,)).fetchone()
total_fact_skus = r[0] or 0
pct_nov = round(100.0 * nuevos / total_fact_skus, 1) if total_fact_skus else 0
kpis[22] = K(22, "Novedad de Surtido", 3, "CALCULADO", pct_nov, "%", "(Nuevos 3 meses / Activos) × 100", "5-15%",
    f"{nuevos} nuevos de {total_fact_skus} activos")

kpis[23] = K(23, "Contribución Marginal", 3, "REQUIERE DATO", None, "USD", "Precio - Costos totales", "> 20%",
    "Falta flete, arancel, comisión.", "Contabilidad", "Solicitar desglose")

kpis[24] = K(24, "Contribución Marginal por Ítem", 3, "REQUIERE DATO", None, "USD", "Precio - Costos totales", "> 20%",
    "Mismos datos que KPI 23.", "Contabilidad", "Solicitar desglose")

# ============================================================
# GUARDAR
# ============================================================
out = BASE / f"kpis_24_nodo_v2_{FECHA}.json"
with open(out, 'w', encoding='utf-8') as f:
    json.dump(list(kpis.values()), f, indent=2, ensure_ascii=False)

from collections import Counter
estados = Counter(k['estado'] for k in kpis.values())

print("=" * 70)
print(f"RESUMEN 24 KPIs — {NODO} (v2)")
print("=" * 70)
print()
print(f"  CALCULADOS:     {estados.get('CALCULADO', 0)}")
print(f"  PARCIALES:      {estados.get('PARCIAL', 0)}")
print(f"  REQUIEREN DATO: {estados.get('REQUIERE DATO', 0)}")
print()

for nivel in [1, 2, 3]:
    print(f"NIVEL {nivel}:")
    for k in kpis.values():
        if k['nivel'] == nivel:
            icono = {'CALCULADO': '✅', 'PARCIAL': '⚠️', 'REQUIERE DATO': '❌'}[k['estado']]
            valor = k['valor'] if k['valor'] is not None else '—'
            print(f"  {icono} KPI {k['id']:02d} {k['nombre']:40s} : {valor} {k['unidad']}")
    print()

print(f"Guardado en: {out}")
conn.close()

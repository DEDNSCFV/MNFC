#!/usr/bin/env python3
"""
Calcula los 24 KPIs por nodo reconstruyendo el stock desde los movimientos.
Uso: python kpis_nodo_real.py "<nodo_db>" "<nodo_tecnico>"
"""
import sys, json
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

if len(sys.argv) < 2:
    print("Uso: python kpis_nodo_real.py '<nodo_db>' ['<nodo_tecnico>']")
    sys.exit(1)

NODO = sys.argv[1]
NODO_TEC = sys.argv[2] if len(sys.argv) > 2 else NODO.replace(" ", "_")
DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"
BASE = Path.home() / "DARTONY_CONTROL" / NODO_TEC / "control" / "kpis"
FECHA = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
BASE.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(DB)

kpis = {}

def K(id, nombre, nivel, estado, valor, unidad, formula, benchmark, nota, donde_buscar=None, accion=None):
    return {
        'id': id, 'nombre': nombre, 'nivel': nivel, 'estado': estado,
        'valor': valor, 'unidad': unidad, 'formula': formula,
        'benchmark': benchmark, 'nota': nota,
        'donde_buscar': donde_buscar, 'accion': accion,
        'nodo': NODO, 'fecha': FECHA
    }

# ============================================================
# RECONSTRUIR STOCK DEL NODO
# ============================================================
# Para cada SKU del nodo, stock = SUM(entradas) - SUM(salidas)
stock_nodo = {}
for sku, ent, sal in conn.execute("""
    SELECT sku,
           SUM(CASE WHEN es_entrada = 1 THEN cantidad ELSE 0 END),
           SUM(CASE WHEN es_salida = 1 THEN ABS(cantidad) ELSE 0 END)
    FROM movimientos_historico
    WHERE nodo = ?
    GROUP BY sku
""", (NODO,)).fetchall():
    stock_nodo[sku] = (ent or 0) - (sal or 0)

# Costos del maestro
costos = dict(conn.execute("""
    SELECT codigo, costo_unitario_usd FROM maestro_sku
    WHERE costo_unitario_usd > 0
""").fetchall())

# Valor del inventario del nodo
valor_inv = sum(max(0, stock_nodo.get(sku, 0)) * costos.get(sku, 0) for sku in stock_nodo)
skus_con_stock = sum(1 for sku, s in stock_nodo.items() if s > 0 and costos.get(sku, 0) > 0)

# Costo de ventas del nodo (últimos 8 meses)
r = conn.execute("""
    SELECT SUM(ABS(mh.cantidad) * ms.costo_unitario_usd)
    FROM movimientos_historico mh
    JOIN maestro_sku ms ON ms.codigo = mh.sku
    WHERE mh.tipo = 'FACT' AND mh.cantidad < 0 AND ms.costo_unitario_usd > 0 AND mh.nodo = ?
""", (NODO,)).fetchone()
costo_ven = r[0] or 0

print("=" * 70)
print(f"KPI POR NODO — {NODO}")
print("=" * 70)
print()
print(f"Stock reconstruido: {len(stock_nodo)} SKUs con movimiento")
print(f"SKUs con stock > 0: {skus_con_stock}")
print(f"Valor del inventario del nodo: ${valor_inv:,.2f}")
print(f"Costo de ventas del nodo:      ${costo_ven:,.2f}")
print()

# ============================================================
# NIVEL 1 — BÁSICOS
# ============================================================

# KPI 1 — Rotación
rot = round((costo_ven / 8.0 * 12) / valor_inv, 2) if valor_inv else 0
kpis[1] = K(1, "Rotación de Inventario", 1, "CALCULADO", rot, "veces/año",
    "Costo Ventas Anual / Valor Inventario del nodo",
    "4-6x (retail autopartes)",
    f"Stock reconstruido desde movimientos del nodo. Valor: {rot}x.")

# KPI 2 — DOH
doh = round(365 / rot, 0) if rot else 0
kpis[2] = K(2, "Días de Inventario (DOH)", 1, "CALCULADO", doh, "días",
    "365 / Rotación",
    "60-90 días",
    f"Derivado de la rotación del nodo: {doh} días.")

# KPI 3 — Fill Rate
r = conn.execute("""
    SELECT COUNT(*), SUM(CASE WHEN stock_actual > 0 THEN 1 ELSE 0 END)
    FROM movimientos_historico WHERE tipo = 'FACT' AND nodo = ?
""", (NODO,)).fetchone()
tf, cs = r[0] or 0, r[1] or 0
fr = round(100.0 * cs / tf, 1) if tf else 0
kpis[3] = K(3, "Fill Rate", 1, "CALCULADO", fr, "%",
    "(Pedidos surtidos / Total pedidos) × 100",
    "> 95%",
    f"{cs:,} de {tf:,} facturas con stock.")

# KPI 4 — Exactitud
if NODO == "01 Central":
    r = conn.execute("""
        SELECT COUNT(*), SUM(CASE WHEN ABS((stock_inicial+compras+entradas-ventas-salidas)-stock_final) <= 0.01 THEN 1 ELSE 0 END)
        FROM movimientos_sep
    """).fetchone()
    tk, ok = r[0] or 0, r[1] or 0
    ex = round(100.0 * ok / tk, 1) if tk else 0
    kpis[4] = K(4, "Exactitud de Inventario", 1, "CALCULADO", ex, "%",
        "Kardex cuadrado", "> 95%", f"Kardex cuadra al {ex}%.")
else:
    kpis[4] = K(4, "Exactitud de Inventario", 1, "REQUIERE DATO", None, "%",
        "(Conteos correctos / Total ítems) × 100", "> 95%",
        "No hay conteo físico del nodo. El stock se reconstruyó desde movimientos.",
        "Conteo físico (NIA 501)", "Ejecutar auditoría NIA 501 con conteo real")

# KPI 5 — Stockout
kpis[5] = K(5, "Stockout Rate", 1, "CALCULADO", round(100 - fr, 1), "%",
    "100 - Fill Rate", "< 5%", f"{tf - cs:,} facturas sin stock.")

# KPI 6 — Inmovilizado
skus_sin_venta = set(stock_nodo.keys()) - set(
    r[0] for r in conn.execute("SELECT DISTINCT sku FROM movimientos_historico WHERE tipo='FACT' AND nodo=?", (NODO,)).fetchall()
)
valor_inm = sum(max(0, stock_nodo.get(sku, 0)) * costos.get(sku, 0) for sku in skus_sin_venta)
pct_inm = round(100.0 * valor_inm / valor_inv, 1) if valor_inv else 0
kpis[6] = K(6, "Valor Inmovilizado", 1, "CALCULADO", pct_inm, "%",
    "(Valor SKUs sin venta / Valor total) × 100", "< 20%",
    f"{len(skus_sin_venta)} SKUs sin venta. Valor: ${valor_inm:,.2f}.")

# KPI 7 — ROP
kpis[7] = K(7, "Punto de Reorden (ROP)", 1, "REQUIERE DATO", None, "unidades",
    "(Demanda diaria × Lead Time) + Stock Seguridad", "Depende",
    "Falta lead time de proveedores.",
    "Módulo de Compras → Lead time", "Solicitar reporte de compras con fechas")

# ============================================================
# NIVEL 2 — AVANZADOS
# ============================================================

# KPI 8 — GMROI
kpis[8] = K(8, "GMROI", 2, "PARCIAL", None, "ratio",
    "Margen Bruto / Costo Promedio Inventario", "> 2.0x",
    "El margen bruto no es válido por el problema bimonetario.",
    "Corregir margen", "Corregir escalas de precio y costo")

# KPI 9 — Lost Sales
r = conn.execute("""
    SELECT COUNT(*), SUM(ms.precio_unitario_usd)
    FROM movimientos_historico mh
    JOIN maestro_sku ms ON ms.codigo = mh.sku
    WHERE mh.tipo = 'FACT' AND mh.stock_actual <= 0 AND mh.nodo = ?
""", (NODO,)).fetchone()
n_lost, valor_lost = r[0] or 0, r[1] or 0
kpis[9] = K(9, "Lost Sales", 2, "PARCIAL", round(valor_lost, 2), "USD",
    "N° solicitudes × Precio Unitario", "0",
    f"{n_lost:,} facturas. Estimado con precio del maestro.")

# KPI 10 — Obsolescencia
pct_obs = pct_inm  # mismo cálculo que inmovilizado
kpis[10] = K(10, "Obsolescencia", 2, "CALCULADO", pct_obs, "%",
    "(Costo obsoletos / Costo total) × 100", "< 20%",
    f"{pct_obs}% del valor en SKUs sin venta.")

# KPI 11 — Carrying Cost
kpis[11] = K(11, "Carrying Cost", 2, "REQUIERE DATO", None, "%",
    "(Almacenamiento + Seguros + Impuestos + Mermas) / Valor", "15-25%",
    "Falta desglose de gastos.", "Módulo Contabilidad", "Solicitar gastos desagregados")

# KPI 12 — Canibalización
kpis[12] = K(12, "Canibalización", 2, "REQUIERE DATO", None, "%",
    "(Repuestos de motos nuevas / Ventas) × 100", "< 5%",
    "Dato físico, no está en Profit.", "Proceso manual", "Marcar en taller")

# KPI 13 — Rentabilidad por Categoría
kpis[13] = K(13, "Rentabilidad por Categoría", 2, "REQUIERE DATO", None, "ratio",
    "Margen / Costo por categoría", "> 2.0x",
    "No hay campo categoría. Requiere mapeo manual.",
    "Catálogo", "Mapear familias a categorías")

# KPI 14 — TIC
kpis[14] = K(14, "TIC", 2, "REQUIERE DATO", None, "USD",
    "Ordenar + Mantener + Compra + Seguridad", "Minimizar",
    "Falta costo ordenar y mantener.", "Contabilidad", "Solicitar costos")

# KPI 15 — EOQ
kpis[15] = K(15, "EOQ", 2, "REQUIERE DATO", None, "unidades",
    "√((2 × D × S) / H)", "Depende",
    "Falta S y H.", "Compras + Contabilidad", "Mismos datos que TIC")

# ============================================================
# NIVEL 3 — PREDICTIVOS
# ============================================================

# KPI 16 — MAPE
kpis[16] = K(16, "MAPE", 3, "REQUIERE DATO", None, "%",
    "100% - MAPE", "> 80%",
    "Sin pronóstico previo.", "Modelo predictivo", "Construir pronóstico")

# KPI 17 — SS Dinámico
kpis[17] = K(17, "Stock Seguridad Dinámico", 3, "REQUIERE DATO", None, "unidades",
    "Z × Desv Est × √Lead Time", "Depende",
    "Falta lead time.", "Compras", "Solicitar lead time")

# KPI 18 — Tiempo hasta Ruptura
# Calcular por SKU: stock / demanda diaria
dias_ruptura = []
for sku, stock in stock_nodo.items():
    if stock <= 0 or costos.get(sku, 0) <= 0:
        continue
    r = conn.execute("""
        SELECT COUNT(*) FROM movimientos_historico
        WHERE sku = ? AND tipo = 'FACT' AND nodo = ?
    """, (sku, NODO)).fetchone()
    n_fact = r[0] or 0
    if n_fact > 0:
        demanda_diaria = n_fact / 240
        dias = stock / demanda_diaria
        dias_ruptura.append((sku, stock, dias))

if dias_ruptura:
    # Ordenar por SKUs de mayor valor
    dias_ruptura.sort(key=lambda x: costos.get(x[0], 0) * x[1], reverse=True)
    top_20 = dias_ruptura[:20]
    promedio_dias = sum(d[2] for d in top_20) / len(top_20)
    minimo_dias = min(d[2] for d in top_20)
    kpis[18] = K(18, "Tiempo hasta Ruptura", 3, "CALCULADO", round(promedio_dias, 1), "días",
        "Stock actual / Demanda diaria por SKU",
        "> 30 días",
        f"Promedio top 20 SKUs clase A: {promedio_dias:.1f} días. Mínimo: {minimo_dias:.1f} días.")
else:
    kpis[18] = K(18, "Tiempo hasta Ruptura", 3, "REQUIERE DATO", None, "días",
        "Stock / Demanda", "> 30 días", "Sin datos suficientes.")

# KPI 19 — IML
kpis[19] = K(19, "IML", 3, "REQUIERE DATO", None, "días",
    "Cobertura - Lead Time", "> 0",
    "Falta lead time.", "Compras", "Solicitar lead time")

# KPI 20 — Demanda Perdida
kpis[20] = K(20, "Demanda Perdida", 3, "REQUIERE DATO", None, "USD",
    "Prob × Demanda × Margen", "0",
    "Falta modelo y margen.", "No en Profit", "Modelo predictivo")

# KPI 21 — Segmento
kpis[21] = K(21, "Participación por Segmento", 3, "PARCIAL", None, "%",
    "(Ventas segmento / Total) × 100", "Depende",
    "ventas_segmento_central corrupta.", "Ventas", "Pedir data limpia")

# KPI 22 — Novedad
r = conn.execute("""
    SELECT COUNT(DISTINCT sku) FROM movimientos_historico
    WHERE tipo = 'FACT' AND nodo = ?
      AND sku NOT IN (
        SELECT DISTINCT sku FROM movimientos_historico WHERE tipo = 'FACT' AND nodo = ?
          AND SUBSTR(fecha,7,4)||SUBSTR(fecha,4,2) = '202601'
      )
""", (NODO, NODO)).fetchone()
nuevos = r[0] or 0
r = conn.execute("SELECT COUNT(DISTINCT sku) FROM movimientos_historico WHERE tipo = 'FACT' AND nodo = ?", (NODO,)).fetchone()
total_skus_fact = r[0] or 0
pct_nov = round(100.0 * nuevos / total_skus_fact, 1) if total_skus_fact else 0
kpis[22] = K(22, "Novedad de Surtido", 3, "CALCULADO", pct_nov, "%",
    "(Nuevos / Activos) × 100", "> 5%",
    f"{nuevos} SKUs nuevos de {total_skus_fact} activos.")

# KPI 23 — Contribución Marginal
kpis[23] = K(23, "Contribución Marginal", 3, "REQUIERE DATO", None, "USD",
    "Precio - (Costo + Flete + Arancel + Comisión)", "> 20%",
    "Falta flete, arancel, comisión.", "Contabilidad", "Solicitar desglose")

# KPI 24 — Contribución Marginal por Ítem (variante)
kpis[24] = K(24, "Contribución Marginal por Ítem", 3, "REQUIERE DATO", None, "USD",
    "Precio Venta - (Costo Compra + Flete + Arancel + Comisión)", "> 20%",
    "Falta flete, arancel, comisión.", "Contabilidad", "Solicitar desglose")

# ============================================================
# GUARDAR
# ============================================================
out = BASE / f"kpis_24_nodo_{FECHA}.json"
with open(out, 'w', encoding='utf-8') as f:
    json.dump(list(kpis.values()), f, indent=2, ensure_ascii=False)

from collections import Counter
estados = Counter(k['estado'] for k in kpis.values())

print("=" * 70)
print(f"RESUMEN 24 KPIs — {NODO}")
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

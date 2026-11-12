#!/usr/bin/env python3
"""
24 KPIs de inventario con 3 estados:
- CALCULADO: se calcula con los datos actuales
- PARCIAL: se calcula con salvedad documentada
- REQUIERE DATO: no se calcula, se documenta qué falta y dónde buscarlo
Uso: python kpis_24.py "<nodo_db>" "<nodo_tecnico>"
"""
import sys, json
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

if len(sys.argv) < 2:
    print("Uso: python kpis_24.py '<nodo_db>' ['<nodo_tecnico>']")
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
        'id': id,
        'nombre': nombre,
        'nivel': nivel,
        'estado': estado,
        'valor': valor,
        'unidad': unidad,
        'formula': formula,
        'benchmark': benchmark,
        'nota': nota,
        'donde_buscar': donde_buscar,
        'accion': accion,
        'nodo': NODO,
        'fecha': FECHA
    }

# ============================================================
# NIVEL 1 — BÁSICOS
# ============================================================

# KPI 1 — Rotación
r = conn.execute("""
    SELECT SUM(stock_central * costo_unitario_usd) FROM maestro_sku
    WHERE stock_central > 0 AND costo_unitario_usd > 0
""").fetchone()
valor_inv = r[0] or 0
r = conn.execute("""
    SELECT SUM(ABS(mh.cantidad) * ms.costo_unitario_usd)
    FROM movimientos_historico mh
    JOIN maestro_sku ms ON ms.codigo = mh.sku
    WHERE mh.tipo = 'FACT' AND mh.cantidad < 0 AND ms.costo_unitario_usd > 0 AND mh.nodo = ?
""", (NODO,)).fetchone()
costo_ven = r[0] or 0
rot = round((costo_ven / 8.0 * 12) / valor_inv, 2) if valor_inv else 0
kpis[1] = K(1, "Rotación de Inventario", 1, "PARCIAL", rot, "veces/año",
    "Costo de Ventas Anual / Valor Inventario",
    "4-6x (retail autopartes)",
    f"Calculado con USD/USD (corrección bimonetaria). Valor real: {rot}x. El cálculo anterior (8.83x) mezclaba escalas.")

# KPI 2 — DOH
doh = round(365 / rot, 0) if rot else 0
kpis[2] = K(2, "Días de Inventario (DOH)", 1, "PARCIAL", doh, "días",
    "365 / Rotación",
    "60-90 días",
    f"Derivado de la rotación corregida. Real: {doh} días, no 41.")

# KPI 3 — Fill Rate
r = conn.execute("""
    SELECT COUNT(*), SUM(CASE WHEN stock_actual > 0 THEN 1 ELSE 0 END)
    FROM movimientos_historico WHERE tipo = 'FACT' AND nodo = ?
""", (NODO,)).fetchone()
tf, cs = r[0] or 0, r[1] or 0
fr = round(100.0 * cs / tf, 1) if tf else 0
kpis[3] = K(3, "Fill Rate (Nivel de Servicio)", 1, "CALCULADO", fr, "%",
    "(Pedidos surtidos / Total pedidos) × 100",
    "> 95%",
    f"{cs:,} de {tf:,} facturas con stock. Por debajo del benchmark.")

# KPI 4 — Exactitud de Inventario
if NODO == "01 Central":
    r = conn.execute("""
        SELECT COUNT(*), SUM(CASE WHEN ABS((stock_inicial+compras+entradas-ventas-salidas)-stock_final) <= 0.01 THEN 1 ELSE 0 END)
        FROM movimientos_sep
    """).fetchone()
    tk, ok = r[0] or 0, r[1] or 0
    ex = round(100.0 * ok / tk, 1) if tk else 0
    kpis[4] = K(4, "Exactitud de Inventario", 1, "PARCIAL", ex, "%",
        "(Conteos correctos / Total ítems contados) × 100",
        "> 95%",
        f"Kardex cuadra al {ex}%. Solo verificable para Central. Para los otros nodos, el kardex está en movimientos_historico pero no hay validación cruzada.")
else:
    kpis[4] = K(4, "Exactitud de Inventario", 1, "REQUIERE DATO", None, "%",
        "(Conteos correctos / Total ítems contados) × 100",
        "> 95%",
        "No hay conteo físico de este nodo. Solo se puede verificar el kardex de Central.",
        "Módulo de Inventario → Reporte 'Kardex por artículo' o 'Resumen de inventario'",
        "Generar el TXT de 'Resumen de Inventario por Artículo' del nodo y cargarlo al corpus")

# KPI 5 — Stockout
kpis[5] = K(5, "Tasa de Ruptura (Stockout)", 1, "CALCULADO", round(100 - fr, 1), "%",
    "(N° sin stock / Total solicitudes) × 100",
    "< 5%",
    f"Complemento del fill rate. {tf - cs:,} facturas sin stock.")

# KPI 6 — Valor Inmovilizado
r = conn.execute("""
    SELECT COUNT(*) FROM (
        SELECT codigo FROM stock_central WHERE stock > 0
        EXCEPT
        SELECT DISTINCT sku FROM movimientos_historico WHERE tipo = 'FACT' AND nodo = ?
    )
""", (NODO,)).fetchone()
sin_venta = r[0] or 0
r = conn.execute("SELECT COUNT(*) FROM stock_central WHERE stock > 0").fetchone()
total_skus = r[0] or 0
pct_inm = round(100.0 * sin_venta / total_skus, 1) if total_skus else 0
kpis[6] = K(6, "Valor del Inventario Inmovilizado", 1, "CALCULADO", pct_inm, "%",
    "(SKUs sin movimiento > 12 meses / Total SKUs) × 100",
    "< 20%",
    f"{sin_venta:,} SKUs sin ventas en 8 meses = {pct_inm}% del catálogo.")

# KPI 7 — ROP
kpis[7] = K(7, "Punto de Reorden (ROP)", 1, "REQUIERE DATO", None, "unidades",
    "(Demanda diaria × Lead Time) + Stock de Seguridad",
    "Depende del SKU",
    "La demanda diaria se calcula con movimientos_historico. Falta el lead time de proveedores.",
    "Módulo de Compras → 'Órdenes de compra' o 'Tiempo de entrega por proveedor'",
    "Solicitar al mandante el reporte de órdenes de compra con fechas de emisión y recepción")

# ============================================================
# NIVEL 2 — AVANZADOS
# ============================================================

# KPI 8 — GMROI
kpis[8] = K(8, "GMROI", 2, "PARCIAL", None, "ratio",
    "Margen Bruto ($) / Costo Promedio del Inventario",
    "> 2.0x (repuestos)",
    "El costo de ventas está en USD. El margen bruto no es válido porque precio y costo están en escalas distintas (margen 171.98x es imposible). No es calculable hasta corregir el margen.",
    "Módulo de Ventas → 'Margen por producto' o 'Estado de resultados'",
    "Solicitar al mandante el desglose de precio de venta y costo en la misma moneda")

# KPI 9 — Lost Sales (parcial con estimación)
r = conn.execute("""
    SELECT COUNT(*), SUM(ms.precio_unitario_usd)
    FROM movimientos_historico mh
    JOIN maestro_sku ms ON ms.codigo = mh.sku
    WHERE mh.tipo = 'FACT' AND mh.stock_actual <= 0 AND mh.nodo = ?
""", (NODO,)).fetchone()
n_lost = r[0] or 0
valor_lost = r[1] or 0
kpis[9] = K(9, "Ventas Perdidas (Lost Sales)", 2, "PARCIAL", round(valor_lost, 2), "USD",
    "N° solicitudes no atendidas × Precio de Venta Unitario",
    "0",
    f"{n_lost:,} facturas sin stock. Estimación con precio_unitario_usd del maestro: ${valor_lost:,.2f}. No incluye margen perdido.",
    "Módulo de Ventas → 'Facturas con stock 0' (si existe el reporte nativo)",
    "Verificar si Profit tiene un reporte nativo de 'Ventas no surtidas'")

# KPI 10 — Obsolescencia
r = conn.execute("""
    SELECT SUM(ms.stock_central * ms.costo_unitario_usd)
    FROM maestro_sku ms
    WHERE ms.stock_central > 0
      AND ms.codigo NOT IN (
        SELECT DISTINCT sku FROM movimientos_historico WHERE tipo = 'FACT' AND nodo = ?
      )
""", (NODO,)).fetchone()
valor_obsoleto = r[0] or 0
pct_obs = round(100.0 * valor_obsoleto / valor_inv, 1) if valor_inv else 0
kpis[10] = K(10, "Índice de Obsolescencia", 2, "CALCULADO", pct_obs, "%",
    "(Costo SKUs obsoletos / Costo total inventario) × 100",
    "< 20%",
    f"{pct_obs}% del valor ($ {valor_obsoleto:,.2f}) está en SKUs sin ventas.")

# KPI 11 — Carrying Cost
kpis[11] = K(11, "Costo de Mantenimiento (Carrying Cost)", 2, "REQUIERE DATO", None, "%",
    "(Almacenamiento + Seguros + Impuestos + Mermas) / Valor Inventario",
    "15-25% anual",
    "Falta desagregación de costos de almacenamiento, seguros, impuestos y mermas.",
    "Módulo de Contabilidad → 'Gastos operativos' desagregados",
    "Solicitar al mandante el desglose de gastos de almacenamiento y seguros")

# KPI 12 — Canibalización
kpis[12] = K(12, "Tasa de Canibalización", 2, "REQUIERE DATO", None, "%",
    "(Valor repuestos extraídos de motos nuevas / Ventas totales) × 100",
    "< 5%",
    "Falta identificar qué SKUs se extrajeron de motos nuevas. Es dato físico, no de sistema.",
    "No está en Profit. Requiere marcado manual o integración con taller",
    "Acordar con el mandante un proceso de marcado en el taller")

# KPI 13 — Rentabilidad por Categoría
# Usar 'familia' como proxy si existe
r = conn.execute("PRAGMA table_info(maestro_sku);").fetchall()
tiene_familia = any(c[1] == 'familia' for c in r)
if tiene_familia:
    kpis[13] = K(13, "Rentabilidad por Categoría", 2, "PARCIAL", "Ver detalle por familia", "ratio",
        "Margen Bruto de categoría / Costo Promedio de categoría",
        "> 2.0x",
        "Se puede calcular agrupando por 'familia'. La categoría formal (aceites, frenos, etc.) requiere mapeo manual.",
        "El campo 'familia' existe en maestro_sku",
        "Crear un mapeo de familias a categorías de negocio")
else:
    kpis[13] = K(13, "Rentabilidad por Categoría", 2, "REQUIERE DATO", None, "ratio",
        "Margen Bruto de categoría / Costo Promedio de categoría",
        "> 2.0x",
        "No hay campo 'categoría' ni 'familia' en maestro_sku.",
        "Módulo de Inventario → 'Catálogo de artículos'",
        "Solicitar al mandante el catálogo con categorías")

# KPI 14 — TIC
kpis[14] = K(14, "Costo Total del Inventario (TIC)", 2, "REQUIERE DATO", None, "USD",
    "Costo de ordenar + Costo de mantener + Costo de compra + Costo stock seguridad",
    "Minimizar",
    "Falta costo de ordenar y costo de mantener. Sin esos dos, no se puede calcular.",
    "Módulo de Contabilidad → 'Costos operativos'",
    "Solicitar al mandante el costo por orden de compra y el costo anual de mantenimiento")

# KPI 15 — EOQ
kpis[15] = K(15, "Cantidad Económica de Pedido (EOQ)", 2, "REQUIERE DATO", None, "unidades",
    "√((2 × Demanda × Costo por pedido) / Costo de mantener unitario)",
    "Depende del SKU",
    "Falta costo por pedido y costo de mantener unitario.",
    "Módulo de Compras y Contabilidad",
    "Mismos datos que el TIC")

# ============================================================
# NIVEL 3 — PREDICTIVOS
# ============================================================

# KPI 16 — MAPE
kpis[16] = K(16, "Precisión del Pronóstico (MAPE)", 3, "REQUIERE DATO", None, "%",
    "100% - MAPE",
    "> 80%",
    "No hay pronóstico histórico. Para calcular MAPE se necesita comparar demanda real vs pronóstico.",
    "No está en Profit. Requiere construir un modelo de pronóstico",
    "Implementar pronóstico (proyecto aparte) o usar el promedio móvil de los últimos 3 meses")

# KPI 17 — SS Dinámico
kpis[17] = K(17, "Stock de Seguridad Dinámico (SS)", 3, "PARCIAL", None, "unidades",
    "Z × Desviación Estándar Demanda × √(Lead Time)",
    "Depende del nivel de servicio",
    "La desviación estándar se calcula con movimientos_historico. Falta el lead time. Sin él, SS no es calculable.",
    "Módulo de Compras → Lead time por proveedor",
    "Solicitar al mandante el lead time")

# KPI 18 — Tiempo hasta Ruptura
dias_hasta_rupt = round(doh / (tf / 240) if tf else 0, 1)  # 240 días = 8 meses
kpis[18] = K(18, "Tiempo hasta Ruptura", 3, "CALCULADO", dias_hasta_rupt, "días",
    "DOH / Demanda diaria promedio",
    "> 30 días",
    f"Con DOH de {doh} días y demanda diaria promedio de {tf/240:.1f} facturas/día, el tiempo hasta ruptura es {dias_hasta_rupt} días.")

# KPI 19 — IML
kpis[19] = K(19, "Índice de Margen Logístico (IML)", 3, "REQUIERE DATO", None, "días",
    "Cobertura de Stock - Lead Time del Proveedor",
    "> 0 (positivo)",
    "Falta lead time del proveedor.",
    "Módulo de Compras → Lead time",
    "Solicitar al mandante el lead time por proveedor")

# KPI 20 — Demanda Perdida
kpis[20] = K(20, "Demanda Perdida Proyectada", 3, "REQUIERE DATO", None, "USD",
    "Probabilidad Quiebre × Demanda Promedio × Margen Contribución Unitario",
    "0",
    "Falta probabilidad de quiebre (modelo predictivo) y margen de contribución unitario (bimonetario).",
    "No está en Profit",
    "Requiere modelo predictivo y corrección bimonetaria")

# KPI 21 — Participación por Segmento
kpis[21] = K(21, "Participación de Ventas por Segmento", 3, "PARCIAL", None, "%",
    "(Ventas a talleres / Ventas totales) × 100",
    "Depende de la estrategia",
    "La tabla ventas_segmento_central está corrupta: monto_ves = 0.0 y el monto está en el nombre del segmento.",
    "Módulo de Ventas → 'Análisis por segmento de cliente'",
    "Solicitar al mandante la data limpia de segmentación")

# KPI 22 — Novedad de Surtido
r = conn.execute("""
    SELECT COUNT(DISTINCT sku) FROM movimientos_historico
    WHERE tipo = 'FACT' AND nodo = ?
      AND sku NOT IN (
        SELECT DISTINCT sku FROM movimientos_historico WHERE tipo = 'FACT' AND nodo = ?
          AND SUBSTR(fecha,7,4)||SUBSTR(fecha,4,2) < '202601'
      )
""", (NODO, NODO)).fetchone()
nuevos = r[0] or 0
r = conn.execute("SELECT COUNT(DISTINCT sku) FROM movimientos_historico WHERE tipo = 'FACT' AND nodo = ?", (NODO,)).fetchone()
total_fact_skus = r[0] or 0
pct_nov = round(100.0 * nuevos / total_fact_skus, 1) if total_fact_skus else 0
kpis[22] = K(22, "Índice de Novedad de Surtido", 3, "CALCULADO", pct_nov, "%",
    "(SKUs nuevos / SKUs activos) × 100",
    "> 5%",
    f"{nuevos:,} SKUs nuevos de {total_fact_skus:,} activos en el período.")

# KPI 23 — Contribución Marginal por Ítem
kpis[23] = K(23, "Contribución Marginal por Ítem", 3, "REQUIERE DATO", None, "USD",
    "Precio - (Costo Compra + Flete + Arancel + Comisión)",
    "> 20%",
    "Falta flete, arancel y comisión. Solo tienes precio y costo.",
    "Módulo de Contabilidad → 'Costos de importación' o 'Gastos de venta'",
    "Solicitar al mandante el desglose de costos por transacción")

# ============================================================
# GUARDAR
# ============================================================
out = BASE / f"kpis_24_{FECHA}.json"
with open(out, 'w', encoding='utf-8') as f:
    json.dump(list(kpis.values()), f, indent=2, ensure_ascii=False)

# Resumen
from collections import Counter
estados = Counter(k['estado'] for k in kpis.values())

print("=" * 70)
print(f"24 KPIs DE INVENTARIO — {NODO}")
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

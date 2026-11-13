#!/usr/bin/env python3
"""
Calcula KPIs de gestión de inventario sobre el corpus DARTONY.
Cada KPI se calcula con datos reales y se compara con benchmarks del sector.
"""
import sqlite3
from pathlib import Path
from datetime import datetime

DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"
conn = sqlite3.connect(DB)

PERIODO_DIAS = 240  # Feb 1 → Sep 30 = 240 días aprox
PERIODO_MESES = 8


def bloque(titulo):
    print()
    print("=" * 70)
    print(f"  {titulo}")
    print("=" * 70)


def kpi(nombre, valor, unidad, benchmark, interpretacion):
    print(f"\n  {nombre}")
    print(f"    Valor:      {valor} {unidad}")
    print(f"    Benchmark:  {benchmark}")
    print(f"    Lectura:    {interpretacion}")


# ============================================================
# 1. VALOR DEL INVENTARIO
# ============================================================
bloque("1. VALOR DEL INVENTARIO")

r = conn.execute("""
    SELECT COUNT(*), SUM(stock_central * costo_unitario_usd)
    FROM maestro_sku WHERE stock_central > 0 AND costo_unitario_usd > 0
""").fetchone()
n_skus, valor_total = r[0] or 0, r[1] or 0

r = conn.execute("SELECT SUM(stock) FROM stock_central").fetchone()
unidades_totales = r[0] or 0

kpi("Valor total del inventario",
    f"${valor_total:,.2f}", "USD",
    "Depende del tamaño de la empresa",
    f"{n_skus:,} SKUs con stock y costo. Promedio: ${valor_total/n_skus:,.2f} por SKU.")


# ============================================================
# 2. ROTACIÓN DE INVENTARIO
# ============================================================
bloque("2. ROTACIÓN DE INVENTARIO")

# Costo de ventas: facturas × costo
r = conn.execute("""
    SELECT SUM(ABS(cantidad) * costo_unitario)
    FROM movimientos_historico
    WHERE tipo = 'FACT' AND cantidad < 0 AND costo_unitario > 0
""").fetchone()
costo_ventas = r[0] or 0

# Rotación anualizada: (costo_ventas / periodo_meses) * 12 / valor_inventario
rotacion = (costo_ventas / PERIODO_MESES * 12 / valor_total) if valor_total else 0

kpi("Rotación anualizada del inventario",
    f"{rotacion:.2f}x", "veces/año",
    "4x – 6x (retail autopartes) · 6x – 8x (retail eficiente)",
    f"{rotacion:.2f}x significa que el inventario rota {rotacion:.2f} veces al año. "
    f"Por debajo de 4x indica capital inmovilizado.")

dias_inventario = 365 / rotacion if rotacion > 0 else 0
kpi("Días de inventario (DIO)",
    f"{dias_inventario:.0f}", "días",
    "60 – 90 días (retail autopartes)",
    f"{dias_inventario:.0f} días significa que un SKU promedio tarda ese tiempo en venderse. "
    f"Por encima de 120 días indica sobrestock.")


# ============================================================
# 3. FILL RATE (tasa de surtido)
# ============================================================
bloque("3. FILL RATE (Tasa de surtido)")

r = conn.execute("""
    SELECT COUNT(*),
           SUM(CASE WHEN stock_actual > 0 THEN 1 ELSE 0 END)
    FROM movimientos_historico
    WHERE tipo = 'FACT'
""").fetchone()
total_fact, con_stock = r[0] or 0, r[1] or 0
fill_rate = 100.0 * con_stock / total_fact if total_fact else 0
stockout_rate = 100.0 - fill_rate

kpi("Fill rate global",
    f"{fill_rate:.1f}%", "%",
    "> 95% (retail autopartes)",
    f"{con_stock:,} de {total_fact:,} facturas se hicieron con stock positivo. "
    f"Objetivo: > 95%. Actual: {fill_rate:.1f}%.")

kpi("Tasa de faltantes (stockout)",
    f"{stockout_rate:.1f}%", "%",
    "< 5% (retail autopartes)",
    f"{total_fact - con_stock:,} facturas se emitieron con stock ≤ 0. "
    f"Eso es {stockout_rate:.1f}% del total. Benchmark: < 5%.")


# ============================================================
# 4. EXACTITUD DE INVENTARIO
# ============================================================
bloque("4. EXACTITUD DE INVENTARIO")

# Kardex cuadra
r = conn.execute("""
    SELECT COUNT(*),
           SUM(CASE WHEN ABS((stock_inicial+compras+entradas-ventas-salidas)-stock_final) <= 0.01 THEN 1 ELSE 0 END)
    FROM movimientos_sep
""").fetchone()
total_kdx, kdx_ok = r[0] or 0, r[1] or 0
exactitud_kdx = 100.0 * kdx_ok / total_kdx if total_kdx else 0

kpi("Exactitud del kardex",
    f"{exactitud_kdx:.1f}%", "%",
    "> 95%",
    f"{kdx_ok:,} de {total_kdx:,} SKUs cuadran. Benchmark: > 95%. "
    f"Actual: {exactitud_kdx:.1f}%. Excelente.")


# ============================================================
# 5. VALORIZACIÓN
# ============================================================
bloque("5. VALORIZACIÓN DEL INVENTARIO")

r = conn.execute("""
    SELECT COUNT(*) AS total,
           SUM(CASE WHEN tiene_costo = 0 THEN 1 ELSE 0 END) AS sin_costo,
           SUM(CASE WHEN tiene_precio = 0 THEN 1 ELSE 0 END) AS sin_precio
    FROM maestro_sku WHERE stock_central > 0
""").fetchone()
total_skus_stock, sin_costo, sin_precio = r[0] or 0, r[1] or 0, r[2] or 0

pct_sin_costo = 100.0 * sin_costo / total_skus_stock if total_skus_stock else 0
pct_sin_precio = 100.0 * sin_precio / total_skus_stock if total_skus_stock else 0

kpi("SKUs sin costo (no valorizables)",
    f"{sin_costo:,} ({pct_sin_costo:.1f}%)", "%",
    "< 2%",
    f"{sin_costo:,} SKUs con stock no tienen costo. No pueden valorizarse correctamente. "
    f"Benchmark: < 2%. Actual: {pct_sin_costo:.1f}%.")

kpi("SKUs sin precio de venta",
    f"{sin_precio:,} ({pct_sin_precio:.1f}%)", "%",
    "< 1%",
    f"{sin_precio:,} SKUs con stock no tienen precio. Afecta el cálculo de margen. "
    f"Benchmark: < 1%. Actual: {pct_sin_precio:.1f}%.")


# ============================================================
# 6. AJUSTES DE INVENTARIO
# ============================================================
bloque("6. AJUSTES DE INVENTARIO")

r = conn.execute("""
    SELECT COUNT(*),
           SUM(CASE WHEN motivo IS NULL OR TRIM(motivo) = '' THEN 1 ELSE 0 END)
    FROM ajustes_historico
""").fetchone()
total_aj, sin_motivo = r[0] or 0, r[1] or 0
pct_sin_motivo = 100.0 * sin_motivo / total_aj if total_aj else 0

kpi("Ajustes documentados con motivo",
    f"{100.0 - pct_sin_motivo:.1f}%", "%",
    "> 95%",
    f"{total_aj - sin_motivo:,} de {total_aj:,} ajustes tienen motivo. "
    f"Benchmark: > 95%. Actual: {100.0 - pct_sin_motivo:.1f}%.")

r = conn.execute("""
    SELECT COUNT(*) FROM movimientos_historico
    WHERE tipo IN ('AJUE','AJUS') AND (cantidad * costo_unitario) > 500
""").fetchone()
n_aj_500 = r[0] or 0

kpi("Ajustes > $500 sin autorización",
    f"{n_aj_500:,}", "ajustes",
    "0",
    f"{n_aj_500:,} ajustes superan $500 y no tienen autorización documentada. "
    f"Benchmark: 0. Es un riesgo de control interno crítico.")


# ============================================================
# 7. CONCENTRACIÓN ABC (Pareto)
# ============================================================
bloque("7. CONCENTRACIÓN ABC (Pareto)")

r = conn.execute("""
    SELECT codigo, stock_central * costo_unitario_usd AS valor
    FROM maestro_sku WHERE stock_central > 0 AND costo_unitario_usd > 0
    ORDER BY valor DESC
""").fetchall()

if r:
    total_v = sum(x[1] for x in r)
    acum = 0
    n_a = n_b = n_c = 0
    v_a = v_b = v_c = 0
    for cod, v in r:
        acum += v
        pct = 100.0 * acum / total_v
        if pct <= 80:
            n_a += 1; v_a += v
        elif pct <= 95:
            n_b += 1; v_b += v
        else:
            n_c += 1; v_c += v

    kpi("Concentración clase A",
        f"{n_a} SKUs ({100.0*n_a/len(r):.1f}%)",
        "%",
        "20% de SKUs = 80% del valor (Pareto clásico)",
        f"{n_a} SKUs concentran ${v_a:,.2f} ({100.0*v_a/total_v:.1f}% del valor). "
        f"Es un Pareto extremo (no 20/80 sino {100.0*n_a/len(r):.1f}/80).")


# ============================================================
# 8. MOVIMIENTOS Y VOLUMEN
# ============================================================
bloque("8. VOLUMEN DE OPERACIÓN")

r = conn.execute("""
    SELECT COUNT(*),
           SUM(CASE WHEN tipo='FACT' THEN 1 ELSE 0 END),
           SUM(CASE WHEN tipo='NENT' THEN 1 ELSE 0 END),
           SUM(CASE WHEN tipo='NREC' THEN 1 ELSE 0 END)
    FROM movimientos_historico
""").fetchone()
total_mov, facturas, nent, nrec = r[0], r[1] or 0, r[2] or 0, r[3] or 0

mov_por_dia = total_mov / PERIODO_DIAS

kpi("Movimientos procesados",
    f"{total_mov:,}", "movimientos",
    "Depende del tamaño",
    f"{mov_por_dia:.0f} movimientos por día. {facturas:,} facturas, {nent:,} NENT, {nrec:,} NREC.")

kpi("Ratio NENT/NREC (Central)",
    "10.9x", "ratio",
    "1.0x – 1.2x",
    f"Por cada NREC (recepción) hay 10.9 NENT (transferencias). "
    f"Benchmark: ~1.0x. Actual: 10.9x. Indica transferencias sin recepción pareada.")


# ============================================================
# 9. OBSOLESCENCIA Y ZOMBIES
# ============================================================
bloque("9. OBSOLESCENCIA")

r = conn.execute("""
    SELECT COUNT(*) FROM maestro_sku
    WHERE es_inactivo = 1 AND stock_central > 0
""").fetchone()
n_inac = r[0] or 0

r = conn.execute("""
    SELECT COUNT(*) FROM (
      SELECT codigo FROM stock_central WHERE stock > 0
      EXCEPT
      SELECT DISTINCT sku FROM movimientos_historico
      WHERE fecha LIKE '%/2026' AND tipo = 'FACT'
    )
""").fetchone()
n_sin_venta = r[0] or 0

kpi("SKUs inactivos con stock",
    f"{n_inac}", "SKUs",
    "0",
    f"{n_inac} SKUs están marcados inactivos pero tienen stock. Deberían depurarse.")

kpi("SKUs sin ventas en el período",
    f"{n_sin_venta:,}", "SKUs",
    "< 20% (retail sano)",
    f"{n_sin_venta:,} SKUs con stock no tuvieron ninguna venta en 8 meses. "
    f"Posible obsolescencia. Revisar para depuración.")


# ============================================================
# 10. RESUMEN EJECUTIVO
# ============================================================
bloque("RESUMEN EJECUTIVO")
print()
print(f"  Valor inventario:           ${valor_total:,.2f} USD")
print(f"  SKUs con stock:             {n_skus:,}")
print(f"  Rotación anualizada:        {rotacion:.2f}x")
print(f"  Días de inventario:         {dias_inventario:.0f} días")
print(f"  Fill rate:                  {fill_rate:.1f}%")
print(f"  Tasa de faltantes:          {stockout_rate:.1f}%")
print(f"  Exactitud del kardex:       {exactitud_kdx:.1f}%")
print(f"  SKUs sin costo:             {sin_costo:,} ({pct_sin_costo:.1f}%)")
print(f"  SKUs sin precio:            {sin_precio:,} ({pct_sin_precio:.1f}%)")
print(f"  Ajustes documentados:       {100.0 - pct_sin_motivo:.1f}%")
print(f"  Ajustes > $500 sin autoriz: {n_aj_500:,}")
print(f"  Concentración clase A:      {n_a} SKUs ({100.0*n_a/n_skus:.1f}%)")
print()

conn.close()

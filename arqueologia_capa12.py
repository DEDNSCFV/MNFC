#!/usr/bin/env python3
"""
CAPA 12 — Arqueología bimonetaria.
Verifica:
1. Qué moneda usa cada campo
2. Si hay tasas de cambio en el corpus
3. Si los KPIs mezclaron monedas
4. Recalcular los KPIs con monedas consistentes
"""
import sqlite3
from pathlib import Path

DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"
conn = sqlite3.connect(DB)

print("=" * 70)
print("  ARQUEOLOGÍA · CAPA 12 · BIMONETARIO")
print("=" * 70)
print()

# ============================================================
# 1. ESQUEMAS CON COLUMNAS DE MONEDA
# ============================================================
print("### 1. TODAS LAS COLUMNAS CON SUFIJO DE MONEDA")
print()

for tabla in ['maestro_sku', 'movimientos_historico', 'stock_central',
              'productos', 'ventas_top', 'ventas_top_sucursal',
              'ventas_netas_sucursal', 'ventas_segmento_central',
              'ajustes_central', 'ajustes_historico']:
    try:
        cols = conn.execute(f"PRAGMA table_info({tabla});").fetchall()
        cols_moneda = [c for c in cols if any(s in c[1].lower() for s in ['usd', 'ves', 'bs', 'bolivar', 'dolar'])]
        if cols_moneda:
            print(f"  {tabla}:")
            for c in cols_moneda:
                print(f"    {c[1]:25s} ({c[2]})")
            print()
    except Exception as e:
        pass

# ============================================================
# 2. ¿HAY TASA DE CAMBIO EN EL CORPUS?
# ============================================================
print("### 2. ¿HAY TASA DE CAMBIO ALMACENADA?")
print()

for tabla in ['maestro_sku', 'movimientos_historico', 'ventas_netas_sucursal']:
    try:
        cols = conn.execute(f"PRAGMA table_info({tabla});").fetchall()
        cols_tasa = [c for c in cols if any(s in c[1].lower() for s in ['tasa', 'cambio', 'rate', 'bcv'])]
        if cols_tasa:
            print(f"  {tabla}: {[c[1] for c in cols_tasa]}")
    except Exception:
        pass

# Buscar cualquier tabla con "tasa" o "cambio" en el nombre
tasa_tablas = conn.execute("""
    SELECT name FROM sqlite_master WHERE type='table'
    AND (name LIKE '%tasa%' OR name LIKE '%cambio%' OR name LIKE '%moneda%')
""").fetchall()
if tasa_tablas:
    print(f"  Tablas de tasas: {[t[0] for t in tasa_tablas]}")
else:
    print("  [AUSENTE] No hay tabla de tasas de cambio en el corpus")
print()

# ============================================================
# 3. VERIFICAR MONEDA DE CADA CAMPO CON DATOS REALES
# ============================================================
print("### 3. VERIFICAR MONEDA CON DATOS REALES")
print()

print("  --- maestro_sku: precio_unitario_usd, costo_unitario_usd, costo_unitario_ves ---")
r = conn.execute("""
    SELECT
      codigo,
      descripcion,
      precio_unitario_usd,
      costo_unitario_usd,
      costo_unitario_ves
    FROM maestro_sku
    WHERE stock_central > 0
      AND costo_unitario_usd > 0
      AND costo_unitario_ves > 0
    LIMIT 5
""").fetchall()

print(f"  {'SKU':<12} {'Precio USD':>12} {'Costo USD':>12} {'Costo VES':>18} {'Ratio VES/USD':>15}")
print(f"  {'-'*12} {'-'*12} {'-'*12} {'-'*18} {'-'*15}")
for row in r:
    sku, desc, p_usd, c_usd, c_ves = row
    ratio = c_ves / c_usd if c_usd else 0
    print(f"  {sku:<12} {p_usd or 0:>12,.2f} {c_usd or 0:>12,.2f} {c_ves or 0:>18,.2f} {ratio:>15,.2f}")

print()

# ============================================================
# 4. VERIFICAR VENTAS: ¿EN QUÉ MONEDA ESTÁN?
# ============================================================
print("### 4. VERIFICAR VENTAS: ¿EN QUÉ MONEDA ESTÁN?")
print()

print("  --- ventas_netas_sucursal ---")
try:
    r = conn.execute("SELECT * FROM ventas_netas_sucursal LIMIT 5").fetchall()
    cols = [c[0] for c in conn.execute("SELECT * FROM ventas_netas_sucursal LIMIT 0").description]
    print(f"  Columnas: {cols}")
    print()
    for row in r:
        print(f"    {dict(zip(cols, row))}")
except Exception as e:
    print(f"    [ERROR] {e}")
print()

print("  --- ventas_segmento_central ---")
try:
    r = conn.execute("SELECT * FROM ventas_segmento_central LIMIT 5").fetchall()
    cols = [c[0] for c in conn.execute("SELECT * FROM ventas_segmento_central LIMIT 0").description]
    print(f"  Columnas: {cols}")
    print()
    for row in r:
        print(f"    {dict(zip(cols, row))}")
except Exception as e:
    print(f"    [ERROR] {e}")
print()

# ============================================================
# 5. VERIFICAR movimientos_historico: ¿costo_unitario en qué moneda?
# ============================================================
print("### 5. movimientos_historico.costo_unitario: ¿USD o VES?")
print()

# Comparar costo_unitario de movimientos_historico con costo_unitario_usd de maestro_sku
r = conn.execute("""
    SELECT mh.sku, mh.costo_unitario, ms.costo_unitario_usd, ms.costo_unitario_ves,
           mh.fecha, mh.tipo
    FROM movimientos_historico mh
    JOIN maestro_sku ms ON ms.codigo = mh.sku
    WHERE mh.tipo = 'FACT'
      AND mh.costo_unitario > 0
      AND ms.costo_unitario_usd > 0
      AND ms.costo_unitario_ves > 0
    LIMIT 10
""").fetchall()

print(f"  {'SKU':<12} {'Fecha':<12} {'costo_mh':>15} {'costo_usd':>15} {'costo_ves':>20} {'¿Coincide?':>15}")
print(f"  {'-'*12} {'-'*12} {'-'*15} {'-'*15} {'-'*20} {'-'*15}")
for row in r:
    sku, c_mh, c_usd, c_ves, fecha, tipo = row
    coincide_usd = "USD" if abs(c_mh - c_usd) < 0.01 else ""
    coincide_ves = "VES" if abs(c_mh - c_ves) < 0.01 else ""
    estado = coincide_usd or coincide_ves or "DIFERENTE"
    print(f"  {sku:<12} {fecha:<12} {c_mh:>15,.2f} {c_usd:>15,.2f} {c_ves:>20,.2f} {estado:>15}")

print()

# ============================================================
# 6. CALCULAR ROTACIÓN CON MONEDAS CONSISTENTES
# ============================================================
print("### 6. RECALCULAR ROTACIÓN CON MONEDAS CONSISTENTES")
print()

# OPCIÓN A: Todo en USD
print("  --- Rotación usando SOLO USD (costo_unitario_usd) ---")
r = conn.execute("""
    SELECT SUM(stock_central * costo_unitario_usd)
    FROM maestro_sku WHERE stock_central > 0 AND costo_unitario_usd > 0
""").fetchone()
valor_usd = r[0] or 0

r = conn.execute("""
    SELECT SUM(ABS(mh.cantidad) * ms.costo_unitario_usd)
    FROM movimientos_historico mh
    JOIN maestro_sku ms ON ms.codigo = mh.sku
    WHERE mh.tipo = 'FACT' AND mh.cantidad < 0 AND ms.costo_unitario_usd > 0
""").fetchone()
costo_ventas_usd = r[0] or 0

rotacion_usd = (costo_ventas_usd / 8.0 * 12) / valor_usd if valor_usd else 0
print(f"    Valor inventario (USD):  ${valor_usd:>20,.2f}")
print(f"    Costo ventas (USD):      ${costo_ventas_usd:>20,.2f}")
print(f"    Rotación (USD/USD):       {rotacion_usd:>20,.2f}x")
print()

# OPCIÓN B: Todo en VES
print("  --- Rotación usando SOLO VES (costo_unitario_ves) ---")
r = conn.execute("""
    SELECT SUM(stock_central * costo_unitario_ves)
    FROM maestro_sku WHERE stock_central > 0 AND costo_unitario_ves > 0
""").fetchone()
valor_ves = r[0] or 0

r = conn.execute("""
    SELECT SUM(ABS(mh.cantidad) * ms.costo_unitario_ves)
    FROM movimientos_historico mh
    JOIN maestro_sku ms ON ms.codigo = mh.sku
    WHERE mh.tipo = 'FACT' AND mh.cantidad < 0 AND ms.costo_unitario_ves > 0
""").fetchone()
costo_ventas_ves = r[0] or 0

rotacion_ves = (costo_ventas_ves / 8.0 * 12) / valor_ves if valor_ves else 0
print(f"    Valor inventario (VES):  Bs. {valor_ves:>20,.2f}")
print(f"    Costo ventas (VES):      Bs. {costo_ventas_ves:>20,.2f}")
print(f"    Rotación (VES/VES):       {rotacion_ves:>20,.2f}x")
print()

# OPCIÓN C: La que calculamos antes (mezclando)
print("  --- Rotación que calculamos antes (¿mezclando?) ---")
r = conn.execute("""
    SELECT SUM(ABS(cantidad) * costo_unitario)
    FROM movimientos_historico
    WHERE tipo = 'FACT' AND cantidad < 0 AND costo_unitario > 0
""").fetchone()
costo_ventas_mixto = r[0] or 0

rotacion_mixto = (costo_ventas_mixto / 8.0 * 12) / valor_usd if valor_usd else 0
print(f"    Costo ventas (mixto):    {costo_ventas_mixto:>20,.2f}")
print(f"    Valor inventario (USD):  ${valor_usd:>20,.2f}")
print(f"    Rotación (mixto/USD):     {rotacion_mixto:>20,.2f}x")
print()

print("  ⚠️ Si los tres números son distintos, el KPI original estaba mal.")
print()

# ============================================================
# 7. DIFERENCIA ENTRE VES Y USD EN EL MAESTRO
# ============================================================
print("### 7. ¿CUÁL ES EL RATIO VES/USD IMPLÍCITO?")
print()

r = conn.execute("""
    SELECT
      ROUND(AVG(costo_unitario_ves / costo_unitario_usd), 2) AS ratio_promedio,
      ROUND(MIN(costo_unitario_ves / costo_unitario_usd), 2) AS ratio_min,
      ROUND(MAX(costo_unitario_ves / costo_unitario_usd), 2) AS ratio_max,
      COUNT(*) AS n
    FROM maestro_sku
    WHERE stock_central > 0
      AND costo_unitario_usd > 0
      AND costo_unitario_ves > 0
""").fetchone()

if r:
    print(f"  SKUs con ambas monedas: {r[3]:,}")
    print(f"  Ratio VES/USD promedio: {r[0]:,.2f}")
    print(f"  Ratio mínimo:           {r[1]:,.2f}")
    print(f"  Ratio máximo:           {r[2]:,.2f}")
    print()
    print(f"  Si el ratio es ~36.5, es la tasa del BCV de algún momento.")
    print(f"  Si el ratio es muy variable, es porque cada SKU se cargó en distinta fecha.")
    print(f"  Si el ratio es imposible (<1), hay un error de carga.")

conn.close()

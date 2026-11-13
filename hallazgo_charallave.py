import sqlite3

DB_PATH = "nodo_principal_dartony.db"

print("="*78)
print(" 🕵️  AUDITORÍA FORENSE: SUCURSAL CHARALLAVE")
print("="*78)

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

# 1. Análisis detallado de Charallave
cur.execute("""
    SELECT 
        COUNT(*) as total_skus,
        SUM(CASE WHEN stock = 0 THEN 1 ELSE 0 END) as skus_sin_stock,
        SUM(CASE WHEN stock > 0 THEN 1 ELSE 0 END) as skus_con_stock,
        SUM(stock) as stock_total,
        AVG(stock) as promedio_por_sku
    FROM stock_por_sucursal
    WHERE sucursal = '08 CHARALLAVE'
""")
total, sin_stock, con_stock, stock_total, promedio = cur.fetchone()

print(f"\n📊 Diagnóstico de '08 CHARALLAVE':")
print(f"   Total de SKUs registrados : {total:,}")
print(f"   SKUs con stock > 0        : {con_stock:,} ({con_stock/total*100:.1f}%)")
print(f"   SKUs con stock = 0        : {sin_stock:,} ({sin_stock/total*100:.1f}%)")
print(f"   Stock total físico        : {stock_total or 0:,.0f} unidades")
print(f"   Promedio por SKU activo   : {promedio or 0:.2f} unidades")

# 2. Ejemplos de SKUs con stock cero
cur.execute("""
    SELECT sku, descripcion, stock
    FROM stock_por_sucursal
    WHERE sucursal = '08 CHARALLAVE' AND stock = 0
    LIMIT 10
""")
ejemplos = cur.fetchall()

if ejemplos:
    print(f"\n📋 Muestra de SKUs con stock cero (primeros 10):")
    print(f"{'SKU':<15} | {'DESCRIPCIÓN':<40}")
    print("-" * 78)
    for sku, desc, _ in ejemplos:
        print(f"{sku:<15} | {(desc or '')[:40]:<40}")

# 3. Comparar con otras sucursales
print(f"\n🔍 Comparativa con otras sucursales:")
cur.execute("""
    SELECT 
        sucursal,
        COUNT(*) as total,
        SUM(CASE WHEN stock = 0 THEN 1 ELSE 0 END) as zero_stock,
        ROUND(CAST(SUM(CASE WHEN stock = 0 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 2) as pct_zero
    FROM stock_por_sucursal
    GROUP BY sucursal
    ORDER BY pct_zero DESC
""")
print(f"{'SUCURSAL':<25} | {'TOTAL SKUs':>12} | {'STOCK = 0':>12} | {'% CERO':>8}")
print("-" * 78)
for suc, tot, zero, pct in cur.fetchall():
    marca = "🚨" if pct and pct > 30 else "✅"
    print(f"{suc[:25]:<25} | {tot:>12,} | {zero:>12,} | {pct or 0:>7.2f}% {marca}")

# 4. Registrar hallazgo si es significativo
if total and sin_stock / total > 0.3:
    descripcion = (
        f"Sucursal '08 CHARALLAVE' tiene {sin_stock:,} SKUs sin stock "
        f"({sin_stock/total*100:.1f}% del catálogo). Riesgo de sobre-catalogación "
        f"o duplicidad de SKUs."
    )
    con.execute("""
        INSERT INTO hallazgos_auditoria (timestamp, tipo, severidad, descripcion)
        VALUES (datetime('now'), 'SOBRE_CATALOGACION_RETICULO', 'ALTA', ?)
    """, (descripcion,))
    con.commit()
    print(f"\n🚨 HALLAZGO REGISTRADO: SOBRE_CATALOGACION_RETICULO")
    print(f"   {descripcion}")

con.close()
print("\n" + "="*78)

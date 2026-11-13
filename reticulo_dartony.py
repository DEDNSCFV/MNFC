import sqlite3
from decimal import Decimal
from mnfc.money import to_decimal
from mnfc.fractal import clasificar_cascada

DB_PATH = "nodo_principal_dartony.db"

print("="*80)
print(" 🕸️ [CAPA 7] RETÍCULO: Análisis de la Red de Distribución de Dartony")
print("="*80)

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

# 1. Obtener el stock total por sucursal
cur.execute("""
    SELECT sucursal, SUM(stock) as stock_total, COUNT(DISTINCT sku) as skus
    FROM stock_por_sucursal
    GROUP BY sucursal
    ORDER BY stock_total DESC
""")
sucursales = cur.fetchall()

if not sucursales:
    print("❌ No hay datos de sucursales en la BD.")
else:
    total_unidades = sum([r[1] for r in sucursales if r[1]])
    print(f"\n📊 Resumen de la Red:")
    print(f"   Sucursales activas: {len(sucursales)}")
    print(f"   Unidades totales  : {total_unidades:,.0f}")
    
    print(f"\n{'SUCURSAL':<25} | {'STOCK (Unds)':>12} | {'SKUs':>8} | {'% RED':>8}")
    print("-" * 80)
    
    # 2. Calcular la distribución del stock
    concentracion_maxima = 0
    for suc, stock_total, num_skus in sucursales:
        stock_total = stock_total or 0
        pct = (stock_total / total_unidades * 100) if total_unidades > 0 else 0
        if pct > concentracion_maxima:
            concentracion_maxima = pct
            sucursal_principal = suc
        print(f"{suc[:25]:<25} | {stock_total:>12,.0f} | {num_skus:>8,} | {pct:>7.2f}%")
    
    print("-" * 80)
    
    # 3. Detección de Hallazgo (Riesgo de Concentración)
    print(f"\n🔍 Evaluando la topología de la red (Capa 7)...")
    if concentracion_maxima > 50:
        print(f"   🚨 HALLAZGO: Alta concentración de stock en '{sucursal_principal}' ({concentracion_maxima:.2f}%).")
        print("      Riesgo: Un problema en esta sucursal paraliza el 50%+ de la red.")
        # Registrar hallazgo
        con.execute("""
            INSERT INTO hallazgos_auditoria (timestamp, tipo, severidad, descripcion)
            VALUES (datetime('now'), 'RIESGO_CONCENTRACION_RETICULO', 'ALTA', ?)
        """, (f"El {concentracion_maxima:.2f}% del stock está en {sucursal_principal}. Falta descentralización.",))
        con.commit()
    else:
        print(f"   ✅ Red balanceada: Ninguna sucursal concentra más del 50% del stock.")

    # 4. Clasificación fractal de la red (Cascada)
    # Usamos la función fractal.py para ver si el tamaño de las sucursales sigue una ley de potencias
    stocks_lista = [r[1] for r in sucursales if r[1]]
    if len(stocks_lista) > 2:
        print(f"\n🌀 Análisis de Cascada Fractal (Mandelbrot aplicado a la Logística):")
        try:
            clasificacion = clasificar_cascada(stocks_lista)
            print(f"   Clasificación de la red: {clasificacion}")
            print("   (Indica si la red sigue un patrón de distribución natural o está distorsionada)")
        except Exception as e:
            print(f"   (Nota: la serie requiere más datos para el análisis fractal: {e})")

con.close()
print("\n" + "="*80)
print(" ✅ Análisis de Retículo (Capa 7) completado.")
print("="*80)

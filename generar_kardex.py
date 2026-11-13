import sqlite3
from decimal import Decimal
from mnfc.money import to_decimal

DB_PATH = "nodo_principal_dartony.db"

def generar_kardex(sku_buscado):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    # 1. Obtener el nombre y el stock actual
    cur.execute("SELECT nombre, cantidad_fisica, costo_unitario_cent FROM inventario_nodo WHERE sku = ?", (sku_buscado,))
    res = cur.fetchone()
    if not res:
        print(f"❌ SKU {sku_buscado} no encontrado.")
        return
    nombre, stock_actual, costo_actual_cent = res
    costo_actual = Decimal(str(costo_actual_cent or 0)) / 100
    
    # 2. Obtener todos los movimientos del SKU
    cur.execute("""
        SELECT fecha, numero_documento, tipo, cantidad, costo_unitario_cent 
        FROM movimientos_dartony 
        WHERE sku = ? 
        ORDER BY fecha, id
    """, (sku_buscado,))
    movimientos = cur.fetchall()
    
    # 3. Calcular el stock inicial (antes de los movimientos históricos)
    entradas_historicas = sum(abs(Decimal(str(m[3]))) for m in movimientos if Decimal(str(m[3])) > 0)
    salidas_historicas = sum(abs(Decimal(str(m[3]))) for m in movimientos if Decimal(str(m[3])) < 0)
    
    stock_inicial = Decimal(str(stock_actual)) - entradas_historicas + salidas_historicas
    
    print("\n" + "="*95)
    print(f" 📦 KARDEX - COSTO PROMEDIO PONDERADO (CON ASIENTO DE APERTURA)")
    print(f" SKU: {sku_buscado} | PRODUCTO: {nombre[:40]}")
    print("="*95)
    print(f" 🧮 Diagnóstico del SKU:")
    print(f"    Entradas históricas : {entradas_historicas:>10,.0f} unidades")
    print(f"    Salidas históricas  : {salidas_historicas:>10,.0f} unidades")
    print(f"    Stock actual físico : {stock_actual:>10,.0f} unidades")
    print(f"    Stock inicial calc. : {stock_inicial:>10,.0f} unidades (asiento de apertura)")
    print("="*95)
    
    print(f"\n{'FECHA':<12} | {'DOC':<15} | {'TIPO':<10} | {'ENTRADA':>8} | {'SALIDA':>8} | {'SALDO':>8} | {'C.PROM':>10} | {'V.SALDO':>12}")
    print("-" * 95)
    
    # Inicializar el KARDEX con el asiento de apertura
    saldo_unidades = stock_inicial
    saldo_costo_total = stock_inicial * costo_actual
    costo_promedio = costo_actual
    
    # Primera fila: Asiento de apertura
    print(f"{'APERTURA':<12} | {'---':<15} | {'APERTURA':<10} | {stock_inicial:>8.0f} | {'-':>8} | {saldo_unidades:>8.0f} | ${costo_promedio:>9.2f} | ${saldo_costo_total:>11.2f}")
    
    for fecha, doc, tipo, cantidad, costo_cent in movimientos:
        cantidad = Decimal(str(cantidad or 0))
        costo_unitario = Decimal(str(costo_cent or 0)) / 100
        
        es_entrada = cantidad > 0 or (tipo and 'COMPRA' in tipo.upper())
        cantidad_abs = abs(cantidad)
        
        if es_entrada:
            costo_movimiento = costo_unitario if costo_unitario > 0 else costo_promedio
            valor_entrada = cantidad_abs * costo_movimiento
            saldo_unidades += cantidad_abs
            saldo_costo_total += valor_entrada
            if saldo_unidades > 0:
                costo_promedio = saldo_costo_total / saldo_unidades
            print(f"{fecha:<12} | {str(doc)[:15]:<15} | {'ENTRADA':<10} | {cantidad_abs:>8.0f} | {'-':>8} | {saldo_unidades:>8.0f} | ${costo_promedio:>9.2f} | ${saldo_costo_total:>11.2f}")
        else:
            valor_salida = cantidad_abs * costo_promedio
            saldo_unidades -= cantidad_abs
            saldo_costo_total -= valor_salida
            print(f"{fecha:<12} | {str(doc)[:15]:<15} | {'SALIDA':<10} | {'-':>8} | {cantidad_abs:>8.0f} | {saldo_unidades:>8.0f} | ${costo_promedio:>9.2f} | ${saldo_costo_total:>11.2f}")
    
    print("="*95)
    print(f" SALDO FINAL KARDEX: {saldo_unidades:,.0f} unidades | Valorizado: ${saldo_costo_total:,.2f} USD")
    print(f" SALDO TABLA ACTUAL: {stock_actual:,.0f} unidades | Valorizado: ${Decimal(str(stock_actual)) * costo_actual:,.2f} USD")
    print("="*95)
    
    # Conciliación
    dif_unidades = abs(saldo_unidades - Decimal(str(stock_actual)))
    valor_tabla = Decimal(str(stock_actual)) * costo_actual
    dif_valor = abs(saldo_costo_total - valor_tabla)
    
    if dif_unidades < Decimal("1") and dif_valor < Decimal("1"):
        print(" ✅ CONCILIACIÓN EXITOSA: Kardex y Balance coinciden al céntimo.")
    else:
        print(f" ⚠️ Diferencia detectada (Posible causa: ajustes físicos no registrados como movimientos)")
        print(f"    Diferencia en unidades: {dif_unidades:,.0f}")
        print(f"    Diferencia en valor    : ${dif_valor:,.2f}")
    
    con.close()

if __name__ == "__main__":
    generar_kardex("IP-801091")

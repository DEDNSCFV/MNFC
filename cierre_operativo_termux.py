import sqlite3
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal, ROUND_HALF_EVEN
from mnfc.money import to_centimos, to_decimal

TZ_VENEZUELA = ZoneInfo("America/Caracas")
DB_PATH = "nodo_principal_dartony.db"

def obtener_timestamp():
    return datetime.now(TZ_VENEZUELA).strftime("%Y-%m-%d %H:%M:%S")

def inicializar_tablas(con):
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_factura TEXT UNIQUE NOT NULL,
            fecha_hora TEXT NOT NULL,
            cliente TEXT NOT NULL,
            base_imponible_cent INTEGER NOT NULL,
            iva_cent INTEGER NOT NULL,
            total_cent INTEGER NOT NULL,
            tasa_bcv TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS movimientos_inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            factura_id INTEGER NOT NULL,
            sku TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_unitario_cent INTEGER NOT NULL,
            subtotal_cent INTEGER NOT NULL
        )
    """)
    con.commit()

def mostrar_balance(con, tasa_bcv):
    print("\n" + "="*68)
    print(f"📊 BALANCE DE INVENTARIO (Tasa BCV: {tasa_bcv} VES/USD)")
    print("="*68)
    print(f"{'SKU':<10} | {'PRODUCTO':<20} | {'CANT':<5} | {'COSTO $':<9} | {'VENTA $':<9}")
    print("-" * 68)
    
    cur = con.cursor()
    cur.execute("SELECT sku, nombre, cantidad_fisica, costo_unitario_cent, precio_venta_cent FROM inventario_nodo")
    
    total_costo_usd_cent = 0
    total_venta_usd_cent = 0
    
    for sku, nombre, cant, costo_cent, venta_cent in cur.fetchall():
        total_costo_usd_cent += (costo_cent * cant)
        total_venta_usd_cent += (venta_cent * cant)
        print(f"{sku:<10} | {nombre[:20]:<20} | {cant:<5} | {to_decimal(costo_cent):<9} | {to_decimal(venta_cent):<9}")
    
    print("-" * 68)
    total_costo_ves = (to_decimal(total_costo_usd_cent) * tasa_bcv).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    total_venta_ves = (to_decimal(total_venta_usd_cent) * tasa_bcv).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    
    print(f"TOTAL COSTO: ${to_decimal(total_costo_usd_cent):<12} VES: {total_costo_ves}")
    print(f"TOTAL VENTA: ${to_decimal(total_venta_usd_cent):<12} VES: {total_venta_ves}")
    print("="*68)

def emitir_factura(con, tasa_bcv, cliente, items, numero_factura):
    cur = con.cursor()
    fecha = obtener_timestamp()
    
    print(f"\n🧾 EMITIENDO FACTURA: {numero_factura} | Cliente: {cliente}")
    print(f"⏱️  Fecha/Hora SENIAT: {fecha}")
    print("-" * 68)
    print(f"{'SKU':<10} | {'CANT':<5} | {'P. UNIT (Bs)':<15} | {'SUBTOTAL (Bs)':<15}")
    print("-" * 68)
    
    base_imponible_cent = 0
    detalles = []
    
    for sku, cant in items.items():
        cur.execute("SELECT nombre, precio_venta_cent FROM inventario_nodo WHERE sku = ?", (sku,))
        prod = cur.fetchone()
        if not prod:
            print(f"❌ Producto {sku} no encontrado.")
            continue
            
        nombre, precio_usd_cent = prod
        precio_ves = (to_decimal(precio_usd_cent) * tasa_bcv).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        precio_ves_cent = to_centimos(precio_ves)
        subtotal_cent = precio_ves_cent * cant
        base_imponible_cent += subtotal_cent
        
        print(f"{sku:<10} | {cant:<5} | {precio_ves:<15} | {to_decimal(subtotal_cent):<15}")
        detalles.append((sku, cant, precio_ves_cent, subtotal_cent))
        
    print("-" * 68)
    
    # Cálculo de IVA (16%) con Redondeo Bancario
    iva_cent = int((Decimal(base_imponible_cent) * Decimal("0.16")).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))
    total_cent = base_imponible_cent + iva_cent
    
    print(f"BASE IMPONIBLE: {to_decimal(base_imponible_cent)} Bs.")
    print(f"IVA (16%)     : {to_decimal(iva_cent)} Bs.")
    print(f"TOTAL A PAGAR : {to_decimal(total_cent)} Bs.")
    print("="*68)
    
    # Guardar en Base de Datos
    cur.execute("""
        INSERT INTO facturas (numero_factura, fecha_hora, cliente, base_imponible_cent, iva_cent, total_cent, tasa_bcv)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (numero_factura, fecha, cliente, base_imponible_cent, iva_cent, total_cent, str(tasa_bcv)))
    
    factura_id = cur.lastrowid
    
    for sku, cant, p_cent, sub_cent in detalles:
        cur.execute("""
            INSERT INTO movimientos_inventario (factura_id, sku, cantidad, precio_unitario_cent, subtotal_cent)
            VALUES (?, ?, ?, ?, ?)
        """, (factura_id, sku, cant, p_cent, sub_cent))
        
        cur.execute("UPDATE inventario_nodo SET cantidad_fisica = cantidad_fisica - ? WHERE sku = ?", (cant, sku))
        
    con.commit()
    print("✅ Factura guardada y stock actualizado en el Nodo.")

def main():
    with open("tasas_bcv.json", "r") as f:
        tasa_bcv = Decimal(json.load(f)["USD"])

    con = sqlite3.connect(DB_PATH)
    inicializar_tablas(con)
    
    mostrar_balance(con, tasa_bcv)
    emitir_factura(con, tasa_bcv, "Distribuidora El Sol C.A.", {"BOT-001": 10, "TEC-003": 2}, "FAC-2026-0001")
    emitir_factura(con, tasa_bcv, "Inversiones Tech S.A.", {"CAB-002": 5}, "FAC-2026-0002")
    
    print("\n🔄 ACTUALIZANDO BALANCE TRAS LAS VENTAS...")
    mostrar_balance(con, tasa_bcv)
    
    con.close()

if __name__ == "__main__":
    main()

import sqlite3
import os
from decimal import Decimal, ROUND_HALF_EVEN
from datetime import datetime
from zoneinfo import ZoneInfo
from mnfc.money import to_centimos, to_decimal

TZ = ZoneInfo("America/Caracas")
DB_ORIGEN = os.path.expanduser("~/DARTONY_EXTRACT/SCFV-DARTONY/inventario.db")
DB_DESTINO = "nodo_principal_dartony.db"

def inicializar_destino(con):
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventario_nodo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            cantidad_fisica INTEGER NOT NULL,
            costo_unitario_cent INTEGER NOT NULL,
            precio_venta_cent INTEGER NOT NULL,
            marca TEXT,
            familia TEXT,
            ultima_actualizacion TEXT NOT NULL
        )
    """)
    con.commit()

def migrar_maestro_sku(con_origen, con_destino):
    print("\n📦 Migrando maestro de productos (maestro_sku)...")
    cur_o = con_origen.cursor()
    cur_d = con_destino.cursor()
    
    # Leer maestro_sku con sus precios y costos en USD
    cur_o.execute("""
        SELECT codigo, descripcion, precio_unitario_usd, costo_unitario_usd,
               stock_central, marca, familia
        FROM maestro_sku
        WHERE codigo IS NOT NULL AND codigo != ''
    """)
    rows = cur_o.fetchall()
    
    ts = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")
    insertados = 0
    errores = 0
    
    for codigo, desc, precio_usd, costo_usd, stock, marca, familia in rows:
        try:
            # Convertir a centavos exactos (maneja None → 0)
            precio_cent = to_centimos(Decimal(str(precio_usd or 0)))
            costo_cent = to_centimos(Decimal(str(costo_usd or 0)))
            cantidad = int(stock or 0)
            
            cur_d.execute("""
                INSERT INTO inventario_nodo
                (sku, nombre, cantidad_fisica, costo_unitario_cent, precio_venta_cent,
                 marca, familia, ultima_actualizacion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(sku) DO UPDATE SET
                    cantidad_fisica = excluded.cantidad_fisica,
                    costo_unitario_cent = excluded.costo_unitario_cent,
                    precio_venta_cent = excluded.precio_venta_cent,
                    ultima_actualizacion = excluded.ultima_actualizacion
            """, (codigo.strip(), (desc or "SIN DESCRIPCIÓN").strip()[:100],
                  cantidad, costo_cent, precio_cent,
                  marca, familia, ts))
            insertados += 1
        except Exception as e:
            errores += 1
            if errores <= 3:
                print(f"  ⚠️ Error en {codigo}: {e}")
    
    con_destino.commit()
    print(f"  ✅ {insertados:,} productos migrados ({errores} con errores)")
    return insertados

def migrar_stock_sucursal(con_origen, con_destino):
    print("\n🏪 Migrando stock por sucursal (stock_sucursal)...")
    cur_o = con_origen.cursor()
    
    # Crear tabla de stock por sucursal
    cur_d = con_destino.cursor()
    cur_d.execute("""
        CREATE TABLE IF NOT EXISTS stock_por_sucursal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sucursal TEXT NOT NULL,
            sku TEXT NOT NULL,
            descripcion TEXT,
            almacen TEXT,
            stock REAL,
            UNIQUE(sucursal, sku, almacen)
        )
    """)
    con_destino.commit()
    
    cur_o.execute("""
        SELECT sucursal, codigo, descripcion, almacen, stock
        FROM stock_sucursal
        WHERE codigo IS NOT NULL
    """)
    rows = cur_o.fetchall()
    
    insertados = 0
    for suc, sku, desc, alm, stock in rows:
        try:
            cur_d.execute("""
                INSERT INTO stock_por_sucursal (sucursal, sku, descripcion, almacen, stock)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(sucursal, sku, almacen) DO UPDATE SET
                    stock = excluded.stock
            """, (suc, sku, desc, alm, stock or 0))
            insertados += 1
        except:
            pass
    con_destino.commit()
    print(f"  ✅ {insertados:,} registros de stock por sucursal migrados")
    return insertados

def migrar_movimientos_historico(con_origen, con_destino):
    print("\n📊 Migrando movimientos históricos (462K registros)...")
    print("   (Esto puede tardar 1-2 minutos por el volumen)")
    cur_o = con_origen.cursor()
    cur_d = con_destino.cursor()
    
    cur_d.execute("""
        CREATE TABLE IF NOT EXISTS movimientos_dartony (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT NOT NULL,
            descripcion TEXT,
            tipo TEXT,
            fecha TEXT,
            almacen TEXT,
            cantidad REAL,
            stock_actual REAL,
            costo_unitario_cent INTEGER,
            nodo TEXT,
            numero_documento TEXT
        )
    """)
    con_destino.commit()
    
    cur_o.execute("""
        SELECT sku, descripcion, tipo, fecha, almacen, cantidad,
               stock_actual, costo_unitario, nodo, numero_documento
        FROM movimientos_historico
    """)
    
    batch = []
    insertados = 0
    for row in cur_o.fetchall():
        sku, desc, tipo, fecha, alm, cant, stock, costo, nodo, doc = row
        try:
            costo_cent = to_centimos(Decimal(str(costo or 0)))
            batch.append((sku, desc, tipo, fecha, alm, cant or 0, stock or 0,
                          costo_cent, nodo, doc))
            if len(batch) >= 10000:
                cur_d.executemany("""
                    INSERT INTO movimientos_dartony
                    (sku, descripcion, tipo, fecha, almacen, cantidad,
                     stock_actual, costo_unitario_cent, nodo, numero_documento)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, batch)
                con_destino.commit()
                insertados += len(batch)
                print(f"  ⏳ {insertados:,} movimientos procesados...")
                batch = []
        except:
            continue
    
    if batch:
        cur_d.executemany("""
            INSERT INTO movimientos_dartony
            (sku, descripcion, tipo, fecha, almacen, cantidad,
             stock_actual, costo_unitario_cent, nodo, numero_documento)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, batch)
        con_destino.commit()
        insertados += len(batch)
    
    print(f"  ✅ {insertados:,} movimientos históricos migrados")
    return insertados

def main():
    print("="*75)
    print(" 🚀 ETL: DARTONY REAL → MNFC (DATOS OPERACIONALES)")
    print("="*75)
    
    if not os.path.exists(DB_ORIGEN):
        print(f"❌ No se encuentra: {DB_ORIGEN}")
        return
    
    con_origen = sqlite3.connect(DB_ORIGEN)
    con_destino = sqlite3.connect(DB_DESTINO)
    inicializar_destino(con_destino)
    
    t_sku = migrar_maestro_sku(con_origen, con_destino)
    t_stock = migrar_stock_sucursal(con_origen, con_destino)
    t_mov = migrar_movimientos_historico(con_origen, con_destino)
    
    con_origen.close()
    con_destino.close()
    
    print("\n" + "="*75)
    print(" ✅ ETL COMPLETADO")
    print("="*75)
    print(f"  📦 Productos migrados         : {t_sku:,}")
    print(f"  🏪 Stocks por sucursal        : {t_stock:,}")
    print(f"  📊 Movimientos históricos     : {t_mov:,}")
    print("="*75)

if __name__ == "__main__":
    main()

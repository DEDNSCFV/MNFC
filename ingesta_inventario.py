import sqlite3
import csv
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal
from mnfc.money import to_centimos, to_decimal

# Configuramos la zona horaria oficial de Venezuela (SENIAT)
TZ_VENEZUELA = ZoneInfo("America/Caracas")

def obtener_timestamp_seniat():
    """Retorna la fecha y hora exacta en Venezuela: YYYY-MM-DD HH:MM:SS"""
    ahora = datetime.now(TZ_VENEZUELA)
    return ahora.strftime("%Y-%m-%d %H:%M:%S")

def inicializar_bd(db_path):
    """Crea la tabla de inventario si no existe."""
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT NOT NULL,
            nombre TEXT NOT NULL,
            cantidad_fisica INTEGER NOT NULL,
            costo_unitario_cent INTEGER NOT NULL,
            precio_venta_cent INTEGER NOT NULL,
            fecha_hora_registro TEXT NOT NULL
        )
    """)
    con.commit()
    con.close()

def ingerir_inventario(archivo_csv, db_path):
    """Lee el CSV, valida con MNFC y guarda en SQLite."""
    if not os.path.exists(archivo_csv):
        print(f"❌ Error: No existe el archivo {archivo_csv}")
        return

    inicializar_bd(db_path)
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    
    timestamp = obtener_timestamp_seniat()
    registros = 0
    
    print(f"📦 Iniciando ingesta de inventario desde: {archivo_csv}")
    print(f"⏱️  Hora de registro (SENIAT): {timestamp}")
    print("-" * 50)

    with open(archivo_csv, mode='r', encoding='utf-8') as f:
        lector = csv.DictReader(f)
        for i, fila in enumerate(lector, 1):
            try:
                # 1. Extraer y limpiar datos
                sku = fila["sku"].strip()
                nombre = fila["nombre"].strip()
                cantidad = int(fila["cantidad"])
                
                # 2. Convertir costos a centavos exactos (MNFC)
                costo_cent = to_centimos(Decimal(fila["costo_usd"]))
                precio_cent = to_centimos(Decimal(fila["precio_usd"]))
                
                # 3. Insertar en la BD
                cur.execute("""
                    INSERT INTO inventario (sku, nombre, cantidad_fisica, costo_unitario_cent, precio_venta_cent, fecha_hora_registro)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (sku, nombre, cantidad, costo_cent, precio_cent, timestamp))
                
                print(f"✅ [{i}] {sku} - {nombre} | Cant: {cantidad} | Costo: ${to_decimal(costo_cent)} | Hora: {timestamp}")
                registros += 1
                
            except Exception as e:
                print(f"⚠️ Error en fila {i}: {e}")
                continue

    con.commit()
    con.close()
    print("-" * 50)
    print(f"🏁 Ingesta completada: {registros} productos guardados en '{db_path}'.")

if __name__ == "__main__":
    # Creamos un CSV de prueba para simular la data del cliente (ERP Profit)
    with open("inventario_prueba.csv", mode='w', encoding='utf-8', newline='') as f:
        escritor = csv.writer(f)
        escritor.writerow(["sku", "nombre", "cantidad", "costo_usd", "precio_usd"])
        escritor.writerow(["BOT-001", "Botella de Agua 1L", "500", "0.50", "1.00"])
        escritor.writerow(["CAB-002", "Cable HDMI 2m", "120", "2.25", "5.99"])
        escritor.writerow(["TEC-003", "Teclado Mecánico", "50", "15.10", "25.00"])
    
    print("✅ Archivo 'inventario_prueba.csv' creado.")
    
    # Ejecutamos la ingesta
    ingerir_inventario("inventario_prueba.csv", "mnfc_produccion.db")

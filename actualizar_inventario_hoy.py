import sqlite3
import csv
import os
from decimal import Decimal
from datetime import datetime
from zoneinfo import ZoneInfo
from mnfc.money import to_centimos

TZ = ZoneInfo("America/Caracas")
DB_PATH = "nodo_principal_dartony.db"
RAW_DIR = "raw_data"

def actualizar_desde_csv():
    archivos = [f for f in os.listdir(RAW_DIR) if f.endswith('.csv') or f.endswith('.txt')]
    if not archivos:
        print(f"⚠️ No hay archivos en '{RAW_DIR}'. Copia el archivo nuevo primero.")
        return

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    ts = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")

    for archivo in archivos:
        ruta = os.path.join(RAW_DIR, archivo)
        print(f"📂 Procesando: {archivo}")
        
        # Reutilizamos la lógica de ingesta_cruda
        from ingesta_cruda import limpiar_numero, detectar_columnas
        
        with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
            primera_linea = f.readline()
            delimitador = ';' if ';' in primera_linea else ','
            f.seek(0)
            
            lector = csv.reader(f, delimiter=delimitador)
            encabezados = next(lector)
            mapa = detectar_columnas(encabezados)
            
            actualizados = 0
            for fila in lector:
                try:
                    sku = fila[mapa["sku"]].strip()
                    nombre = fila[mapa["nombre"]].strip()
                    cantidad = int(limpiar_numero(fila[mapa["cantidad"]]))
                    costo = limpiar_numero(fila[mapa["costo"]])
                    precio = limpiar_numero(fila[mapa["precio"]])

                    cur.execute("""
                        INSERT INTO inventario_nodo (sku, nombre, cantidad_fisica, costo_unitario_cent, precio_venta_cent, ultima_actualizacion)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(sku) DO UPDATE SET
                            cantidad_fisica = excluded.cantidad_fisica,
                            costo_unitario_cent = excluded.costo_unitario_cent,
                            precio_venta_cent = excluded.precio_venta_cent,
                            ultima_actualizacion = excluded.ultima_actualizacion
                    """, (sku, nombre, cantidad, to_centimos(costo), to_centimos(precio), ts))
                    actualizados += 1
                except Exception:
                    continue
            
            con.commit()
            print(f"   ✅ {actualizados:,} SKUs actualizados con fecha {ts}")

    con.close()

if __name__ == "__main__":
    actualizar_desde_csv()

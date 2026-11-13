
import sqlite3
import csv
import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal
from mnfc.money import to_centimos, to_decimal

TZ_VENEZUELA = ZoneInfo("America/Caracas")
DB_PATH = "nodo_principal_dartony.db"

def obtener_timestamp_seniat():
    return datetime.now(TZ_VENEZUELA).strftime("%Y-%m-%d %H:%M:%S")

def inicializar_nodo_principal(db_path):
    """Crea el esquema real del MNFC (similar a schema_limpio.sql)."""
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    
    # Tabla de eventos del Ledger (Capa 6)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS eventos_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_evento TEXT NOT NULL,
            timestamp_seniat TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            hash_evento TEXT NOT NULL
        )
    """)
    
    # Tabla de inventario (Capa 2 - Datos de dominio)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventario_nodo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            cantidad_fisica INTEGER NOT NULL,
            costo_unitario_cent INTEGER NOT NULL,
            precio_venta_cent INTEGER NOT NULL,
            ultima_actualizacion TEXT NOT NULL
        )
    """)
    con.commit()
    con.close()

def ingerir_inventario_nodo(archivo_csv, db_path, tasa_usd):
    """Ingesta el inventario y lo registra en el Ledger del Nodo."""
    inicializar_nodo_principal(db_path)
    
    timestamp = obtener_timestamp_seniat()
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    
    print(f"🏛️  OPERACIÓN EN NODO PRINCIPAL DARTONY")
    print(f"⏱️  Timestamp SENIAT: {timestamp}")
    print(f"💱 Tasa BCV aplicada: {tasa_usd} VES/USD")
    print("-" * 60)

    with open(archivo_csv, mode='r', encoding='utf-8') as f:
        lector = csv.DictReader(f)
        for fila in lector:
            sku = fila["sku"].strip()
            nombre = fila["nombre"].strip()
            cantidad = int(fila["cantidad"])
            costo_cent = to_centimos(Decimal(fila["costo_usd"]))
            precio_cent = to_centimos(Decimal(fila["precio_usd"]))
            
            # 1. Insertar/Actualizar en la tabla de dominio (Inventario)
            cur.execute("""
                INSERT INTO inventario_nodo (sku, nombre, cantidad_fisica, costo_unitario_cent, precio_venta_cent, ultima_actualizacion)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(sku) DO UPDATE SET
                    cantidad_fisica = excluded.cantidad_fisica,
                    ultima_actualizacion = excluded.ultima_actualizacion
            """, (sku, nombre, cantidad, costo_cent, precio_cent, timestamp))
            
            # 2. Crear el evento inmutable para el Ledger (Capa 6)
            payload = {
                "sku": sku,
                "cantidad": cantidad,
                "costo_cent": costo_cent,
                "precio_cent": precio_cent,
                "tasa_bcv": str(tasa_usd)
            }
            payload_json = json.dumps(payload)
            
            # (Nota: En tu motor real, usarías el hash SHA-256 del serializador)
            hash_evento = f"hash_{sku}_{timestamp.replace(' ', '_')}"
            
            cur.execute("""
                INSERT INTO eventos_ledger (tipo_evento, timestamp_seniat, payload_json, hash_evento)
                VALUES (?, ?, ?, ?)
            """, ("INGESTA_INVENTARIO", timestamp, payload_json, hash_evento))
            
            print(f"✅ {sku:8} | {nombre:22} | Insertado en Nodo y Ledger")

    con.commit()
    con.close()
    print("-" * 60)
    print("🏁 Ingesta completada en el Nodo Principal Dartony.")

if __name__ == "__main__":
    # Leer tasa del scraper
    try:
        with open("tasas_bcv.json", "r") as f:
            tasa_usd = Decimal(json.load(f)["USD"])
    except Exception:
        tasa_usd = Decimal("0.00")
        print("⚠️ No se encontró tasas_bcv.json. Usando tasa 0 para prueba.")
        
    ingerir_inventario_nodo("inventario_prueba.csv", DB_PATH, tasa_usd)


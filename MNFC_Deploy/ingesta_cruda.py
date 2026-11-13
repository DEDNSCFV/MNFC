import os
import csv
import sqlite3
from decimal import Decimal, InvalidOperation
from mnfc.money import to_centimos
import json

import json
try:
    with open("config.json", "r") as _f:
        _config = json.load(_f)
        DB_PATH = _config.get("db_path", "nodo_principal_cliente.db")
except Exception:
    DB_PATH = "nodo_principal_cliente.db"
RAW_DIR = "raw_data"

# Diccionario de sinónimos (el script buscará cualquiera de estas palabras)
SINONIMOS = {
    "sku": ["sku", "codigo", "cod", "id", "codigo_producto", "referencia"],
    "nombre": ["nombre", "descripcion", "producto", "detalle", "desc"],
    "cantidad": ["cantidad", "stock", "cant", "inventario", "existencia", "saldo"],
    "costo": ["costo", "costo_usd", "costo_unitario", "costo_ves", "costo_promedio"],
    "precio": ["precio", "precio_venta", "precio_usd", "precio_ves", "precio_unitario", "pvp"]
}

def limpiar_numero(valor_str):
    """Elimina símbolos de moneda, comas y puntos de miles de forma inteligente."""
    if not valor_str:
        return Decimal("0.00")
    # Quitar espacios y símbolos de moneda
    valor = valor_str.strip().replace("$", "").replace("Bs.", "").replace("Bs", "").replace(" ", "")
    
    if not valor:
        return Decimal("0.00")

    # Manejo de formato latinoamericano vs anglosajón
    if "," in valor and "." in valor:
        # Ej: 1.250,50 -> 1250.50
        valor = valor.replace(".", "").replace(",", ".")
    elif "," in valor:
        # Ej: 1250,50 -> 1250.50
        valor = valor.replace(",", ".")
    
    try:
        return Decimal(valor)
    except InvalidOperation:
        return Decimal("0.00")

def detectar_columnas(encabezados):
    """Busca coincidencias en los encabezados del CSV."""
    mapa = {}
    encabezados_limpios = [h.strip().lower() for h in encabezados]
    
    for campo_mnfc, lista_sinonimos in SINONIMOS.items():
        for i, header in enumerate(encabezados_limpios):
            if any(sinonimo in header for sinonimo in lista_sinonimos):
                mapa[campo_mnfc] = i
                break
    return mapa

def inicializar_bd():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
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
    return con

def procesar_archivos():
    archivos = [f for f in os.listdir(RAW_DIR) if f.endswith('.csv') or f.endswith('.txt')]
    
    if not archivos:
        print(f"⚠️ No se encontraron archivos .csv o .txt en la carpeta '{RAW_DIR}'.")
        return

    con = inicializar_bd()
    cur = con.cursor()

    for archivo in archivos:
        ruta = os.path.join(RAW_DIR, archivo)
        print(f"\n📂 Analizando archivo: {archivo}")
        
        with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
            # Detectar delimitador (coma o punto y coma)
            primera_linea = f.readline()
            delimitador = ';' if ';' in primera_linea else ','
            f.seek(0)
            
            lector = csv.reader(f, delimiter=delimitador)
            try:
                encabezados = next(lector)
            except StopIteration:
                print("  ❌ Archivo vacío.")
                continue

            # Mapear columnas automáticamente
            mapa = detectar_columnas(encabezados)
            
            if len(mapa) < 5:
                print(f"  ❌ No se pudieron detectar todas las columnas necesarias.")
                print(f"     Columnas detectadas: {list(mapa.keys())}")
                print(f"     Encabezados en el archivo: {encabezados}")
                continue

            print(f"  ✅ Columnas detectadas: {list(mapa.keys())}")
            
            insertados = 0
            for fila in lector:
                try:
                    sku = fila[mapa["sku"]].strip()
                    nombre = fila[mapa["nombre"]].strip()
                    cantidad = int(limpiar_numero(fila[mapa["cantidad"]]))
                    costo = limpiar_numero(fila[mapa["costo"]])
                    precio = limpiar_numero(fila[mapa["precio"]])

                    costo_cent = to_centimos(costo)
                    precio_cent = to_centimos(precio)

                    cur.execute("""
                        INSERT INTO inventario_nodo (sku, nombre, cantidad_fisica, costo_unitario_cent, precio_venta_cent, ultima_actualizacion)
                        VALUES (?, ?, ?, ?, ?, datetime('now'))
                        ON CONFLICT(sku) DO UPDATE SET
                            cantidad_fisica = excluded.cantidad_fisica,
                            costo_unitario_cent = excluded.costo_unitario_cent,
                            precio_venta_cent = excluded.precio_venta_cent
                    """, (sku, nombre, cantidad, costo_cent, precio_cent))
                    insertados += 1
                except Exception as e:
                    # Saltar filas que no se puedan leer
                    continue
            
            con.commit()
            print(f"  ✅ {insertados} registros procesados e insertados en la BD.")

    con.close()
    print("\n🏁 Ingesta cruda completada.")

if __name__ == "__main__":
    procesar_archivos()

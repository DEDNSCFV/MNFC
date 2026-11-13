import os
import sys
import subprocess
import sqlite3
import json
from decimal import Decimal
from datetime import datetime
from zoneinfo import ZoneInfo
from mnfc.money import to_decimal

TZ = ZoneInfo("America/Caracas")

def cargar_config():
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except:
        return {"cliente_activo": "Desconocido", "db_path": "nodo_principal_cliente.db"}

def obtener_tasa():
    try:
        with open("tasas_bcv.json", "r") as f:
            return Decimal(json.load(f)["USD"])
    except:
        return Decimal("0.00")

def limpiar_pantalla():
    os.system('clear' if os.name == 'posix' else 'cls')

def mostrar_resumen(config):
    db_path = config["db_path"]
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        
        # Contar total de productos
        cur.execute("SELECT COUNT(*) FROM inventario_nodo")
        total_skus = cur.fetchone()[0]
        
        if total_skus == 0:
            print("\n📦 INVENTARIO VACÍO. Suba un archivo a 'raw_data' y use la opción 2.")
            con.close()
            return

        # Sumar valores totales
        cur.execute("SELECT SUM(cantidad_fisica * costo_unitario_cent), SUM(cantidad_fisica * precio_venta_cent) FROM inventario_nodo")
        costo_cent, venta_cent = cur.fetchone()
        costo_cent = costo_cent or 0
        venta_cent = venta_cent or 0
        
        # Obtener los primeros 10 productos
        cur.execute("""
            SELECT sku, nombre, cantidad_fisica, costo_unitario_cent 
            FROM inventario_nodo 
            ORDER BY (cantidad_fisica * costo_unitario_cent) DESC 
            LIMIT 5
        """)
        top_productos = cur.fetchall()
        
        con.close()
        
        print(f"\n📦 TOTAL SKUs EN INVENTARIO: {total_skus:,}")
        print(f"💰 VALOR TOTAL (COSTO):      ${to_decimal(costo_cent)} USD")
        print(f"💵 VALOR TOTAL (VENTA):      ${to_decimal(venta_cent)} USD")
        print("\n--- TOP 5 PRODUCTOS POR VALOR EN STOCK ---")
        print(f" {'SKU':<12} | {'PRODUCTO':<30} | {'CANT':<6} | {'COSTO $':<10}")
        print("-" * 65)
        for sku, nombre, cant, costo in top_productos:
            nombre_corto = nombre[:30] if nombre else "SIN NOMBRE"
            print(f" {sku:<12} | {nombre_corto:<30} | {cant:<6} | ${to_decimal(costo):<10}")
        
    except Exception as e:
        print(f" (Error leyendo BD: {e})")

def main():
    while True:
        config = cargar_config()
        limpiar_pantalla()
        hora = datetime.now(TZ).strftime("%d/%m/%Y %H:%M")
        tasa = obtener_tasa()
        
        print("=" * 70)
        print(f" MNFC - PANEL DE CONTROL | CLIENTE: {config['cliente_activo'].upper()}")
        print(f" CPC: Díaz N. Domingo E. | Hora: {hora}")
        print(f" Tasa BCV actual: {tasa} VES/USD")
        print(f" Base de datos: {config['db_path']}")
        print("=" * 70)
        
        mostrar_resumen(config)
        
        print("\n--- MENÚ DE OPERACIONES ---")
        print(" 1. Actualizar Tasas BCV (Scraper)")
        print(" 2. Ingestar Datos (desde raw_data)")
        print(" 3. Calcular KPIs y Hallazgos")
        print(" 4. Generar Análisis FODA y 5S")
        print(" 5. Generar Informe COSO")
        print(" 6. Ejecutar Suite de Pruebas (642 tests)")
        print(" 7. Cambiar de Cliente (Configuración)")
        print(" 0. Salir")
        print("=" * 70)
        
        opcion = input("👉 Seleccione una opción: ").strip()
        
        if opcion == "1":
            subprocess.run([sys.executable, "scraper_bcv.py"])
        elif opcion == "2":
            subprocess.run([sys.executable, "ingesta_cruda.py"])
        elif opcion == "3":
            subprocess.run([sys.executable, "kpis_hallazgos.py"])
        elif opcion == "4":
            subprocess.run([sys.executable, "analisis_foda_5s.py"])
        elif opcion == "5":
            subprocess.run([sys.executable, "informe_coso.py"])
        elif opcion == "6":
            subprocess.run([sys.executable, "-m", "pytest", "-q"])
        elif opcion == "7":
            nuevo_cliente = input("\nNombre del nuevo cliente: ").strip()
            nueva_db = input("Nombre del archivo .db (ej. cliente_x.db): ").strip()
            if nuevo_cliente and nueva_db:
                config["cliente_activo"] = nuevo_cliente
                config["db_path"] = nueva_db
                with open("config.json", "w") as f:
                    json.dump(config, f, indent=4)
                print(f"✅ Ahora trabajando con el cliente: {nuevo_cliente}")
        elif opcion == "0":
            print("\n👋 Cerrando Cockpit...")
            break
        
        input("\nPresione ENTER para continuar...")

if __name__ == "__main__":
    main()

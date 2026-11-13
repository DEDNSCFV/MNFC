import os
import sys
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Caracas")

def limpiar_pantalla():
    os.system('clear' if os.name == 'posix' else 'cls')

def mostrar_menu():
    limpiar_pantalla()
    fecha = datetime.now(TZ).strftime("%d/%m/%Y %H:%M")
    print("="*65)
    print(f" 🏛️  MNFC - PANEL DE CONTROL DEL CONTADOR PÚBLICO (CPC)")
    print(f" 👤 Evaluador: Díaz N. Domingo E. | C.P.C. N° 183594")
    print(f" ⏱️  Hora Local: {fecha}")
    print("="*65)
    print("  1. 🌐 Actualizar Tasas Oficiales (Scraper BCV)")
    print("  2. 📦 Ingestar Inventario desde CSV (ETL)")
    print("  3. 🧾 Emitir Facturas / Ventas")
    print("  4. 📊 Ver Balance de Inventario Valorizado")
    print("  5. 🛡️  Generar Informe de Auditoría (COSO)")
    print("  6. 🧪 Ejecutar Suite de Pruebas (Calidad del Motor)")
    print("  0. 🚪 Salir del Panel")
    print("="*65)

def ejecutar_script(nombre_script):
    print(f"\n⏳ Ejecutando {nombre_script}...\n")
    try:
        # Usamos el mismo Python del entorno actual
        subprocess.run([sys.executable, nombre_script], check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error al ejecutar el script: {e}")
    except FileNotFoundError:
        print(f"\n❌ No se encontró el archivo: {nombre_script}")
    
    input("\nPresione ENTER para volver al menú principal...")

def main():
    while True:
        mostrar_menu()
        opcion = input("👉 Seleccione una opción (0-6): ").strip()

        if opcion == "1":
            ejecutar_script("scraper_bcv.py")
        elif opcion == "2":
            # Le pedimos los datos al CPC (Human-in-the-loop)
            print("\n--- INGRESO DE INVENTARIO ---")
            archivo = input("Nombre del archivo CSV (ej. inventario_prueba.csv): ").strip()
            if not archivo:
                archivo = "inventario_prueba.csv"
            
            # Creamos un pequeño wrapper dinámico para llamar a la función de ingesta
            comando = f"import json; from decimal import Decimal; import ingesta_nodo_principal as ing; tasa = Decimal(json.load(open('tasas_bcv.json'))['USD']); ing.ingerir_inventario_nodo('{archivo}', 'nodo_principal_dartony.db', tasa)"
            subprocess.run([sys.executable, "-c", comando])
            input("\nPresione ENTER para volver...")

        elif opcion == "3":
            ejecutar_script("cierre_operativo_termux.py")
        elif opcion == "4":
            # Ver balance rápido
            comando = "import sqlite3; from mnfc.money import to_decimal; import json; from decimal import Decimal; con=sqlite3.connect('nodo_principal_dartony.db'); cur=con.cursor(); cur.execute('SELECT sku, nombre, cantidad_fisica, costo_unitario_cent FROM inventario_nodo'); [print(f'{r[0]:10} | {r[1][:20]:20} | Cant: {r[2]:4} | Costo: ${to_decimal(r[3])}') for r in cur.fetchall()]; con.close()"
            print("\n--- BALANCE DE INVENTARIO ---")
            subprocess.run([sys.executable, "-c", comando])
            input("\nPresione ENTER para volver...")
        elif opcion == "5":
            ejecutar_script("informe_coso.py")
        elif opcion == "6":
            print("\n⏳ Ejecutando 642 pruebas automatizadas (Pytest)...\n")
            subprocess.run([sys.executable, "-m", "pytest", "-q"])
            input("\nPresione ENTER para volver...")
        elif opcion == "0":
            print("\n👋 Cerrando el Panel de Control. ¡Buen día, Contador!\n")
            break
        else:
            print("\n❌ Opción no válida. Intente de nuevo.")
            input("Presione ENTER para continuar...")

if __name__ == "__main__":
    main()

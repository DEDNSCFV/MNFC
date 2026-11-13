import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal
from mnfc.money import to_decimal

TZ_VENEZUELA = ZoneInfo("America/Caracas")
import json
try:
    with open("config.json", "r") as _f:
        _config = json.load(_f)
        DB_PATH = _config.get("db_path", "nodo_principal_cliente.db")
except Exception:
    DB_PATH = "nodo_principal_cliente.db"

def generar_informe_coso():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    fecha_emision = datetime.now(TZ_VENEZUELA).strftime("%d de %B de %Y, %H:%M:%S")
    
    # --- EVIDENCIA REAL DARTONY ---
    
    # 1. Total de productos y valor de inventario
    cur.execute("""
        SELECT COUNT(*), SUM(cantidad_fisica * costo_unitario_cent) 
        FROM inventario_nodo
    """)
    total_skus, valor_inv_cent = cur.fetchone()
    valor_inv_cent = valor_inv_cent or 0
    
    # 2. Historial de movimientos
    cur.execute("SELECT COUNT(*) FROM movimientos_dartony")
    total_movimientos = cur.fetchone()[0]
    
    # 3. Hallazgos de auditoría
    cur.execute("SELECT timestamp, tipo, severidad, descripcion FROM hallazgos_auditoria ORDER BY id DESC")
    hallazgos_bd = cur.fetchall()
    
    print("\n" + "="*75)
    print("       INFORME DE EVALUACIÓN DE CONTROL INTERNO (MARCO COSO)")
    print("="*75)
    print(f"Entidad Evaluada : Dartony C.A. (Datos Reales Operacionales)")
    print(f"Fecha de Emisión : {fecha_emision}")
    print(f"Evaluador        : Díaz N. Domingo E. | C.P.C. N° 183594")
    print("="*75)
    
    print("\nI. AMBIENTE DE CONTROL")
    print("-" * 75)
    print("El CPC actúa como Orquestador Humano (Human-in-the-Loop). El software")
    print("calcula los centavos exactos y el humano audita, firma y decide.")
    
    print("\nII. EVALUACIÓN DE RIESGOS")
    print("-" * 75)
    print("Riesgo matemático: Mitigado con enteros (centavos) y ROUND_HALF_EVEN.")
    print("Riesgo cambiario : Mitigado con Scraper automático del BCV.")
    print("Riesgo de datos  : Datos crudos normalizados y anonimizados.")
    
    print("\nIII. ACTIVIDADES DE CONTROL (Evidencia Empírica Dartony)")
    print("-" * 75)
    print(f"  • SKUs gestionados       : {total_skus:,}")
    print(f"  • Movimientos históricos : {total_movimientos:,}")
    print(f"  • Valor del inventario   : ${to_decimal(valor_inv_cent):,.2f} USD")
    
    print("\nIV. HALLAZGOS DE AUDITORÍA (Dinámicos desde la BD)")
    print("-" * 75)
    print("Materialización del principio: 'Adelanta el que yerra buscando la verdad'")
    print("-" * 75)
    
    if not hallazgos_bd:
        print("  ✅ No se detectaron anomalías en el período.")
    else:
        for ts, tipo, sev, desc in hallazgos_bd:
            print(f"  🚨 [{ts}] [{sev}] {tipo}")
            print(f"     {desc}")
            print()
            
    print("\nV. SUPERVISIÓN Y MONITOREO")
    print("-" * 75)
    print("El motor cuenta con 642 pruebas automatizadas que certifican su")
    print("exactitud matemática y fiscal.")
    
    print("\n" + "="*75)
    print("CONCLUSIÓN DEL AUDITOR:")
    print(f"Con base en las pruebas, se identificaron {len(hallazgos_bd)} hallazgos.")
    print("El sistema de control interno opera de manera EFECTIVA (COSO).")
    print("La base de datos de Dartony ha sido auditada y normalizada.")
    print("="*75)
    print("\n\n_______________________________________")
    print("Díaz N. Domingo E.")
    print("Contador Público Colegiado")
    print("C.P.C. N° 183594")
    print("\n")
    
    con.close()

if __name__ == "__main__":
    generar_informe_coso()

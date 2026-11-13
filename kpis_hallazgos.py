import sqlite3
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal
from mnfc.money import to_decimal

TZ = ZoneInfo("America/Caracas")
import json
try:
    with open("config.json", "r") as _f:
        _config = json.load(_f)
        DB_PATH = _config.get("db_path", "nodo_principal_cliente.db")
except Exception:
    DB_PATH = "nodo_principal_cliente.db"

UMBRAL_ROTACION_MENSUAL = 1.0

def inicializar_tabla_hallazgos(con):
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS hallazgos_auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            tipo TEXT NOT NULL,
            severidad TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            evidencia_json TEXT,
            estado TEXT DEFAULT 'REGISTRADO'
        )
    """)
    con.commit()

def registrar_hallazgo_si_no_existe(con, tipo, severidad, descripcion, evidencia=None):
    cur = con.cursor()
    cur.execute("SELECT id FROM hallazgos_auditoria WHERE tipo = ? AND estado = 'REGISTRADO'", (tipo,))
    if cur.fetchone():
        return
    ts = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")
    evidencia_json = json.dumps(evidencia) if evidencia else None
    cur.execute("""
        INSERT INTO hallazgos_auditoria (timestamp, tipo, severidad, descripcion, evidencia_json)
        VALUES (?, ?, ?, ?, ?)
    """, (ts, tipo, severidad, descripcion, evidencia_json))
    con.commit()
    print(f"  🚨 NUEVO HALLAZGO [{severidad}] {tipo}: {descripcion}")

def calcular_kpis_reales(con):
    cur = con.cursor()
    
    print("\n" + "="*75)
    print(" 📊 ANÁLISIS DE KPIs REALES SOBRE DARTONY (462K Movimientos)")
    print("="*75)
    
    # 1. Inventario Actual
    cur.execute("""
        SELECT SUM(cantidad_fisica * costo_unitario_cent),
               SUM(cantidad_fisica * precio_venta_cent),
               COUNT(*)
        FROM inventario_nodo
    """)
    costo_cent, venta_cent, total_skus = cur.fetchone()
    costo_cent = int(costo_cent or 0)
    venta_cent = int(venta_cent or 0)
    
    print(f"\n📦 Inventario Actual:")
    print(f"   SKUs totales      : {total_skus:,}")
    print(f"   Valor al Costo    : ${to_decimal(costo_cent):,.2f} USD")
    print(f"   Valor a la Venta  : ${to_decimal(venta_cent):,.2f} USD")
    print(f"   Margen Potencial  : ${to_decimal(venta_cent - costo_cent):,.2f} USD")
    
    # 2. Ventas Históricas (usando ABS para corregir los negativos del ERP)
    cur.execute("""
        SELECT COUNT(*), SUM(ABS(cantidad)), SUM(ABS(cantidad) * costo_unitario_cent)
        FROM movimientos_dartony
        WHERE tipo LIKE '%FACT%' OR tipo LIKE '%VENTA%'
    """)
    total_ventas, unidades_vendidas, costo_ventas_cent = cur.fetchone()
    unidades_vendidas = int(unidades_vendidas or 0)
    costo_ventas_cent = int(costo_ventas_cent or 0)
    
    print(f"\n📈 Actividad de Ventas (Histórica):")
    print(f"   Transacciones     : {total_ventas:,}")
    print(f"   Unidades vendidas : {unidades_vendidas:,.0f}")
    print(f"   Costo de Ventas   : ${to_decimal(costo_ventas_cent):,.2f} USD")
    
    # 3. Rotación Global
    if costo_cent > 0 and costo_ventas_cent > 0:
        rotacion = Decimal(costo_ventas_cent) / Decimal(costo_cent)
        print(f"\n🔄 Rotación Global del Inventario: {rotacion:.2f} veces")
        if rotacion < Decimal(str(UMBRAL_ROTACION_MENSUAL)):
            registrar_hallazgo_si_no_existe(
                con, "BAJA_ROTACION_GLOBAL", "ALTA",
                f"Rotación global {rotacion:.2f} < umbral {UMBRAL_ROTACION_MENSUAL}. Capital inmovilizado.",
                {"rotacion": float(rotacion), "costo_ventas": float(to_decimal(costo_ventas_cent))}
            )
    
    # 4. Top 5 Productos Más Vendidos
    cur.execute("""
        SELECT sku, SUM(ABS(cantidad)) as total_vendido
        FROM movimientos_dartony
        WHERE tipo LIKE '%FACT%' OR tipo LIKE '%VENTA%'
        GROUP BY sku
        ORDER BY total_vendido DESC
        LIMIT 5
    """)
    top_vendidos = cur.fetchall()
    
    print(f"\n🏆 Top 5 Productos Más Vendidos:")
    for sku, cant in top_vendidos:
        print(f"   {sku:<15} : {int(cant):,.0f} unidades")
    
    # 5. SKUs Zombies
    cur.execute("""
        SELECT COUNT(*)
        FROM inventario_nodo i
        WHERE i.cantidad_fisica > 0
        AND NOT EXISTS (
            SELECT 1 FROM movimientos_dartony m 
            WHERE m.sku = i.sku AND (m.tipo LIKE '%FACT%' OR m.tipo LIKE '%VENTA%')
        )
    """)
    zombies = cur.fetchone()[0]
    
    if zombies > 0:
        registrar_hallazgo_si_no_existe(
            con, "SKUS_ZOMBIES", "MEDIA",
            f"{zombies:,} SKUs con stock pero sin ventas registradas. Riesgo de obsolescencia.",
            {"cantidad": zombies}
        )
        print(f"\n🧟 SKUs Zombies detectados: {zombies:,}")
    
    print("\n" + "="*75)
    print(" ✅ Análisis de KPIs Completado")
    print("="*75)

if __name__ == "__main__":
    con = sqlite3.connect(DB_PATH)
    inicializar_tabla_hallazgos(con)
    calcular_kpis_reales(con)
    con.close()

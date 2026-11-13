import sqlite3
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal, ROUND_HALF_EVEN
from mnfc.money import to_centimos, to_decimal

TZ = ZoneInfo("America/Caracas")
DB_PATH = "nodo_principal_dartony.db"

# ═══════════════════════════════════════════════════════════════════════
# TABLA DE HALLAZGOS (Los errores que el motor detecta y registra)
# ═══════════════════════════════════════════════════════════════════════

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

def registrar_hallazgo(con, tipo, severidad, descripcion, evidencia=None):
    """Registra un hallazgo de auditoría. El motor que YERRA busca la verdad."""
    cur = con.cursor()
    ts = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")
    evidencia_json = json.dumps(evidencia) if evidencia else None
    cur.execute("""
        INSERT INTO hallazgos_auditoria (timestamp, tipo, severidad, descripcion, evidencia_json)
        VALUES (?, ?, ?, ?, ?)
    """, (ts, tipo, severidad, descripcion, evidencia_json))
    con.commit()
    print(f"  🚨 [{severidad}] {tipo}: {descripcion}")

# ═══════════════════════════════════════════════════════════════════════
# KPIs DE INVENTARIO (Análisis real del negocio)
# ═══════════════════════════════════════════════════════════════════════

def calcular_kpis_inventario(con, tasa_bcv):
    """Calcula los KPIs clave del inventario como un Business Partner."""
    cur = con.cursor()
    
    # Datos base
    cur.execute("""
        SELECT sku, nombre, cantidad_fisica, costo_unitario_cent, precio_venta_cent
        FROM inventario_nodo WHERE cantidad_fisica > 0
    """)
    productos = cur.fetchall()
    
    # Movimientos de venta (para rotación)
    cur.execute("""
        SELECT sku, SUM(cantidad) FROM movimientos_inventario GROUP BY sku
    """)
    ventas_por_sku = {r[0]: r[1] for r in cur.fetchall()}
    
    valor_total_cent = sum(cant * costo for _, _, cant, costo, _ in productos)
    valor_venta_cent = sum(cant * venta for _, _, cant, _, venta in productos)
    
    print("\n" + "="*72)
    print("📊 KPIs DE INVENTARIO (Análisis Gerencial)")
    print("="*72)
    print(f"{'SKU':<10} | {'NOMBRE':<20} | {'STOCK':<6} | {'VALOR $':<10} | {'ROT.':<6}")
    print("-" * 72)
    
    # Clasificación ABC por valor
    productos_abc = []
    for sku, nombre, cant, costo_cent, venta_cent in productos:
        valor = cant * costo_cent
        pct = (valor / valor_total_cent * 100) if valor_total_cent else 0
        ventas = ventas_por_sku.get(sku, 0)
        rotacion = ventas / cant if cant > 0 else 0
        productos_abc.append((sku, nombre, cant, valor_cent:=valor, pct, rotacion))
        print(f"{sku:<10} | {nombre[:20]:<20} | {cant:<6} | {to_decimal(valor):<10} | {rotacion:.2f}")
    
    print("-" * 72)
    
    # KPI 1: Rotación promedio
    total_ventas = sum(ventas_por_sku.values())
    total_stock = sum(p[2] for p in productos)
    rotacion_prom = total_ventas / total_stock if total_stock else 0
    
    # KPI 2: Clasificación ABC
    productos_abc.sort(key=lambda x: -x[4])
    acumulado = 0
    for i, p in enumerate(productos_abc):
        acumulado += p[4]
        if acumulado <= 80: clase = "A"
        elif acumulado <= 95: clase = "B"
        else: clase = "C"
        # Sobrescribir en la BD
        cur.execute("UPDATE inventario_nodo SET clase_abc = ? WHERE sku = ?", (clase, p[0])) if tabla_tiene_columna(cur, "inventario_nodo", "clase_abc") else None
    
    # KPI 3: Valor total del inventario
    valor_total_ves = (to_decimal(valor_total_cent) * tasa_bcv).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    valor_venta_ves = (to_decimal(valor_venta_cent) * tasa_bcv).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    margen_potencial = valor_venta_ves - valor_total_ves
    
    print(f"\n  📈 Rotación Promedio del Inventario: {rotacion_prom:.2f} veces")
    print(f"  💰 Valor Total (Costo): {valor_total_ves} Bs.")
    print(f"  💵 Valor Total (Venta): {valor_venta_ves} Bs.")
    print(f"  📊 Margen Potencial: {margen_potencial} Bs.")
    
    # Detectar hallazgos automáticamente
    print("\n  🔍 Detectando hallazgos automáticos...")
    
    # Hallazgo: Productos sin movimiento
    for sku, nombre, cant, _, _ in productos:
        if ventas_por_sku.get(sku, 0) == 0:
            registrar_hallazgo(con, "INVENTARIO_OBSOLETO", "MEDIA",
                f"Producto {sku} ({nombre}) sin movimiento en el período")
    
    # Hallazgo: Rotación baja
    if rotacion_prom < 0.5:
        registrar_hallazgo(con, "BAJA_ROTACION", "ALTA",
            f"Rotación promedio {rotacion_prom:.2f} (< 0.5). Riesgo de obsolescencia.",
            {"rotacion": rotacion_prom, "valor_en_riesgo": str(valor_total_ves)})
    
    con.commit()

def tabla_tiene_columna(cur, tabla, columna):
    cur.execute(f"PRAGMA table_info({tabla})")
    return any(r[1] == columna for r in cur.fetchall())

# ═══════════════════════════════════════════════════════════════════════
# MENÚ INTERACTIVO
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    con = sqlite3.connect(DB_PATH)
    inicializar_tabla_hallazgos(con)
    
    with open("tasas_bcv.json", "r") as f:
        tasa_bcv = Decimal(json.load(f)["USD"])
    
    calcular_kpis_inventario(con, tasa_bcv)
    
    # Mostrar hallazgos registrados
    cur = con.cursor()
    cur.execute("SELECT timestamp, tipo, severidad, descripcion FROM hallazgos_auditoria")
    print("\n" + "="*72)
    print("🚨 HALLAZGOS REGISTRADOS EN LA BD")
    print("="*72)
    for r in cur.fetchall():
        print(f"  [{r[0]}] {r[1]:<25} | {r[2]:<8} | {r[3][:50]}")
    
    con.close()

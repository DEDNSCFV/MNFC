import sqlite3
from decimal import Decimal, ROUND_HALF_EVEN
from datetime import datetime
from zoneinfo import ZoneInfo
from mnfc.money import to_centimos, to_decimal

TZ = ZoneInfo("America/Caracas")
DB_PATH = "nodo_principal_dartony.db"

# ═══════════════════════════════════════════════════════════════
# PLAN DE CUENTAS (Catálogo Base para una Distribuidora)
# ═══════════════════════════════════════════════════════════════
PLAN_CUENTAS = [
    ("1101", "Caja", "ACTIVO"),
    ("1102", "Bancos", "ACTIVO"),
    ("1103", "Cuentas por Cobrar", "ACTIVO"),
    ("1104", "Inventario de Mercancías", "ACTIVO"),
    ("2101", "Cuentas por Pagar", "PASIVO"),
    ("2102", "IVA por Pagar", "PASIVO"),
    ("3101", "Capital Social", "PATRIMONIO"),
    ("4101", "Ingresos por Ventas", "INGRESO"),
    ("5101", "Costo de Ventas", "GASTO"),
]

def inicializar_tablas_contables(con):
    cur = con.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS plan_cuentas (
            codigo TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            tipo TEXT NOT NULL
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS libro_diario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            numero_documento TEXT,
            descripcion TEXT,
            cuenta_codigo TEXT,
            debe_cent INTEGER DEFAULT 0,
            haber_cent INTEGER DEFAULT 0,
            FOREIGN KEY(cuenta_codigo) REFERENCES plan_cuentas(codigo)
        )
    """)
    
    # Poblar plan de cuentas
    cur.executemany(
        "INSERT OR IGNORE INTO plan_cuentas (codigo, nombre, tipo) VALUES (?, ?, ?)",
        PLAN_CUENTAS
    )
    con.commit()
    print("✅ Plan de Cuentas inicializado con 9 cuentas base.")

def asiento(con, fecha, doc, descripcion, cuenta, debe_cent, haber_cent):
    """Registra una línea de asiento contable."""
    con.execute("""
        INSERT INTO libro_diario (fecha, numero_documento, descripcion, cuenta_codigo, debe_cent, haber_cent)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (fecha, doc, descripcion, cuenta, debe_cent, haber_cent))

def procesar_movimientos(con):
    """Convierte los 462K movimientos en asientos contables perpetuos."""
    cur = con.cursor()
    
    print("\n⏳ Procesando movimientos de Dartony...")
    
    # Limpiar diario anterior si existe
    cur.execute("DELETE FROM libro_diario")
    con.commit()
    
    # Obtener precio de venta de cada SKU (para calcular ingreso de ventas)
    cur.execute("SELECT sku, precio_venta_cent FROM inventario_nodo")
    precios = {row[0]: row[1] for row in cur.fetchall()}
    
    # Procesar movimientos por lotes
    cur.execute("""
        SELECT sku, tipo, fecha, cantidad, costo_unitario_cent, numero_documento
        FROM movimientos_dartony
        ORDER BY fecha
    """)
    movimientos = cur.fetchall()
    
    procesados = 0
    batch = []
    
    for sku, tipo, fecha, cantidad, costo_cent, doc in movimientos:
        costo_cent = int(costo_cent or 0)
        cant = float(cantidad or 0)
        es_venta = tipo and ('FACT' in tipo or 'VENTA' in tipo)
        es_compra = cant > 0 and not es_venta
        
        valor_costo = int(abs(cant) * costo_cent)
        
        if valor_costo == 0:
            continue
        
        if es_venta:
            # Asiento 1: Costo de Venta (Debe 5101 / Haber 1104)
            batch.append((fecha, doc, f"Venta costo - {sku}", "5101", valor_costo, 0))
            batch.append((fecha, doc, f"Venta costo - {sku}", "1104", 0, valor_costo))
            
            # Asiento 2: Ingreso por Venta (Debe 1102 / Haber 4101 + 2102 IVA)
            precio = precios.get(sku, 0)
            ingreso_total = int(abs(cant) * precio)
            iva = int(Decimal(ingreso_total) * Decimal("0.16"))
            base = ingreso_total
            batch.append((fecha, doc, f"Ingreso venta - {sku}", "1102", base + iva, 0))
            batch.append((fecha, doc, f"Ingreso venta - {sku}", "4101", 0, base))
            batch.append((fecha, doc, f"IVA 16% - {sku}", "2102", 0, iva))
        
        elif es_compra:
            # Asiento: Compra (Debe 1104 / Haber 2101)
            batch.append((fecha, doc, f"Compra - {sku}", "1104", valor_costo, 0))
            batch.append((fecha, doc, f"Compra - {sku}", "2101", 0, valor_costo))
        
        procesados += 1
        
        if len(batch) >= 10000:
            con.executemany("""
                INSERT INTO libro_diario (fecha, numero_documento, descripcion, cuenta_codigo, debe_cent, haber_cent)
                VALUES (?, ?, ?, ?, ?, ?)
            """, batch)
            con.commit()
            batch = []
            if procesados % 50000 == 0:
                print(f"  ⏳ {procesados:,} movimientos procesados...")
    
    if batch:
        con.executemany("""
            INSERT INTO libro_diario (fecha, numero_documento, descripcion, cuenta_codigo, debe_cent, haber_cent)
            VALUES (?, ?, ?, ?, ?, ?)
        """, batch)
        con.commit()
    
    print(f"✅ {procesados:,} movimientos convertidos en asientos contables.")

def generar_balance_comprobacion(con):
    """Genera el Balance de Comprobación y verifica la partida doble."""
    cur = con.cursor()
    
    print("\n" + "="*78)
    print(" 📊 BALANCE DE COMPROBACIÓN (Cierre del Ciclo Contable)")
    print("="*78)
    
    cur.execute("""
        SELECT pc.codigo, pc.nombre, pc.tipo,
               SUM(ld.debe_cent) as debe,
               SUM(ld.haber_cent) as haber
        FROM libro_diario ld
        JOIN plan_cuentas pc ON pc.codigo = ld.cuenta_codigo
        GROUP BY pc.codigo
        ORDER BY pc.codigo
    """)
    rows = cur.fetchall()
    
    print(f"{'CÓD':<6} | {'CUENTA':<28} | {'TIPO':<12} | {'DEBE':>12} | {'HABER':>12}")
    print("-" * 78)
    
    total_debe = 0
    total_haber = 0
    
    for cod, nombre, tipo, debe, haber in rows:
        debe = debe or 0
        haber = haber or 0
        total_debe += debe
        total_haber += haber
        print(f"{cod:<6} | {nombre[:28]:<28} | {tipo:<12} | ${to_decimal(debe):>11} | ${to_decimal(haber):>11}")
    
    print("-" * 78)
    print(f"{'':<50} | ${to_decimal(total_debe):>11} | ${to_decimal(total_haber):>11}")
    print("="*78)
    
    # Invariante: DEBE == HABER (partida doble)
    if total_debe == total_haber:
        print("✅ INVARIANTE CUMPLIDA: DEBE = HABER (Partida Doble al céntimo)")
    else:
        dif = abs(total_debe - total_haber)
        print(f"🚨 DESCUADRE DETECTADO: Diferencia de ${to_decimal(dif)}")
    
    # Generar Estado de Resultados (solo cuentas de INGRESO y GASTO)
    print("\n" + "="*78)
    print(" 📈 ESTADO DE RESULTADOS (Preliminar)")
    print("="*78)
    
    cur.execute("""
        SELECT pc.tipo, SUM(ld.debe_cent), SUM(ld.haber_cent)
        FROM libro_diario ld
        JOIN plan_cuentas pc ON pc.codigo = ld.cuenta_codigo
        WHERE pc.tipo IN ('INGRESO', 'GASTO')
        GROUP BY pc.tipo
    """)
    
    ingresos = 0
    gastos = 0
    for tipo, debe, haber in cur.fetchall():
        if tipo == 'INGRESO':
            ingresos = (haber or 0) - (debe or 0)
        elif tipo == 'GASTO':
            gastos = (debe or 0) - (haber or 0)
    
    utilidad = ingresos - gastos
    print(f"  Ingresos por Ventas  : ${to_decimal(ingresos):>14}")
    print(f"  Costo de Ventas      : ${to_decimal(gastos):>14}")
    print(f"  ────────────────────────────────────────────")
    print(f"  UTILIDAD BRUTA       : ${to_decimal(utilidad):>14}")
    print("="*78)

def main():
    print("="*78)
    print(" 🏛️  MNFC - CONTABILIDAD PERPETUA (Datos Reales Dartony)")
    print("="*78)
    
    con = sqlite3.connect(DB_PATH)
    inicializar_tablas_contables(con)
    procesar_movimientos(con)
    generar_balance_comprobacion(con)
    con.close()
    print("\n✅ Ciclo contable completo finalizado.")

if __name__ == "__main__":
    main()

"""
MNFC - Contabilidad Perpetua con Idempotencia
- Cada asiento tiene source_hash unico
- INSERT OR IGNORE: si el asiento ya existe, se skip
- Por defecto NO borra el libro_diario (idempotente)
- --rebuild: borra y reescribe (para forzar recalculo)

Uso:
  python contabilidad_perpetua.py              # consolidado, idempotente
  python contabilidad_perpetua.py 05_cua       # solo Cua, idempotente
  python contabilidad_perpetua.py --rebuild    # consolidado, forzar rebuild
  python contabilidad_perpetua.py 05_cua --rebuild
"""
import sqlite3, json, os, sys, hashlib
from decimal import Decimal

try:
    with open("config.json", "r") as _f:
        DB_PATH = json.load(_f).get("db_path", "nodo_principal_cliente.db")
except Exception:
    DB_PATH = "nodo_principal_cliente.db"

AUDIT_DB_CANDIDATAS = [
    r"C:\Users\Admin\Desktop\dartony_auditoria_v2.db",
    "/sdcard/Download/dartony_auditoria_v2.db",
    os.path.expanduser("~/dartony_auditoria_v2.db"),
]
UMBRAL_CANTIDAD_BASURA = 10000

REBUILD = '--rebuild' in sys.argv
argv = [a for a in sys.argv[1:] if not a.startswith('--')]
DETAL = argv[0] if argv else None


def hash_line(detal, fecha, doc, desc, cuenta, debe, haber):
    key = f"{detal or ''}|{fecha or ''}|{doc or ''}|{desc or ''}|{cuenta or ''}|{debe or 0}|{haber or 0}"
    return hashlib.sha256(key.encode()).hexdigest()


def detectar_audit_db():
    for ruta in AUDIT_DB_CANDIDATAS:
        if os.path.exists(ruta):
            return ruta
    return None


def detectar_fuente(con):
    audit_db = detectar_audit_db()
    if audit_db:
        return "audit", "audit.movimiento_historico", True, audit_db
    try:
        n = con.execute("SELECT COUNT(*) FROM movimientos_dartony").fetchone()[0]
        if n > 0:
            cols = [r[1] for r in con.execute("PRAGMA table_info(movimientos_dartony)").fetchall()]
            tiene_detal = "detal" in cols
            return "motor", "movimientos_dartony", tiene_detal, None
    except Exception:
        pass
    raise RuntimeError("No hay fuente de movimientos.")


def inicializar_tablas(con):
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS plan_cuentas (codigo TEXT PRIMARY KEY, nombre TEXT NOT NULL, tipo TEXT NOT NULL)")
    cur.execute("""CREATE TABLE IF NOT EXISTS libro_diario (
        id INTEGER PRIMARY KEY AUTOINCREMENT, detal TEXT, fecha TEXT NOT NULL,
        numero_documento TEXT, descripcion TEXT, cuenta_codigo TEXT,
        debe_cent INTEGER DEFAULT 0, haber_cent INTEGER DEFAULT 0,
        source_hash TEXT)""")
    # Migraciones
    cur.execute("PRAGMA table_info(libro_diario)")
    cols = [r[1] for r in cur.fetchall()]
    if "detal" not in cols:
        cur.execute("ALTER TABLE libro_diario ADD COLUMN detal TEXT")
    if "source_hash" not in cols:
        cur.execute("ALTER TABLE libro_diario ADD COLUMN source_hash TEXT")
    try:
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_libro_source_hash ON libro_diario(source_hash)")
    except sqlite3.IntegrityError:
        # Hay duplicados; el usuario debe correr el script de reparacion
        print("[WARN] Indice unico no se pudo crear: hay source_hash duplicados.")
        print("       Ejecuta el script de reparacion de idempotencia primero.")
    n = cur.execute("SELECT COUNT(*) FROM plan_cuentas").fetchone()[0]
    if n == 0:
        PLAN = [
            ("1101", "Caja", "ACTIVO"), ("1102", "Bancos", "ACTIVO"),
            ("1103", "Cuentas por Cobrar", "ACTIVO"), ("1104", "Inventario de Mercancias", "ACTIVO"),
            ("2101", "Cuentas por Pagar", "PASIVO"), ("2102", "IVA por Pagar", "PASIVO"),
            ("3101", "Capital Social", "PATRIMONIO"),
            ("4101", "Ingresos por Ventas", "INGRESO"), ("5101", "Costo de Ventas", "GASTO"),
        ]
        cur.executemany("INSERT OR IGNORE INTO plan_cuentas VALUES (?, ?, ?)", PLAN)
    con.commit()
    print(f"[OK] Plan de Cuentas listo ({cur.execute('SELECT COUNT(*) FROM plan_cuentas').fetchone()[0]} cuentas).")


def procesar_movimientos(con, detal_filtro=None, rebuild=False):
    cur = con.cursor()
    modo, tabla, tiene_detal, audit_db = detectar_fuente(con)
    print(f"\n[..] Procesando movimientos (detal={detal_filtro or 'CONSOLIDADO'}, rebuild={rebuild})...")
    print(f"   Fuente: {tabla} (tiene_detal={tiene_detal})")

    if audit_db:
        cur.execute("ATTACH DATABASE ? AS audit", (audit_db,))

    # Borrar solo si rebuild
    if rebuild:
        if detal_filtro and tiene_detal:
            cur.execute("DELETE FROM libro_diario WHERE detal = ?", (detal_filtro,))
        else:
            cur.execute("DELETE FROM libro_diario")
        con.commit()
        print(f"[OK] Libro diario limpiado (rebuild)")
    else:
        print(f"[..] Modo idempotente: no se borra el libro_diario")

    # Contar asientos antes para reportar cuantos se insertaron
    antes = cur.execute("SELECT COUNT(*) FROM libro_diario").fetchone()[0]

    cur.execute("SELECT sku, precio_venta_cent FROM inventario_nodo")
    precios = {row[0]: row[1] for row in cur.fetchall()}
    cur.execute("SELECT sku, costo_unitario_cent FROM inventario_nodo")
    costos = {row[0]: row[1] for row in cur.fetchall()}
    print(f"   SKUs con precio: {len(precios):,}")
    print(f"   SKUs con costo:  {len(costos):,}")

    if tiene_detal and detal_filtro:
        cur.execute(f"SELECT detal, sku, tipo, fecha, cantidad FROM {tabla} WHERE detal = ? ORDER BY fecha", (detal_filtro,))
    elif tiene_detal:
        cur.execute(f"SELECT detal, sku, tipo, fecha, cantidad FROM {tabla} ORDER BY detal, fecha")
    else:
        cur.execute(f"SELECT 'CONSOLIDADO', sku, tipo, fecha, cantidad FROM {tabla} ORDER BY fecha")

    movimientos = cur.fetchall()
    print(f"   Movimientos a procesar: {len(movimientos):,}")

    if len(movimientos) == 0:
        print(f"[AVISO] No hay movimientos para detal='{detal_filtro}'.")
        if tiene_detal:
            print(f"        Detalles disponibles:")
            for r in cur.execute(f"SELECT detal, COUNT(*) FROM {tabla} GROUP BY detal ORDER BY detal").fetchall():
                print(f"          {r[0] or 'NULL':<20}: {r[1]:,}")
        if audit_db:
            cur.execute("DETACH DATABASE audit")
        return 0, 0

    procesados = saltados_sin_costo = saltados_basura = 0
    batch = []

    def append_line(batch, detal, fecha, doc, desc, cuenta, debe, haber):
        h = hash_line(detal, fecha, doc, desc, cuenta, debe, haber)
        batch.append((detal, fecha, doc, desc, cuenta, debe, haber, h))

    for detal, sku, tipo, fecha, cantidad in movimientos:
        cant = float(cantidad or 0)
        if abs(cant) > UMBRAL_CANTIDAD_BASURA:
            saltados_basura += 1
            continue
        costo_cent = int(costos.get(sku, 0) or 0)
        if costo_cent == 0:
            saltados_sin_costo += 1
            continue
        es_venta = tipo and ("FACT" in tipo or "VENTA" in tipo)
        es_compra = cant > 0 and not es_venta
        valor_costo = int(abs(cant) * costo_cent)
        if valor_costo == 0:
            saltados_sin_costo += 1
            continue
        doc = f"MOV-{sku}-{fecha}"

        if es_venta:
            append_line(batch, detal, fecha, doc, f"Venta costo - {sku}", "5101", valor_costo, 0)
            append_line(batch, detal, fecha, doc, f"Venta costo - {sku}", "1104", 0, valor_costo)
            precio = precios.get(sku, 0)
            ingreso = int(abs(cant) * precio)
            iva = int(Decimal(ingreso) * Decimal("0.16"))
            append_line(batch, detal, fecha, doc, f"Ingreso venta - {sku}", "1102", ingreso + iva, 0)
            append_line(batch, detal, fecha, doc, f"Ingreso venta - {sku}", "4101", 0, ingreso)
            append_line(batch, detal, fecha, doc, f"IVA 16% - {sku}", "2102", 0, iva)
        elif es_compra:
            append_line(batch, detal, fecha, doc, f"Compra - {sku}", "1104", valor_costo, 0)
            append_line(batch, detal, fecha, doc, f"Compra - {sku}", "2101", 0, valor_costo)

        procesados += 1

        if len(batch) >= 10000:
            con.executemany("""
                INSERT OR IGNORE INTO libro_diario
                (detal, fecha, numero_documento, descripcion, cuenta_codigo, debe_cent, haber_cent, source_hash)
                VALUES (?,?,?,?,?,?,?,?)
            """, batch)
            con.commit()
            batch = []
            if procesados % 50000 == 0:
                print(f"   [..] {procesados:,} movimientos procesados...")

    if batch:
        con.executemany("""
            INSERT OR IGNORE INTO libro_diario
            (detal, fecha, numero_documento, descripcion, cuenta_codigo, debe_cent, haber_cent, source_hash)
            VALUES (?,?,?,?,?,?,?,?)
        """, batch)
        con.commit()

    if audit_db:
        cur.execute("DETACH DATABASE audit")

    despues = cur.execute("SELECT COUNT(*) FROM libro_diario").fetchone()[0]
    nuevos = despues - antes

    print(f"[OK] {procesados:,} movimientos procesados.")
    print(f"     Asientos nuevos insertados: {nuevos:,}")
    print(f"     Asientos ya existentes (skip): {len(movimientos)*2 - nuevos if not es_venta else '~'}")
    print(f"     {saltados_basura:,} movimientos saltados (basura).")
    print(f"     {saltados_sin_costo:,} movimientos saltados (sin costo).")
    return procesados, nuevos


def generar_balance(con, detal_filtro=None):
    cur = con.cursor()
    print("\n" + "=" * 78)
    print(f" BALANCE DE COMPROBACION (detal={detal_filtro or 'CONSOLIDADO'})")
    print("=" * 78)
    print(f"{'COD':<6} | {'CUENTA':<28} | {'TIPO':<12} | {'DEBE':>15} | {'HABER':>15}")
    print("-" * 78)
    if detal_filtro:
        cur.execute("SELECT pc.codigo,pc.nombre,pc.tipo,SUM(ld.debe_cent),SUM(ld.haber_cent) FROM libro_diario ld JOIN plan_cuentas pc ON pc.codigo=ld.cuenta_codigo WHERE ld.detal=? GROUP BY pc.codigo ORDER BY pc.codigo", (detal_filtro,))
    else:
        cur.execute("SELECT pc.codigo,pc.nombre,pc.tipo,SUM(ld.debe_cent),SUM(ld.haber_cent) FROM libro_diario ld JOIN plan_cuentas pc ON pc.codigo=ld.cuenta_codigo GROUP BY pc.codigo ORDER BY pc.codigo")
    td = th = 0
    for cod, nom, tipo, debe, haber in cur.fetchall():
        debe = debe or 0
        haber = haber or 0
        td += debe
        th += haber
        print(f"{cod:<6} | {nom[:28]:<28} | {tipo:<12} | ${debe/100:>14,.2f} | ${haber/100:>14,.2f}")
    print("-" * 78)
    print(f"{'':<6} | {'TOTAL':<28} | {'':<12} | ${td/100:>14,.2f} | ${th/100:>14,.2f}")
    print("=" * 78)
    if td == th:
        print("[OK] INVARIANTE CUMPLIDA: DEBE = HABER")
    else:
        print(f"[ERROR] INVARIANTE ROTA: dif={td-th}")


def generar_resultados(con, detal_filtro=None):
    cur = con.cursor()
    print("\n" + "=" * 78)
    print(f" ESTADO DE RESULTADOS (detal={detal_filtro or 'CONSOLIDADO'})")
    print("=" * 78)
    if detal_filtro:
        cur.execute("SELECT pc.codigo,pc.nombre,pc.tipo,SUM(ld.debe_cent),SUM(ld.haber_cent) FROM libro_diario ld JOIN plan_cuentas pc ON pc.codigo=ld.cuenta_codigo WHERE ld.detal=? AND pc.tipo IN ('INGRESO','GASTO') GROUP BY pc.codigo ORDER BY pc.codigo", (detal_filtro,))
    else:
        cur.execute("SELECT pc.codigo,pc.nombre,pc.tipo,SUM(ld.debe_cent),SUM(ld.haber_cent) FROM libro_diario ld JOIN plan_cuentas pc ON pc.codigo=ld.cuenta_codigo WHERE pc.tipo IN ('INGRESO','GASTO') GROUP BY pc.codigo ORDER BY pc.codigo")
    ing = gas = 0
    for cod, nom, tipo, debe, haber in cur.fetchall():
        debe = debe or 0
        haber = haber or 0
        if tipo == "INGRESO":
            m = haber - debe
            ing += m
            print(f"  {nom:<30}: ${m/100:>15,.2f}")
        elif tipo == "GASTO":
            m = debe - haber
            gas += m
            print(f"  {nom:<30}: ${m/100:>15,.2f}")
    print(f"  {'-' * 50}")
    print(f"  {'UTILIDAD BRUTA':<30}: ${(ing-gas)/100:>15,.2f}")
    print("=" * 78)


def main():
    print("=" * 78)
    print(" MNFC - CONTABILIDAD PERPETUA (con Idempotencia)")
    print("=" * 78)
    print(f"BD motor:    {DB_PATH}")
    print(f"Detal:       {DETAL or 'CONSOLIDADO'}")
    print(f"Rebuild:     {REBUILD}")
    print(f"Filtro basura: cantidad > {UMBRAL_CANTIDAD_BASURA:,}")
    con = sqlite3.connect(DB_PATH)
    inicializar_tablas(con)
    procesar_movimientos(con, DETAL, rebuild=REBUILD)
    generar_balance(con, DETAL if DETAL else None)
    generar_resultados(con, DETAL if DETAL else None)
    con.close()
    print("\n" + "=" * 78)
    print(" [OK] Ciclo contable completo finalizado.")
    print("=" * 78)


if __name__ == "__main__":
    main()

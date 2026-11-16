import sqlite3
import os
from decimal import Decimal, ROUND_HALF_EVEN
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Caracas")
DB_ORIGEN = r'C:\Users\Admin\Desktop\dartony_auditoria_v2.db'
DB_DESTINO = 'nodo_principal_cliente.db'

def to_centimos(valor):
    try:
        d = Decimal(str(valor or 0))
        return int((d * 100).quantize(Decimal('1'), rounding=ROUND_HALF_EVEN))
    except:
        return 0

def normalizar_fecha(f):
    if not f: return None
    f = str(f).strip()
    if '/' in f:
        partes = f.split('/')
        if len(partes) == 3:
            return f"{partes[2]}-{partes[1]}-{partes[0]}"
    return f

print('='*70)
print(' 🚀 ETL REAL: DARTONY PRODUCCIÓN → MNFC')
print('='*70)

con_o = sqlite3.connect(DB_ORIGEN)
con_d = sqlite3.connect(DB_DESTINO)
cur_o = con_o.cursor()
cur_d = con_d.cursor()
ts = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")

# ═══ 1. PLAN DE CUENTAS ═══
print("\n[1/6] Migrando Plan de Cuentas...")
cur_o.execute("SELECT codigo, nombre, tipo FROM plan_cuentas")
cuentas = cur_o.fetchall()
for cod, nom, tipo in cuentas:
    cur_d.execute("INSERT OR REPLACE INTO plan_cuentas (codigo, nombre, tipo) VALUES (?,?,?)", (cod, nom, tipo))
print(f"  ✅ {len(cuentas)} cuentas contables migradas")

# ═══ 2. LIBRO DIARIO ═══
print("\n[2/6] Migrando Libro Diario...")
cur_o.execute("SELECT fecha, numero_asiento, descripcion, cuenta_codigo, debe_centimos, haber_centimos FROM libro_diario")
asientos = cur_o.fetchall()
for f, na, desc, cc, debe, haber in asientos:
    cur_d.execute("INSERT INTO libro_diario (fecha, numero_documento, descripcion, cuenta_codigo, debe_cent, haber_cent) VALUES (?,?,?,?,?,?)", (f, na, desc, cc, debe or 0, haber or 0))
print(f"  ✅ {len(asientos)} asientos migrados")

# ═══ 3. INVENTARIO (JOIN de stock + precio + costo) ═══
print("\n[3/6] Construyendo Inventario desde stock_am1 + precio_sku + costo_sku_norm...")
cur_d.execute("DELETE FROM inventario_nodo")

# Stock consolidado por SKU
cur_o.execute("""
    SELECT sku, MAX(descripcion), SUM(stock)
    FROM stock_am1
    WHERE sku IS NOT NULL AND sku != ''
    GROUP BY sku
""")
stocks = {r[0]: (r[1] or '', r[2] or 0) for r in cur_o.fetchall()}

# Precios
cur_o.execute("SELECT sku, MAX(precio) FROM precio_sku WHERE sku IS NOT NULL GROUP BY sku")
precios = {r[0]: r[1] or 0 for r in cur_o.fetchall()}

# Costos
cur_o.execute("SELECT sku_norm, MAX(costo) FROM costo_sku_norm WHERE sku_norm IS NOT NULL GROUP BY sku_norm")
costos = {r[0]: r[1] or 0 for r in cur_o.fetchall()}

# Estimar costos desde margen_estimado si falta
cur_o.execute("SELECT sku, MAX(costo_estimado) FROM margen_estimado WHERE sku IS NOT NULL GROUP BY sku")
costos_est = {r[0]: r[1] or 0 for r in cur_o.fetchall()}

insertados = 0
for sku, (nombre, stock) in stocks.items():
    precio = precios.get(sku, 0)
    costo = costos.get(sku, 0)
    if costo == 0:
        costo = costos_est.get(sku, 0)
    if costo == 0 and precio > 0:
        costo = precio * 0.60  # estimación 60%
    
    cur_d.execute("""
        INSERT INTO inventario_nodo (sku, nombre, cantidad_fisica, costo_unitario_cent, precio_venta_cent, marca, familia, ultima_actualizacion)
        VALUES (?,?,?,?,?,?,?,?)
    """, (sku, nombre[:100], int(stock), to_centimos(costo), to_centimos(precio), None, None, ts))
    insertados += 1
print(f"  ✅ {insertados:,} SKUs con stock consolidado")

# ═══ 4. MOVIMIENTOS HISTÓRICOS ═══
print("\n[4/6] Migrando Movimientos Históricos (puede tardar 30s)...")
cur_d.execute("DELETE FROM movimientos_dartony")
cur_o.execute("SELECT detal, sku, fecha, tipo, cantidad FROM movimiento_historico")
batch = []
total_movs = 0
for detal, sku, fecha, tipo, cant in cur_o.fetchall():
    fecha_norm = normalizar_fecha(fecha)
    batch.append((sku, '', tipo, fecha_norm, detal, cant or 0, 0, 0, detal, ''))
    if len(batch) >= 50000:
        cur_d.executemany("INSERT INTO movimientos_dartony (sku, descripcion, tipo, fecha, almacen, cantidad, stock_actual, costo_unitario_cent, nodo, numero_documento) VALUES (?,?,?,?,?,?,?,?,?,?)", batch)
        total_movs += len(batch)
        print(f"  ⏳ {total_movs:,} movimientos...")
        batch = []
if batch:
    cur_d.executemany("INSERT INTO movimientos_dartony (sku, descripcion, tipo, fecha, almacen, cantidad, stock_actual, costo_unitario_cent, nodo, numero_documento) VALUES (?,?,?,?,?,?,?,?,?,?)", batch)
    total_movs += len(batch)
print(f"  ✅ {total_movs:,} movimientos migrados")

# ═══ 5. DECISIONES → HALLAZGOS ═══
print("\n[5/6] Migrando Decisiones de Auditoría → Hallazgos...")
cur_d.execute("DELETE FROM hallazgos_auditoria WHERE tipo LIKE 'DECISION_%'")
cur_o.execute("SELECT sku, detal, hallazgo, decision_tomada, justificacion, fecha FROM decision")
decisiones = cur_o.fetchall()
for sku, detal, hall, dec, just, fecha in decisiones:
    desc = f"[{dec}] {hall} — {just[:100] if just else ''}"
    cur_d.execute("INSERT INTO hallazgos_auditoria (timestamp, tipo, severidad, descripcion) VALUES (?,?,?,?)", (fecha or ts, f"DECISION_{sku}", "MEDIA", desc))
print(f"  ✅ {len(decisiones)} decisiones migradas a hallazgos")

# SKUs sin costo
cur_o.execute("SELECT sku, detal, stock_promedio, estado FROM sku_sin_costo WHERE estado = 'sin_costo_real'")
sin_costo = cur_o.fetchall()
for sku, detal, stock, estado in sin_costo:
    cur_d.execute("INSERT INTO hallazgos_auditoria (timestamp, tipo, severidad, descripcion) VALUES (?,?,?,?)", 
                  (ts, "SKU_SIN_COSTO", "ALTA", f"SKU {sku} en {detal} sin costo real (stock: {stock})"))
print(f"  ✅ {len(sin_costo)} SKUs sin costo registrados como hallazgos")

# ═══ 6. FIRMA AUDITOR → LEDGER ═══
print("\n[6/6] Migrando Firmas del Auditor al Ledger...")
cur_o.execute("SELECT cpc, nombre, datos_firmados, timestamp, hash_firma FROM firma_auditor")
firmas = cur_o.fetchall()
import json
for cpc, nombre, datos, ts_f, hash_f in firmas:
    payload = json.dumps({"cpc": cpc, "nombre": nombre, "datos": datos})
    cur_d.execute("INSERT INTO eventos_ledger (tipo_evento, timestamp_seniat, payload_json, hash_evento) VALUES (?,?,?,?)", 
                  ("FIRMA_AUDITOR", ts_f or ts, payload, hash_f or ''))
print(f"  ✅ {len(firmas)} firma(s) del CPC migradas al Ledger")

con_d.commit()

# ═══ RESUMEN ═══
print("\n" + "="*70)
print(" ✅ ETL COMPLETADO")
print("="*70)
cur_d.execute("SELECT COUNT(*) FROM inventario_nodo")
print(f"  SKUs en inventario    : {cur_d.fetchone()[0]:,}")
cur_d.execute("SELECT COUNT(*) FROM movimientos_dartony")
print(f"  Movimientos históricos: {cur_d.fetchone()[0]:,}")
cur_d.execute("SELECT COUNT(*) FROM plan_cuentas")
print(f"  Cuentas contables     : {cur_d.fetchone()[0]:,}")
cur_d.execute("SELECT COUNT(*) FROM libro_diario")
print(f"  Asientos libro diario : {cur_d.fetchone()[0]:,}")
cur_d.execute("SELECT COUNT(*) FROM hallazgos_auditoria")
print(f"  Hallazgos de auditoría: {cur_d.fetchone()[0]:,}")
cur_d.execute("SELECT COUNT(*) FROM eventos_ledger")
print(f"  Eventos en Ledger     : {cur_d.fetchone()[0]:,}")
print("="*70)

con_o.close()
con_d.close()

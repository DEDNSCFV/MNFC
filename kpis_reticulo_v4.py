#!/usr/bin/env python3
"""
KPIs por SKU y por conjunto con stock_actual del nodo (no stock_central).
Uso: python kpis_reticulo_v2.py "<nodo_db>" "<nodo_tecnico>"
"""
import sys, json
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

sys.path.insert(0, str(Path.home() / "MNFC/src"))
from mnfc import estadistica

NODO = sys.argv[1] if len(sys.argv) > 1 else "04 La Urbina"
NODO_TEC = sys.argv[2] if len(sys.argv) > 2 else "04_La_Urbina"
DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"
BASE = Path.home() / "DARTONY_CONTROL" / NODO_TEC / "control" / "kpis"
FECHA = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
BASE.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(DB)

print("=" * 70)
print(f"KPIs ATÓMICOS POR SKU — {NODO}")
print("=" * 70)
print()

# ============================================================
# 1. STOCK DEL NODO: último stock_actual por SKU
# ============================================================
print("[1/5] Stock del nodo desde última transacción...")

stock_nodo = {}
ultima_fecha = {}
for sku, stock, fecha in conn.execute("""
    SELECT mh.sku, mh.stock_actual, mh.fecha
    FROM movimientos_historico mh
    INNER JOIN (
        SELECT sku, MAX(id) AS max_id
        FROM movimientos_historico WHERE nodo = ?
        GROUP BY sku
    ) latest ON mh.sku = latest.sku AND mh.id = latest.max_id
    WHERE mh.nodo = ?
""", (NODO, NODO)).fetchall():
    if stock is not None:
        stock_nodo[sku] = stock
        ultima_fecha[sku] = fecha

# Costos del maestro
costos = dict(conn.execute("""
    SELECT codigo, costo_unitario_usd FROM maestro_sku WHERE costo_unitario_usd > 0
""").fetchall())

print(f"  SKUs con stock en el nodo: {len(stock_nodo)}")
print(f"  SKUs con stock > 0:        {sum(1 for s in stock_nodo.values() if s > 0)}")
print()

# ============================================================
# 2. VENTAS DEL NODO
# ============================================================
print("[2/5] Ventas del nodo...")

ventas = {}
for sku, n_fact, unidades, primera, ultima in conn.execute("""
    SELECT sku, COUNT(*), SUM(ABS(cantidad)), MIN(fecha), MAX(fecha)
    FROM movimientos_historico
    WHERE tipo = 'FACT' AND cantidad < 0 AND nodo = ?
    GROUP BY sku
""", (NODO,)).fetchall():
    ventas[sku] = {
        'n_facturas': n_fact,
        'unidades': unidades or 0,
        'primera': primera,
        'ultima': ultima,
    }

print(f"  SKUs con ventas en el nodo: {len(ventas)}")
print()

# ============================================================
# 3. ATRIBUTOS POR SKU
# ============================================================
print("[3/5] Construyendo atributos atómicos...")

skus = {}
for sku in stock_nodo:
    stock = stock_nodo[sku]
    costo = costos.get(sku, 0)
    v = ventas.get(sku, {'n_facturas': 0, 'unidades': 0, 'primera': None, 'ultima': None})
    
    # Demanda diaria (basada en ventas del período de 8 meses)
    demanda_diaria = v['unidades'] / 240 if v['unidades'] else 0
    
    skus[sku] = {
        'stock': stock,
        'costo': costo,
        'valor': max(0, stock) * costo,
        'n_facturas': v['n_facturas'],
        'unidades': v['unidades'],
        'demanda_diaria': demanda_diaria,
        'primera_venta': v['primera'],
        'ultima_venta': v['ultima'],
        'ultima_transaccion': ultima_fecha.get(sku),
    }

# ============================================================
# 4. CONJUNTOS (RETÍCULO)
# ============================================================
print("[4/5] Construyendo conjuntos...")

universo = list(skus.keys())
total_valor = sum(s['valor'] for s in skus.values())

# ABC por valor
skus_ord = sorted(skus.items(), key=lambda x: -x[1]['valor'])
acum = 0
A, B, C = [], [], []
for sku, attrs in skus_ord:
    acum += attrs['valor']
    pct = 100.0 * acum / total_valor if total_valor else 0
    if pct <= 80:
        A.append(sku)
    elif pct <= 95:
        B.append(sku)
    else:
        C.append(sku)

# Activos vs Inmovilizados (sin ventas)
activos = [sku for sku in universo if skus[sku]['n_facturas'] > 0]
inmovilizados = [sku for sku in universo if skus[sku]['n_facturas'] == 0]

# Obsoletos: SKUs con stock > 0 pero sin ventas en los últimos 3 meses
obsoletos = []
for sku in universo:
    if skus[sku]['stock'] <= 0:
        continue
    ultima = skus[sku]['ultima_venta']
    if not ultima or ultima[6:10] + ultima[3:5] < '202607':
        obsoletos.append(sku)

print(f"  Universo:      {len(universo):,} SKUs")
print(f"  Clase A:       {len(A):,} SKUs")
print(f"  Clase B:       {len(B):,} SKUs")
print(f"  Clase C:       {len(C):,} SKUs")
print(f"  Activos:       {len(activos):,} SKUs")
print(f"  Inmovilizados: {len(inmovilizados):,} SKUs")
print(f"  Obsoletos:     {len(obsoletos):,} SKUs")
print()

# ============================================================
# 5. KPIs POR CONJUNTO Y POR SKU
# ============================================================
print("[5/5] Calculando KPIs...")
print()

def kpis_conj(nombre, conjunto):
    valor = sum(skus[s]['valor'] for s in conjunto if s in skus)
    costo_ventas = sum(skus[s]['unidades'] * skus[s]['costo'] for s in conjunto if s in skus and skus[s]['costo'] > 0)
    rotacion = round((costo_ventas / 8 * 12) / valor, 2) if valor > 0 else 0
    return {
        'n_skus': len(conjunto),
        'valor': round(valor, 2),
        'costo_ventas_anual': round(costo_ventas / 8 * 12, 2),
        'rotacion': rotacion,
    }

for nombre, conjunto in [('A', A), ('B', B), ('C', C), ('Activos', activos), ('Inmovilizados', inmovilizados), ('Obsoletos', obsoletos)]:
    k = kpis_conj(nombre, conjunto)
    print(f"  {nombre:15s}: {k['n_skus']:>6,} SKUs | ${k['valor']:>15,.2f} | rotación {k['rotacion']}x")
print()

# KPIs por SKU de clase A
print("KPIs por SKU de clase A (top 10 por valor):")
print()
kpis_por_sku = []
for sku in A:
    attrs = skus[sku]
    if attrs['stock'] <= 0:
        continue
    if attrs['demanda_diaria'] < 0.1:
        # Demanda insuficiente: no se calcula rotación ni ruptura
        kpis_por_sku.append({
            'sku': sku,
            'stock': attrs['stock'],
            'valor': attrs['valor'],
            'demanda_diaria': round(attrs['demanda_diaria'], 4),
            'rotacion': None,
            'dias_inventario': None,
            'tiempo_ruptura': None,
            'estado': 'DEMANDA_INSUFICIENTE',
        })
        continue
    rot = (attrs['demanda_diaria'] * 365) / attrs['stock']
    dias = 365 / rot if rot else 0
    ruptura = attrs['stock'] / attrs['demanda_diaria']
    # Acotar a 365 días máximo
    ruptura_acotada = min(ruptura, 365)
    kpis_por_sku.append({
        'sku': sku,
        'stock': attrs['stock'],
        'valor': attrs['valor'],
        'demanda_diaria': round(attrs['demanda_diaria'], 2),
        'rotacion': round(rot, 2),
        'dias_inventario': round(dias, 1),
        'tiempo_ruptura': round(ruptura_acotada, 1),
        'ruptura_real': round(ruptura, 1),
        'estado': 'CALCULADO',
    })

kpis_por_sku.sort(key=lambda x: -x['valor'])
print(f"  {'SKU':15s} {'Stock':>8s} {'Valor':>12s} {'Rotación':>10s} {'Días':>8s} {'Ruptura':>8s} {'Estado':>20s}")
print("  " + "-" * 90)
for k in kpis_por_sku[:15]:
    rot_str = f"{k['rotacion']:.2f}x" if k['rotacion'] is not None else "—"
    dias_str = f"{k['dias_inventario']:.1f}" if k['dias_inventario'] is not None else "—"
    rupt_str = f"{k['tiempo_ruptura']:.1f}d" if k['tiempo_ruptura'] is not None else "—"
    print(f"  {k['sku']:15s} {k['stock']:>8.0f} ${k['valor']:>11,.0f} {rot_str:>10s} {dias_str:>8s} {rupt_str:>8s} {k.get('estado', ''):>20s}")
print()

# Estadísticas de rotación de clase A
rotaciones = [k['rotacion'] for k in kpis_por_sku if k['rotacion'] is not None and k['rotacion'] > 0]
if rotaciones:
    print("Estadísticas de rotación (clase A):")
    print(f"  Media:               {estadistica.media(rotaciones):.2f}x")
    print(f"  Mediana:             {estadistica.mediana(rotaciones):.2f}x")
    print(f"  Desviación muestral: {estadistica.desviacion_muestral(rotaciones):.2f}")
    print(f"  CV:                  {estadistica.coef_variacion(rotaciones):.2f}")
    print(f"  Cuartiles (Q1,Q2,Q3): {tuple(round(q, 2) for q in estadistica.cuartiles(rotaciones))}")
    print()

# Guardar
out = BASE / f"kpis_atomicos_{FECHA}.json"
with open(out, 'w', encoding='utf-8') as f:
    json.dump({
        'nodo': NODO,
        'fecha': FECHA,
        'universo': len(universo),
        'conjuntos': {
            'A': len(A), 'B': len(B), 'C': len(C),
            'Activos': len(activos), 'Inmovilizados': len(inmovilizados), 'Obsoletos': len(obsoletos),
        },
        'kpis_por_sku': kpis_por_sku,
    }, f, indent=2, ensure_ascii=False)

print(f"Guardado en: {out}")
conn.close()

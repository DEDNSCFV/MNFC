#!/usr/bin/env python3
"""
KPIs por SKU y por conjunto, usando reticulo.py y estadistica.py.
Cada SKU es un átomo. Los conjuntos son segmentaciones.
Uso: python kpis_reticulo.py "<nodo_db>" "<nodo_tecnico>"
"""
import sys, json
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

sys.path.insert(0, str(Path.home() / "MNFC/src"))

from mnfc.extensiones.reticulo import ReticuloCuentas
from mnfc import estadistica

NODO = sys.argv[1] if len(sys.argv) > 1 else "04 La Urbina"
NODO_TEC = sys.argv[2] if len(sys.argv) > 2 else "04_La_Urbina"
DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"
BASE = Path.home() / "DARTONY_CONTROL" / NODO_TEC / "control" / "kpis"
FECHA = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
BASE.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(DB)

print("=" * 70)
print(f"KPIs POR SKU Y POR CONJUNTO — {NODO}")
print("=" * 70)
print()

# ============================================================
# 1. CONSTRUIR LOS ATRIBUTOS DE CADA SKU
# ============================================================
print("[1/5] Construyendo atributos de cada SKU...")

skus = {}
# Stock y costo del maestro
for codigo, stock, costo in conn.execute("""
    SELECT codigo, stock_central, costo_unitario_usd
    FROM maestro_sku WHERE stock_central > 0
""").fetchall():
    skus[codigo] = {
        'stock': stock or 0,
        'costo': costo or 0,
        'valor': (stock or 0) * (costo or 0),
        'ventas': 0,
        'unidades_vendidas': 0,
        'primera_venta': None,
        'ultima_venta': None,
    }

# Ventas del nodo
for sku, n_fact, unidades, primera, ultima in conn.execute("""
    SELECT sku, COUNT(*), SUM(ABS(cantidad)), MIN(fecha), MAX(fecha)
    FROM movimientos_historico
    WHERE tipo = 'FACT' AND cantidad < 0 AND nodo = ?
    GROUP BY sku
""", (NODO,)).fetchall():
    if sku in skus:
        skus[sku]['ventas'] = n_fact
        skus[sku]['unidades_vendidas'] = unidades or 0
        skus[sku]['primera_venta'] = primera
        skus[sku]['ultima_venta'] = ultima

print(f"  SKUs con stock: {len(skus)}")
print()

# ============================================================
# 2. CONSTRUIR EL RETÍCULO
# ============================================================
print("[2/5] Construyendo el retículo de SKUs...")

universo = list(skus.keys())

# Conjuntos por valor (ABC)
skus_ordenados = sorted(skus.items(), key=lambda x: -x[1]['valor'])
total_valor = sum(s['valor'] for s in skus.values())
acum = 0
clase_a, clase_b, clase_c = [], [], []
for sku, attrs in skus_ordenados:
    acum += attrs['valor']
    pct = 100.0 * acum / total_valor if total_valor else 0
    if pct <= 80:
        clase_a.append(sku)
    elif pct <= 95:
        clase_b.append(sku)
    else:
        clase_c.append(sku)

# Conjuntos por ventas
activos = [sku for sku in universo if skus[sku]['ventas'] > 0]
inmovilizados = [sku for sku in universo if skus[sku]['ventas'] == 0]

# Conjuntos por rotación (últimos 3 meses)
obsoletos = []
for sku in universo:
    ultima = skus[sku]['ultima_venta']
    if ultima:
        # Si la última venta fue antes de agosto 2026, es obsoleto
        if ultima[3:5] + ultima[6:10] < '202608':
            obsoletos.append(sku)
    elif skus[sku]['stock'] > 0:
        obsoletos.append(sku)

reticulo = ReticuloCuentas(
    universo=universo,
    subconjuntos={
        'A': clase_a,
        'B': clase_b,
        'C': clase_c,
        'Activos': activos,
        'Inmovilizados': inmovilizados,
        'Obsoletos': obsoletos,
    }
)

print(f"  Universo: {len(universo)} SKUs")
print(f"  Clase A:  {len(clase_a)} SKUs")
print(f"  Clase B:  {len(clase_b)} SKUs")
print(f"  Clase C:  {len(clase_c)} SKUs")
print(f"  Activos:  {len(activos)} SKUs")
print(f"  Inmovilizados: {len(inmovilizados)} SKUs")
print(f"  Obsoletos: {len(obsoletos)} SKUs")
print()

# ============================================================
# 3. CALCULAR KPIs POR SKU
# ============================================================
print("[3/5] Calculando KPIs por SKU...")

# Para cada SKU de clase A, calcular:
# - Rotación individual (ventas / stock)
# - Días de inventario
# - Tiempo hasta ruptura
kpis_por_sku = {}
for sku in clase_a:
    attrs = skus[sku]
    if attrs['stock'] > 0 and attrs['ventas'] > 0:
        # Rotación individual: ventas anualizadas / stock
        demanda_diaria = attrs['ventas'] / 240
        rotacion = (demanda_diaria * 365) / attrs['stock'] if attrs['stock'] else 0
        dias_inv = 365 / rotacion if rotacion else 0
        tiempo_ruptura = attrs['stock'] / demanda_diaria if demanda_diaria else 0
        
        kpis_por_sku[sku] = {
            'stock': attrs['stock'],
            'valor': attrs['valor'],
            'ventas': attrs['ventas'],
            'unidades_vendidas': attrs['unidades_vendidas'],
            'demanda_diaria': round(demanda_diaria, 2),
            'rotacion': round(rotacion, 2),
            'dias_inventario': round(dias_inv, 1),
            'tiempo_ruptura': round(tiempo_ruptura, 1),
        }

print(f"  SKUs clase A con KPIs calculados: {len(kpis_por_sku)}")
print()

# ============================================================
# 4. CALCULAR KPIs POR CONJUNTO
# ============================================================
print("[4/5] Calculando KPIs por conjunto...")

def kpis_conjunto(nombre, conjunto):
    """Calcula KPIs agregados para un conjunto de SKUs."""
    valor = sum(skus[sku]['valor'] for sku in conjunto if sku in skus)
    ventas = sum(skus[sku]['ventas'] for sku in conjunto if sku in skus)
    unidades = sum(skus[sku]['unidades_vendidas'] for sku in conjunto if sku in skus)
    n_skus = len(conjunto)
    
    # Rotación del conjunto
    rotacion = 0
    if valor > 0:
        # Costo de ventas anualizado / valor
        costo_ventas = 0
        for sku in conjunto:
            if sku in skus and skus[sku]['costo'] > 0:
                costo_ventas += skus[sku]['unidades_vendidas'] * skus[sku]['costo']
        rotacion = round((costo_ventas / 8 * 12) / valor, 2) if valor else 0
    
    return {
        'nombre': nombre,
        'n_skus': n_skus,
        'valor': round(valor, 2),
        'ventas': ventas,
        'unidades': unidades,
        'rotacion': rotacion,
    }

print()
for nombre in ['A', 'B', 'C', 'Activos', 'Inmovilizados', 'Obsoletos']:
    conjunto = reticulo.obtener(nombre) if hasattr(reticulo, 'obtener') else []
    # Si no tiene método obtener, acceder directamente
    if not conjunto:
        conjunto = {
            'A': clase_a, 'B': clase_b, 'C': clase_c,
            'Activos': activos, 'Inmovilizados': inmovilizados,
            'Obsoletos': obsoletos,
        }[nombre]
    k = kpis_conjunto(nombre, conjunto)
    print(f"  {nombre:15s}: {k['n_skus']:>6,} SKUs | ${k['valor']:>15,.2f} | rotación {k['rotacion']}x")
print()

# ============================================================
# 5. ESTADÍSTICAS POR CONJUNTO
# ============================================================
print("[5/5] Estadísticas por conjunto...")
print()

# Para clase A, calcular estadísticas de la rotación individual
rotaciones_a = [v['rotacion'] for v in kpis_por_sku.values() if v['rotacion'] > 0]
if rotaciones_a:
    print(f"  Clase A — Rotación individual:")
    print(f"    Media:               {estadistica.media(rotaciones_a):.2f}x")
    print(f"    Mediana:             {estadistica.mediana(rotaciones_a):.2f}x")
    print(f"    Desviación muestral: {estadistica.desviacion_muestral(rotaciones_a):.2f}")
    print(f"    CV:                  {estadistica.coef_variacion(rotaciones_a):.2f}")
    print(f"    Q1-Q3:               {estadistica.cuartiles(rotaciones_a)}")
    print()

# Tiempo hasta ruptura
rupturas = [v['tiempo_ruptura'] for v in kpis_por_sku.values() if v['tiempo_ruptura'] > 0]
if rupturas:
    print(f"  Clase A — Tiempo hasta ruptura (días):")
    print(f"    Media:               {estadistica.media(rupturas):.1f}")
    print(f"    Mediana:             {estadistica.mediana(rupturas):.1f}")
    print(f"    Mínimo:              {min(rupturas):.1f}")
    print(f"    Máximo:              {max(rupturas):.1f}")
    print()

# ============================================================
# GUARDAR
# ============================================================
out = BASE / f"kpis_reticulo_{FECHA}.json"
with open(out, 'w', encoding='utf-8') as f:
    json.dump({
        'nodo': NODO,
        'fecha': FECHA,
        'universo': len(universo),
        'conjuntos': {n: len({'A': clase_a, 'B': clase_b, 'C': clase_c, 'Activos': activos, 'Inmovilizados': inmovilizados, 'Obsoletos': obsoletos}[n]) for n in ['A','B','C','Activos','Inmovilizados','Obsoletos']},
        'kpis_por_sku': kpis_por_sku,
        'estadisticas': {
            'rotacion_A': {
                'media': round(estadistica.media(rotaciones_a), 2) if rotaciones_a else 0,
                'mediana': round(estadistica.mediana(rotaciones_a), 2) if rotaciones_a else 0,
                'desviacion': round(estadistica.desviacion_muestral(rotaciones_a), 2) if rotaciones_a else 0,
                'cv': round(estadistica.coef_variacion(rotaciones_a), 2) if rotaciones_a else 0,
            },
            'ruptura_A': {
                'media': round(estadistica.media(rupturas), 1) if rupturas else 0,
                'mediana': round(estadistica.mediana(rupturas), 1) if rupturas else 0,
                'min': round(min(rupturas), 1) if rupturas else 0,
                'max': round(max(rupturas), 1) if rupturas else 0,
            }
        }
    }, f, indent=2, ensure_ascii=False)

print(f"Guardado en: {out}")
conn.close()

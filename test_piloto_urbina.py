#!/usr/bin/env python3
"""
test_piloto_urbina.py
Test end-to-end del motor con URBINA (único Detal con datos completos).
Prueba: 7 dimensiones, detección de cruces, CBR retrieve, sinopsis.
"""

import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from difflib import SequenceMatcher
from collections import defaultdict

DB = "/data/data/com.termux/files/home/MNFC/nodo_principal_dartony.db"
OUT_DIR = Path("/data/data/com.termux/files/home/MNFC/TEST_URBINA_2026-11-15")
OUT_DIR.mkdir(exist_ok=True)

DETAL = '04 LA URBINA'
ALMACEN = '0401'

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

print("=" * 78)
print(f"TEST PILOTO — {DETAL} (almacén {ALMACEN})")
print("=" * 78)
print()

# ============================================================
# 1. CARGAR SKUs DE URBINA
# ============================================================
print("1. CARGANDO SKUs DE URBINA")
print("-" * 78)
print()

skus_urbina = {}
for row in con.execute("""
    SELECT sku, SUM(stock) as stock
    FROM stock_por_sucursal
    WHERE sucursal = ? AND almacen = ? AND stock > 0
    GROUP BY sku
""", (DETAL, ALMACEN)):
    skus_urbina[row['sku']] = {'stock_sucursal': row['stock']}

# Enriquecer con catálogo
for sku in skus_urbina:
    inv = con.execute("SELECT * FROM inventario_nodo WHERE sku=?", (sku,)).fetchone()
    if inv:
        skus_urbina[sku]['descripcion'] = inv['nombre']
        skus_urbina[sku]['familia'] = inv['familia']
        skus_urbina[sku]['stock_fisico'] = inv['cantidad_fisica']
        skus_urbina[sku]['costo'] = inv['costo_unitario_cent']

print(f"  SKUs cargados: {len(skus_urbina)}")
print()

# ============================================================
# 2. EVALUAR LAS 7 DIMENSIONES
# ============================================================
print("2. EVALUACIÓN DE LAS 7 DIMENSIONES")
print("-" * 78)
print()

hoy = datetime(2026, 11, 15)
corte_90d = (hoy - timedelta(days=90)).strftime('%d/%m/%Y')

# Cargar movimientos por SKU
movimientos = {}
for row in con.execute("SELECT sku, MAX(fecha) as ultimo FROM movimientos_dartony GROUP BY sku"):
    movimientos[row['sku']] = row['ultimo']

# Stock negativo
stock_negativo = set(row['sku'] for row in con.execute(
    "SELECT DISTINCT sku FROM movimientos_dartony WHERE stock_actual < 0"
))

# Duplicados (case-insensitive)
skus_norm = {}
for sku in skus_urbina:
    skus_norm.setdefault(sku.strip().upper(), []).append(sku)

dimensiones_rotas = {
    'D1_EXISTENCIA': 0,
    'D2_UBICACION': 0,
    'D3_ROTACION': 0,
    'D4_COSTO': 0,
    'D5_CONSISTENCIA': 0,
    'D6_INTEGRIDAD': 0,
    'D7_UNICIDAD': 0,
}

for sku, data in skus_urbina.items():
    stock_inv = data.get('stock_fisico') or 0
    stock_suc = data.get('stock_sucursal') or 0

    # D1: SKU en catálogo → tiene stock
    if data.get('descripcion') is None:
        dimensiones_rotas['D1_EXISTENCIA'] += 1

    # D2: SKU con stock → tiene ubicación (siempre true aquí)
    # (todos los SKUs cargados están en URBINA)

    # D3: SKU con stock → tiene movimiento en 90d
    if stock_suc > 0:
        ultimo = movimientos.get(sku)
        if not ultimo or ultimo < corte_90d:
            dimensiones_rotas['D3_ROTACION'] += 1

    # D4: SKU con stock → tiene costo
    if stock_suc > 0:
        costo = data.get('costo') or 0
        if costo == 0:
            dimensiones_rotas['D4_COSTO'] += 1

    # D5: stock inventario = stock sucursal
    if abs(stock_inv - stock_suc) >= 0.01:
        dimensiones_rotas['D5_CONSISTENCIA'] += 1

    # D6: SKU con movimientos → stock >= 0
    if sku in stock_negativo:
        dimensiones_rotas['D6_INTEGRIDAD'] += 1

    # D7: código único
    if len(skus_norm.get(sku.strip().upper(), [])) > 1:
        dimensiones_rotas['D7_UNICIDAD'] += 1

print(f"  {'Dimensión':25s} {'Roturas':>10s} {'%':>8s}")
print(f"  {'-'*25} {'-'*10} {'-'*8}")
for dim, n in dimensiones_rotas.items():
    pct = 100.0 * n / len(skus_urbina) if skus_urbina else 0
    print(f"  {dim:25s} {n:>10,} {pct:>7.1f}%")

print()

# ============================================================
# 3. DETECCIÓN DE CRUCES EN URBINA
# ============================================================
print("3. DETECCIÓN DE CRUCES EN URBINA")
print("-" * 78)
print()

def similitud(a, b):
    return SequenceMatcher(None, (a or '').upper(), (b or '').upper()).ratio()

# Agrupar por familia
por_familia = defaultdict(list)
for sku, data in skus_urbina.items():
    fam = data.get('familia') or 'SIN_FAMILIA'
    por_familia[fam].append((sku, data))

# Buscar pares compensatorios
cruces_detectados = []
for fam, items in por_familia.items():
    if fam == 'SIN_FAMILIA' or len(items) < 2:
        continue
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            sku_a, data_a = items[i]
            sku_b, data_b = items[j]

            sc = similitud(sku_a, sku_b)
            sd = similitud(data_a.get('descripcion', ''), data_b.get('descripcion', ''))

            if sc > 0.5 or sd > 0.5:
                cruces_detectados.append({
                    'sku_a': sku_a,
                    'sku_b': sku_b,
                    'familia': fam,
                    'sim_codigo': round(sc, 3),
                    'sim_desc': round(sd, 3),
                    'stock_a': data_a.get('stock_sucursal', 0),
                    'stock_b': data_b.get('stock_sucursal', 0),
                })

print(f"  Cruces detectados: {len(cruces_detectados)}")
print()

# Top 10
cruces_detectados.sort(key=lambda x: max(x['sim_codigo'], x['sim_desc']), reverse=True)
print(f"  {'SKU A':15s} {'SKU B':15s} {'Familia':12s} {'Sim':>5s} {'Stock A':>8s} {'Stock B':>8s}")
print(f"  {'-'*15} {'-'*15} {'-'*12} {'-'*5} {'-'*8} {'-'*8}")
for c in cruces_detectados[:10]:
    print(f"  {c['sku_a']:15s} {c['sku_b']:15s} {c['familia']:12s} {max(c['sim_codigo'], c['sim_desc']):>5.2f} {c['stock_a']:>8.0f} {c['stock_b']:>8.0f}")

print()

# ============================================================
# 4. CBR RETRIEVE CON CASOS DE URBINA
# ============================================================
print("4. CBR RETRIEVE — CASOS DE URBINA")
print("-" * 78)
print()

# Buscar casos en el CBR que sean de URBINA
casos_urbina = con.execute("""
    SELECT * FROM casos_resueltos
    WHERE detal = ? OR detal = ?
""", (DETAL, '04_la_urbina')).fetchall()

print(f"  Casos de URBINA en el CBR: {len(casos_urbina)}")
for caso in casos_urbina:
    print(f"    {caso['caso_codigo']}: {caso['clasificacion']} (SKU: {caso['sku_faltante']})")

print()

# Simular retrieve: buscar un caso de cruce
print("  Simulación: si apareciera un nuevo caso en URBINA...")
print("  Retrieve recuperaría los casos similares del CBR")

# Buscar casos con clasificación de cruce
casos_cruce = con.execute("""
    SELECT * FROM casos_resueltos
    WHERE clasificacion LIKE '%CRUCE%' OR clasificacion LIKE '%DUPLICADO%'
    ORDER BY confianza_final DESC
    LIMIT 3
""").fetchall()

print(f"\n  Casos de cruce/duplicado disponibles para retrieve:")
for c in casos_cruce:
    print(f"    {c['caso_codigo']}: {c['clasificacion']} (conf: {c['confianza_final']})")

print()

# ============================================================
# 5. SINOPSIS DE URBINA
# ============================================================
print("5. SINOPSIS DE URBINA — CUADRO DE UN GOLPE")
print("-" * 78)
print()

# Clasificar SKUs
cuadrados = 0
con_rupturas = 0
for sku in skus_urbina:
    rupturas_sku = sum(1 for dim, n in dimensiones_rotas.items() if n > 0)
    # Verificar si este SKU tiene alguna ruptura
    stock_inv = skus_urbina[sku].get('stock_fisico') or 0
    stock_suc = skus_urbina[sku].get('stock_sucursal') or 0
    tiene_ruptura = False

    if skus_urbina[sku].get('descripcion') is None:
        tiene_ruptura = True
    ultimo = movimientos.get(sku)
    if stock_suc > 0 and (not ultimo or ultimo < corte_90d):
        tiene_ruptura = True
    if stock_suc > 0 and (skus_urbina[sku].get('costo') or 0) == 0:
        tiene_ruptura = True
    if abs(stock_inv - stock_suc) >= 0.01:
        tiene_ruptura = True
    if sku in stock_negativo:
        tiene_ruptura = True
    if len(skus_norm.get(sku.strip().upper(), [])) > 1:
        tiene_ruptura = True

    if tiene_ruptura:
        con_rupturas += 1
    else:
        cuadrados += 1

print(f"  ┌─────────────────────────────────────────────────────────┐")
print(f"  │ DETAL: {DETAL:45s}       │")
print(f"  │ Almacén: {ALMACEN:43s}       │")
print(f"  │                                                         │")
print(f"  │ SKUs totales:        {len(skus_urbina):>6}                            │")
print(f"  │ SKUs cuadrados:      {cuadrados:>6}                            │")
print(f"  │ SKUs con rupturas:   {con_rupturas:>6}                            │")
print(f"  │                                                         │")
print(f"  │ D5_CONSISTENCIA:     {dimensiones_rotas['D5_CONSISTENCIA']:>6}  ← TI (fuentes)           │")
print(f"  │ D3_ROTACION:         {dimensiones_rotas['D3_ROTACION']:>6}  ← capital inmovilizado    │")
print(f"  │ D6_INTEGRIDAD:       {dimensiones_rotas['D6_INTEGRIDAD']:>6}  ← stock negativo         │")
print(f"  │ D4_COSTO:            {dimensiones_rotas['D4_COSTO']:>6}  ← sin costo              │")
print(f"  │                                                         │")
print(f"  │ Cruces detectados:   {len(cruces_detectados):>6}                            │")
print(f"  └─────────────────────────────────────────────────────────┘")
print()

# ============================================================
# 6. GUARDAR EVIDENCIA
# ============================================================
resultado = {
    'test': 'piloto_urbina_2026-11-15',
    'timestamp': datetime.now().isoformat(),
    'detal': DETAL,
    'almacen': ALMACEN,
    'skus_totales': len(skus_urbina),
    'cuadrados': cuadrados,
    'con_rupturas': con_rupturas,
    'dimensiones_rotas': dimensiones_rotas,
    'cruces_detectados': len(cruces_detectados),
    'top_10_cruces': cruces_detectados[:10],
    'casos_cbr_urbina': [dict(c) for c in casos_urbina],
}

path = OUT_DIR / "test_piloto_urbina.json"
path.write_text(json.dumps(resultado, indent=2, ensure_ascii=False, default=str), encoding='utf-8')
h = hashlib.sha256(path.read_bytes()).hexdigest()

print("=" * 78)
print("EVIDENCIA")
print("=" * 78)
print(f"  Archivo: {path}")
print(f"  SHA-256: {h}")
print()

con.close()
print("=" * 78)
print("✅ TEST PILOTO URBINA COMPLETADO")
print("=" * 78)

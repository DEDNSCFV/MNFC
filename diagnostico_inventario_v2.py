#!/usr/bin/env python3
"""
diagnostico_inventario_v2.py
Diagnóstico del inventario por Detal CON FILTRO DE ALMACÉN LOCAL.
Dogma del handoff: filtrar por almacén local.
"""

import sqlite3
import hashlib
import json
from datetime import datetime
from pathlib import Path

DB = "/data/data/com.termux/files/home/MNFC/nodo_principal_dartony.db"
OUT_DIR = Path("/data/data/com.termux/files/home/MNFC/DIAGNOSTICO_2026-11-15")
OUT_DIR.mkdir(exist_ok=True)

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

# ============================================================
# MAPEO DETAL → ALMACÉN LOCAL (dogma del handoff)
# ============================================================
DETALES = {
    '04 LA URBINA':  '0401',
    '05 CUA':        'CUA',
    '06 TERE':       'TERE',
    '07 LA RAIZA':   'RAIZA',
    '07 PALO VERDE': '0701',
    '08 CHARALLAVE': '0801',
}

print("=" * 78)
print("DIAGNÓSTICO DEL INVENTARIO — FILTRO POR ALMACÉN LOCAL")
print("=" * 78)
print()
print("Dogma: cada Detal se evalúa SOLO con su almacén local.")
print()

# ============================================================
# 1. VERIFICAR QUÉ DETALES Y ALMACENES HAY EN LA BD
# ============================================================
print("1. DETALES Y ALMACENES REALES EN LA BD")
print("-" * 78)
print()

for row in con.execute("""
    SELECT sucursal, almacen, COUNT(DISTINCT sku) as n, SUM(stock) as unidades
    FROM stock_por_sucursal
    WHERE sucursal IS NOT NULL AND sucursal != ''
    GROUP BY sucursal, almacen
    ORDER BY sucursal, almacen
"""):
    marca = " ← LOCAL" if DETALES.get(row['sucursal']) == row['almacen'] else ""
    print(f"  {row['sucursal']:20s} {row['almacen']:8s} SKUs={row['n']:>5} unidades={row['unidades']:>10,.0f}{marca}")

print()

# ============================================================
# 2. RUPTURAS POR DETAL — FILTRADAS POR ALMACÉN LOCAL
# ============================================================
print("2. RUPTURAS POR DETAL (solo almacén local)")
print("-" * 78)
print()

print(f"  {'Detal':20s} {'Almacén':8s} {'SKUs':>6s} {'Cuad':>6s} {'Rupt':>6s} {'%':>6s}")
print(f"  {'-'*20} {'-'*8} {'-'*6} {'-'*6} {'-'*6} {'-'*6}")

por_detal = []
total_global = {'skus': 0, 'cuad': 0, 'rupt': 0}

for detal, alm_local in DETALES.items():
    # SKUs en este almacén local
    skus_local = set(row['sku'] for row in con.execute("""
        SELECT DISTINCT sku FROM stock_por_sucursal
        WHERE sucursal = ? AND almacen = ? AND stock > 0
    """, (detal, alm_local)))

    if not skus_local:
        print(f"  {detal:20s} {alm_local:8s} (SIN SKUs con stock en almacén local)")
        continue

    # De esos SKUs, cuántos tienen pares rotos
    placeholders = ','.join(['?'] * len(skus_local))
    cuad = con.execute(f"""
        SELECT COUNT(*) FROM sinopsis_rodriguiana
        WHERE sku IN ({placeholders}) AND estado_global = 'CUADRADO'
    """, list(skus_local)).fetchone()[0]

    rupt = con.execute(f"""
        SELECT COUNT(*) FROM sinopsis_rodriguiana
        WHERE sku IN ({placeholders}) AND estado_global = 'CON_RUPTURAS'
    """, list(skus_local)).fetchone()[0]

    total = cuad + rupt
    pct = 100.0 * rupt / total if total > 0 else 0

    print(f"  {detal:20s} {alm_local:8s} {len(skus_local):>6} {cuad:>6} {rupt:>6} {pct:>5.1f}%")

    por_detal.append({
        'detal': detal, 'almacen': alm_local,
        'skus_con_stock': len(skus_local),
        'cuadrados': cuad, 'rupturas': rupt, 'pct': round(pct, 1)
    })
    total_global['skus'] += len(skus_local)
    total_global['cuad'] += cuad
    total_global['rupt'] += rupt

print()
print(f"  {'TOTAL':20s} {'':8s} {total_global['skus']:>6} {total_global['cuad']:>6} {total_global['rupt']:>6}")
print()

# ============================================================
# 3. TOP 20 SKUs CON MÁS RUPTURAS (filtrado por almacén local + stock razonable)
# ============================================================
print("3. TOP 20 SKUs CRÍTICOS (filtrado por almacén local, stock < 10000)")
print("-" * 78)
print()

# Construir lista de SKUs locales
skus_locales = set()
for detal, alm_local in DETALES.items():
    for row in con.execute("""
        SELECT DISTINCT sku FROM stock_por_sucursal
        WHERE sucursal = ? AND almacen = ? AND stock > 0 AND stock < 10000
    """, (detal, alm_local)):
        skus_locales.add(row['sku'])

print(f"  SKUs locales (stock>0, <10000): {len(skus_locales)}")
print()

placeholders = ','.join(['?'] * len(skus_locales))
top = con.execute(f"""
    SELECT s.sku, s.familia, s.stock_fisico, s.pares_rotos,
           GROUP_CONCAT(p.paradigma, ', ') as dims_rotas
    FROM sinopsis_rodriguiana s
    JOIN pares_adyacencia p ON p.sku = s.sku AND p.estado = 'ROTO'
    WHERE s.sku IN ({placeholders})
    GROUP BY s.sku
    ORDER BY s.pares_rotos DESC, s.stock_fisico DESC
    LIMIT 20
""", list(skus_locales)).fetchall()

print(f"  {'SKU':15s} {'Familia':15s} {'Stock':>8s} {'Rupt':>5s} {'Dimensiones rotas':40s}")
print(f"  {'-'*15} {'-'*15} {'-'*8} {'-'*5} {'-'*40}")

for t in top:
    print(f"  {t['sku']:15s} {(t['familia'] or 'N/A'):15s} {t['stock_fisico'] or 0:>8.0f} {t['pares_rotos']:>5d} {t['dims_rotas'][:40]:40s}")

print()

# ============================================================
# 4. DIMENSIONES — SEPARANDO D5 (problema de TI) DEL RESTO
# ============================================================
print("4. RUPTURAS POR DIMENSIÓN (sobre SKUs locales)")
print("-" * 78)
print()

placeholders = ','.join(['?'] * len(skus_locales))

print(f"  {'Dimensión':25s} {'Roturas':>10s} {'% locales':>10s} {'Tipo':>15s}")
print(f"  {'-'*25} {'-'*10} {'-'*10} {'-'*15}")

for row in con.execute(f"""
    SELECT paradigma, COUNT(*) as n
    FROM pares_adyacencia
    WHERE estado = 'ROTO' AND sku IN ({placeholders})
    GROUP BY paradigma
    ORDER BY n DESC
""", list(skus_locales)):
    pct = 100.0 * row['n'] / len(skus_locales) if skus_locales else 0
    tipo = 'TI (fuentes)' if row['paradigma'] == 'D5_CONSISTENCIA' else 'INVENTARIO'
    print(f"  {row['paradigma']:25s} {row['n']:>10,} {pct:>9.1f}% {tipo:>15s}")

print()

# ============================================================
# 5. GUARDAR BASELINE CORREGIDO
# ============================================================
print("5. GUARDANDO BASELINE CORREGIDO")
print("-" * 78)
print()

baseline = {
    'fecha': '2026-11-15',
    'timestamp': datetime.now().isoformat(),
    'filtro': 'almacen_local_por_detal',
    'detales_mapeados': DETALES,
    'total_global': total_global,
    'por_detal': por_detal,
    'top_20': [dict(t) for t in top],
}

path = OUT_DIR / "baseline_inventario_v2_2026-11-15.json"
path.write_text(json.dumps(baseline, indent=2, ensure_ascii=False, default=str), encoding='utf-8')
h = hashlib.sha256(path.read_bytes()).hexdigest()

print(f"  Archivo: {path}")
print(f"  SHA-256: {h}")
print()

con.close()

print("=" * 78)
print("✅ DIAGNÓSTICO V2 COMPLETADO — FILTRADO POR ALMACÉN LOCAL")
print("=" * 78)

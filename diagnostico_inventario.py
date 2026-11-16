#!/usr/bin/env python3
"""
diagnostico_inventario.py
Diagnóstico del inventario actual (13,602 SKUs) contra las 7 dimensiones.
Produce el baseline del 15/11/2026 para comparar con la factura del lunes.
"""

import sqlite3
import hashlib
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

DB = "/data/data/com.termux/files/home/MNFC/nodo_principal_dartony.db"
OUT_DIR = Path("/data/data/com.termux/files/home/MNFC/DIAGNOSTICO_2026-11-15")
OUT_DIR.mkdir(exist_ok=True)

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

print("=" * 78)
print("DIAGNÓSTICO DEL INVENTARIO — BASELINE 15/11/2026")
print("=" * 78)
print()

# ============================================================
# 1. RESUMEN GLOBAL
# ============================================================
print("1. RESUMEN GLOBAL")
print("-" * 78)
print()

r = con.execute("""
    SELECT
        COUNT(*) as total_skus,
        SUM(CASE WHEN estado_global='CUADRADO' THEN 1 ELSE 0 END) as cuadrados,
        SUM(CASE WHEN estado_global='CON_RUPTURAS' THEN 1 ELSE 0 END) as con_rupturas,
        SUM(pares_totales) as pares_total,
        SUM(pares_rotos) as pares_rotos
    FROM sinopsis_rodriguiana
""").fetchone()

print(f"  SKUs totales:        {r['total_skus']:>8,}")
print(f"  SKUs cuadrados:      {r['cuadrados']:>8,}  ({100.0*r['cuadrados']/r['total_skus']:.1f}%)")
print(f"  SKUs con rupturas:   {r['con_rupturas']:>8,}  ({100.0*r['con_rupturas']/r['total_skus']:.1f}%)")
print(f"  Pares totales:       {r['pares_total']:>8,}")
print(f"  Pares rotos:         {r['pares_rotos']:>8,}")
print()

# ============================================================
# 2. RUPTURAS POR DIMENSIÓN
# ============================================================
print("2. RUPTURAS POR DIMENSIÓN")
print("-" * 78)
print()

print(f"  {'Dimensión':25s} {'Roturas':>10s} {'% SKUs':>10s} {'Severidad':>12s}")
print(f"  {'-'*25} {'-'*10} {'-'*10} {'-'*12}")

total_skus = r['total_skus']
dimensiones = []
for row in con.execute("""
    SELECT paradigma, COUNT(*) as n
    FROM pares_adyacencia
    WHERE estado = 'ROTO'
    GROUP BY paradigma
    ORDER BY n DESC
"""):
    pct = 100.0 * row['n'] / total_skus
    if pct > 50: sev = 'CRITICA'
    elif pct > 15: sev = 'ALTA'
    elif pct > 5: sev = 'MEDIA'
    else: sev = 'BAJA'
    print(f"  {row['paradigma']:25s} {row['n']:>10,} {pct:>9.1f}% {sev:>12s}")
    dimensiones.append({'dim': row['paradigma'], 'roturas': row['n'], 'pct': round(pct, 1), 'sev': sev})

print()

# ============================================================
# 3. RUPTURAS POR DETAL (si stock_por_sucursal tiene sucursal)
# ============================================================
print("3. RUPTURAS POR DETAL")
print("-" * 78)
print()

detales = [row['sucursal'] for row in con.execute(
    "SELECT DISTINCT sucursal FROM stock_por_sucursal WHERE sucursal IS NOT NULL AND sucursal != '' ORDER BY sucursal"
)]

por_detal = []
for detal in detales:
    n_skus = con.execute(
        "SELECT COUNT(DISTINCT sku) FROM stock_por_sucursal WHERE sucursal=?", (detal,)
    ).fetchone()[0]

    n_rupturas = con.execute("""
        SELECT COUNT(*) FROM pares_adyacencia p
        WHERE p.estado = 'ROTO'
        AND p.sku IN (SELECT sku FROM stock_por_sucursal WHERE sucursal=?)
    """, (detal,)).fetchone()[0]

    n_cuadrados = con.execute("""
        SELECT COUNT(*) FROM sinopsis_rodriguiana s
        WHERE s.estado_global = 'CUADRADO'
        AND s.sku IN (SELECT sku FROM stock_por_sucursal WHERE sucursal=?)
    """, (detal,)).fetchone()[0]

    pct = 100.0 * n_rupturas / (n_rupturas + n_cuadrados) if (n_rupturas + n_cuadrados) > 0 else 0
    print(f"  {detal:25s} SKUs={n_skus:>5}  Cuadrados={n_cuadrados:>4}  Rupturas={n_rupturas:>5}  ({pct:.1f}%)")
    por_detal.append({'detal': detal, 'skus': n_skus, 'cuadrados': n_cuadrados, 'rupturas': n_rupturas, 'pct': round(pct, 1)})

print()

# ============================================================
# 4. TOP 20 SKUs CON MÁS RUPTURAS (priorizados por stock)
# ============================================================
print("4. TOP 20 SKUs CON MÁS RUPTURAS (priorizados por stock)")
print("-" * 78)
print()

print(f"  {'SKU':15s} {'Familia':15s} {'Stock':>8s} {'Rupturas':>10s} {'Dimensiones rotas':40s}")
print(f"  {'-'*15} {'-'*15} {'-'*8} {'-'*10} {'-'*40}")

top = con.execute("""
    SELECT s.sku, s.familia, s.stock_fisico, s.pares_rotos,
           GROUP_CONCAT(p.paradigma, ', ') as dims_rotas
    FROM sinopsis_rodriguiana s
    JOIN pares_adyacencia p ON p.sku = s.sku AND p.estado = 'ROTO'
    WHERE s.pares_rotos > 0
    GROUP BY s.sku
    ORDER BY s.pares_rotos DESC, s.stock_fisico DESC
    LIMIT 20
""").fetchall()

top_skus = []
for t in top:
    print(f"  {t['sku']:15s} {(t['familia'] or 'N/A'):15s} {t['stock_fisico'] or 0:>8.0f} {t['pares_rotos']:>10d} {t['dims_rotas'][:40]:40s}")
    top_skus.append(dict(t))

print()

# ============================================================
# 5. CLASIFICACIÓN POR SEVERIDAD
# ============================================================
print("5. CLASIFICACIÓN POR SEVERIDAD")
print("-" * 78)
print()

criticos = con.execute("""
    SELECT COUNT(*) FROM sinopsis_rodriguiana
    WHERE pares_rotos >= 4 AND stock_fisico > 0
""").fetchone()[0]

altos = con.execute("""
    SELECT COUNT(*) FROM sinopsis_rodriguiana
    WHERE pares_rotos >= 3 AND pares_rotos < 4 AND stock_fisico > 0
""").fetchone()[0]

medios = con.execute("""
    SELECT COUNT(*) FROM sinopsis_rodriguiana
    WHERE pares_rotos >= 1 AND pares_rotos < 3 AND stock_fisico > 0
""").fetchone()[0]

bajos = con.execute("""
    SELECT COUNT(*) FROM sinopsis_rodriguiana
    WHERE pares_rotos >= 1 AND (stock_fisico IS NULL OR stock_fisico = 0)
""").fetchone()[0]

print(f"  🔴 Críticos (>3 dim rotas + stock>0):    {criticos:>5}")
print(f"  🟠 Altos (3 dim rotas + stock>0):        {altos:>5}")
print(f"  🟡 Medios (1-2 dim rotas + stock>0):     {medios:>5}")
print(f"  🟢 Bajos (ruptura sin stock):            {bajos:>5}")
print()

# ============================================================
# 6. GUARDAR BASELINE CON HASH
# ============================================================
print("6. GUARDANDO BASELINE")
print("-" * 78)
print()

baseline = {
    'fecha': '2026-11-15',
    'timestamp': datetime.now().isoformat(),
    'resumen_global': dict(r),
    'por_dimension': dimensiones,
    'por_detal': por_detal,
    'top_20_skus': top_skus,
    'severidad': {
        'criticos': criticos,
        'altos': altos,
        'medios': medios,
        'bajos': bajos,
    }
}

path = OUT_DIR / "baseline_inventario_2026-11-15.json"
path.write_text(json.dumps(baseline, indent=2, ensure_ascii=False, default=str), encoding='utf-8')
h = hashlib.sha256(path.read_bytes()).hexdigest()

print(f"  Archivo: {path}")
print(f"  SHA-256: {h}")
print(f"  Tamaño:  {path.stat().st_size:,} bytes")
print()

con.close()

print("=" * 78)
print("✅ DIAGNÓSTICO COMPLETADO")
print("=" * 78)
print()
print("  Baseline guardado para comparar con la factura del lunes.")
print(f"  Hash: {h}")

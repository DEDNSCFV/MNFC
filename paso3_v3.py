#!/usr/bin/env python3
"""Paso 3 v3: Pobla trazabilidad usando el CSV del parser v2 (entradas+salidas)."""
import sys, csv
from pathlib import Path
import sqlite3

if len(sys.argv) < 3:
    print("Uso: python paso3_v3.py '<nodo_db>' '<nodo_tec>'")
    sys.exit(1)

NODO = sys.argv[1]
NODO_TEC = sys.argv[2]
DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"
CSV_PATH = Path.home() / "DARTONY_TXT" / "profit_movimientos_parseados.csv"

print("=" * 70)
print(f"  PASO 3 v3 — POBLAR TRAZABILIDAD · {NODO}")
print("=" * 70)
print()

# 1. Leer CSV
print("[1/4] Leyendo CSV del parser v2...")
NODO_CSV = NODO_TEC.lower()
movs_csv = []
with open(CSV_PATH, encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['nodo'].lower() == NODO_CSV:
            movs_csv.append(row)

print(f"  Movimientos del CSV para {NODO}: {len(movs_csv):,}")
print()

# 2. Leer BD
print("[2/4] Leyendo BD...")
conn = sqlite3.connect(DB)
movs_bd = conn.execute("""
    SELECT id, sku, tipo, fecha, cantidad, costo_unitario, stock_actual
    FROM movimientos_historico
    WHERE nodo = ?
    ORDER BY id
""", (NODO,)).fetchall()
print(f"  Movimientos en la BD: {len(movs_bd):,}")
print()

# 3. Match por posición
print("[3/4] Actualizando BD con match por posición...")
actualizados = 0
fallos = 0
n = min(len(movs_csv), len(movs_bd))

for i in range(n):
    id_bd, sku_bd, tipo_bd, fecha_bd, cant_bd, costo_bd, stock_bd = movs_bd[i]
    csv_row = movs_csv[i]

    try:
        entradas = float(csv_row.get('entradas') or 0)
        salidas = float(csv_row.get('salidas') or 0)
        cantidad_csv = entradas + salidas

        if (csv_row['tipo'] != tipo_bd or
            csv_row['fecha'] != fecha_bd or
            abs(cantidad_csv - (cant_bd or 0)) > 0.01):
            fallos += 1
            if fallos <= 5:
                print(f"  Mismatch pos {i}:")
                print(f"    BD:  {tipo_bd} {fecha_bd} cant={cant_bd}")
                print(f"    CSV: {csv_row['tipo']} {csv_row['fecha']} cant={cantidad_csv} (ent={entradas}, sal={salidas})")
            continue

        conn.execute("""
            UPDATE movimientos_historico
            SET numero_documento = ?,
                renglon = ?,
                archivo_origen = ?,
                linea_origen = ?
            WHERE id = ?
        """, (
            csv_row['numero_documento'],
            int(csv_row['renglon']),
            csv_row['archivo_origen'],
            int(csv_row['linea_origen']),
            id_bd
        ))
        actualizados += 1

        if actualizados % 10000 == 0:
            print(f"  ... {actualizados:,} actualizados")

    except Exception as e:
        fallos += 1
        if fallos <= 5:
            print(f"  Error pos {i}: {e}")

conn.commit()

print()
print(f"  Actualizados:  {actualizados:,}")
print(f"  Fallos:        {fallos:,}")
print()

# 4. Verificar
r = conn.execute("""
    SELECT COUNT(*) FROM movimientos_historico
    WHERE nodo = ? AND numero_documento IS NOT NULL
""", (NODO,)).fetchone()[0]
print(f"[4/4] Verificación:")
print(f"  Movimientos con numero_documento: {r:,}")
print(f"  Movimientos totales:              {len(movs_bd):,}")
print(f"  Cobertura:                        {100.0*r/len(movs_bd):.1f}%")

conn.close()

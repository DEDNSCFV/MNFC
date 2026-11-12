#!/usr/bin/env python3
"""
Paso 3 v2: Pobla trazabilidad usando el parser v2 (probado) y match por posición.
Uso: python paso3_v2.py "<nodo_db>" "<nodo_tec>"
"""
import sys, subprocess, csv
from pathlib import Path
import sqlite3

if len(sys.argv) < 3:
    print("Uso: python paso3_v2.py '<nodo_db>' '<nodo_tec>'")
    sys.exit(1)

NODO = sys.argv[1]
NODO_TEC = sys.argv[2]
DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"
CSV_PATH = Path.home() / "DARTONY_TXT" / "profit_movimientos_parseados.csv"

print("=" * 70)
print(f"  PASO 3 v2 — POBLAR TRAZABILIDAD · {NODO}")
print("=" * 70)
print()

# 1. Verificar que el CSV existe (lo genera parser_profit_v2.py)
if not CSV_PATH.exists():
    print(f"[FATAL] No existe {CSV_PATH}")
    print("Ejecuta primero: python ~/MNFC/parser_profit_v2.py")
    sys.exit(1)

# 2. Leer el CSV y filtrar por nodo
print("[1/4] Leyendo CSV del parser v2...")
NODO_CSV = NODO_TEC.lower()  # 04_la_urbina
movs_csv = []
with open(CSV_PATH, encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['nodo'].lower() == NODO_CSV:
            movs_csv.append(row)

print(f"  Movimientos del CSV para {NODO}: {len(movs_csv):,}")
print()

# 3. Leer la BD
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

if len(movs_csv) != len(movs_bd):
    print(f"⚠️ DIFERENCIA: CSV={len(movs_csv):,} vs BD={len(movs_bd):,}")
    print(f"   Diferencia: {abs(len(movs_csv) - len(movs_bd)):,}")
    print()
    print("   Posibles causas:")
    print("   - El CSV incluye movimientos que no están en la BD (o viceversa)")
    print("   - Hay que reconciliar antes de continuar")
    print()

# 4. Match por posición
print("[3/4] Actualizando BD con match por posición...")

actualizados = 0
fallos = 0

# Tomar el mínimo de los dos para evitar IndexError
n = min(len(movs_csv), len(movs_bd))

for i in range(n):
    id_bd, sku_bd, tipo_bd, fecha_bd, cant_bd, costo_bd, stock_bd = movs_bd[i]
    csv_row = movs_csv[i]

    try:
        # Verificar que el movimiento coincide (tipo + fecha + cantidad)
        if (csv_row['tipo'] != tipo_bd or
            csv_row['fecha'] != fecha_bd or
            abs(float(csv_row['cantidad'] or 0) - (cant_bd or 0)) > 0.01):
            fallos += 1
            if fallos <= 5:
                print(f"  ⚠️ Mismatch en posición {i}:")
                print(f"     BD:  {tipo_bd} {fecha_bd} cant={cant_bd}")
                print(f"     CSV: {csv_row['tipo']} {csv_row['fecha']} cant={csv_row['cantidad']}")
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
            print(f"  ⚠️ Error en posición {i}: {e}")

conn.commit()

print()
print(f"  Actualizados:  {actualizados:,}")
print(f"  Fallos:        {fallos:,}")
print()

# 5. Verificar
r = conn.execute("""
    SELECT COUNT(*) FROM movimientos_historico
    WHERE nodo = ? AND numero_documento IS NOT NULL
""", (NODO,)).fetchone()[0]
print(f"[4/4] Verificación:")
print(f"  Movimientos con numero_documento: {r:,}")
print(f"  Movimientos totales:              {len(movs_bd):,}")
print(f"  Cobertura:                        {100.0*r/len(movs_bd):.1f}%")

conn.close()

#!/usr/bin/env python3
"""Cargador seguro: INSERT OR IGNORE. Evita duplicados."""
import sys, csv, sqlite3
from pathlib import Path

if len(sys.argv) < 3:
    print("Uso: python cargar_txt_seguro.py '<archivo.csv>' '<nodo_db>'")
    sys.exit(1)

ARCHIVO = sys.argv[1]
NODO = sys.argv[2]
DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"
conn = sqlite3.connect(DB)

print(f"Cargando {ARCHIVO} en {NODO}...")
insertados = 0
ignorados = 0

with open(ARCHIVO, encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['nodo'].lower() != NODO.lower().replace(" ", "_"):
            continue
        try:
            entradas = float(row.get('entradas') or 0)
            salidas = float(row.get('salidas') or 0)
            cantidad = entradas + salidas
            antes = conn.total_changes
            conn.execute("""
                INSERT OR IGNORE INTO movimientos_historico
                (nodo, sku, descripcion, tipo, fecha, almacen,
                 cantidad, stock_actual, costo_unitario, es_entrada, es_salida,
                 numero_documento, renglon, archivo_origen, linea_origen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (NODO, row['sku'], row['descripcion'], row['tipo'], row['fecha'],
                  row['almacen'], cantidad, float(row.get('stock_actual') or 0),
                  float(row.get('costo_unitario') or 0),
                  1 if entradas > 0 else 0, 1 if salidas < 0 else 0,
                  row['numero_documento'], int(row['renglon']),
                  row['archivo_origen'], int(row['linea_origen'])))
            if conn.total_changes > antes:
                insertados += 1
            else:
                ignorados += 1
        except Exception as e:
            print(f"  Error: {e}")

conn.commit()
print(f"  Insertados: {insertados}")
print(f"  Ignorados:  {ignorados}")
conn.close()

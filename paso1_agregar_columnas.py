#!/usr/bin/env python3
"""Paso 1: Agrega columnas de trazabilidad a movimientos_historico."""
import sqlite3
from pathlib import Path

DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"
conn = sqlite3.connect(DB)

print("=" * 70)
print("  PASO 1 — AGREGAR COLUMNAS DE TRAZABILIDAD")
print("=" * 70)
print()

# Verificar columnas actuales
cols = [c[1] for c in conn.execute("PRAGMA table_info(movimientos_historico)").fetchall()]
print(f"Columnas actuales: {len(cols)}")
for c in cols:
    print(f"  {c}")

nuevas = ['numero_documento', 'renglon', 'archivo_origen', 'linea_origen']

print()
print("Agregando columnas nuevas:")
for col in nuevas:
    if col not in cols:
        tipo = 'TEXT' if col in ('numero_documento', 'archivo_origen') else 'INTEGER'
        conn.execute(f"ALTER TABLE movimientos_historico ADD COLUMN {col} {tipo}")
        print(f"  ✓ {col} ({tipo})")
    else:
        print(f"  - {col} ya existe")

conn.commit()

# Verificar
cols = [c[1] for c in conn.execute("PRAGMA table_info(movimientos_historico)").fetchall()]
print()
print(f"Columnas después: {len(cols)}")
for c in cols:
    print(f"  {c}")

conn.close()
print()
print("Paso 1 completado.")

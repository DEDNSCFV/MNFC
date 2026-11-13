#!/usr/bin/env python3
"""Verifica la cobertura de trazabilidad en toda la BD."""
import sqlite3
from pathlib import Path

DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"
conn = sqlite3.connect(DB)

print("=" * 70)
print("  COBERTURA TOTAL DE TRAZABILIDAD")
print("=" * 70)
print()

print("Por nodo:")
total_global = 0
con_global = 0
for nodo, total, con_doc, sin_doc in conn.execute("""
    SELECT nodo,
           COUNT(*) AS total,
           SUM(CASE WHEN numero_documento IS NOT NULL THEN 1 ELSE 0 END) AS con_doc,
           SUM(CASE WHEN numero_documento IS NULL THEN 1 ELSE 0 END) AS sin_doc
    FROM movimientos_historico
    GROUP BY nodo
    ORDER BY nodo
""").fetchall():
    pct = round(100.0 * con_doc / total, 1) if total else 0
    print(f"  {nodo:15s}: {total:>7,} total | {con_doc:>7,} con traz ({pct:>5}%) | {sin_doc:>7,} sin traz")
    total_global += total
    con_global += con_doc

print()
print(f"TOTAL: {total_global:,} movimientos | {con_global:,} con trazabilidad ({100.0*con_global/total_global:.1f}%)")
print()

print("Índice único:")
r = conn.execute("""
    SELECT name, sql FROM sqlite_master
    WHERE type = 'index' AND name = 'idx_movimiento_unico'
""").fetchone()
if r:
    print(f"  ✓ {r[0]} existe")
else:
    print(f"  ✗ No existe")

conn.close()

#!/usr/bin/env python3
"""Verifica los 2 movimientos con mismatch."""
import sqlite3
from pathlib import Path

DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"
conn = sqlite3.connect(DB)

print("=" * 70)
print("  VERIFICACIÓN DE LOS 2 MISMATCHES")
print("=" * 70)
print()

for row in conn.execute("""
    SELECT id, sku, tipo, fecha, cantidad, stock_actual,
           numero_documento, renglon, archivo_origen, linea_origen
    FROM movimientos_historico
    WHERE nodo = '04 La Urbina'
      AND tipo = 'FACT'
      AND fecha = '05/01/2026'
      AND cantidad = -1.0
      AND numero_documento IS NOT NULL
    LIMIT 5
""").fetchall():
    print(f"  id={row[0]}")
    print(f"    sku:              {row[1]}")
    print(f"    tipo:             {row[2]}")
    print(f"    fecha:            {row[3]}")
    print(f"    cantidad:         {row[4]}")
    print(f"    stock_actual:     {row[5]}")
    print(f"    numero_documento: {row[6]}")
    print(f"    renglon:          {row[7]}")
    print(f"    archivo_origen:   {row[8]}")
    print(f"    linea_origen:     {row[9]}")
    print()

# ¿Hay duplicados reales con la nueva clave?
print("Duplicados con la clave (nodo, tipo, numero_documento, renglon, fecha):")
r = conn.execute("""
    SELECT COUNT(*) FROM (
        SELECT nodo, tipo, numero_documento, renglon, fecha, COUNT(*) AS n
        FROM movimientos_historico
        WHERE numero_documento IS NOT NULL
        GROUP BY nodo, tipo, numero_documento, renglon, fecha
        HAVING COUNT(*) > 1
    )
""").fetchone()[0]
print(f"  Grupos duplicados con la nueva clave: {r:,}")
print()

# ¿Cuántos movimientos tienen la clave completa?
r = conn.execute("""
    SELECT COUNT(*) FROM movimientos_historico
    WHERE numero_documento IS NOT NULL AND renglon IS NOT NULL AND fecha IS NOT NULL
""").fetchone()[0]
print(f"Movimientos con clave completa: {r:,}")

conn.close()

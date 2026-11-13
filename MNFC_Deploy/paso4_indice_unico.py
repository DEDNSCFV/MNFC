#!/usr/bin/env python3
"""
Paso 4: Crea el índice único parcial para movimientos con trazabilidad.
Solo aplica a movimientos con numero_documento (Central no lo tiene).
"""
import sqlite3
from pathlib import Path

DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"
conn = sqlite3.connect(DB)

print("=" * 70)
print("  PASO 4 — CREAR ÍNDICE ÚNICO PARCIAL")
print("=" * 70)
print()

# Verificar que no hay duplicados
print("[1/3] Verificando que no hay duplicados con la nueva clave...")
r = conn.execute("""
    SELECT COUNT(*) FROM (
        SELECT nodo, tipo, numero_documento, renglon, fecha, COUNT(*) AS n
        FROM movimientos_historico
        WHERE numero_documento IS NOT NULL
        GROUP BY nodo, tipo, numero_documento, renglon, fecha
        HAVING COUNT(*) > 1
    )
""").fetchone()[0]

if r > 0:
    print(f"  ⚠️ Hay {r} grupos duplicados. No se puede crear el índice único.")
    print("  Primero hay que limpiarlos.")
    conn.close()
    exit(1)

print(f"  ✅ 0 duplicados. Se puede crear el índice.")

# Verificar si ya existe
print()
print("[2/3] Creando índice único parcial...")
existe = conn.execute("""
    SELECT COUNT(*) FROM sqlite_master
    WHERE type = 'index' AND name = 'idx_movimiento_unico'
""").fetchone()[0]

if existe:
    print("  - El índice ya existe. Se elimina y se recrea.")
    conn.execute("DROP INDEX idx_movimiento_unico")

# Crear el índice único PARCIAL (solo para movimientos con numero_documento)
conn.execute("""
    CREATE UNIQUE INDEX idx_movimiento_unico
    ON movimientos_historico (nodo, tipo, numero_documento, renglon, fecha)
    WHERE numero_documento IS NOT NULL
""")
conn.commit()

print("  ✅ Índice único parcial creado.")

# Verificar
print()
print("[3/3] Verificación:")
r = conn.execute("""
    SELECT sql FROM sqlite_master
    WHERE type = 'index' AND name = 'idx_movimiento_unico'
""").fetchone()
print(f"  SQL del índice:")
print(f"    {r[0]}")

# Estadísticas
r = conn.execute("""
    SELECT COUNT(*) FROM movimientos_historico
    WHERE numero_documento IS NOT NULL
""").fetchone()[0]
print()
print(f"  Movimientos con trazabilidad (protegidos por el índice): {r:,}")
print(f"  Movimientos sin trazabilidad (no protegidos):            {462104 - r:,}")

conn.close()
print()
print("Paso 4 completado.")

#!/usr/bin/env python3
"""
sync_bom_boo.py
Sincroniza las tablas de datos brutos desde la BOM (PC) a la BOO (Termux).
Se ejecuta en el PC después de cada extracción AM0/PM0.
Produce un archivo .db parcial que se transfiere a Termux.
"""

import sqlite3
import shutil
import hashlib
from datetime import datetime
from pathlib import Path

# ⚠️ AJUSTAR: rutas del PC
BOM_PATH = Path("C:/Users/Admin/Desktop/dartony_auditoria_v2.db")
SYNC_OUT = Path("C:/Users/Admin/Desktop/sync_boo_2026-11-16.db")

TABLAS_SYNC = [
    'inventario_nodo',
    'stock_por_sucursal',
    'movimientos_dartony',
]

print("=" * 72)
print("SINCRONIZACIÓN BOM → BOO")
print("=" * 72)
print()

# 1. Copiar la BOM
print(f"1. Copiando BOM: {BOM_PATH}")
shutil.copy2(BOM_PATH, SYNC_OUT)
print(f"   ✅ Copia: {SYNC_OUT}")

# 2. Limpiar tablas que no van a la BOO
print("\n2. Limpiando tablas que no se sincronizan...")
con = sqlite3.connect(SYNC_OUT)
tablas_existentes = [r[0] for r in con.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
)]

for t in tablas_existentes:
    if t not in TABLAS_SYNC and not t.startswith('sqlite_'):
        con.execute(f"DROP TABLE IF EXISTS {t}")
        print(f"   - {t} eliminada")

con.commit()
con.close()

# 3. Hash del archivo sincronizado
h = hashlib.sha256(SYNC_OUT.read_bytes()).hexdigest()
size = SYNC_OUT.stat().st_size

print(f"\n3. Archivo de sincronización:")
print(f"   Ruta: {SYNC_OUT}")
print(f"   Tamaño: {size:,} bytes")
print(f"   SHA-256: {h}")
print()

# 4. Instrucciones
print("=" * 72)
print("PRÓXIMO PASO")
print("=" * 72)
print()
print("  1. Transferir el archivo a Termux:")
print(f"     adb push {SYNC_OUT} /sdcard/Download/")
print("     (o USB, o sync)")
print()
print("  2. En Termux, reemplazar la BOO:")
print(f"     cp /sdcard/Download/sync_boo_2026-11-16.db ~/MNFC/nodo_principal_dartony.db")
print()
print("  3. Verificar:")
print("     cd ~/MNFC && python3 -c 'import sqlite3; c=sqlite3.connect(\"nodo_principal_dartony.db\"); print(c.execute(\"SELECT COUNT(*) FROM inventario_nodo\").fetchone())'")
print()

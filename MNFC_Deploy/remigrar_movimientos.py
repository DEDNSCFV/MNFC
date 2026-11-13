import sqlite3
import os
from decimal import Decimal
from mnfc.money import to_centimos

DB_ORIGEN = os.path.expanduser("~/DARTONY_EXTRACT/SCFV-DARTONY/inventario.db")
DB_DESTINO = "nodo_principal_dartony.db"

print("🚀 Re-migrando 462K movimientos originales...")
con_o = sqlite3.connect(DB_ORIGEN)
con_d = sqlite3.connect(DB_DESTINO)
cur_o = con_o.cursor()
cur_d = con_d.cursor()

cur_d.execute("""
    CREATE TABLE movimientos_dartony (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku TEXT NOT NULL,
        descripcion TEXT,
        tipo TEXT,
        fecha TEXT,
        almacen TEXT,
        cantidad REAL,
        stock_actual REAL,
        costo_unitario_cent INTEGER,
        nodo TEXT,
        numero_documento TEXT
    )
""")

cur_o.execute("""
    SELECT sku, descripcion, tipo, fecha, almacen, cantidad,
           stock_actual, costo_unitario, nodo, numero_documento
    FROM movimientos_historico
""")

batch = []
insertados = 0
for row in cur_o.fetchall():
    sku, desc, tipo, fecha, alm, cant, stock, costo, nodo, doc = row
    try:
        costo_cent = to_centimos(Decimal(str(costo or 0)))
        batch.append((sku, desc, tipo, fecha, alm, cant or 0, stock or 0, costo_cent, nodo, doc))
        if len(batch) >= 10000:
            cur_d.executemany("""
                INSERT INTO movimientos_dartony (sku, descripcion, tipo, fecha, almacen, cantidad, stock_actual, costo_unitario_cent, nodo, numero_documento)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            con_d.commit()
            insertados += len(batch)
            batch = []
    except:
        continue

if batch:
    cur_d.executemany("""
        INSERT INTO movimientos_dartony (sku, descripcion, tipo, fecha, almacen, cantidad, stock_actual, costo_unitario_cent, nodo, numero_documento)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, batch)
    con_d.commit()
    insertados += len(batch)

con_o.close()
con_d.close()
print(f"✅ {insertados:,} movimientos re-migrados exitosamente.")

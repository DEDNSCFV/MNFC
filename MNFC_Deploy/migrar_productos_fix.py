import sqlite3
import os
from decimal import Decimal
from datetime import datetime
from zoneinfo import ZoneInfo
from mnfc.money import to_centimos

TZ = ZoneInfo("America/Caracas")
DB_ORIGEN = os.path.expanduser("~/DARTONY_EXTRACT/SCFV-DARTONY/inventario.db")
DB_DESTINO = "nodo_principal_dartony.db"

print("📦 Migrando maestro de productos (13,874 SKUs reales)...")
con_o = sqlite3.connect(DB_ORIGEN)
con_d = sqlite3.connect(DB_DESTINO)
cur_o = con_o.cursor()
cur_d = con_d.cursor()

cur_o.execute("""
    SELECT codigo, descripcion, precio_unitario_usd, costo_unitario_usd,
           stock_central, marca, familia
    FROM maestro_sku
    WHERE codigo IS NOT NULL AND codigo != ''
""")
rows = cur_o.fetchall()
ts = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")

insertados = 0
for codigo, desc, precio_usd, costo_usd, stock, marca, familia in rows:
    try:
        precio_cent = to_centimos(Decimal(str(precio_usd or 0)))
        costo_cent = to_centimos(Decimal(str(costo_usd or 0)))
        cur_d.execute("""
            INSERT INTO inventario_nodo
            (sku, nombre, cantidad_fisica, costo_unitario_cent, precio_venta_cent,
             marca, familia, ultima_actualizacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(sku) DO UPDATE SET
                cantidad_fisica = excluded.cantidad_fisica,
                costo_unitario_cent = excluded.costo_unitario_cent,
                precio_venta_cent = excluded.precio_venta_cent,
                ultima_actualizacion = excluded.ultima_actualizacion
        """, (codigo.strip(), (desc or "SIN DESCRIPCIÓN").strip()[:100],
              int(stock or 0), costo_cent, precio_cent,
              marca, familia, ts))
        insertados += 1
    except Exception as e:
        pass

con_d.commit()
con_o.close()
con_d.close()
print(f"✅ {insertados:,} productos migrados exitosamente.")

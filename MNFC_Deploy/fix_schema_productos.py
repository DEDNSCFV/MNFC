import sqlite3

DB_DESTINO = "nodo_principal_dartony.db"
con = sqlite3.connect(DB_DESTINO)
cur = con.cursor()

# Borrar la tabla vieja (está vacía, no perdemos nada)
cur.execute("DROP TABLE IF EXISTS inventario_nodo")

# Crear la tabla con la estructura correcta
cur.execute("""
    CREATE TABLE inventario_nodo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku TEXT UNIQUE NOT NULL,
        nombre TEXT NOT NULL,
        cantidad_fisica INTEGER NOT NULL,
        costo_unitario_cent INTEGER NOT NULL,
        precio_venta_cent INTEGER NOT NULL,
        marca TEXT,
        familia TEXT,
        ultima_actualizacion TEXT NOT NULL
    )
""")
con.commit()
con.close()
print("✅ Tabla 'inventario_nodo' recreada con columnas completas.")

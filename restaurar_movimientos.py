import sqlite3

DB = "nodo_principal_dartony.db"
con = sqlite3.connect(DB)
cur = con.cursor()

print("🗑️ Borrando tabla de movimientos corrupta...")
cur.execute("DROP TABLE IF EXISTS movimientos_dartony")
con.commit()
con.close()
print("✅ Tabla borrada. Listos para re-migrar.")

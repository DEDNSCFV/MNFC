import sqlite3
import os

DB_NUEVA = "nodo_principal_cliente.db"
SCHEMA = "migrations/schema_vacio.sql"

print("="*60)
print(" 🏛️  MNFC - INSTALADOR PARA NUEVO CLIENTE")
print("="*60)

if not os.path.exists(SCHEMA):
    print(f"❌ Error: No se encuentra el archivo {SCHEMA}")
    exit(1)

print(f"⏳ Creando base de datos en blanco: {DB_NUEVA}...")

con = sqlite3.connect(DB_NUEVA)
with open(SCHEMA, "r") as f:
    schema_sql = f.read()
    con.executescript(schema_sql)

con.commit()
con.close()

print(f"✅ Base de datos creada exitosamente.")
print(f"👉 Ahora puede ejecutar 'python mnfc_cli.py' o 'python ingesta_cruda.py'")
print("="*60)

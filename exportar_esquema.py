import sqlite3

DB_ORIGEN = "nodo_principal_dartony.db"
ARCHIVO_SQL = "migrations/schema_vacio.sql"

con = sqlite3.connect(DB_ORIGEN)
cur = con.cursor()

# Obtener todo el SQL de creación de tablas e índices
cur.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%'")
sentencias = cur.fetchall()

with open(ARCHIVO_SQL, "w") as f:
    f.write("-- ESQUEMA MNFC v0.5.0 (Base de Datos Vacía)\n")
    f.write("-- Generado automáticamente para despliegue en cliente\n\n")
    for (sql,) in sentencias:
        if sql:
            f.write(sql + ";\n\n")

con.close()
print(f"✅ Esquema exportado a: {ARCHIVO_SQL}")

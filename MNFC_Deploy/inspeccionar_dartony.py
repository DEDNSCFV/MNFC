import sqlite3
import os

DB_ORIGEN = os.path.expanduser("~/DARTONY_EXTRACT/SCFV-DARTONY/inventario.db")

print("="*70)
print("🔍 INSPECCIONANDO BASE DE DATOS ORIGINAL DE DARTONY")
print("="*70)

if not os.path.exists(DB_ORIGEN):
    print(f"❌ No se encontró la base de datos en: {DB_ORIGEN}")
    print("   Verifica la ruta.")
else:
    print(f"✅ Base de datos encontrada: {DB_ORIGEN}")
    print(f"   Tamaño: {os.path.getsize(DB_ORIGEN) / (1024*1024):.2f} MB\n")
    
    con = sqlite3.connect(DB_ORIGEN)
    cur = con.cursor()
    
    # Ver todas las tablas
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tablas = [r[0] for r in cur.fetchall()]
    print(f"📁 Tablas encontradas: {tablas}\n")
    
    for tabla in tablas:
        print(f"--- Estructura de la tabla '{tabla}' ---")
        cur.execute(f"PRAGMA table_info({tabla})")
        cols = cur.fetchall()
        for c in cols:
            print(f"   {c[1]:<20} | Tipo: {c[2]}")
        
        # Contar registros
        cur.execute(f"SELECT COUNT(*) FROM {tabla}")
        count = cur.fetchone()[0]
        print(f"   Total de registros: {count:,}")
        
        # Mostrar 1 fila de ejemplo
        cur.execute(f"SELECT * FROM {tabla} LIMIT 1")
        muestra = cur.fetchone()
        if muestra:
            print(f"   Ejemplo (1er registro): {muestra[:5]}...")  # Solo primeros 5 campos
        print()
    
    con.close()

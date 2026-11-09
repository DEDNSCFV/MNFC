import csv
import sqlite3
from pathlib import Path

DB = Path.home() / "dartony_auditoria.db"
TXT = Path.home() / "conteo_fisico.txt" # Asegúrate de poner el nombre real de tu archivo txt
FECHA_CONTEO = "2026-11-01" # Cambia la fecha si es necesario
DELIMITADOR = ';' # Puede ser ',', ';' o '\t' (tabulación)

print(f"Abriendo: {TXT.name}")
con = sqlite3.connect(DB)
insertados = 0

# Abrimos el TXT. Ojo: si el TXT viene de Windows, usamos cp1252 o latin-1
with open(TXT, 'r', encoding='cp1252') as f:
    lector = csv.reader(f, delimiter=DELIMITADOR)
    
    # Si el TXT tiene encabezados, descomenta la siguiente línea:
    # next(lector, None)
    
    for fila in lector:
        if len(fila) < 4: continue # Saltar filas vacías
        
        empresa = fila[0].strip()
        sku = fila[1].strip()
        descripcion = fila[2].strip()
        cantidad = float(fila[3].strip()) if fila[3].strip() else 0.0
        
        if not sku: continue
        
        con.execute("""
            INSERT OR REPLACE INTO conteo_fisico 
            (empresa, sku, descripcion, cantidad_fisica, fecha_conteo, archivo_origen)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (empresa, sku, descripcion, cantidad, FECHA_CONTEO, TXT.name))
        insertados += 1

con.commit()
con.close()
print(f"✅ Ingeridos: {insertados} productos desde TXT.")

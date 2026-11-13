import os
import re

# Lista de archivos a parchear
archivos = ["ingesta_cruda.py", "kpis_hallazgos.py", "analisis_foda_5s.py", "informe_coso.py"]

for archivo in archivos:
    if not os.path.exists(archivo):
        continue
    
    with open(archivo, "r") as f:
        contenido = f.read()
    
    # Reemplazar la asignación estática por una lectura dinámica del config
    if 'DB_PATH = "nodo_principal_dartony.db"' in contenido:
        nuevo_bloque = '''import json
try:
    with open("config.json", "r") as _f:
        _config = json.load(_f)
        DB_PATH = _config.get("db_path", "nodo_principal_cliente.db")
except Exception:
    DB_PATH = "nodo_principal_cliente.db"'''
        
        contenido = contenido.replace('DB_PATH = "nodo_principal_dartony.db"', nuevo_bloque)
        
        with open(archivo, "w") as f:
            f.write(contenido)
        print(f"✅ Parcheado: {archivo}")
    else:
        print(f"ℹ️  Sin cambios (ya es dinámico o usa otra variable): {archivo}")

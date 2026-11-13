#!/usr/bin/env python3
"""
Registro de idempotencia: evita procesar TXT ya procesados.
Uso:
  python idempotencia.py verificar "<nodo_tecnico>" "<ruta_txt>"
  python idempotencia.py registrar "<nodo_tecnico>" "<ruta_txt>"
  python idempotencia.py estado    "<nodo_tecnico>"
"""
import sys, hashlib, json
from pathlib import Path
from datetime import datetime, timezone

if len(sys.argv) < 3:
    print("Uso:")
    print("  python idempotencia.py verificar '<nodo>' '<ruta_txt>'")
    print("  python idempotencia.py registrar '<nodo>' '<ruta_txt>'")
    print("  python idempotencia.py estado    '<nodo>'")
    sys.exit(1)

ACCION = sys.argv[1]
NODO = sys.argv[2]
BASE = Path.home() / "DARTONY_CONTROL" / NODO / "idempotencia"
BASE.mkdir(parents=True, exist_ok=True)
REGISTRO = BASE / "procesados.json"

# Cargar registro existente
if REGISTRO.exists():
    with open(REGISTRO, encoding='utf-8') as f:
        registro = json.load(f)
else:
    registro = {"nodo": NODO, "procesados": {}}

def calcular_hash(ruta):
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()

if ACCION == "verificar":
    ruta = sys.argv[3]
    h = calcular_hash(ruta)
    if h in registro["procesados"]:
        print(f"YA_PROCESADO|{h}|{registro['procesados'][h]['fecha']}")
    else:
        print(f"NUEVO|{h}|")

elif ACCION == "registrar":
    ruta = sys.argv[3]
    h = calcular_hash(ruta)
    fecha = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    registro["procesados"][h] = {
        "archivo": str(ruta),
        "fecha": fecha,
    }
    with open(REGISTRO, 'w', encoding='utf-8') as f:
        json.dump(registro, f, indent=2, ensure_ascii=False)
    print(f"REGISTRADO|{h}|{fecha}")

elif ACCION == "estado":
    print(f"Nodo: {NODO}")
    print(f"Total TXT procesados: {len(registro['procesados'])}")
    print()
    for h, info in list(registro["procesados"].items())[:10]:
        print(f"  {h[:16]}... | {info['fecha']} | {info['archivo']}")
    if len(registro["procesados"]) > 10:
        print(f"  ... y {len(registro['procesados']) - 10} más")

else:
    print(f"Acción desconocida: {ACCION}")
    sys.exit(1)

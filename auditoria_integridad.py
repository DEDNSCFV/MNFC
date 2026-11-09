#!/usr/bin/env python3
"""Auditoría de integridad — verifica hashes del corpus."""
import hashlib, sys, json
from datetime import datetime, timezone
from pathlib import Path

if len(sys.argv) < 2:
    print("Uso: python auditoria_integridad.py '<nodo>'")
    sys.exit(1)

NODO = sys.argv[1]
NODO_SLUG = NODO.replace(" ", "_")
BASE = Path.home() / "DARTONY_CONTROL" / NODO_SLUG / "auditoria" / "4_integridad"
BASE.mkdir(parents=True, exist_ok=True)
CORPUS = Path.home() / "DARTONY_CONTROL" / NODO_SLUG / "corpus"
FECHA = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

print("=" * 60)
print(f"AUDITORÍA DE INTEGRIDAD — {NODO}")
print("=" * 60)

archivos = list(CORPUS.rglob("*.TXT"))
if not archivos:
    print(f"No hay archivos TXT en {CORPUS}")
    sys.exit(0)

print(f"Archivos a verificar: {len(archivos)}")

verificacion = BASE / "hashes" / f"verificacion_{FECHA}.json"
verificacion.parent.mkdir(parents=True, exist_ok=True)

resultados = []
for archivo in archivos:
    h = hashlib.sha256(archivo.read_bytes()).hexdigest()
    resultados.append({
        'archivo': str(archivo.relative_to(CORPUS)),
        'sha256': h,
        'tamano': archivo.stat().st_size
    })

with open(verificacion, 'w', encoding='utf-8') as f:
    json.dump({
        'nodo': NODO,
        'fecha_verificacion': FECHA,
        'archivos': resultados
    }, f, indent=2, ensure_ascii=False)

print(f"Verificación guardada: {verificacion.name}")
print(f"Total archivos: {len(resultados)}")

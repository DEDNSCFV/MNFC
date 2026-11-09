#!/usr/bin/env python3
"""Analiza la naturaleza de los TXT: acumulativos, incrementales o diarios."""
import re
from pathlib import Path
from datetime import datetime
from collections import Counter

BASE = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/corpus/fuentes_profit_diarias"

RE_FECHA = re.compile(r'(\d{2}/\d{2}/\d{4})')
RE_ENCABEZADO = re.compile(r'Rangos?:\s*Fecha:\s*(\d{2}/\d{2}/\d{4})\s*Hasta\s*(\d{2}/\d{2}/\d{4})')

print("=" * 70)
print("  ANÁLISIS DE LA NATURALEZA DE LOS TXT")
print("=" * 70)
print()

for nodo_dir in BASE.iterdir():
    if not nodo_dir.is_dir():
        continue

    nodo = nodo_dir.name
    print(f"════════════════════════════════════════════════════════════")
    print(f"  NODO: {nodo}")
    print(f"════════════════════════════════════════════════════════════")
    print()

    for archivo in sorted(nodo_dir.glob("*.TXT")):
        with open(archivo, 'r', encoding='latin-1', errors='replace') as f:
            contenido = f.read()

        # Buscar el encabezado con el rango declarado
        m = RE_ENCABEZADO.search(contenido)
        rango_declarado = None
        if m:
            rango_declarado = (m.group(1), m.group(2))

        # Extraer todas las fechas del contenido
        fechas = RE_FECHA.findall(contenido)

        # Convertir a objetos date
        fechas_obj = []
        for f in fechas:
            try:
                fechas_obj.append(datetime.strptime(f, '%d/%m/%Y').date())
            except ValueError:
                pass

        if not fechas_obj:
            print(f"  {archivo.name[:60]}")
            print(f"    Sin fechas detectadas")
            print()
            continue

        fechas_unicas = sorted(set(fechas_obj))
        fecha_min = fechas_unicas[0]
        fecha_max = fechas_unicas[-1]

        # Distribución por mes
        por_mes = Counter(f.strftime('%Y-%m') for f in fechas_obj)

        print(f"  {archivo.name[:60]}")
        print(f"    Tamaño:              {archivo.stat().st_size:,} bytes")
        if rango_declarado:
            print(f"    Rango declarado:     {rango_declarado[0]} → {rango_declarado[1]}")
        print(f"    Fecha mínima real:   {fecha_min}")
        print(f"    Fecha máxima real:   {fecha_max}")
        print(f"    Días únicos:         {len(fechas_unicas)}")
        print(f"    Total fechas:        {len(fechas_obj):,}")
        print(f"    Meses cubiertos:     {len(por_mes)}")
        for mes in sorted(por_mes.keys()):
            print(f"      {mes}: {por_mes[mes]:>8,} fechas")
        print()

conn = None

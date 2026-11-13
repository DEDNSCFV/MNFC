#!/usr/bin/env python3
"""CAPA 15 — Archivos de precio: ¿están en USD o VES? ¿Coinciden con el maestro?"""
import re
import sqlite3
from pathlib import Path

BASE = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/corpus/fuentes_profit_diarias"
DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"

print("=" * 70)
print("  CAPA 15 · ARCHIVOS DE PRECIO vs MAESTRO")
print("=" * 70)
print()

# Archivo de precio de La Urbina
arch = BASE / "04_la_urbina" / "ARTÍCULOS CON SU PRECIO TERES AL 24OCT2026.TXT"

RE_PRECIO = re.compile(
    r'^(?P<codigo>[A-Z0-9][A-Z0-9_\-\.]{2,30})\s{5,}'
    r'(?P<descripcion>.+?)\s{5,}'
    r'(?P<precio>[\d,]+\.\d{2})\s+'
    r'(?P<unidad>\w+)\s*$'
)

if arch.exists():
    precios_archivo = {}
    with open(arch, 'r', encoding='latin-1', errors='replace') as f:
        for linea in f:
            m = RE_PRECIO.match(linea.rstrip('\n\r'))
            if m:
                try:
                    precio = float(m.group('precio').replace(',', ''))
                    precios_archivo[m.group('codigo')] = precio
                except ValueError:
                    pass

    print(f"SKUs con precio en el archivo: {len(precios_archivo):,}")
    print()

    conn = sqlite3.connect(DB)
    precios_db = dict(conn.execute("""
        SELECT codigo, precio_unitario_usd FROM maestro_sku
        WHERE precio_unitario_usd > 0
    """).fetchall())

    print(f"SKUs con precio en la DB: {len(precios_db):,}")
    print()

    # Comparar
    en_ambos = 0
    iguales = 0
    diferentes = 0
    suma_archivo = 0
    suma_db = 0
    ejemplos_dif = []

    for sku, p_arch in precios_archivo.items():
        if sku in precios_db:
            en_ambos += 1
            p_db = precios_db[sku]
            suma_archivo += p_arch
            suma_db += p_db
            if abs(p_arch - p_db) < 0.01:
                iguales += 1
            else:
                diferentes += 1
                if len(ejemplos_dif) < 5:
                    ejemplos_dif.append((sku, p_arch, p_db))

    print(f"SKUs en ambos: {en_ambos:,}")
    print(f"  Precios iguales: {iguales:,} ({100.0*iguales/en_ambos if en_ambos else 0:.1f}%)")
    print(f"  Precios DIFERENTES: {diferentes:,} ({100.0*diferentes/en_ambos if en_ambos else 0:.1f}%)")
    print()
    print(f"  Suma archivo: {suma_archivo:,.2f}")
    print(f"  Suma DB:      {suma_db:,.2f}")
    print()

    if ejemplos_dif:
        print("  Primeros 5 ejemplos de diferencia:")
        print(f"  {'SKU':<15} {'Precio archivo':>18} {'Precio DB':>18}")
        for sku, pa, pd in ejemplos_dif:
            print(f"  {sku:<15} {pa:>18,.2f} {pd:>18,.2f}")
        print()

    conn.close()
else:
    print(f"[AUSENTE] {arch}")

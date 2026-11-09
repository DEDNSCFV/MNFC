#!/usr/bin/env python3
"""
Parser de archivos Profit Plus Administrativo · v2
Fix: SKU empieza en columna 0, movimiento empieza con 2 espacios.
"""
import os
import re
import csv
import sys
from pathlib import Path
from collections import Counter

BASE = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/corpus/fuentes_profit_diarias"
OUT = Path.home() / "DARTONY_TXT"

TIPOS = ['NREC', 'NENT', 'FACT', 'FAC', 'AJUE', 'AJUS', 'DCLI', 'DPRO', 'DEV', 'NCRE', 'NDEB']

# Movimiento: 2+ espacios iniciales, tipo, número, renglón
RE_MOV = re.compile(
    r'^\s{2,}(' + '|'.join(TIPOS) + r')\s+(\d+)\s+(\d+)\s+'
)

# SKU: empieza en columna 0, código, 8+ espacios, descripción con mayúscula
RE_SKU = re.compile(
    r'^([A-Z0-9][A-Z0-9_\-\.]{2,30})\s{8,}([A-ZÁÉÍÓÚÑ][A-Za-z0-9ÁÉÍÓÚÑáéíóúñ\s\-\.,/()]+?)\s{5,}[\d,]+\.\d{2}\s*$'
)

# Fecha dentro de línea
RE_FECHA = re.compile(r'(\d{2}/\d{2}/\d{4})\s+\d{2}:\d{2}\s+[AP]M')

# Almacén después de la fecha
RE_ALMACEN = re.compile(r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}\s+[AP]M\s+(\d{3,4})')

# Excluir líneas de cabecera / pie / estructura
EXCLUIR_HEADERS = [
    'Profit Plus', 'INVERSIONES CAUCHOS', 'Rangos:',
    'Sub-Total', 'Tipo/Op', '* Movimiento ya contabilizado',
    'MOVIMIENTOS DE INVENTARIO', 'AJUSTES DE ENTRADA',
]


def es_excluible(linea):
    if not linea.strip():
        return True
    for patron in EXCLUIR_HEADERS:
        if patron in linea:
            return True
    # Página con caracteres raros de encoding
    if 'gina:' in linea or 'Página' in linea or 'P�gina' in linea:
        return True
    # Artículo (header de columna)
    if linea.strip().startswith('Art') and 'culo' in linea:
        return True
    return False


def extraer_numeros(linea):
    """Extrae los números decimales del final de la línea, en orden."""
    return re.findall(r'-?[\d,]+\.\d{2}', linea)


def parsear_archivo(archivo, nodo):
    movimientos = []
    sku_actual = None
    desc_actual = None
    n_linea = 0

    with open(archivo, 'r', encoding='latin-1', errors='replace') as f:
        for linea in f:
            n_linea += 1
            linea = linea.rstrip('\n\r')

            if es_excluible(linea):
                continue

            # ¿Es movimiento?
            m = RE_MOV.match(linea)
            if m and sku_actual:
                tipo = m.group(1)
                numero = m.group(2)
                renglon = m.group(3)

                mf = RE_FECHA.search(linea)
                fecha = mf.group(1) if mf else ''
                if not fecha:
                    # Sin fecha = no es movimiento real (probablemente sub-línea)
                    continue

                ma = RE_ALMACEN.search(linea)
                almacen = ma.group(1) if ma else ''

                numeros = extraer_numeros(linea)
                entradas = ''
                salidas = ''
                stock = ''
                costo = ''
                if len(numeros) >= 1:
                    costo = numeros[-1].replace(',', '')
                if len(numeros) >= 2:
                    stock = numeros[-2].replace(',', '')
                if len(numeros) >= 3:
                    for n in numeros[:-2]:
                        if n.startswith('-'):
                            salidas = n.replace(',', '')
                        elif n not in ('0.00', '0'):
                            entradas = n.replace(',', '')

                movimientos.append({
                    'nodo': nodo,
                    'sku': sku_actual,
                    'descripcion': (desc_actual or '')[:50],
                    'tipo': tipo,
                    'numero_documento': numero,
                    'renglon': renglon,
                    'fecha': fecha,
                    'almacen': almacen,
                    'entradas': entradas,
                    'salidas': salidas,
                    'stock_actual': stock,
                    'costo_unitario': costo,
                    'archivo_origen': os.path.basename(archivo),
                    'linea_origen': n_linea,
                })
                continue

            # ¿Es SKU? Solo si empieza en columna 0
            if not linea or linea[0] == ' ':
                continue
            ms = RE_SKU.match(linea)
            if ms:
                sku_actual = ms.group(1)
                desc_actual = ms.group(2).strip()
                continue

    return movimientos


def main():
    if not BASE.exists():
        print(f"[FATAL] No existe: {BASE}", file=sys.stderr)
        sys.exit(1)

    patrones = ['MOVIMIENTOS DE INVENTARIO', 'AJUSTES ENTRADA', 'AJUSTES ENTRADAS']
    archivos = []
    for d in sorted(BASE.iterdir()):
        if not d.is_dir():
            continue
        for f in sorted(d.iterdir()):
            if f.suffix.upper() != '.TXT':
                continue
            if any(p in f.name.upper() for p in patrones):
                archivos.append((d.name, f))

    print(f"Archivos: {len(archivos)}")
    print()

    todos = []
    for nodo, archivo in archivos:
        movs = parsear_archivo(archivo, nodo)
        print(f"[{nodo}] {archivo.name[:60]}... -> {len(movs):>8,d}")
        todos.extend(movs)

    print()
    print(f"TOTAL: {len(todos):,d} movimientos")
    print()

    csv_path = OUT / "profit_movimientos_parseados.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        if todos:
            writer = csv.DictWriter(f, fieldnames=list(todos[0].keys()))
            writer.writeheader()
            writer.writerows(todos)

    print(f"CSV: {csv_path}")
    print()

    print("=== POR NODO Y TIPO ===")
    for (nodo, tipo), n in sorted(Counter((m['nodo'], m['tipo']) for m in todos).items()):
        print(f"  {nodo:15s} {tipo:6s}: {n:>8,d}")

    print()
    print("=== TIPOS ===")
    for tipo, n in sorted(Counter(m['tipo'] for m in todos).items()):
        print(f"  {tipo:8s}: {n:>8,d}")

    print()
    print("=== CALIDAD ===")
    for campo in ['sku', 'fecha', 'numero_documento']:
        vacios = sum(1 for m in todos if not m[campo])
        print(f"  Sin {campo:18s}: {vacios:>8,d} ({100*vacios/max(len(todos),1):.2f}%)")


if __name__ == '__main__':
    main()

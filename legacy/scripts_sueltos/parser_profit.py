#!/usr/bin/env python3
"""
Parser de archivos Profit Plus Administrativo.
Extrae movimientos de los TXT generados por Profit, con trazabilidad de fila.
Procesa todos los archivos de movimientos y ajustes del corpus.
"""
import os
import re
import csv
import sys
from pathlib import Path
from collections import Counter

BASE = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/corpus/fuentes_profit_diarias"
OUT = Path.home() / "DARTONY_TXT"

# Tipos de movimiento reconocidos
TIPOS = ['NREC', 'NENT', 'FACT', 'FAC', 'AJUE', 'AJUS', 'DCLI', 'DPRO', 'DEV', 'NCRE', 'NDEB']

# Patrón de movimiento: empieza con 2+ espacios, luego tipo, luego número, luego renglón
RE_MOV = re.compile(
    r'^\s{2,}(' + '|'.join(TIPOS) + r')\s+(\d+)\s+(\d+)\s+'
)

# Patrón de header de SKU: empieza con 2+ espacios, código corto, muchos espacios, descripción
RE_SKU = re.compile(r'^\s{2,}([A-Z0-9][A-Z0-9_\-\.]{1,30})\s{8,}([A-Z].*)$')

# Patrón de fecha en la línea
RE_FECHA = re.compile(r'(\d{2}/\d{2}/\d{4})\s+\d{2}:\d{2}\s+[AP]M')

# Patrón de almacén (4 dígitos después de la fecha)
RE_ALMACEN = re.compile(r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}\s+[AP]M\s+(\d{3,4})')

# Excluir líneas de estructura
EXCLUIR = ['Profit Plus', 'INVERSIONES CAUCHOS', 'Página', 'P�gina', 'Rangos:',
           'Sub-Total', 'Tipo/Op', '* Movimiento ya contabilizado', '#']


def es_header_o_pie(linea):
    for patron in EXCLUIR:
        if patron in linea:
            return True
    if not linea.strip():
        return True
    return False


def parsear_archivo(archivo, nodo):
    """Procesa un archivo TXT de Profit y devuelve lista de movimientos."""
    movimientos = []
    sku_actual = None
    desc_actual = None
    n_linea = 0

    with open(archivo, 'r', encoding='latin-1', errors='replace') as f:
        for linea in f:
            n_linea += 1
            linea_limpia = linea.rstrip('\n\r')

            if es_header_o_pie(linea_limpia):
                continue

            # ¿Es línea de movimiento?
            m = RE_MOV.match(linea_limpia)
            if m and sku_actual:
                tipo = m.group(1)
                numero = m.group(2)
                renglon = m.group(3)

                # Extraer fecha
                mf = RE_FECHA.search(linea_limpia)
                fecha = mf.group(1) if mf else ''

                # Extraer almacén
                ma = RE_ALMACEN.search(linea_limpia)
                almacen = ma.group(1) if ma else ''

                # Extraer números al final (entradas, salidas, stock, costo)
                # Buscar todos los números con formato decimal en la línea
                numeros = re.findall(r'-?[\d,]+\.\d{2}', linea_limpia)
                entradas = ''
                salidas = ''
                stock = ''
                costo = ''
                if len(numeros) >= 1:
                    # Último es costo
                    costo = numeros[-1].replace(',', '')
                if len(numeros) >= 2:
                    stock = numeros[-2].replace(',', '')
                if len(numeros) >= 3:
                    # Entradas o salidas (el que tenga signo - es salida)
                    for n in numeros[:-2]:
                        if n.startswith('-'):
                            salidas = n.replace(',', '')
                        elif n != '0.00' and n != '0':
                            entradas = n.replace(',', '')

                movimientos.append({
                    'nodo': nodo,
                    'sku': sku_actual,
                    'descripcion': desc_actual[:50] if desc_actual else '',
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

            # ¿Es header de SKU?
            ms = RE_SKU.match(linea_limpia)
            if ms:
                candidato = ms.group(1)
                # Evitar confundir con tipos de movimiento
                if candidato not in TIPOS:
                    sku_actual = candidato
                    desc_actual = ms.group(2).strip()
                    continue

    return movimientos


def main():
    if not BASE.exists():
        print(f"[FATAL] No existe: {BASE}", file=sys.stderr)
        sys.exit(1)

    # Buscar todos los archivos de movimientos y ajustes
    patrones = ['MOVIMIENTOS DE INVENTARIO', 'AJUSTES ENTRADA', 'AJUSTES ENTRADAS']
    archivos = []
    for d in sorted(BASE.iterdir()):
        if not d.is_dir():
            continue
        nodo = d.name
        for f in d.iterdir():
            if f.suffix.upper() != '.TXT':
                continue
            if any(p in f.name.upper() for p in patrones):
                archivos.append((nodo, f))

    print(f"Archivos a procesar: {len(archivos)}")
    print()

    todos = []
    for nodo, archivo in archivos:
        print(f"[{nodo}] {archivo.name}")
        movs = parsear_archivo(archivo, nodo)
        print(f"  Movimientos extraídos: {len(movs)}")
        todos.extend(movs)

    print()
    print(f"TOTAL: {len(todos)} movimientos extraídos")
    print()

    # Escribir CSV
    csv_path = OUT / "profit_movimientos_parseados.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        if todos:
            writer = csv.DictWriter(f, fieldnames=list(todos[0].keys()))
            writer.writeheader()
            writer.writerows(todos)

    print(f"CSV: {csv_path}")
    print()

    # Verificación por tipo y nodo
    print("=== VERIFICACIÓN POR TIPO Y NODO ===")
    print()
    por_tipo_nodo = Counter((m['nodo'], m['tipo']) for m in todos)
    for (nodo, tipo), n in sorted(por_tipo_nodo.items()):
        print(f"  {nodo:15s} {tipo:6s}: {n:>8,d}")

    print()
    print("=== TIPOS ÚNICOS ENCONTRADOS ===")
    tipos = Counter(m['tipo'] for m in todos)
    for tipo, n in sorted(tipos.items()):
        print(f"  {tipo:8s}: {n:>8,d}")

    # Detectar problemas
    print()
    print("=== CALIDAD DEL PARSEO ===")
    sin_sku = sum(1 for m in todos if not m['sku'])
    sin_fecha = sum(1 for m in todos if not m['fecha'])
    sin_numero = sum(1 for m in todos if not m['numero_documento'])
    print(f"  Sin SKU:     {sin_sku:>8,d} ({100*sin_sku/max(len(todos),1):.2f}%)")
    print(f"  Sin fecha:   {sin_fecha:>8,d} ({100*sin_fecha/max(len(todos),1):.2f}%)")
    print(f"  Sin número:  {sin_numero:>8,d} ({100*sin_numero/max(len(todos),1):.2f}%)")


if __name__ == '__main__':
    main()

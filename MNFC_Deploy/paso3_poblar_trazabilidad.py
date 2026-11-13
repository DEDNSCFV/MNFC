#!/usr/bin/env python3
"""
Paso 3: Pobla numero_documento, renglon, archivo_origen, linea_origen
desde los TXT de Profit, para los 3 nodos con archivo fuente.
Uso: python paso3_poblar_trazabilidad.py "<nodo_db>" "<nodo_tec>"
"""
import sys, re
from pathlib import Path
from collections import defaultdict
import sqlite3

if len(sys.argv) < 3:
    print("Uso: python paso3_poblar_trazabilidad.py '<nodo_db>' '<nodo_tec>'")
    sys.exit(1)

NODO = sys.argv[1]
NODO_TEC = sys.argv[2]
NODO_TXT = NODO_TEC.lower().replace("_", "_")

# Mapeo de nombres de carpetas
MAPA = {
    "04 La Urbina": "04_la_urbina",
    "05 Cúa": "05_cua",
    "06 TERE": "06_tere",
}
CARPETA = MAPA.get(NODO, NODO_TXT)

BASE = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/corpus/fuentes_profit_diarias" / CARPETA
DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"

if not BASE.exists():
    print(f"[FATAL] No existe {BASE}")
    sys.exit(1)

# Buscar el archivo de movimientos
archivo_mov = None
for f in BASE.glob("*.TXT"):
    if "MOVIMIENTOS DE INVENTARIO" in f.name.upper():
        archivo_mov = f
        break

if not archivo_mov:
    print(f"[FATAL] No se encontró MOVIMIENTOS DE INVENTARIO en {BASE}")
    sys.exit(1)

print("=" * 70)
print(f"  PASO 3 — POBLAR TRAZABILIDAD · {NODO}")
print("=" * 70)
print(f"  Archivo: {archivo_mov.name}")
print()

# Regex del parser
RE_MOV = re.compile(
    r'^\s{2,}(?P<tipo>FACT|NREC|NENT|AJUE|AJUS|DCLI|DPRO)\s+'
    r'(?P<numero>\d+)\s+(?P<renglon>\d+)\s+(?P<usuario>\S+)\s+(?P<cliente>\S+)\s+'
    r'(?P<fecha>\d{2}/\d{2}/\d{4})\s+(?P<hora>\d{2}:\d{2}\s+[AP]M)\s+'
    r'(?P<almacen>\d{3,4})\s+(?P<resto>.+)$'
)
RE_SKU = re.compile(r'^([A-Z0-9][A-Z0-9_\-\.]{2,30})\s{8,}(.+)$')

# Parsear el TXT
print("[1/3] Parseando el TXT...")
movimientos_parser = []
sku_actual = None
desc_actual = None
n_linea = 0

with open(archivo_mov, 'r', encoding='latin-1', errors='replace') as f:
    for linea in f:
        n_linea += 1
        linea = linea.rstrip('\n\r')

        # ¿Es SKU?
        ms = RE_SKU.match(linea)
        if ms:
            candidato = ms.group(1)
            if candidato not in ('FACT', 'NREC', 'NENT', 'AJUE', 'AJUS', 'DCLI', 'DPRO'):
                sku_actual = candidato
                desc_actual = ms.group(2).strip()
                continue

        # ¿Es movimiento?
        m = RE_MOV.match(linea)
        if m and sku_actual:
            d = m.groupdict()
            nums = re.findall(r'-?[\d,]+\.\d{2}', d['resto'])
            stock = None
            costo = None
            cantidad = None
            if len(nums) >= 1:
                try: costo = float(nums[-1].replace(',', ''))
                except: pass
            if len(nums) >= 2:
                try: stock = float(nums[-2].replace(',', ''))
                except: pass
            if len(nums) >= 3:
                for n in nums[:-2]:
                    if n.startswith('-') or n not in ('0.00', '0'):
                        try:
                            cantidad = float(n.replace(',', ''))
                        except: pass
                        break

            movimientos_parser.append({
                'sku': sku_actual,
                'tipo': d['tipo'],
                'numero_documento': d['numero'],
                'renglon': int(d['renglon']),
                'fecha': d['fecha'],
                'cantidad': cantidad,
                'costo_unitario': costo,
                'stock_actual': stock,
                'archivo_origen': archivo_mov.name,
                'linea_origen': n_linea,
            })

print(f"  Movimientos extraídos del parser: {len(movimientos_parser):,}")
print()

# Conectar a la BD
conn = sqlite3.connect(DB)

# Leer los movimientos de la BD para este nodo (sin los campos nuevos)
print("[2/3] Leyendo movimientos de la BD...")
movs_bd = conn.execute("""
    SELECT id, sku, tipo, fecha, cantidad, costo_unitario, stock_actual
    FROM movimientos_historico
    WHERE nodo = ?
    ORDER BY id
""", (NODO,)).fetchall()
print(f"  Movimientos en la BD: {len(movs_bd):,}")
print()

# Índice por clave (sku, tipo, fecha, cantidad, costo, stock) para hacer match
# Nota: puede haber múltiples movimientos con la misma clave
parser_por_clave = defaultdict(list)
for mp in movimientos_parser:
    clave = (mp['sku'], mp['tipo'], mp['fecha'], mp['cantidad'], mp['costo_unitario'], mp['stock_actual'])
    parser_por_clave[clave].append(mp)

# Contadores
match_ok = 0
match_fail = 0
actualizados = 0

print("[3/3] Actualizando BD con los campos de trazabilidad...")

# Para cada movimiento de la BD, buscar su match en el parser
# Usamos el orden: el primer id con la clave X -> primer parser con la clave X
for idx, (id_bd, sku, tipo, fecha, cantidad, costo, stock) in enumerate(movs_bd):
    clave = (sku, tipo, fecha, cantidad, costo, stock)
    candidatos = parser_por_clave.get(clave, [])

    if not candidatos:
        match_fail += 1
        continue

    # Tomar el primero y removerlo (para no reusarlo)
    mp = candidatos.pop(0)
    match_ok += 1

    conn.execute("""
        UPDATE movimientos_historico
        SET numero_documento = ?,
            renglon = ?,
            archivo_origen = ?,
            linea_origen = ?
        WHERE id = ?
    """, (mp['numero_documento'], mp['renglon'], mp['archivo_origen'], mp['linea_origen'], id_bd))
    actualizados += 1

    if actualizados % 10000 == 0:
        print(f"  ... {actualizados:,} actualizados")

conn.commit()

print()
print(f"  Movimientos con match:    {match_ok:,}")
print(f"  Movimientos sin match:    {match_fail:,}")
print(f"  Actualizados en la BD:    {actualizados:,}")
print()

# Verificar
r = conn.execute("""
    SELECT COUNT(*) FROM movimientos_historico
    WHERE nodo = ? AND numero_documento IS NOT NULL
""", (NODO,)).fetchone()[0]
print(f"  Movimientos con numero_documento: {r:,}")

conn.close()
print()
print("Paso 3 completado.")

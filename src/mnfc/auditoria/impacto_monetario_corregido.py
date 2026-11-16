# impacto_monetario_corregido.py - SOLO precio de venta
import openpyxl
import os
import sqlite3
from collections import defaultdict

LISTAS = [
    (r'C:\Users\Admin\Desktop\GRAN MAYOR 07.11.26.xlsx', 19),
    (r'C:\Users\Admin\Desktop\LISTA DE BICICLETA 07.11.26.xlsx', 11),
    (r'C:\Users\Admin\Desktop\MULTIMARCA 07.11.26.xlsx', 18),
]
DB = r'C:\Users\Admin\Desktop\dartony_auditoria_v2.db'

# Fuente 1: listas Excel (precio de venta OFICIAL)
precios_lista = {}
for ruta, header_row in LISTAS:
    if not os.path.exists(ruta):
        continue
    wb = openpyxl.load_workbook(ruta, data_only=True, read_only=True)
    ws = wb[wb.sheetnames[0]]
    for i, row in enumerate(ws.iter_rows(values_only=True), 1):
        if i <= header_row or not row or len(row) < 4:
            continue
        codigo = str(row[1]).strip() if row[1] else ''
        precio_raw = row[3]
        if not codigo:
            continue
        try:
            precio = float(str(precio_raw).replace(',', '.'))
        except (ValueError, TypeError):
            continue
        if codigo not in precios_lista:
            precios_lista[codigo] = precio
    wb.close()
print(f"Listas Excel: {len(precios_lista)} SKUs con precio de venta")

# Fuente 2: precio_sku BD (SOLO si no esta en lista, y SOLO precio > 0)
con = sqlite3.connect(DB)
cur = con.cursor()
precios_bd = {}
cur.execute("SELECT sku, precio FROM precio_sku WHERE precio IS NOT NULL AND precio > 0")
for sku, precio in cur.fetchall():
    sku = str(sku).strip()
    if sku and sku not in precios_bd:
        precios_bd[sku] = float(precio)
print(f"precio_sku BD: {len(precios_bd)} SKUs con precio de venta")

# Combinar: lista tiene prioridad, BD como fallback
precios = {}
fuente_precio = {}
for sku in precios_lista:
    precios[sku] = precios_lista[sku]
    fuente_precio[sku] = 'LISTA'
for sku in precios_bd:
    if sku not in precios:
        precios[sku] = precios_bd[sku]
        fuente_precio[sku] = 'BD:precio_sku'

# Hallazgos (excluyendo 2333/2347 que son cruce estructural)
HALLAZGOS = [
    ('R-044',  'CHARALLAVE',  -4),
    ('R-108',  'CHARALLAVE',  -3),
    ('MO-266', 'CHARALLAVE',  -1),
    ('19939',  'CHARALLAVE',  -1),
    ('15616',  'CHARALLAVE',  -1),
    ('MZ-9',   'CHARALLAVE',  +2),
    ('R-108',  'PALO_VERDE', -16),
    ('R-100',  'PALO_VERDE',  +4),
    ('MO-465', 'PALO_VERDE',  +4),
    ('R-157',  'PALO_VERDE',  +5),
    ('LJ597',  'PALO_VERDE',  -1),
    ('MO-308', 'TERE',        -1),
    ('MO-307', 'TERE',        +1),
    ('6238',   'TERE',        -4),
    ('MO-440', 'CUA',         +1),
    ('2333',   'CUA',         +1),
    ('17373',  'CUA',         +1),
    ('MO-019', 'URBINA',      +1),
    ('ROS37536','URBINA',     +1),
    ('YU731003C','URBINA',    +1),
    ('10002',  'LA_RAIZA',    -1),
    ('MO-009', 'PALO_VERDE',  -1),
]

print("\n" + "="*110)
print("IMPACTO MONETARIO CORREGIDO (SOLO PRECIO DE VENTA)")
print("="*110)
print(f"{'SKU':<12} | {'SUCURSAL':<14} | {'DIF':>5} | {'PRECIO VENTA':>12} | {'IMPACTO':>11} | {'MATERIAL':<8} | FUENTE")
print("-"*110)

total = 0.0
por_suc = defaultdict(float)
sin_precio = []

for sku, detal, dif in HALLAZGOS:
    if sku in precios:
        precio = precios[sku]
        imp = dif * precio
        mat = "SI" if abs(imp) >= 10 else "no"
        print(f"{sku:<12} | {detal:<14} | {dif:>+5} | ${precio:>11.2f} | ${imp:>+10.2f} | {mat:<8} | {fuente_precio[sku]}")
        total += imp
        por_suc[detal] += imp
    else:
        print(f"{sku:<12} | {detal:<14} | {dif:>+5} | {'SIN PRECIO':>12} | {'?':>11} | {'?':<8} | ?")
        sin_precio.append((sku, detal, dif))

print("-"*110)
print(f"{'TOTAL':<12} | {'':<14} | {'':>5} | {'':>12} | ${total:>+10.2f} |")

print("\n" + "="*110)
print("RESUMEN POR SUCURSAL")
print("="*110)
for suc in sorted(por_suc.keys()):
    imp = por_suc[suc]
    mat = "MATERIAL" if abs(imp) >= 10 else "inmaterial"
    print(f"  {suc:<20}: ${imp:>+10.2f}  ({mat})")

if sin_precio:
    print("\n" + "="*110)
    print(f"SKUs SIN PRECIO DE VENTA ({len(sin_precio)})")
    print("="*110)
    for sku, detal, dif in sin_precio:
        print(f"  {sku:<15} | {detal:<14} | dif={dif:+d}")

# Top 5 materiales
print("\n" + "="*110)
print("TOP 5 IMPACTOS ABSOLUTOS (solo precio de venta)")
print("="*110)
impactos = []
for sku, detal, dif in HALLAZGOS:
    if sku in precios:
        imp = dif * precios[sku]
        impactos.append((abs(imp), sku, detal, dif, precios[sku], imp, fuente_precio[sku]))
impactos.sort(reverse=True)
for _, sku, detal, dif, precio, imp, f in impactos[:5]:
    print(f"  {sku:<12} | {detal:<14} | dif={dif:+d} × ${precio:.2f} = ${imp:+.2f} ({f})")

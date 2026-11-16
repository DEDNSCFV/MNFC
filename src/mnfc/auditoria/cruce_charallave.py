# cruce_charallave.py
import os, re
from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal, InvalidOperation
import openpyxl

TZ = ZoneInfo("America/Caracas")
ESCRITORIO = r'C:\Users\Admin\Desktop'
RUTA_REPORTES = r'C:\Users\Admin\Desktop\ARBOL_SCFV\07_REPORTES'
ALMACEN = "0801"

print("="*95)
print(" CRUCE CHARALLAVE - ALMACEN 0801")
print(f" Fecha: {datetime.now(TZ).strftime('%d/%m/%Y %H:%M')}")
print("="*95)

# 1. Localizar archivos
conteo_path = None
am2_path = None
for f in os.listdir(ESCRITORIO):
    fu = f.upper()
    if 'CONTEO' in fu and 'CHARALLAVE' in fu and f.lower().endswith('.xlsx'):
        conteo_path = os.path.join(ESCRITORIO, f)
    if 'CHARALLAVE' in fu and 'X ALMAC' in fu and 'AM2' in fu and f.upper().endswith('.TXT'):
        am2_path = os.path.join(ESCRITORIO, f)

print(f"\nConteo: {os.path.basename(conteo_path) if conteo_path else 'NO ENCONTRADO'}")
print(f"AM2:    {os.path.basename(am2_path) if am2_path else 'NO ENCONTRADO'}")

if not conteo_path or not am2_path:
    print("Falta archivo. Abortando.")
    exit(1)

# 2. Leer conteo
print(f"\n{'='*95}")
print(" 1. LEYENDO CONTEO")
print("="*95)

wb = openpyxl.load_workbook(conteo_path, data_only=True)
ws = wb.active
print(f"Hoja: '{ws.title}' | filas: {ws.max_row} | cols: {ws.max_column}")

header_row = None
header_vals = None
for i, row in enumerate(ws.iter_rows(values_only=True), 1):
    if not row:
        continue
    row_str = [str(c).upper().strip() if c else '' for c in row]
    if any('DIGO' in c or c == 'COD' or 'SKU' in c for c in row_str[:6]):
        header_row = i
        header_vals = row
        print(f"\nHeader en fila {i}:")
        for j, c in enumerate(row):
            if c:
                print(f"   col {j}: '{c}'")
        break

if header_row is None:
    print("No se encontro header. Primeras 15 filas:")
    for i, row in enumerate(ws.iter_rows(max_row=15, values_only=True), 1):
        print(f"   [{i:>2}] {row}")
    wb.close()
    exit(1)

col_codigo = None
col_cantidad = None
for j, c in enumerate([str(x).upper().strip() if x else '' for x in header_vals]):
    if ('DIGO' in c or c == 'COD' or 'SKU' in c) and col_codigo is None:
        col_codigo = j
    if ('CANT' in c or 'FISICO' in c or 'CONTEO' in c or 'UNIDAD' in c) and col_cantidad is None:
        col_cantidad = j

print(f"\nColumnas: codigo=col[{col_codigo}]  cantidad=col[{col_cantidad}]")

if col_codigo is None:
    print("Sin columna de codigo. Abortando.")
    wb.close()
    exit(1)

if col_cantidad is None:
    print("Sin columna de cantidad. Primeras 10 filas de datos:")
    for i, row in enumerate(ws.iter_rows(min_row=header_row+1, max_row=header_row+10, values_only=True), header_row+1):
        print(f"   [{i:>3}] {row}")
    wb.close()
    exit(1)

skus_conteo = {}
for row in ws.iter_rows(min_row=header_row+1, values_only=True):
    if not row or col_codigo >= len(row):
        continue
    codigo = str(row[col_codigo]).strip() if row[col_codigo] else ''
    if not codigo:
        continue
    if 'FIRMA' in codigo.upper():
        break
    if 'TOTAL' in codigo.upper():
        continue
    if col_cantidad >= len(row) or row[col_cantidad] is None:
        continue
    try:
        val = str(row[col_cantidad]).replace(',', '.')
        cantidad = Decimal(val)
    except (InvalidOperation, ValueError):
        continue
    skus_conteo[codigo] = cantidad

print(f"\nSKUs en conteo: {len(skus_conteo)}")
for sku, cant in list(skus_conteo.items())[:5]:
    print(f"   '{sku}': {cant}")

wb.close()

# 3. Leer AM2
print(f"\n{'='*95}")
print(f" 2. LEYENDO AM2 (almacen {ALMACEN})")
print("="*95)

stock_sistema = {}
lineas_total = 0
lineas_match = 0
patron = re.compile(r'\b' + ALMACEN + r'\s+([\d.,]+)\s+UNIDAD')

with open(am2_path, encoding='latin-1') as fh:
    for linea in fh:
        lineas_total += 1
        if not linea.strip():
            continue
        codigo = linea[:30].strip()
        if not codigo:
            continue
        m = patron.search(linea)
        if m:
            lineas_match += 1
            num = m.group(1)
            if ',' in num:
                num = num.replace('.', '').replace(',', '.')
            try:
                stock_sistema[codigo] = stock_sistema.get(codigo, Decimal('0')) + Decimal(num)
            except InvalidOperation:
                pass

print(f"Lineas totales: {lineas_total:,}")
print(f"Lineas con '{ALMACEN}' + num + UNIDAD: {lineas_match:,}")
print(f"SKUs con stock en {ALMACEN}: {len(stock_sistema)}")
for sku, cant in list(stock_sistema.items())[:5]:
    print(f"   '{sku}': {cant}")

# 4. Cruce
print(f"\n{'='*95}")
print(" 3. CRUCE CONTEO vs AM2 (0801)")
print("="*95)

resultados = []
for sku, fisico in skus_conteo.items():
    sistema = stock_sistema.get(sku, Decimal('0'))
    resultados.append({'sku': sku, 'fisico': fisico, 'sistema': sistema, 'dif': fisico - sistema})

resultados.sort(key=lambda r: (r['dif'] == 0, -abs(r['dif'])))

print(f"\n{'SKU':<22} | {'FISICO':>10} | {'SISTEMA':>10} | {'DIF':>8} | ESTADO")
print("-"*80)
con_dif = 0
for r in resultados:
    if r['dif'] == 0:
        estado = "OK"
    elif r['dif'] < 0:
        estado = "FALTANTE"
        con_dif += 1
    else:
        estado = "SOBRANTE"
        con_dif += 1
    print(f"{r['sku']:<22} | {r['fisico']:>10} | {r['sistema']:>10} | {r['dif']:>+8} | {estado}")

print("-"*80)
print(f"SKUs en conteo: {len(resultados)}  |  Con diferencia: {con_dif}  |  OK: {len(resultados)-con_dif}")

no_en_conteo = [s for s in stock_sistema if s not in skus_conteo]
print(f"\nSKUs con stock en AM2 (0801) pero NO en conteo: {len(no_en_conteo)}")

# 5. Guardar Acta
ahora = datetime.now(TZ)
os.makedirs(RUTA_REPORTES, exist_ok=True)

acta_path = os.path.join(RUTA_REPORTES, f"Acta_Cruce_Charallave_{ahora.strftime('%Y%m%d_%H%M')}.txt")
with open(acta_path, 'w', encoding='utf-8') as f:
    f.write("="*85 + "\n")
    f.write("       CRUCE CHARALLAVE - ALMACEN 0801\n")
    f.write(f"       Fecha: {ahora.strftime('%d/%m/%Y %H:%M')}\n")
    f.write("       Auditor: CPC N 183594 - Diaz N. Domingo E.\n")
    f.write("="*85 + "\n\n")
    f.write(f"SKUs en conteo: {len(resultados)}\n")
    f.write(f"Con diferencia: {con_dif}  |  OK: {len(resultados)-con_dif}\n\n")
    f.write(f"{'SKU':<22} | {'FISICO':>10} | {'SISTEMA':>10} | {'DIF':>8} | ESTADO\n")
    f.write("-"*80 + "\n")
    for r in resultados:
        estado = "OK" if r['dif'] == 0 else ("FALTANTE" if r['dif'] < 0 else "SOBRANTE")
        f.write(f"{r['sku']:<22} | {r['fisico']:>10} | {r['sistema']:>10} | {r['dif']:>+8} | {estado}\n")
    f.write("\n" + "="*85 + "\n\nFIRMA:\n\n")
    f.write("_______________________________________\n")
    f.write("Diaz N. Domingo E.\nC.P.C. N 183594\n")

print(f"\nActa guardada: {acta_path}")
print("\n" + "="*95)
#!/usr/bin/env python3
"""
Genera el libro pedagógico de UN NODO.
Uso: python gen_libro_nodo.py "04 La Urbina"
"""
import json, hashlib, sys
from datetime import datetime, timezone
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

if len(sys.argv) < 2:
    print("Uso: python gen_libro_nodo.py '<nombre nodo>'")
    sys.exit(1)

NODO = sys.argv[1]
NODO_SLUG = NODO.replace(" ", "_")
OUT = Path.home() / "DARTONY_TXT"
DATOS = OUT / f"eval_{NODO_SLUG}.json"

if not DATOS.exists():
    print(f"[FATAL] No existe: {DATOS}")
    print("Ejecutar primero: python eval_nodo.py '{NODO}'")
    sys.exit(1)

with open(DATOS, encoding='utf-8') as f:
    reglas = json.load(f)

FECHA = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

TITULO = Font(bold=True, size=14, color="1F4E79")
SUBT = Font(bold=True, size=11, color="333333")
BLOQUE = Font(bold=True, size=11, color="1F4E79")
TEXTO = Font(size=10)
CODE = Font(name='Courier New', size=9, color='666666')
HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=10)
OK_FILL = PatternFill(start_color="C6EFCE", fill_type="solid")
VIO_FILL = PatternFill(start_color="FFC7CE", fill_type="solid")
ADV_FILL = PatternFill(start_color="FFEB9C", fill_type="solid")
SIN_FILL = PatternFill(start_color="D9D9D9", fill_type="solid")
BORDER = Border(left=Side(style='thin'), right=Side(style='thin'),
                top=Side(style='thin'), bottom=Side(style='thin'))

def fill_estado(estado):
    return {"OK": OK_FILL, "VIOLACIÓN": VIO_FILL,
            "ADVERTENCIA": ADV_FILL, "SIN_DATOS": SIN_FILL}.get(estado, SIN_FILL)

wb = Workbook()

# Hoja 0 — Guía
ws = wb.active
ws.title = "0_Guia"
ws['A1'] = f"CONTROL INTERNO — NODO {NODO.upper()}"
ws['A1'].font = TITULO
ws['A2'] = "Guía para leer este libro"
ws['A2'].font = SUBT
ws.append([])
ws.append(["Este libro contiene las 17 reglas de control interno,"])
ws.append(["evaluadas SOLO sobre este nodo."])
ws.append([])
ws.append(["Para cada regla, el libro explica:"])
ws.append(["  1. ¿Qué mide?"])
ws.append(["  2. ¿Por qué importa?"])
ws.append(["  3. ¿Cómo se calcula?"])
ws.append(["  4. ¿Qué dice el dato?"])
ws.append(["  5. ¿Qué significa?"])
ws.append(["  6. ¿Cómo se compara?"])
ws.append(["  7. ¿Qué hacer?"])
ws.append([])
ws.append(["Nodo:", NODO])
ws.append(["Fecha:", FECHA])
ws.append(["Analista:", "Domingo E. Díaz N. | C.P.C. N.º 183594"])
ws.append(["Reglas:", len(reglas)])

# Hoja 1 — Resumen
ws = wb.create_sheet("1_Resumen")
ws['A1'] = f"RESUMEN DE LAS 17 REGLAS — {NODO.upper()}"
ws['A1'].font = TITULO
ws.append([])
headers = ["#", "Regla", "Categoría", "Estado", "Interpretación"]
for i, h in enumerate(headers, 1):
    c = ws.cell(row=3, column=i, value=h)
    c.fill = HEADER_FILL
    c.font = HEADER_FONT
    c.border = BORDER

for i, r in enumerate(reglas, 4):
    ws.cell(row=i, column=1, value=r['id']).border = BORDER
    ws.cell(row=i, column=2, value=r['nombre']).border = BORDER
    ws.cell(row=i, column=3, value=r['categoria']).border = BORDER
    c = ws.cell(row=i, column=4, value=r['estado'])
    c.fill = fill_estado(r['estado'])
    c.border = BORDER
    ws.cell(row=i, column=5, value=r['interpretacion'][:100]).border = BORDER
    ws.row_dimensions[i].height = 30

for col, w in [('A', 5), ('B', 35), ('C', 12), ('D', 14), ('E', 80)]:
    ws.column_dimensions[col].width = w

# Hojas 2..18 — Una por regla
for r in reglas:
    nombre = f"{r['id']:02d}_{r['nombre'][:24].replace(' ', '_').replace('>', '').replace('$', '')}"
    ws = wb.create_sheet(nombre[:31])
    ws['A1'] = f"REGLA #{r['id']} — {r['nombre'].upper()}"
    ws['A1'].font = TITULO
    ws['A2'] = f"Categoría: {r['categoria']} | Nodo: {NODO}"
    ws['A2'].font = SUBT

    ws['A4'] = "ESTADO:"
    ws['A4'].font = SUBT
    c = ws['B4']
    c.value = r['estado']
    c.fill = fill_estado(r['estado'])
    c.font = Font(bold=True, size=12)
    c.border = BORDER

    fila = 6
    bloques = [
        ("1. ¿QUÉ MIDE?", r['que_mide'], TEXTO),
        ("2. ¿POR QUÉ IMPORTA?", r['por_que_importa'], TEXTO),
        ("3. ¿CÓMO SE CALCULA?", r['formula'], TEXTO),
        ("   Consulta SQL:", r['consulta'], CODE),
        ("4. ¿QUÉ DICE EL DATO?", r['dato'], Font(bold=True, size=11)),
        ("5. ¿QUÉ SIGNIFICA?", r['interpretacion'], TEXTO),
        ("6. ¿CÓMO SE COMPARA?", f"Benchmark: {r['benchmark']}  |  Actual: {r['comparacion']}", TEXTO),
        ("7. ¿QUÉ HACER?", r['recomendacion'], TEXTO),
    ]
    for titulo, contenido, fuente in bloques:
        ws.cell(row=fila, column=1, value=titulo).font = BLOQUE
        fila += 1
        c = ws.cell(row=fila, column=1, value=contenido)
        c.font = fuente
        c.alignment = Alignment(wrap_text=True, vertical='top')
        fila += 2
    ws.column_dimensions['A'].width = 110

# Hoja Inmutabilidad
ws = wb.create_sheet("Inmutabilidad")
ws['A1'] = "INMUTABILIDAD"
ws['A1'].font = TITULO
ws.append([])
ws.append(["Versión:", "V001"])
ws.append(["Nodo:", NODO])
ws.append(["Fecha:", FECHA])
ws.append(["Analista:", "Domingo E. Díaz N. | C.P.C. N.º 183594"])
ws.append([])
ws.append(["Hoja", "Filas", "SHA256"])

for nombre in wb.sheetnames:
    if nombre == "Inmutabilidad":
        continue
    ws2 = wb[nombre]
    contenido = ""
    for row in ws2.iter_rows(values_only=True):
        contenido += "|".join(str(v) for v in row if v is not None) + "\n"
    h = hashlib.sha256(contenido.encode('utf-8')).hexdigest()[:16] if contenido else "vacia"
    ws.append([nombre, ws2.max_row, h])

archivo = OUT / f"DARTONY_{NODO_SLUG}_PEDAGOGICO_{FECHA}.xlsx"
wb.save(archivo)

with open(archivo, 'rb') as f:
    hash_libro = hashlib.sha256(f.read()).hexdigest()

print(f"Libro del nodo: {archivo.name}")
print(f"Nodo: {NODO}")
print(f"Hojas: {len(wb.sheetnames)}")
print(f"SHA256: {hash_libro}")

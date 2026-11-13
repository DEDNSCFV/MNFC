#!/usr/bin/env python3
"""
Genera el libro pedagógico de las 17 reglas.
Cada regla tiene su hoja con 6 bloques:
- Qué mide
- Cómo se calcula
- Qué dice el dato
- Qué significa
- Cómo se compara
- Qué hacer
"""
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    print("[FATAL] pip install openpyxl")
    raise SystemExit(1)

OUT = Path.home() / "DARTONY_TXT"
DATOS = OUT / "17_reglas_pedagogico.json"
FECHA = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

with open(DATOS, encoding='utf-8') as f:
    reglas = json.load(f)

# Estilos
HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
TITULO_FONT = Font(bold=True, size=14, color="1F4E79")
SUBTITULO_FONT = Font(bold=True, size=12, color="333333")
BLOQUE_FONT = Font(bold=True, size=11, color="1F4E79")
TEXTO_FONT = Font(size=10)
OK_FILL = PatternFill(start_color="C6EFCE", fill_type="solid")
VIO_FILL = PatternFill(start_color="FFC7CE", fill_type="solid")
ADV_FILL = PatternFill(start_color="FFEB9C", fill_type="solid")
BORDER = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)

wb = Workbook()

# ============================================================
# HOJA 0 — GUÍA
# ============================================================
ws = wb.active
ws.title = "0_Guia"
ws['A1'] = "CONTROL INTERNO DE INVENTARIO"
ws['A1'].font = TITULO_FONT
ws['A2'] = "Guía para leer este libro"
ws['A2'].font = SUBTITULO_FONT
ws.append([])
ws.append(["Este libro no es un informe de hallazgos."])
ws.append(["Es el MÉTODO completo, mostrado paso a paso."])
ws.append([])
ws.append(["Para cada una de las 17 reglas de control, el libro explica:"])
ws.append(["1. ¿Qué mide?"])
ws.append(["2. ¿Por qué importa?"])
ws.append(["3. ¿Cómo se calcula?"])
ws.append(["4. ¿Qué dice el dato?"])
ws.append(["5. ¿Qué significa?"])
ws.append(["6. ¿Cómo se compara con el estándar?"])
ws.append(["7. ¿Qué hacer?"])
ws.append([])
ws.append(["El mandante puede leer cada hoja y entender el razonamiento completo."])
ws.append(["No hay cajas negras. Cada número tiene su explicación."])
ws.append([])
ws.append(["Fecha de emisión:", FECHA])
ws.append(["Analista:", "Domingo E. Díaz N. | C.P.C. N.º 183594"])
ws.append(["Reglas evaluadas:", len(reglas)])

# ============================================================
# HOJA 1 — RESUMEN DE LAS 17 REGLAS
# ============================================================
ws = wb.create_sheet("1_Resumen")
ws['A1'] = "RESUMEN DE LAS 17 REGLAS"
ws['A1'].font = TITULO_FONT
ws.append([])

headers = ["#", "Regla", "Categoría", "Estado", "Interpretación breve"]
for i, h in enumerate(headers, 1):
    c = ws.cell(row=3, column=i, value=h)
    c.fill = HEADER_FILL
    c.font = HEADER_FONT
    c.border = BORDER

fila = 4
for r in reglas:
    ws.cell(row=fila, column=1, value=r['id']).border = BORDER
    ws.cell(row=fila, column=2, value=r['nombre']).border = BORDER
    ws.cell(row=fila, column=3, value=r['categoria']).border = BORDER
    c = ws.cell(row=fila, column=4, value=r['estado'])
    c.border = BORDER
    if r['estado'] == "OK": c.fill = OK_FILL
    elif r['estado'] == "VIOLACIÓN": c.fill = VIO_FILL
    else: c.fill = ADV_FILL
    ws.cell(row=fila, column=5, value=r['interpretacion'][:100]).border = BORDER
    fila += 1

# ============================================================
# HOJAS 2 a 18 — UNA POR REGLA
# ============================================================
for idx, r in enumerate(reglas, 2):
    nombre_hoja = f"{r['id']:02d}_{r['nombre'][:25].replace(' ', '_')}"
    ws = wb.create_sheet(nombre_hoja[:31])

    # Título
    ws['A1'] = f"REGLA #{r['id']} — {r['nombre'].upper()}"
    ws['A1'].font = TITULO_FONT
    ws['A2'] = f"Categoría: {r['categoria']}"
    ws['A2'].font = SUBTITULO_FONT
    ws.append([])

    # Estado
    ws.append(["ESTADO:", r['estado']])
    estado_cell = ws.cell(row=4, column=2)
    if r['estado'] == "OK": estado_cell.fill = OK_FILL
    elif r['estado'] == "VIOLACIÓN": estado_cell.fill = VIO_FILL
    else: estado_cell.fill = ADV_FILL
    ws.append([])

    # Bloque 1: Qué mide
    ws.append(["1. ¿QUÉ MIDE?"])
    ws.cell(row=ws.max_row, column=1).font = BLOQUE_FONT
    ws.append([r['que_mide']])
    ws.append([])

    # Bloque 2: Por qué importa
    ws.append(["2. ¿POR QUÉ IMPORTA?"])
    ws.cell(row=ws.max_row, column=1).font = BLOQUE_FONT
    ws.append([r['por_que_importa']])
    ws.append([])

    # Bloque 3: Cómo se calcula
    ws.append(["3. ¿CÓMO SE CALCULA?"])
    ws.cell(row=ws.max_row, column=1).font = BLOQUE_FONT
    ws.append([r['formula']])
    ws.append([])
    ws.append(["Consulta ejecutable:"])
    ws.cell(row=ws.max_row, column=1).font = Font(italic=True, size=9)
    ws.append([r['consulta']])
    ws.cell(row=ws.max_row, column=1).font = Font(name='Courier New', size=9, color='666666')
    ws.append([])

    # Bloque 4: Qué dice el dato
    ws.append(["4. ¿QUÉ DICE EL DATO?"])
    ws.cell(row=ws.max_row, column=1).font = BLOQUE_FONT
    ws.append([r['dato']])
    ws.cell(row=ws.max_row, column=1).font = Font(bold=True, size=11)
    ws.append([])

    # Bloque 5: Qué significa
    ws.append(["5. ¿QUÉ SIGNIFICA?"])
    ws.cell(row=ws.max_row, column=1).font = BLOQUE_FONT
    ws.append([r['interpretacion']])
    ws.append([])

    # Bloque 6: Cómo se compara
    ws.append(["6. ¿CÓMO SE COMPARA?"])
    ws.cell(row=ws.max_row, column=1).font = BLOQUE_FONT
    ws.append(["Benchmark:", r['benchmark']])
    ws.append(["Actual:", r['comparacion']])
    ws.append([])

    # Bloque 7: Qué hacer
    ws.append(["7. ¿QUÉ HACER?"])
    ws.cell(row=ws.max_row, column=1).font = BLOQUE_FONT
    ws.append([r['recomendacion']])
    ws.append([])

    # Ajustar ancho de columna
    ws.column_dimensions['A'].width = 100
    ws.column_dimensions['B'].width = 40

# ============================================================
# HOJA FINAL — INMUTABILIDAD
# ============================================================
ws = wb.create_sheet("Inmutabilidad")
ws['A1'] = "INMUTABILIDAD"
ws['A1'].font = TITULO_FONT
ws.append([])
ws.append(["Versión:", "V001"])
ws.append(["Fecha:", FECHA])
ws.append(["Analista:", "Domingo E. Díaz N. | C.P.C. N.º 183594"])
ws.append([])

# Hash por hoja
for nombre in wb.sheetnames:
    if nombre == "Inmutabilidad":
        continue
    ws2 = wb[nombre]
    contenido = ""
    for row in ws2.iter_rows(values_only=True):
        contenido += "|".join(str(v) for v in row if v is not None) + "\n"
    h = hashlib.sha256(contenido.encode('utf-8')).hexdigest()[:16] if contenido else "vacia"
    ws.append([nombre, ws2.max_row, h])

# Guardar
archivo = OUT / f"DARTONY_PEDAGOGICO_17REGLAS_{FECHA}.xlsx"
wb.save(archivo)

with open(archivo, 'rb') as f:
    hash_libro = hashlib.sha256(f.read()).hexdigest()

print(f"Libro generado: {archivo.name}")
print(f"Tamaño: {archivo.stat().st_size:,} bytes")
print(f"Hojas: {len(wb.sheetnames)}")
print(f"SHA256: {hash_libro}")
print()
print("El libro tiene:")
print(f"  - 1 hoja de guía")
print(f"  - 1 hoja de resumen de las 17 reglas")
print(f"  - {len(reglas)} hojas, una por regla, con 7 bloques explicativos")
print(f"  - 1 hoja de inmutabilidad")

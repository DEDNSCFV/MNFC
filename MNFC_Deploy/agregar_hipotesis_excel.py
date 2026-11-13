#!/usr/bin/env python3
"""
Agrega hoja 21_Hipotesis al libro mensual con las 3 hipótesis falsables.
"""
import json
import hashlib
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

HOME = Path.home()
OUT = HOME / "DARTONY_TXT"

# Encontrar el libro mensual más reciente
libros = sorted(OUT.glob("DARTONY_MENSUAL_*.xlsx"))
if not libros:
    print("[FATAL] No hay libro mensual.")
    raise SystemExit(1)
LIBRO = libros[-1]

# Encontrar el JSON de hipótesis más reciente
hip_files = sorted(OUT.glob("hipotesis_datos_faltantes_*.json"))
if not hip_files:
    print("[FATAL] No hay archivo de hipótesis.")
    raise SystemExit(1)
HIP_FILE = hip_files[-1]

print(f"Libro: {LIBRO.name}")
print(f"Hipótesis: {HIP_FILE.name}")

with open(HIP_FILE, encoding='utf-8') as f:
    hip = json.load(f)

# Estilos
HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
TITULO_FONT = Font(bold=True, size=14, color="1F4E79")
SUB_FONT = Font(italic=True, size=10, color="555555")
HIP_FILL = PatternFill(start_color="DDEBF7", fill_type="solid")
BORDER = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)

wb = load_workbook(LIBRO)

# Si ya existe la hoja, borrarla
if "21_Hipotesis" in wb.sheetnames:
    del wb["21_Hipotesis"]

ws = wb.create_sheet("21_Hipotesis")

# Encabezado
ws['A1'] = "HIPÓTESIS SOBRE DATOS FALTANTES"
ws['A1'].font = TITULO_FONT
ws['A2'] = "Predicciones falsables registradas ANTES de cargar los datos. Si fallan, se refutan."
ws['A2'].font = SUB_FONT
ws.append([])

# Información general
ws.append(["Fecha de registro:", hip['fecha_registro']])
ws.append(["Autor:", hip['autor']])
ws.append(["SHA256 del registro:", hashlib.sha256(open(HIP_FILE, 'rb').read()).hexdigest()])
ws.append([])

# Principio
ws.append(["PRINCIPIO EPISTEMOLÓGICO"])
c = ws.cell(row=ws.max_row, column=1)
c.font = Font(bold=True, size=12, color="1F4E79")
ws.append([hip['principio_epistemologico']])
ws.append([])

# Estado actual
ws.append(["ESTADO ACTUAL DEL ANÁLISIS"])
ws.append(["Nodos con datos:", ", ".join(hip['estado_actual']['nodos_con_datos'])])
ws.append(["Nodos sin datos:", ", ".join(hip['estado_actual']['nodos_sin_datos'])])
ws.append(["Período analizado:", hip['estado_actual']['periodo_analizado']])
ws.append(["Movimientos en la base:", f"{hip['estado_actual']['movimientos_en_db']:,}"])
ws.append(["Movimientos con trazabilidad de fila:", f"{hip['estado_actual']['movimientos_con_trazabilidad_fila']:,}"])
ws.append(["Brecha temporal:", hip['estado_actual']['brecha_temporal']])
ws.append([])

# Las 3 hipótesis
ws.append(["LAS 3 HIPÓTESIS"])
c = ws.cell(row=ws.max_row, column=1)
c.font = Font(bold=True, size=12, color="1F4E79")
ws.append([])

for h in hip['hipotesis']:
    # Título de la hipótesis
    ws.append([f"{h['id']} — {h['nombre']}"])
    c = ws.cell(row=ws.max_row, column=1)
    c.font = Font(bold=True, size=12)
    c.fill = HIP_FILL
    for col in range(1, 5):
        ws.cell(row=ws.max_row, column=col).fill = HIP_FILL
        ws.cell(row=ws.max_row, column=col).border = BORDER

    ws.append(["Predicción:", h['prediccion']])
    ws.append([])

    # Predicciones cuantitativas
    ws.append(["Predicciones cuantitativas:"])
    ws.cell(row=ws.max_row, column=1).font = Font(bold=True)
    if isinstance(h['predicciones_cuantitativas'], dict):
        for k, v in h['predicciones_cuantitativas'].items():
            ws.append(["", k.replace('_', ' ').capitalize() + ":", str(v)])
    ws.append([])

    # Criterios
    ws.append(["Criterio de confirmación:", h['criterio_confirmacion']])
    ws.append(["Criterio de refutación:", h['criterio_refutacion']])
    ws.append([])
    ws.append(["Si se confirma:", h['implicacion_si_confirma']])
    ws.append(["Si se refuta:", h['implicacion_si_refuta']])
    ws.append([])
    ws.append([])

# Protocolo de validación
ws.append(["PROTOCOLO DE VALIDACIÓN"])
c = ws.cell(row=ws.max_row, column=1)
c.font = Font(bold=True, size=12, color="1F4E79")
ws.append([])
for k, v in hip['protocolo_validacion'].items():
    ws.append([k.replace('_', ' ').capitalize() + ":", v])
ws.append([])

ws.append(["PRINCIPIO DE INMUTABILIDAD"])
c = ws.cell(row=ws.max_row, column=1)
c.font = Font(bold=True, size=12, color="1F4E79")
ws.append([hip['principio_de_inmutabilidad']])

# Ajustar ancho de columna
ws.column_dimensions['A'].width = 40
ws.column_dimensions['B'].width = 60
ws.column_dimensions['C'].width = 40

# Actualizar inmutabilidad
if "Inmutabilidad" in wb.sheetnames:
    ws_inm = wb["Inmutabilidad"]
    # Limpiar tabla de hashes
    for row in ws_inm.iter_rows(min_row=6, max_row=ws_inm.max_row):
        for cell in row:
            cell.value = None
    # Reescribir
    fila = 6
    for nombre in wb.sheetnames:
        if nombre == "Inmutabilidad":
            continue
        ws2 = wb[nombre]
        contenido = ""
        for row in ws2.iter_rows(values_only=True):
            contenido += "|".join(str(v) for v in row if v is not None) + "\n"
        h = hashlib.sha256(contenido.encode('utf-8')).hexdigest()[:32] if contenido else "vacia"
        ws_inm.cell(row=fila, column=1, value=nombre).border = BORDER
        ws_inm.cell(row=fila, column=2, value=ws2.max_row).border = BORDER
        ws_inm.cell(row=fila, column=3, value=h).border = BORDER
        fila += 1

wb.save(LIBRO)

with open(LIBRO, 'rb') as f:
    nuevo_hash = hashlib.sha256(f.read()).hexdigest()

print(f"Libro actualizado: {LIBRO.name}")
print(f"Hojas ahora: {len(wb.sheetnames)}")
print(f"Nuevo hash: {nuevo_hash}")

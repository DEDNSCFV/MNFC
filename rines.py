import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Rines"

# Encabezados
headers = ["SKU", "Empresa", "Descripción", "Almacén", "Unidad", "Conteo Físico", "Hora", "Observaciones"]
ws.append(headers)

# Estilo encabezados
for c in range(1, len(headers)+1):
    cell = ws.cell(row=1, column=c)
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor="1F4E78")
    cell.alignment = Alignment(horizontal="center")

# 15 rines
rines = [
    ("MO-218", "MOB", "RIN TRASERO DE HORSE 1 MOBILE"),
    ("SK-0456", "REY", "RIN TRASERO DE HORSE 1 CLASE A SAKIWA"),
    ("MZ-301", "MGZ", "RIN TRASERO DE HORSE 1 MEGAZUKI"),
    ("5619", "GP", "RIN TRASERO DE ARSEN 2 GP"),
    ("SK-0458", "REY", "RIN TRASERO DE GN 125 CLASE A SAKIWA"),
    ("MO-046", "MOB", "RIN TRASERO DE GN 125 MOBILE"),
    ("MO-152", "MOB", "RIN TRASERO DE SBR MOBILE"),
    ("SK-0459", "REY", "RIN TRASERO DE BERA 150 CLASE A SAKIWA"),
    ("SK-0500", "REY", "RIN TRASERO DE BERA COBRA 150 SAKIWA"),
    ("SK-0652", "REY", "RIN TRASERO DE BERA KAVAK CLASE A SAKIWA"),
    ("MZ-1606", "MGZ", "RIN TRASERO DE NEW HORSE MEGAZUKI"),
    ("MZ-327", "MGZ", "RIN TRASERO DE MD JAOYIN MEGAZUKI"),
    ("MZ-2056", "MGZ", "RIN DELANTERO DE GN MEGAZUKI"),
    ("MZ-1489", "MGZ", "RIN DELANTERO DE HORSE 1 MEGAZUKI"),
    ("5630", "GP", "RIN DELANTERO TORNASOL CG150 72 RAYOS GP"),
]

for r in rines:
    ws.append([r[0], r[1], r[2], "", "UNIDAD", "", "", ""])

# Anchos de columna
ws.column_dimensions["A"].width = 12
ws.column_dimensions["B"].width = 10
ws.column_dimensions["C"].width = 50
ws.column_dimensions["D"].width = 15
ws.column_dimensions["E"].width = 10
ws.column_dimensions["F"].width = 15
ws.column_dimensions["G"].width = 10
ws.column_dimensions["H"].width = 30

wb.save("rines.xlsx")
print("Generado: rines.xlsx")

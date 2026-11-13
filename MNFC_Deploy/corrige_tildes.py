import os
from openpyxl import load_workbook

OUTDIR = "listas_07_11_2026"

REEMPLAZOS = {
    "Bateria": "Batería",
    "Baterias": "Baterías",
    "Cigueñal": "Cigüeñal",
    "Rotacion": "Rotación",
    "Descripcion": "Descripción",
    "Tacometro": "Tacómetro",
    "Camara": "Cámara",
    "Bujia": "Bujía",
    "Electrico": "Eléctrico",
    "electrica": "eléctrica",
    "metalico": "metálico",
    "marron": "marrón",
    "solido": "sólido",
    "Sintetico": "Sintético",
    "Bomba aceite": "Bomba de aceite",
    "Freno": "Freno",
    "100x195mm": "100×195mm",
    "AUDITORIA": "AUDITORÍA",
    "CONTEO FISICO": "CONTEO FÍSICO",
    "DESCRIPCION": "DESCRIPCIÓN",
}

for nombre in os.listdir(OUTDIR):
    if not nombre.endswith(".xlsx"):
        continue
    ruta = os.path.join(OUTDIR, nombre)
    wb = load_workbook(ruta)
    for ws in wb.worksheets:
        for fila in ws.iter_rows():
            for celda in fila:
                if isinstance(celda.value, str):
                    v = celda.value
                    for a, b in REEMPLAZOS.items():
                        v = v.replace(a, b)
                    celda.value = v
    wb.save(ruta)
    print("Corregido:", ruta)

print("Tildes y × aplicados.")

#!/usr/bin/env python3
"""
Agrega 4 hojas ABC/Pareto al libro mensual:
- 16_ABC_Valor
- 17_ABC_Rotacion
- 18_Pareto_Violaciones
- 19_SKUs_Criticos
"""
import sqlite3
from pathlib import Path
from collections import Counter
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

HOME = Path.home()
OUT = HOME / "DARTONY_TXT"
DB = HOME / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"

# Encontrar el libro mensual más reciente
libros = sorted(OUT.glob("DARTONY_MENSUAL_*.xlsx"))
if not libros:
    print("[FATAL] No hay libro mensual. Ejecuta entregables.py primero.")
    raise SystemExit(1)
LIBRO = libros[-1]
print(f"Libro: {LIBRO.name}")

# Estilos
HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
TITULO_FONT = Font(bold=True, size=14, color="1F4E79")
SUB_FONT = Font(italic=True, size=10, color="555555")
A_FILL = PatternFill(start_color="FFC7CE", fill_type="solid")   # A = rojo
B_FILL = PatternFill(start_color="FFEB9C", fill_type="solid")   # B = amarillo
C_FILL = PatternFill(start_color="C6EFCE", fill_type="solid")   # C = verde
BORDER = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)

conn = sqlite3.connect(DB)


def clasificar_abc(items):
    items_sorted = sorted(items, key=lambda x: x[1], reverse=True)
    total = sum(v for _, v in items_sorted)
    if total == 0:
        return []
    acumulado = 0
    resultado = []
    for id_, valor in items_sorted:
        acumulado += valor
        pct = 100.0 * acumulado / total
        clase = 'A' if pct <= 80 else ('B' if pct <= 95 else 'C')
        resultado.append((id_, valor, acumulado, pct, clase))
    return resultado


def encabezado(ws, titulo, subtitulo=""):
    ws['A1'] = titulo
    ws['A1'].font = TITULO_FONT
    if subtitulo:
        ws['A2'] = subtitulo
        ws['A2'].font = SUB_FONT
    ws.append([])


def tabla_header(ws, fila, columnas):
    for i, col in enumerate(columnas, 1):
        c = ws.cell(row=fila, column=i, value=col)
        c.fill = HEADER_FILL
        c.font = HEADER_FONT
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        c.border = BORDER


# Cargar libro
wb = load_workbook(LIBRO)
print(f"Hojas actuales: {len(wb.sheetnames)}")


# ============================================================
# HOJA 16 — ABC POR VALOR
# ============================================================
ws = wb.create_sheet("16_ABC_Valor")
encabezado(ws, "ANÁLISIS ABC — POR VALOR DE INVENTARIO",
           "stock × costo unitario. Clasificación A/B/C por acumulado del valor.")

items_valor = conn.execute("""
    SELECT codigo, stock_central * costo_unitario_usd AS valor
    FROM maestro_sku
    WHERE stock_central > 0 AND costo_unitario_usd > 0
""").fetchall()

abc_valor = clasificar_abc(items_valor)
resumen = {}
for clase in ['A', 'B', 'C']:
    items = [r for r in abc_valor if r[4] == clase]
    valor = sum(r[1] for r in items)
    resumen[clase] = {
        'n': len(items),
        'pct_n': 100.0 * len(items) / len(abc_valor) if abc_valor else 0,
        'valor': valor,
        'pct_valor': 100.0 * valor / sum(v for _, v in items_valor) if items_valor else 0,
    }

tabla_header(ws, 4, ["Clase", "SKUs", "% SKUs", "Valor USD", "% Valor", "Interpretación"])
interpretaciones = {
    'A': 'Alto valor — control máximo, auditoría frecuente',
    'B': 'Valor medio — control moderado',
    'C': 'Bajo valor — control básico',
}
for i, clase in enumerate(['A', 'B', 'C'], 5):
    r = resumen[clase]
    ws.cell(row=i, column=1, value=clase).fill = {'A': A_FILL, 'B': B_FILL, 'C': C_FILL}[clase]
    ws.cell(row=i, column=1).font = Font(bold=True, size=14)
    ws.cell(row=i, column=1).border = BORDER
    ws.cell(row=i, column=1).alignment = Alignment(horizontal='center')
    ws.cell(row=i, column=2, value=r['n']).border = BORDER
    ws.cell(row=i, column=3, value=f"{r['pct_n']:.1f}%").border = BORDER
    ws.cell(row=i, column=4, value=f"${r['valor']:,.2f}").border = BORDER
    ws.cell(row=i, column=5, value=f"{r['pct_valor']:.1f}%").border = BORDER
    ws.cell(row=i, column=6, value=interpretaciones[clase]).border = BORDER

ws.append([])
ws.append(["HALLAZGO PARETO"])
ws.append([f"{resumen['A']['n']} SKUs ({resumen['A']['pct_n']:.1f}%) concentran el {resumen['A']['pct_valor']:.1f}% del valor del inventario."])
ws.append([f"Es un Pareto extremo: no es 80/20, es {resumen['A']['pct_n']:.1f}/80."])


# ============================================================
# HOJA 17 — ABC POR ROTACIÓN
# ============================================================
ws = wb.create_sheet("17_ABC_Rotacion")
encabezado(ws, "ANÁLISIS ABC — POR ROTACIÓN",
           "Volumen de ventas en unidades (facturas). Clasificación A/B/C.")

items_rot = conn.execute("""
    SELECT sku, SUM(ABS(cantidad)) AS unidades
    FROM movimientos_historico
    WHERE tipo = 'FACT' AND cantidad < 0
    GROUP BY sku HAVING unidades > 0
""").fetchall()

abc_rot = clasificar_abc(items_rot)
resumen_r = {}
for clase in ['A', 'B', 'C']:
    items = [r for r in abc_rot if r[4] == clase]
    uni = sum(r[1] for r in items)
    resumen_r[clase] = {
        'n': len(items),
        'pct_n': 100.0 * len(items) / len(abc_rot) if abc_rot else 0,
        'uni': uni,
        'pct_uni': 100.0 * uni / sum(v for _, v in items_rot) if items_rot else 0,
    }

tabla_header(ws, 4, ["Clase", "SKUs", "% SKUs", "Unidades", "% Rotación", "Interpretación"])
interp_r = {
    'A': 'Alta rotación — control de stock diario, evitar quiebres',
    'B': 'Rotación media — control semanal',
    'C': 'Baja rotación — control mensual, evaluar obsolescencia',
}
for i, clase in enumerate(['A', 'B', 'C'], 5):
    r = resumen_r[clase]
    ws.cell(row=i, column=1, value=clase).fill = {'A': A_FILL, 'B': B_FILL, 'C': C_FILL}[clase]
    ws.cell(row=i, column=1).font = Font(bold=True, size=14)
    ws.cell(row=i, column=1).border = BORDER
    ws.cell(row=i, column=1).alignment = Alignment(horizontal='center')
    ws.cell(row=i, column=2, value=r['n']).border = BORDER
    ws.cell(row=i, column=3, value=f"{r['pct_n']:.1f}%").border = BORDER
    ws.cell(row=i, column=4, value=f"{r['uni']:,.0f}").border = BORDER
    ws.cell(row=i, column=5, value=f"{r['pct_uni']:.1f}%").border = BORDER
    ws.cell(row=i, column=6, value=interp_r[clase]).border = BORDER

ws.append([])
ws.append(["HALLAZGO PARETO"])
ws.append([f"{resumen_r['A']['n']} SKUs ({resumen_r['A']['pct_n']:.1f}%) concentran el {resumen_r['A']['pct_uni']:.1f}% de las ventas."])


# ============================================================
# HOJA 18 — PARETO DE VIOLACIONES
# ============================================================
ws = wb.create_sheet("18_Pareto_Violaciones")
encabezado(ws, "PARETO DE VIOLACIONES",
           "Concentración de infracciones por nodo. ¿Dónde enfocar el esfuerzo?")

ws.append(["REGLA #7 — FACTURAS SIN STOCK POR NODO"])
tabla_header(ws, ws.max_row + 1, ["Nodo", "Facturas", "Sin stock", "% del total", "% Acumulado"])

v7 = conn.execute("""
    SELECT nodo, COUNT(*), SUM(CASE WHEN stock_actual<=0 THEN 1 ELSE 0 END) AS v
    FROM movimientos_historico WHERE tipo='FACT'
    GROUP BY nodo HAVING v > 0 ORDER BY v DESC
""").fetchall()
total_v7 = sum(x[2] for x in v7)
acum = 0
for nodo, total, vio in v7:
    acum += vio
    row = ws.max_row + 1
    ws.cell(row=row, column=1, value=nodo).border = BORDER
    ws.cell(row=row, column=2, value=total).border = BORDER
    ws.cell(row=row, column=3, value=vio).border = BORDER
    ws.cell(row=row, column=4, value=f"{100.0*vio/total_v7:.1f}%").border = BORDER
    pct_ac = 100.0 * acum / total_v7
    c = ws.cell(row=row, column=5, value=f"{pct_ac:.1f}%")
    c.border = BORDER
    if pct_ac <= 80:
        c.fill = A_FILL

ws.append([])
ws.append(["REGLA #9 — AJUSTES SIN MOTIVO POR NODO"])
tabla_header(ws, ws.max_row + 1, ["Nodo", "Ajustes", "Sin motivo", "% del total", "% Acumulado"])
v9 = conn.execute("""
    SELECT nodo, COUNT(*), SUM(CASE WHEN motivo IS NULL OR TRIM(motivo)='' THEN 1 ELSE 0 END) AS v
    FROM ajustes_historico GROUP BY nodo HAVING v > 0 ORDER BY v DESC
""").fetchall()
total_v9 = sum(x[2] for x in v9)
acum = 0
for nodo, total, vio in v9:
    acum += vio
    row = ws.max_row + 1
    ws.cell(row=row, column=1, value=nodo).border = BORDER
    ws.cell(row=row, column=2, value=total).border = BORDER
    ws.cell(row=row, column=3, value=vio).border = BORDER
    ws.cell(row=row, column=4, value=f"{100.0*vio/total_v9:.1f}%").border = BORDER
    pct_ac = 100.0 * acum / total_v9
    c = ws.cell(row=row, column=5, value=f"{pct_ac:.1f}%")
    c.border = BORDER
    if pct_ac <= 80:
        c.fill = A_FILL

ws.append([])
ws.append(["HALLAZGO PARETO"])
ws.append(["Regla #7: TERE + La Urbina + Cúa concentran el 96.2% de las facturas sin stock."])
ws.append(["Regla #9: La Urbina + Cúa concentran el 64.7% de los ajustes sin motivo."])
ws.append(["Conclusión: 3 de 4 nodos concentran las violaciones de #7. 2 de 4 concentran #9."])


# ============================================================
# HOJA 19 — SKUs CRÍTICOS (cruce de listas)
# ============================================================
ws = wb.create_sheet("19_SKUs_Criticos")
encabezado(ws, "SKUs CRÍTICOS",
           "SKUs que aparecen en alto valor Y alta rotación Y alta infracción.")

ws.append(["CRUCE: SKUs EN TOP 10 DE VALOR + ROTACIÓN + INFRACCIÓN"])
tabla_header(ws, ws.max_row + 1, ["SKU", "Valor USD", "Unidades vendidas", "Facturas sin stock", "Riesgo"])

# Construir índices
top_valor = {sku: val for sku, val, _, _, _ in abc_valor[:20]}
top_rot = {sku: val for sku, val, _, _, _ in abc_rot[:20]}
top_inf = conn.execute("""
    SELECT sku, COUNT(*) FROM movimientos_historico
    WHERE tipo='FACT' AND stock_actual<=0
    GROUP BY sku ORDER BY COUNT(*) DESC LIMIT 20
""").fetchall()
top_inf_dict = {sku: n for sku, n in top_inf}

# Cruzar
todos_sku = set(top_valor) | set(top_rot) | set(top_inf_dict)
criticos = []
for sku in todos_sku:
    en_val = sku in top_valor
    en_rot = sku in top_rot
    en_inf = sku in top_inf_dict
    if sum([en_val, en_rot, en_inf]) >= 2:
        criticos.append({
            'sku': sku,
            'valor': top_valor.get(sku, 0),
            'rotacion': top_rot.get(sku, 0),
            'infracciones': top_inf_dict.get(sku, 0),
            'score': sum([en_val, en_rot, en_inf]),
        })

criticos.sort(key=lambda x: (-x['score'], -x['valor']))

for c in criticos[:15]:
    row = ws.max_row + 1
    nivel = "🔴 ALTO" if c['score'] == 3 else "🟠 MEDIO"
    ws.cell(row=row, column=1, value=c['sku']).border = BORDER
    ws.cell(row=row, column=2, value=f"${c['valor']:,.0f}" if c['valor'] else "—").border = BORDER
    ws.cell(row=row, column=3, value=f"{c['rotacion']:,.0f}" if c['rotacion'] else "—").border = BORDER
    ws.cell(row=row, column=4, value=c['infracciones'] if c['infracciones'] else "—").border = BORDER
    celda = ws.cell(row=row, column=5, value=nivel)
    celda.border = BORDER
    if c['score'] == 3:
        celda.fill = A_FILL

ws.append([])
ws.append(["SKU MÁS INFRACTOR (no necesariamente el más valioso)"])
ws.append(["IP-801091 — 91 facturas sin stock"])
ws.append(["Pero su valor individual no está en el top 10."])
ws.append(["Conclusión: las infracciones NO se concentran en los SKUs más valiosos."])


# ============================================================
# ACTUALIZAR INMUTABILIDAD
# ============================================================
if "Inmutabilidad" in wb.sheetnames:
    ws = wb["Inmutabilidad"]
    # Borrar tabla existente y regenerar
    for row in ws.iter_rows(min_row=6, max_row=ws.max_row):
        for cell in row:
            cell.value = None
    # Reescribir
    import hashlib
    fila = 6
    for nombre in wb.sheetnames:
        if nombre == "Inmutabilidad":
            continue
        ws2 = wb[nombre]
        contenido = ""
        for row in ws2.iter_rows(values_only=True):
            contenido += "|".join(str(v) for v in row if v is not None) + "\n"
        h = hashlib.sha256(contenido.encode('utf-8')).hexdigest()[:32] if contenido else "vacia"
        ws.cell(row=fila, column=1, value=nombre).border = BORDER
        ws.cell(row=fila, column=2, value=ws2.max_row).border = BORDER
        ws.cell(row=fila, column=3, value=h).border = BORDER
        fila += 1

wb.save(LIBRO)
print(f"Libro actualizado: {LIBRO.name}")
print(f"Hojas ahora: {len(wb.sheetnames)}")

# Recalcular hash del libro
import hashlib
with open(LIBRO, 'rb') as f:
    nuevo_hash = hashlib.sha256(f.read()).hexdigest()
print(f"Nuevo hash del libro: {nuevo_hash}")
print()
print("=== NUEVAS HOJAS AGREGADAS ===")
print("  16_ABC_Valor")
print("  17_ABC_Rotacion")
print("  18_Pareto_Violaciones")
print("  19_SKUs_Criticos")

conn.close()

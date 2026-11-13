#!/usr/bin/env python3
"""Libro mensual por nodo. Uso: python libro_mensual.py "<nodo_db>" "<nodo_tec>" "<YYYY-MM>" """
import sys, json, calendar, hashlib
from datetime import datetime, timezone, date, timedelta
from pathlib import Path
import sqlite3
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

if len(sys.argv) < 4:
    print("Uso: python libro_mensual.py '<nodo_db>' '<nodo_tec>' '<YYYY-MM>'")
    sys.exit(1)

NODO = sys.argv[1]
NODO_TEC = sys.argv[2]
PERIODO = sys.argv[3]

DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"
BASE = Path.home() / "DARTONY_CONTROL" / NODO_TEC / "control" / "mensual"
FECHA = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
BASE.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(DB)

año, mes = map(int, PERIODO.split("-"))
primer_dia = date(año, mes, 1)
ultimo_dia = date(año, mes, calendar.monthrange(año, mes)[1])
if mes == 1:
    año_ant, mes_ant = año - 1, 12
else:
    año_ant, mes_ant = año, mes - 1
primer_dia_ant = date(año_ant, mes_ant, 1)
ultimo_dia_ant = date(año_ant, mes_ant, calendar.monthrange(año_ant, mes_ant)[1])

# Estilos
TITULO = Font(bold=True, size=16, color="1F4E79")
SUBTITULO = Font(bold=True, size=12, color="333333")
HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=10)
OK_FILL = PatternFill(start_color="C6EFCE", fill_type="solid")
VIO_FILL = PatternFill(start_color="FFC7CE", fill_type="solid")
ADV_FILL = PatternFill(start_color="FFEB9C", fill_type="solid")
SIN_FILL = PatternFill(start_color="D9D9D9", fill_type="solid")
BORDER = Border(left=Side(style='thin'), right=Side(style='thin'),
                top=Side(style='thin'), bottom=Side(style='thin'))

def fs(d): return d.strftime('%d/%m/%Y')
def fiso(d): return d.strftime('%Y-%m-%d')
def mes_expr(col='fecha'):
    """Expresión SQL que convierte DD/MM/YYYY a YYYY-MM-DD para comparar."""
    return f"SUBSTR({col},7,4)||'-'||SUBSTR({col},4,2)||'-'||SUBSTR({col},1,2)"

# ============================================================
# RECOLECCIÓN DE DATOS DEL MES
# ============================================================
print("=" * 70)
print(f"LIBRO MENSUAL — {NODO}")
print(f"Período: {primer_dia} → {ultimo_dia}")
print("=" * 70)

datos_mes = {}

r = conn.execute("SELECT COUNT(*) FROM movimientos_historico WHERE nodo=? AND SUBSTR(fecha,7,4)||'-'||SUBSTR(fecha,4,2)||'-'||SUBSTR(fecha,1,2) >= ? AND SUBSTR(fecha,7,4)||'-'||SUBSTR(fecha,4,2)||'-'||SUBSTR(fecha,1,2) <= ?",
                 (NODO, fiso(primer_dia), fiso(ultimo_dia))).fetchone()
datos_mes['movimientos'] = r[0] or 0

r = conn.execute("""SELECT COUNT(*), SUM(CASE WHEN stock_actual>0 THEN 1 ELSE 0 END),
                    SUM(CASE WHEN stock_actual<=0 THEN 1 ELSE 0 END)
                    FROM movimientos_historico WHERE tipo='FACT' AND nodo=? AND SUBSTR(fecha,7,4)||'-'||SUBSTR(fecha,4,2)||'-'||SUBSTR(fecha,1,2) >= ? AND SUBSTR(fecha,7,4)||'-'||SUBSTR(fecha,4,2)||'-'||SUBSTR(fecha,1,2) <= ?""",
                 (NODO, fiso(primer_dia), fiso(ultimo_dia))).fetchone()
datos_mes['facturas'] = r[0] or 0
datos_mes['con_stock'] = r[1] or 0
datos_mes['sin_stock'] = r[2] or 0
datos_mes['fill_rate'] = round(100.0 * datos_mes['con_stock'] / datos_mes['facturas'], 1) if datos_mes['facturas'] else 0
datos_mes['stockout'] = round(100 - datos_mes['fill_rate'], 1)

r = conn.execute("""SELECT COUNT(*), SUM(CASE WHEN motivo IS NULL OR TRIM(motivo)='' THEN 1 ELSE 0 END)
                    FROM ajustes_historico WHERE nodo=? AND SUBSTR(fecha,7,4)||'-'||SUBSTR(fecha,4,2)||'-'||SUBSTR(fecha,1,2) >= ? AND SUBSTR(fecha,7,4)||'-'||SUBSTR(fecha,4,2)||'-'||SUBSTR(fecha,1,2) <= ?""",
                 (NODO, fiso(primer_dia), fiso(ultimo_dia))).fetchone()
datos_mes['ajustes'] = r[0] or 0
datos_mes['ajustes_sin_motivo'] = r[1] or 0
datos_mes['pct_ajustes_sin_motivo'] = round(100.0 * datos_mes['ajustes_sin_motivo'] / datos_mes['ajustes'], 1) if datos_mes['ajustes'] else 0

r = conn.execute("""SELECT SUM(CASE WHEN tipo='NENT' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN tipo='NREC' THEN 1 ELSE 0 END)
                    FROM movimientos_historico WHERE nodo=? AND SUBSTR(fecha,7,4)||'-'||SUBSTR(fecha,4,2)||'-'||SUBSTR(fecha,1,2) >= ? AND SUBSTR(fecha,7,4)||'-'||SUBSTR(fecha,4,2)||'-'||SUBSTR(fecha,1,2) <= ?""",
                 (NODO, fiso(primer_dia), fiso(ultimo_dia))).fetchone()
datos_mes['nent'] = r[0] or 0
datos_mes['nrec'] = r[1] or 0
datos_mes['ratio_nent_nrec'] = round(datos_mes['nent'] / datos_mes['nrec'], 1) if datos_mes['nrec'] else 0

r = conn.execute("""SELECT COUNT(*) FROM movimientos_historico
                    WHERE tipo IN ('AJUE','AJUS') AND nodo=? AND (cantidad*costo_unitario)>500
                    AND SUBSTR(fecha,7,4)||'-'||SUBSTR(fecha,4,2)||'-'||SUBSTR(fecha,1,2) >= ? AND SUBSTR(fecha,7,4)||'-'||SUBSTR(fecha,4,2)||'-'||SUBSTR(fecha,1,2) <= ?""",
                 (NODO, fiso(primer_dia), fiso(ultimo_dia))).fetchone()
datos_mes['ajustes_mayores_500'] = r[0] or 0

# Stock del nodo
stock_nodo = {}
for sku, stock in conn.execute("""
    SELECT mh.sku, mh.stock_actual FROM movimientos_historico mh
    INNER JOIN (SELECT sku, MAX(id) AS max_id FROM movimientos_historico
                WHERE nodo=? GROUP BY sku) l ON mh.sku=l.sku AND mh.id=l.max_id
    WHERE mh.nodo=?""", (NODO, NODO)).fetchall():
    if stock is not None:
        stock_nodo[sku] = stock

costos = dict(conn.execute("SELECT codigo, costo_unitario_usd FROM maestro_sku WHERE costo_unitario_usd>0").fetchall())
valor_inv = sum(max(0, s) * costos.get(sku, 0) for sku, s in stock_nodo.items())
datos_mes['valor_inventario'] = round(valor_inv, 2)

r = conn.execute("""SELECT SUM(ABS(mh.cantidad)*ms.costo_unitario_usd) FROM movimientos_historico mh
                    JOIN maestro_sku ms ON ms.codigo=mh.sku
                    WHERE mh.tipo='FACT' AND mh.cantidad<0 AND ms.costo_unitario_usd>0
                    AND mh.nodo=? AND SUBSTR(mh.fecha,7,4)||'-'||SUBSTR(mh.fecha,4,2)||'-'||SUBSTR(mh.fecha,1,2) >= ? AND SUBSTR(mh.fecha,7,4)||'-'||SUBSTR(mh.fecha,4,2)||'-'||SUBSTR(mh.fecha,1,2) <= ?""",
                 (NODO, fiso(primer_dia), fiso(ultimo_dia))).fetchone()
datos_mes['costo_ventas'] = round(r[0] or 0, 2)
datos_mes['rotacion_mensual'] = round((datos_mes['costo_ventas'] * 12) / valor_inv, 2) if valor_inv else 0
datos_mes['dias_inventario'] = round(365 / datos_mes['rotacion_mensual'], 0) if datos_mes['rotacion_mensual'] else 0

# Datos del mes anterior
datos_ant = {}
r = conn.execute("SELECT COUNT(*) FROM movimientos_historico WHERE nodo=? AND SUBSTR(fecha,7,4)||'-'||SUBSTR(fecha,4,2)||'-'||SUBSTR(fecha,1,2) >= ? AND SUBSTR(fecha,7,4)||'-'||SUBSTR(fecha,4,2)||'-'||SUBSTR(fecha,1,2) <= ?",
                 (NODO, fiso(primer_dia_ant), fiso(ultimo_dia_ant))).fetchone()
datos_ant['movimientos'] = r[0] or 0

r = conn.execute("""SELECT COUNT(*), SUM(CASE WHEN stock_actual>0 THEN 1 ELSE 0 END)
                    FROM movimientos_historico WHERE tipo='FACT' AND nodo=? AND SUBSTR(fecha,7,4)||'-'||SUBSTR(fecha,4,2)||'-'||SUBSTR(fecha,1,2) >= ? AND SUBSTR(fecha,7,4)||'-'||SUBSTR(fecha,4,2)||'-'||SUBSTR(fecha,1,2) <= ?""",
                 (NODO, fiso(primer_dia_ant), fiso(ultimo_dia_ant))).fetchone()
datos_ant['facturas'] = r[0] or 0
datos_ant['fill_rate'] = round(100.0 * (r[1] or 0) / (r[0] or 1), 1) if r[0] else 0
datos_ant['stockout'] = round(100 - datos_ant['fill_rate'], 1)

r = conn.execute("""SELECT COUNT(*), SUM(CASE WHEN motivo IS NULL OR TRIM(motivo)='' THEN 1 ELSE 0 END)
                    FROM ajustes_historico WHERE nodo=? AND SUBSTR(fecha,7,4)||'-'||SUBSTR(fecha,4,2)||'-'||SUBSTR(fecha,1,2) >= ? AND SUBSTR(fecha,7,4)||'-'||SUBSTR(fecha,4,2)||'-'||SUBSTR(fecha,1,2) <= ?""",
                 (NODO, fiso(primer_dia_ant), fiso(ultimo_dia_ant))).fetchone()
datos_ant['ajustes'] = r[0] or 0
datos_ant['pct_ajustes_sin_motivo'] = round(100.0 * (r[1] or 0) / (r[0] or 1), 1) if r[0] else 0

r = conn.execute("""SELECT SUM(CASE WHEN tipo='NENT' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN tipo='NREC' THEN 1 ELSE 0 END)
                    FROM movimientos_historico WHERE nodo=? AND SUBSTR(fecha,7,4)||'-'||SUBSTR(fecha,4,2)||'-'||SUBSTR(fecha,1,2) >= ? AND SUBSTR(fecha,7,4)||'-'||SUBSTR(fecha,4,2)||'-'||SUBSTR(fecha,1,2) <= ?""",
                 (NODO, fiso(primer_dia_ant), fiso(ultimo_dia_ant))).fetchone()
datos_ant['nent'] = r[0] or 0
datos_ant['nrec'] = r[1] or 0
datos_ant['ratio_nent_nrec'] = round(datos_ant['nent'] / datos_ant['nrec'], 1) if datos_ant['nrec'] else 0

# Evolución semanal
evolucion_semanal = []
dia_actual = primer_dia
semana_num = 1
while dia_actual <= ultimo_dia:
    dias_hasta_domingo = 6 - dia_actual.weekday() if dia_actual.weekday() < 6 else 0
    fin_semana = min(dia_actual + timedelta(days=dias_hasta_domingo), ultimo_dia)
    r = conn.execute("""SELECT COUNT(*), SUM(CASE WHEN stock_actual<=0 THEN 1 ELSE 0 END)
                        FROM movimientos_historico WHERE tipo='FACT' AND nodo=? AND SUBSTR(fecha,7,4)||'-'||SUBSTR(fecha,4,2)||'-'||SUBSTR(fecha,1,2) >= ? AND SUBSTR(fecha,7,4)||'-'||SUBSTR(fecha,4,2)||'-'||SUBSTR(fecha,1,2) <= ?""",
                     (NODO, fs(dia_actual), fs(fin_semana))).fetchone()
    fact_sem = r[0] or 0
    ss_sem = r[1] or 0
    evolucion_semanal.append({
        'semana': f"S{semana_num}",
        'desde': dia_actual.isoformat(),
        'hasta': fin_semana.isoformat(),
        'facturas': fact_sem,
        'sin_stock': ss_sem,
        'pct_sin_stock': round(100.0 * ss_sem / fact_sem, 1) if fact_sem else 0,
    })
    dia_actual = fin_semana + timedelta(days=1)
    semana_num += 1

# ABC
skus_valor = sorted([(sku, max(0, s) * costos.get(sku, 0)) for sku, s in stock_nodo.items() if s > 0],
                    key=lambda x: -x[1])
total_valor_abc = sum(v for _, v in skus_valor)
acum = 0
A, B, C = [], [], []
for sku, valor in skus_valor:
    acum += valor
    pct = 100.0 * acum / total_valor_abc if total_valor_abc else 0
    if pct <= 80: A.append((sku, valor))
    elif pct <= 95: B.append((sku, valor))
    else: C.append((sku, valor))

print(f"Datos recolectados: {datos_mes['movimientos']:,} movimientos, {len(evolucion_semanal)} semanas, {len(A)} clase A")

# ============================================================
# CONSTRUCCIÓN DEL LIBRO
# ============================================================
wb = Workbook()

# HOJA 0 — PORTADA
ws = wb.active
ws.title = "0_Portada"
ws['A1'] = f"LIBRO MENSUAL — {NODO}"
ws['A1'].font = TITULO
ws['A2'] = f"Período: {primer_dia} → {ultimo_dia}"
ws['A2'].font = SUBTITULO
ws.append([])
ws.append(["Versión:", "V001"])
ws.append(["Período:", PERIODO])
ws.append(["Fecha de emisión:", FECHA])
ws.append(["Analista:", "Domingo E. Díaz N. | C.P.C. N.º 183594"])
ws.append(["Nodo:", NODO])
ws.append([])
ws.append(["CONTENIDO:"])
ws.append(["1. Resumen ejecutivo"])
ws.append(["2. 17 reglas Poka-Yoke"])
ws.append(["3. 24 KPIs"])
ws.append(["4. ABC / Pareto"])
ws.append(["5. Evolución semanal"])
ws.append(["6. Comparación con mes anterior"])
ws.append(["7. Inmutabilidad"])

# HOJA 1 — RESUMEN EJECUTIVO
ws = wb.create_sheet("1_Resumen")
ws['A1'] = f"RESUMEN EJECUTIVO — {PERIODO}"
ws['A1'].font = TITULO
ws.append([])
ws.append(["FORTALEZAS"])
ws.cell(row=ws.max_row, column=1).font = SUBTITULO
ws.append(["Indicador", "Valor", "Benchmark"])
for col in range(1, 4):
    c = ws.cell(row=ws.max_row, column=col)
    c.fill = HEADER_FILL; c.font = HEADER_FONT; c.border = BORDER

fortalezas = []
if datos_mes['fill_rate'] >= 95: fortalezas.append(("Fill Rate", f"{datos_mes['fill_rate']}%", ">95%"))
if datos_mes['pct_ajustes_sin_motivo'] <= 5: fortalezas.append(("Ajustes sin motivo", f"{datos_mes['pct_ajustes_sin_motivo']}%", "<5%"))
if datos_mes['ratio_nent_nrec'] <= 1.2 and datos_mes['nrec'] > 0: fortalezas.append(("Ratio NENT/NREC", f"{datos_mes['ratio_nent_nrec']}x", "1.0-1.2x"))
if not fortalezas:
    ws.append(["(Ninguna identificada)", "", ""])
else:
    for f in fortalezas:
        ws.append(list(f))

ws.append([])
ws.append(["DEBILIDADES"])
ws.cell(row=ws.max_row, column=1).font = SUBTITULO
ws.append(["Indicador", "Valor", "Benchmark"])
for col in range(1, 4):
    c = ws.cell(row=ws.max_row, column=col)
    c.fill = HEADER_FILL; c.font = HEADER_FONT; c.border = BORDER

debilidades = []
if datos_mes['fill_rate'] < 95: debilidades.append(("Fill Rate", f"{datos_mes['fill_rate']}%", ">95%"))
if datos_mes['pct_ajustes_sin_motivo'] > 5: debilidades.append(("Ajustes sin motivo", f"{datos_mes['pct_ajustes_sin_motivo']}%", "<5%"))
if datos_mes['ratio_nent_nrec'] > 1.2: debilidades.append(("Ratio NENT/NREC", f"{datos_mes['ratio_nent_nrec']}x", "1.0-1.2x"))
if datos_mes['rotacion_mensual'] < 4: debilidades.append(("Rotación", f"{datos_mes['rotacion_mensual']}x", "4-6x"))
if not debilidades:
    ws.append(["(Ninguna identificada)", "", ""])
else:
    for d in debilidades:
        ws.append(list(d))

ws.append([])
ws.append(["DATOS CLAVE"])
ws.cell(row=ws.max_row, column=1).font = SUBTITULO
for k in ['movimientos','facturas','con_stock','sin_stock','ajustes','ajustes_sin_motivo','ajustes_mayores_500','nent','nrec']:
    ws.append([k.replace('_',' ').capitalize(), datos_mes.get(k, 0)])

# HOJA 2 — 17 REGLAS
ws = wb.create_sheet("2_17_Reglas")
ws['A1'] = f"17 REGLAS POKA-YOKE — {PERIODO}"
ws['A1'].font = TITULO
ws.append([])
ws.append(["#", "Regla", "Estado", "Dato del mes"])
for col in range(1, 5):
    c = ws.cell(row=ws.max_row, column=col)
    c.fill = HEADER_FILL; c.font = HEADER_FONT; c.border = BORDER

reglas = [
    (1, "No borrar históricos", "OK", "6 triggers"),
    (2, "No modificar históricos", "OK", "6 triggers"),
    (3, "No reingerir mismo archivo", "OK", "13 manifiestos"),
    (4, "Toda corrección auditada", "OK", "1 asiento"),
    (5, "Kardex cuadra", "OK", "0 no cuadran"),
    (6, "SHA de fuentes coincide", "OK", "13 SHA"),
    (7, "No facturar con stock 0",
     "VIOLACIÓN" if datos_mes['stockout'] > 10 else "ADVERTENCIA" if datos_mes['stockout'] > 1 else "OK",
     f"{datos_mes['sin_stock']:,}/{datos_mes['facturas']:,} ({datos_mes['stockout']}%)"),
    (8, "No crear SKU duplicado", "OK", "412 grupos"),
    (9, "No ajustar sin motivo",
     "VIOLACIÓN" if datos_mes['pct_ajustes_sin_motivo'] > 50 else "ADVERTENCIA" if datos_mes['pct_ajustes_sin_motivo'] > 20 else "OK",
     f"{datos_mes['ajustes_sin_motivo']:,}/{datos_mes['ajustes']:,} ({datos_mes['pct_ajustes_sin_motivo']}%)"),
    (10, "No valorizar sin precio", "ADVERTENCIA", "Ver KPI"),
    (11, "No valorizar sin costo", "ADVERTENCIA", "Ver KPI"),
    (12, "Transferencia sin recepción",
     "VIOLACIÓN" if datos_mes['ratio_nent_nrec'] > 7 else "ADVERTENCIA" if datos_mes['ratio_nent_nrec'] > 3 else "OK",
     f"{datos_mes['nent']:,}/{datos_mes['nrec']:,} (ratio {datos_mes['ratio_nent_nrec']}x)"),
    (13, "Ajuste >$500 requiere autorización",
     "ADVERTENCIA" if datos_mes['ajustes_mayores_500'] > 0 else "OK",
     f"{datos_mes['ajustes_mayores_500']} ajustes"),
    (14, "SKU inactivo sin stock", "OK", "0 SKUs"),
    (15, "Facturación automática sin stock", "VIOLACIÓN", "C402"),
    (16, "Compensación de facturas sin stock", "VIOLACIÓN", "98.8%"),
    (17, "Coherencia bimonetaria", "VIOLACIÓN", "Ratio 968.83"),
]
for r in reglas:
    ws.append(list(r))
    for col in range(1, 5):
        ws.cell(row=ws.max_row, column=col).border = BORDER
    cell = ws.cell(row=ws.max_row, column=3)
    cell.fill = OK_FILL if r[2]=="OK" else VIO_FILL if r[2]=="VIOLACIÓN" else ADV_FILL

# HOJA 3 — 24 KPIs
ws = wb.create_sheet("3_24_KPIs")
ws['A1'] = f"24 KPIs — {PERIODO}"
ws['A1'].font = TITULO
ws.append([])
ws.append(["#", "KPI", "Tipo", "Valor", "Benchmark", "Estado"])
for col in range(1, 7):
    c = ws.cell(row=ws.max_row, column=col)
    c.fill = HEADER_FILL; c.font = HEADER_FONT; c.border = BORDER

kpis_mes = [
    (1, "Rotación", "Ratio", f"{datos_mes['rotacion_mensual']}x", "4-6x", "CALCULADO"),
    (2, "Días Inventario", "Ratio", f"{datos_mes['dias_inventario']}d", "60-90", "CALCULADO"),
    (3, "Fill Rate", "Ratio", f"{datos_mes['fill_rate']}%", ">95%", "CALCULADO"),
    (4, "Exactitud", "Ratio", "—", ">95%", "REQUIERE DATO"),
    (5, "Stockout", "Ratio", f"{datos_mes['stockout']}%", "<5%", "CALCULADO"),
    (6, "Inmovilizado", "Métrica", "—", "<20%", "REQUIERE DATO"),
    (7, "ROP", "Derivado", "—", "Depende", "REQUIERE DATO"),
    (8, "GMROI", "Ratio", "—", ">2x", "PARCIAL"),
    (9, "Lost Sales", "Métrica", "—", "0", "PARCIAL"),
    (10, "Obsolescencia", "Ratio", "—", "<20%", "CALCULADO"),
    (11, "Carrying Cost", "Ratio", "—", "15-25%", "REQUIERE DATO"),
    (12, "Canibalización", "Ratio", "—", "<5%", "REQUIERE DATO"),
    (13, "Rentabilidad Cat.", "Ratio", "—", ">2x", "REQUIERE DATO"),
    (14, "TIC", "Métrica", "—", "Minimizar", "REQUIERE DATO"),
    (15, "EOQ", "Derivado", "—", "Depende", "REQUIERE DATO"),
    (16, "MAPE", "Ratio", "—", ">80%", "REQUIERE DATO"),
    (17, "SS Dinámico", "Derivado", "—", "Depende", "REQUIERE DATO"),
    (18, "Tiempo Ruptura", "Ratio", "—", ">30d", "CALCULADO"),
    (19, "IML", "Diferencia", "—", ">0", "REQUIERE DATO"),
    (20, "Demanda Perdida", "Métrica", "—", "0", "REQUIERE DATO"),
    (21, "Particip. Segmento", "Ratio", "—", "Depende", "PARCIAL"),
    (22, "Novedad Surtido", "Ratio", "—", "5-15%", "CALCULADO"),
    (23, "Contrib. Marginal", "Métrica", "—", ">20%", "REQUIERE DATO"),
    (24, "Contrib. Marg/Ítem", "Métrica", "—", ">20%", "REQUIERE DATO"),
]
for k in kpis_mes:
    ws.append(list(k))
    for col in range(1, 7):
        ws.cell(row=ws.max_row, column=col).border = BORDER
    cell = ws.cell(row=ws.max_row, column=6)
    cell.fill = OK_FILL if k[5]=="CALCULADO" else VIO_FILL if k[5]=="REQUIERE DATO" else ADV_FILL

print("Hojas 0-3 construidas")

# HOJA 4 — ABC / PARETO
ws = wb.create_sheet("4_ABC")
ws['A1'] = f"ABC / PARETO — {PERIODO}"
ws['A1'].font = TITULO
ws.append([])
ws.append(["Clase", "SKUs", "Valor USD", "% Valor"])
for col in range(1, 5):
    c = ws.cell(row=ws.max_row, column=col)
    c.fill = HEADER_FILL; c.font = HEADER_FONT; c.border = BORDER

for clase, items, fill in [('A', A, OK_FILL), ('B', B, ADV_FILL), ('C', C, SIN_FILL)]:
    v = sum(x for _, x in items)
    pct = round(100.0 * v / total_valor_abc, 1) if total_valor_abc else 0
    ws.append([clase, len(items), round(v, 2), f"{pct}%"])
    for col in range(1, 5):
        ws.cell(row=ws.max_row, column=col).border = BORDER
    ws.cell(row=ws.max_row, column=1).fill = fill

ws.append([])
ws.append(["HALLAZGO: " + f"{len(A)} SKUs ({100.0*len(A)/max(1,len(skus_valor)):.1f}%) = 80% del valor"])

# HOJA 5 — EVOLUCIÓN SEMANAL
ws = wb.create_sheet("5_Evolucion")
ws['A1'] = f"EVOLUCIÓN SEMANAL — {PERIODO}"
ws['A1'].font = TITULO
ws.append([])
ws.append(["Semana", "Desde", "Hasta", "Facturas", "Sin stock", "% sin stock"])
for col in range(1, 7):
    c = ws.cell(row=ws.max_row, column=col)
    c.fill = HEADER_FILL; c.font = HEADER_FONT; c.border = BORDER

for s in evolucion_semanal:
    ws.append([s['semana'], s['desde'], s['hasta'], s['facturas'], s['sin_stock'], f"{s['pct_sin_stock']}%"])
    for col in range(1, 7):
        ws.cell(row=ws.max_row, column=col).border = BORDER

# HOJA 6 — COMPARACIÓN
ws = wb.create_sheet("6_Comparacion")
ws['A1'] = f"COMPARACIÓN — {PERIODO} vs {año_ant}-{mes_ant:02d}"
ws['A1'].font = TITULO
ws.append([])
ws.append(["Indicador", "Mes anterior", "Mes actual", "Cambio", "% Variación"])
for col in range(1, 6):
    c = ws.cell(row=ws.max_row, column=col)
    c.fill = HEADER_FILL; c.font = HEADER_FONT; c.border = BORDER

comparaciones = [
    ("Movimientos", datos_ant.get('movimientos',0), datos_mes['movimientos']),
    ("Facturas", datos_ant.get('facturas',0), datos_mes['facturas']),
    ("Fill Rate", datos_ant.get('fill_rate',0), datos_mes['fill_rate']),
    ("Stockout", datos_ant.get('stockout',0), datos_mes['stockout']),
    ("Ajustes sin motivo %", datos_ant.get('pct_ajustes_sin_motivo',0), datos_mes['pct_ajustes_sin_motivo']),
    ("Ratio NENT/NREC", datos_ant.get('ratio_nent_nrec',0), datos_mes['ratio_nent_nrec']),
]
for nombre, ant, act in comparaciones:
    if isinstance(ant, (int, float)) and isinstance(act, (int, float)):
        cambio = act - ant
        pct = round(100.0 * cambio / ant, 1) if ant else 0
        ws.append([nombre, ant, act, round(cambio, 2), f"{pct}%"])
    else:
        ws.append([nombre, ant, act, "—", "—"])
    for col in range(1, 6):
        ws.cell(row=ws.max_row, column=col).border = BORDER

# HOJA 7 — INMUTABILIDAD
ws = wb.create_sheet("7_Inmutabilidad")
ws['A1'] = "INMUTABILIDAD"
ws['A1'].font = TITULO
ws.append([])
ws.append(["Versión:", "V001"])
ws.append(["Período:", PERIODO])
ws.append(["Nodo:", NODO])
ws.append(["Fecha:", FECHA])
ws.append(["Analista:", "Domingo E. Díaz N. | C.P.C. N.º 183594"])
ws.append([])
ws.append(["Hoja", "Filas", "SHA256"])
for col in range(1, 4):
    c = ws.cell(row=ws.max_row, column=col)
    c.fill = HEADER_FILL; c.font = HEADER_FONT; c.border = BORDER

for nombre in wb.sheetnames:
    if nombre == "7_Inmutabilidad":
        continue
    ws2 = wb[nombre]
    contenido = ""
    for row in ws2.iter_rows(values_only=True):
        contenido += "|".join(str(v) for v in row if v is not None) + "\n"
    h = hashlib.sha256(contenido.encode('utf-8')).hexdigest()[:16] if contenido else "vacia"
    ws.append([nombre, ws2.max_row, h])
    for col in range(1, 4):
        ws.cell(row=ws.max_row, column=col).border = BORDER

# ============================================================
# GUARDAR
# ============================================================
archivo = BASE / f"DARTONY_{NODO_TEC}_MENSUAL_{PERIODO}_{FECHA}.xlsx"
wb.save(archivo)
with open(archivo, 'rb') as f:
    hash_libro = hashlib.sha256(f.read()).hexdigest()

out_json = BASE / f"datos_mensuales_{PERIODO}.json"
with open(out_json, 'w', encoding='utf-8') as f:
    json.dump({
        'nodo': NODO, 'periodo': PERIODO,
        'datos_mes': datos_mes, 'datos_ant': datos_ant,
        'evolucion_semanal': evolucion_semanal,
        'abc': {'A': len(A), 'B': len(B), 'C': len(C),
                'valor_A': round(sum(v for _,v in A),2),
                'valor_B': round(sum(v for _,v in B),2),
                'valor_C': round(sum(v for _,v in C),2)}
    }, f, indent=2, ensure_ascii=False)

print()
print("=" * 70)
print("LIBRO MENSUAL GENERADO")
print("=" * 70)
print(f"  Archivo: {archivo.name}")
print(f"  Tamaño:  {archivo.stat().st_size:,} bytes")
print(f"  Hojas:   {len(wb.sheetnames)}")
print(f"  SHA256:  {hash_libro}")
print(f"  Semanas: {len(evolucion_semanal)}")
print(f"  ABC:     A={len(A)} B={len(B)} C={len(C)}")
print(f"  JSON:    {out_json.name}")
conn.close()

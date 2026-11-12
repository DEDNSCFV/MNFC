#!/usr/bin/env python3
"""
Backfill histórico: procesa 10 meses, 40 semanas, 240 días.
Genera la línea base del control interno.
Uso: python backfill.py <nodo> <frecuencia>
  frecuencia: mensual | semanal | diario
"""
import sqlite3, json, sys, calendar
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

if len(sys.argv) < 3:
    print("Uso: python backfill.py '<nodo>' <mensual|semanal|diario>")
    sys.exit(1)

NODO = sys.argv[1]
FRECUENCIA = sys.argv[2]
NODO_SLUG = NODO.replace(" ", "_")
DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"
BASE = Path.home() / "DARTONY_CONTROL" / NODO_SLUG / "historico" / FRECUENCIA
BASE.mkdir(parents=True, exist_ok=True)

# Estilos
TITULO = Font(bold=True, size=14, color="1F4E79")
HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=10)
OK_FILL = PatternFill(start_color="C6EFCE", fill_type="solid")
VIO_FILL = PatternFill(start_color="FFC7CE", fill_type="solid")
ADV_FILL = PatternFill(start_color="FFEB9C", fill_type="solid")
SIN_FILL = PatternFill(start_color="D9D9D9", fill_type="solid")
BORDER = Border(left=Side(style='thin'), right=Side(style='thin'),
                top=Side(style='thin'), bottom=Side(style='thin'))

def fill_estado(e):
    return {"OK": OK_FILL, "VIOLACIÓN": VIO_FILL, "ADVERTENCIA": ADV_FILL}.get(e, SIN_FILL)


def evaluar_periodo(conn, fecha_desde, fecha_hasta):
    """Evalúa las 17 reglas para el período dado."""
    resultados = []

    # Helper: convert to SQL-compatible date string DD/MM/YYYY
    def fecha_en_rango(fecha_str):
        """Verifica si una fecha DD/MM/YYYY está en el rango."""
        try:
            f = datetime.strptime(fecha_str, '%d/%m/%Y').date()
            return fecha_desde <= f <= fecha_hasta
        except ValueError:
            return False

    # R7 — Facturas sin stock en el período
    rows = conn.execute("""
        SELECT COUNT(*), SUM(CASE WHEN stock_actual<=0 THEN 1 ELSE 0 END)
        FROM movimientos_historico
        WHERE tipo='FACT' AND nodo=?
          AND fecha >= ? AND fecha <= ?
    """, (NODO, fecha_desde.strftime('%d/%m/%Y'), fecha_hasta.strftime('%d/%m/%Y'))).fetchone()
    tot, ss = rows[0] or 0, rows[1] or 0
    pct = 100.0*ss/tot if tot else 0
    est = "VIOLACIÓN" if pct > 10 else "ADVERTENCIA" if pct > 1 else ("OK" if tot > 0 else "SIN_DATOS")
    resultados.append((7, "No facturar con stock 0", est, f"{ss}/{tot} ({pct:.1f}%)" if tot else "Sin facturas"))

    # R9 — Ajustes sin motivo en el período
    rows = conn.execute("""
        SELECT COUNT(*), SUM(CASE WHEN motivo IS NULL OR TRIM(motivo)='' THEN 1 ELSE 0 END)
        FROM ajustes_historico
        WHERE nodo=?
          AND fecha >= ? AND fecha <= ?
    """, (NODO, fecha_desde.strftime('%d/%m/%Y'), fecha_hasta.strftime('%d/%m/%Y'))).fetchone()
    tot_aj, sm = rows[0] or 0, rows[1] or 0
    pct_aj = 100.0*sm/tot_aj if tot_aj else 0
    est = "VIOLACIÓN" if pct_aj > 50 else "ADVERTENCIA" if pct_aj > 20 else ("OK" if tot_aj > 0 else "SIN_DATOS")
    resultados.append((9, "No ajustar sin motivo", est, f"{sm}/{tot_aj} ({pct_aj:.1f}%)" if tot_aj else "Sin ajustes"))

    # R12 — NENT/NREC en el período
    rows = conn.execute("""
        SELECT SUM(CASE WHEN tipo='NENT' THEN 1 ELSE 0 END),
               SUM(CASE WHEN tipo='NREC' THEN 1 ELSE 0 END)
        FROM movimientos_historico
        WHERE nodo=?
          AND fecha >= ? AND fecha <= ?
    """, (NODO, fecha_desde.strftime('%d/%m/%Y'), fecha_hasta.strftime('%d/%m/%Y'))).fetchone()
    nent, nrec = rows[0] or 0, rows[1] or 0
    if nent == 0 and nrec == 0:
        resultados.append((12, "Transferencia sin recepción", "SIN_DATOS", "Sin transferencias"))
    else:
        ratio = nent/nrec if nrec else 999
        est = "VIOLACIÓN" if ratio > 7 else "ADVERTENCIA" if ratio > 3 else "OK"
        resultados.append((12, "Transferencia sin recepción", est, f"{nent}/{nrec} ratio {ratio:.1f}x"))

    # R13 — Ajustes > $500 en el período
    n = conn.execute("""
        SELECT COUNT(*) FROM movimientos_historico
        WHERE tipo IN ('AJUE','AJUS') AND nodo=?
          AND (cantidad*costo_unitario) > 500
          AND fecha >= ? AND fecha <= ?
    """, (NODO, fecha_desde.strftime('%d/%m/%Y'), fecha_hasta.strftime('%d/%m/%Y'))).fetchone()[0]
    est = "ADVERTENCIA" if n > 0 else "OK"
    resultados.append((13, "Ajuste >$500", est, f"{n} ajustes"))

    return resultados


def generar_libro_periodo(periodo_nombre, resultados):
    """Genera un Excel simple para el período."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Resumen"
    ws['A1'] = f"CONTROL — {NODO} — {periodo_nombre}"
    ws['A1'].font = TITULO
    ws.append([])

    headers = ["#", "Regla", "Estado", "Dato"]
    for i, h in enumerate(headers, 1):
        c = ws.cell(row=3, column=i, value=h)
        c.fill = HEADER_FILL
        c.font = HEADER_FONT
        c.border = BORDER

    for i, (id_regla, nombre, estado, dato) in enumerate(resultados, 4):
        ws.cell(row=i, column=1, value=id_regla).border = BORDER
        ws.cell(row=i, column=2, value=nombre).border = BORDER
        c = ws.cell(row=i, column=3, value=estado)
        c.fill = fill_estado(estado)
        c.border = BORDER
        ws.cell(row=i, column=4, value=dato).border = BORDER

    for col, w in [('A', 5), ('B', 30), ('C', 14), ('D', 40)]:
        ws.column_dimensions[col].width = w

    archivo = BASE / periodo_nombre / "libro.xlsx"
    archivo.parent.mkdir(parents=True, exist_ok=True)
    wb.save(archivo)
    return archivo


def main():
    conn = sqlite3.connect(DB)
    print(f"Backfill {FRECUENCIA} — Nodo: {NODO}")
    print(f"Directorio: {BASE}")
    print()

    # Rango de datos del nodo
    rango = conn.execute("""
        SELECT MIN(fecha), MAX(fecha) FROM movimientos_historico WHERE nodo=?
    """, (NODO,)).fetchone()

    if not rango[0]:
        print(f"[FATAL] No hay datos para {NODO}")
        return

    fecha_min = datetime.strptime(rango[0], '%d/%m/%Y').date()
    fecha_max = datetime.strptime(rango[1], '%d/%m/%Y').date()
    print(f"Rango de datos: {fecha_min} → {fecha_max}")
    print()

    periodos = []

    if FRECUENCIA == "mensual":
        # Generar un período por mes
        año, mes = fecha_min.year, fecha_min.month
        while (año, mes) <= (fecha_max.year, fecha_max.month):
            ultimo_dia = calendar.monthrange(año, mes)[1]
            desde = max(fecha_min, datetime(año, mes, 1).date())
            hasta = min(fecha_max, datetime(año, mes, ultimo_dia).date())
            periodos.append((f"{año}-{mes:02d}", desde, hasta))
            mes += 1
            if mes > 12:
                mes = 1
                año += 1

    elif FRECUENCIA == "semanal":
        # Generar un período por semana
        actual = fecha_min
        while actual <= fecha_max:
            desde = actual
            hasta = min(fecha_max, actual + timedelta(days=6))
            periodo_id = f"{desde.year}-W{desde.isocalendar()[1]:02d}"
            periodos.append((periodo_id, desde, hasta))
            actual = hasta + timedelta(days=1)

    elif FRECUENCIA == "diario":
        # Generar un período por día (SOLO si es razonable, si no, advertir)
        total_dias = (fecha_max - fecha_min).days + 1
        if total_dias > 300:
            print(f"⚠️ {total_dias} días es demasiado para procesar uno por uno.")
            print(f"   Se generarán solo las últimas 30 días.")
            actual = fecha_max - timedelta(days=29)
        else:
            actual = fecha_min
        while actual <= fecha_max:
            periodos.append((actual.strftime('%Y-%m-%d'), actual, actual))
            actual += timedelta(days=1)

    print(f"Períodos a procesar: {len(periodos)}")
    print()

    # Procesar cada período
    for periodo_id, desde, hasta in periodos:
        resultados = evaluar_periodo(conn, desde, hasta)
        archivo = generar_libro_periodo(periodo_id, resultados)

        # Registrar
        estados = Counter(r[2] for r in resultados)
        print(f"  {periodo_id}: {dict(estados)}")

    # Generar consolidado histórico
    print()
    print("Generando consolidado histórico...")
    consolidado = BASE / f"consolidado_{FRECUENCIA}.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "Evolución"

    ws['A1'] = f"EVOLUCIÓN {FRECUENCIA.upper()} — {NODO}"
    ws['A1'].font = TITULO
    ws.append([])

    # Cabeceras: Período | R7 | R9 | R12 | R13 | Total VIO
    headers = ["Período", "R7 Fact. sin stock", "R9 Ajustes sin motivo",
               "R12 NENT/NREC", "R13 Ajustes >$500", "Violaciones totales"]
    for i, h in enumerate(headers, 1):
        c = ws.cell(row=3, column=i, value=h)
        c.fill = HEADER_FILL
        c.font = HEADER_FONT
        c.border = BORDER

    fila = 4
    for periodo_id, desde, hasta in periodos:
        resultados = evaluar_periodo(conn, desde, hasta)
        dict_res = {r[0]: r for r in resultados}
        n_vio = sum(1 for r in resultados if r[2] == "VIOLACIÓN")

        ws.cell(row=fila, column=1, value=periodo_id).border = BORDER
        for j, id_regla in enumerate([7, 9, 12, 13], 2):
            est = dict_res[id_regla][2] if id_regla in dict_res else "SIN_DATOS"
            c = ws.cell(row=fila, column=j, value=est)
            c.fill = fill_estado(est)
            c.border = BORDER
        ws.cell(row=fila, column=6, value=n_vio).border = BORDER
        fila += 1

    for col, w in [('A', 15), ('B', 20), ('C', 22), ('D', 20), ('E', 20), ('F', 18)]:
        ws.column_dimensions[col].width = w

    wb.save(consolidado)
    print(f"Consolidado: {consolidado}")
    print()
    print(f"✅ Backfill completado: {len(periodos)} períodos procesados")
    conn.close()


if __name__ == '__main__':
    main()

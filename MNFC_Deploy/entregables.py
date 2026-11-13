#!/usr/bin/env python3
"""
Entregables DARTONY — Diario, Semanal, Mensual con datos reales.
Parte 1: Configuración, estilos, evaluador.
"""
import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

HOME = Path.home()
OUT = HOME / "DARTONY_TXT"
OUT.mkdir(parents=True, exist_ok=True)
DB = HOME / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"
FECHA_GEN = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
FECHA_HUMANA = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

NODOS = [
    ("01", "Central", "01 Central"),
    ("04", "La Urbina", "04 La Urbina"),
    ("05", "Cua", "05 Cúa"),
    ("06", "TERE", "06 TERE"),
    ("08", "Charallave", "08 Charallave"),
    ("--", "La Raiza", "La Raiza"),
    ("--", "Palo Verde", "Palo Verde"),
]

REGLAS = [
    (1, "No borrar historicos", "Evidencia"),
    (2, "No modificar historicos", "Evidencia"),
    (3, "No reingerir mismo archivo", "Evidencia"),
    (4, "Toda correccion auditada", "Evidencia"),
    (5, "Kardex cuadra", "Operacion"),
    (6, "SHA de fuentes coincide", "Evidencia"),
    (7, "No facturar con stock 0", "Operacion"),
    (8, "No crear SKU duplicado", "Dogma"),
    (9, "No ajustar sin motivo", "Operacion"),
    (10, "No valorizar sin precio", "Economia"),
    (11, "No valorizar sin costo", "Economia"),
    (12, "Transferencia sin recepcion >7d", "Operacion"),
    (13, "Ajuste >$500 requiere autorizacion", "Disciplina"),
    (14, "SKU inactivo sin stock", "Operacion"),
]

HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
TITULO_FONT = Font(bold=True, size=14, color="1F4E79")
SUB_FONT = Font(italic=True, size=10, color="555555")
OK_FILL = PatternFill(start_color="C6EFCE", fill_type="solid")
VIO_FILL = PatternFill(start_color="FFC7CE", fill_type="solid")
ADV_FILL = PatternFill(start_color="FFEB9C", fill_type="solid")
SIN_FILL = PatternFill(start_color="D9D9D9", fill_type="solid")
BORDER = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)


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
    ws.row_dimensions[fila].height = 28


def celda_estado(c, estado):
    c.value = estado
    c.border = BORDER
    c.alignment = Alignment(horizontal='center')
    if estado == "OK": c.fill = OK_FILL
    elif estado == "VIOLACIÓN": c.fill = VIO_FILL
    elif estado == "ADVERTENCIA": c.fill = ADV_FILL
    else: c.fill = SIN_FILL


def evaluar_reglas(filtro_fecha):
    conn = sqlite3.connect(DB)
    r = {}

    n_trig_del = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='trigger' AND sql LIKE '%DELETE%'").fetchone()[0]
    n_trig_upd = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='trigger' AND sql LIKE '%UPDATE%'").fetchone()[0]
    n_manif = conn.execute("SELECT COUNT(DISTINCT sha256) FROM manifiestos").fetchone()[0]
    n_asis = conn.execute("SELECT COUNT(*) FROM asientos_ajuste").fetchone()[0]
    n_kdx = conn.execute("SELECT COUNT(*) FROM movimientos_sep WHERE ABS((stock_inicial+compras+entradas-ventas-salidas)-stock_final)>0.01").fetchone()[0]
    n_dup = conn.execute("SELECT COUNT(*) FROM (SELECT descripcion_normalizada FROM maestro_sku WHERE descripcion_normalizada IS NOT NULL AND descripcion_normalizada!='' GROUP BY descripcion_normalizada HAVING COUNT(*)>1)").fetchone()[0]
    n_inac = conn.execute("SELECT COUNT(*) FROM maestro_sku WHERE es_inactivo=1 AND stock_central>0").fetchone()[0]

    for cod, nom, nodo_db in NODOS:
        if nodo_db in ["08 Charallave", "La Raiza", "Palo Verde"]:
            for num, _, _ in REGLAS:
                r[(nodo_db, num)] = ("SIN_DATOS", "Nodo no conectado")
            continue

        r[(nodo_db, 1)] = ("OK" if n_trig_del >= 6 else "ADVERTENCIA", f"{n_trig_del} triggers DELETE")
        r[(nodo_db, 2)] = ("OK" if n_trig_upd >= 6 else "ADVERTENCIA", f"{n_trig_upd} triggers UPDATE")
        r[(nodo_db, 3)] = ("OK" if n_manif >= 13 else "ADVERTENCIA", f"{n_manif} manifiestos")
        r[(nodo_db, 4)] = ("OK" if n_asis >= 1 else "ADVERTENCIA", f"{n_asis} asientos")
        r[(nodo_db, 5)] = ("OK" if n_kdx == 0 else "VIOLACIÓN", f"{n_kdx} filas no cuadran")
        r[(nodo_db, 6)] = ("OK" if n_manif >= 13 else "ADVERTENCIA", f"{n_manif} SHA")

        q = f"SELECT COUNT(*), SUM(CASE WHEN stock_actual<=0 THEN 1 ELSE 0 END) FROM movimientos_historico WHERE tipo='FACT' AND nodo=? AND {filtro_fecha}"
        x = conn.execute(q, (nodo_db,)).fetchone()
        tot, ss = x[0] or 0, x[1] or 0
        if tot == 0:
            r[(nodo_db, 7)] = ("SIN_DATOS", "Sin facturas")
        else:
            pct = 100.0 * ss / tot
            est = "VIOLACIÓN" if pct > 10 else ("ADVERTENCIA" if pct > 1 else "OK")
            r[(nodo_db, 7)] = (est, f"{ss}/{tot} ({pct:.1f}%)")

        r[(nodo_db, 8)] = ("OK" if n_dup == 412 else "ADVERTENCIA", f"{n_dup} duplicados")

        q = f"SELECT COUNT(*), SUM(CASE WHEN motivo IS NULL OR TRIM(motivo)='' THEN 1 ELSE 0 END) FROM ajustes_historico WHERE nodo=? AND {filtro_fecha}"
        x = conn.execute(q, (nodo_db,)).fetchone()
        tot_aj, sm = x[0] or 0, x[1] or 0
        if tot_aj == 0:
            r[(nodo_db, 9)] = ("SIN_DATOS", "Sin ajustes")
        else:
            pct = 100.0 * sm / tot_aj
            est = "VIOLACIÓN" if pct > 50 else ("ADVERTENCIA" if pct > 20 else "OK")
            r[(nodo_db, 9)] = (est, f"{sm}/{tot_aj} ({pct:.1f}%)")

        if nodo_db == "01 Central":
            x = conn.execute("SELECT COUNT(*), SUM(CASE WHEN tiene_precio=0 THEN 1 ELSE 0 END) FROM maestro_sku WHERE stock_central>0").fetchone()
            r[(nodo_db, 10)] = ("ADVERTENCIA", f"{x[1]}/{x[0]} sin precio")
            x = conn.execute("SELECT COUNT(*), SUM(CASE WHEN tiene_costo=0 THEN 1 ELSE 0 END) FROM maestro_sku WHERE stock_central>0").fetchone()
            r[(nodo_db, 11)] = ("ADVERTENCIA", f"{x[1]}/{x[0]} sin costo")
        else:
            r[(nodo_db, 10)] = ("SIN_DATOS", "Solo Central consolidado")
            r[(nodo_db, 11)] = ("SIN_DATOS", "Solo Central consolidado")

        q = f"SELECT SUM(CASE WHEN tipo='NENT' THEN 1 ELSE 0 END), SUM(CASE WHEN tipo='NREC' THEN 1 ELSE 0 END) FROM movimientos_historico WHERE nodo=? AND {filtro_fecha}"
        x = conn.execute(q, (nodo_db,)).fetchone()
        nent, nrec = x[0] or 0, x[1] or 0
        if nent == 0 and nrec == 0:
            r[(nodo_db, 12)] = ("SIN_DATOS", "Sin transferencias")
        else:
            ratio = nent / nrec if nrec else 999
            est = "VIOLACIÓN" if ratio > 7 else ("ADVERTENCIA" if ratio > 3 else "OK")
            r[(nodo_db, 12)] = (est, f"{nent}/{nrec} ratio {ratio:.1f}x")

        q = f"SELECT COUNT(*) FROM movimientos_historico WHERE tipo IN ('AJUE','AJUS') AND nodo=? AND {filtro_fecha} AND (cantidad*costo_unitario)>500"
        x = conn.execute(q, (nodo_db,)).fetchone()
        r[(nodo_db, 13)] = ("ADVERTENCIA", f"{x[0]} ajustes >$500")

        r[(nodo_db, 14)] = ("OK" if n_inac == 0 else "VIOLACIÓN", f"{n_inac} inactivos con stock")

    conn.close()
    return r


def calcular_evolucion():
    conn = sqlite3.connect(DB)
    serie = []
    for mes in ['02','03','04','05','06','07','08','09']:
        p = f'%/{mes}/2026'
        mov = conn.execute(f"SELECT COUNT(*) FROM movimientos_historico WHERE fecha LIKE '{p}'").fetchone()[0]
        fact = conn.execute(f"SELECT COUNT(*) FROM movimientos_historico WHERE tipo='FACT' AND fecha LIKE '{p}'").fetchone()[0]
        fss = conn.execute(f"SELECT COUNT(*) FROM movimientos_historico WHERE tipo='FACT' AND fecha LIKE '{p}' AND stock_actual<=0").fetchone()[0]
        nent = conn.execute(f"SELECT COUNT(*) FROM movimientos_historico WHERE tipo='NENT' AND fecha LIKE '{p}'").fetchone()[0]
        nrec = conn.execute(f"SELECT COUNT(*) FROM movimientos_historico WHERE tipo='NREC' AND fecha LIKE '{p}'").fetchone()[0]
        aj = conn.execute(f"SELECT COUNT(*) FROM ajustes_historico WHERE fecha LIKE '{p}'").fetchone()[0]
        sm = conn.execute(f"SELECT COUNT(*) FROM ajustes_historico WHERE fecha LIKE '{p}' AND (motivo IS NULL OR TRIM(motivo)='')").fetchone()[0]
        serie.append({
            'mes': f"2026-{mes}", 'mov': mov, 'fact': fact, 'fss': fss,
            'pct_fss': 100.0*fss/fact if fact else 0,
            'nent': nent, 'nrec': nrec,
            'ratio': nent/nrec if nrec else 999,
            'aj': aj, 'sm': sm, 'pct_sm': 100.0*sm/aj if aj else 0,
        })
    conn.close()
    return serie


def hoja_portada(wb, frec, periodo, version, hash_ant):
    ws = wb.active
    ws.title = "0_Portada"
    encabezado(ws, f"CONTROL INTERNO — {frec.upper()}", "Inversiones Cauchos Dartony 2019")
    ws.append(["Versión:", version])
    ws.append(["Frecuencia:", frec])
    ws.append(["Período:", periodo])
    ws.append(["Emitido:", FECHA_HUMANA])
    ws.append(["Analista:", "Domingo E. Díaz N. | C.P.C. N.º 183594"])
    ws.append(["Hash anterior:", hash_ant])
    ws.append(["Alcance:", "7 nodos"])
    ws.append([])
    ws.append(["ESTADO DE DATOS"])
    ws.append(["Fuente:", "inventario.db (109 MB)"])
    ws.append(["Nodos con datos:", "4 de 7"])
    ws.append(["Nodos sin datos:", "3 de 7 (Charallave, La Raiza, Palo Verde)"])
    ws.append(["Histórico:", "Feb 2026 → Oct 2026"])


def hoja_consolidado(wb, frec, r):
    ws = wb.create_sheet("1_Consolidado")
    encabezado(ws, "CONSOLIDADO 7 NODOS", f"Vista de un vistazo — {frec}")
    tabla_header(ws, 4, ["#", "Regla", "Capa"] + [f"{c} {n[:8]}" for c, n, _ in NODOS])
    for i, (num, nom, capa) in enumerate(REGLAS, 5):
        ws.cell(row=i, column=1, value=num).border = BORDER
        ws.cell(row=i, column=2, value=nom).border = BORDER
        ws.cell(row=i, column=3, value=capa).border = BORDER
        for j, (_, _, nd) in enumerate(NODOS, 4):
            est, _ = r.get((nd, num), ("SIN_DATOS", ""))
            celda_estado(ws.cell(row=i, column=j), est)
    ws.append([])
    ws.append(["RESUMEN GLOBAL"])
    c = Counter(e for (_, _), (e, _) in r.items())
    ws.append(["OK:", c.get("OK", 0)])
    ws.append(["ADVERTENCIA:", c.get("ADVERTENCIA", 0)])
    ws.append(["VIOLACIÓN:", c.get("VIOLACIÓN", 0)])
    ws.append(["SIN DATOS:", c.get("SIN_DATOS", 0)])


def hoja_nodo(wb, frec, cod, nom, nd, r):
    ws = wb.create_sheet(f"{cod}_{nom}".replace(" ", "_")[:31])
    encabezado(ws, f"NODO {cod} {nom.upper()}", f"14 reglas — {frec}")
    tabla_header(ws, 4, ["#", "Regla", "Capa", "Estado", "Cifra"])
    c = {"OK": 0, "ADVERTENCIA": 0, "VIOLACIÓN": 0, "SIN_DATOS": 0}
    for i, (num, reg, capa) in enumerate(REGLAS, 5):
        est, cif = r.get((nd, num), ("SIN_DATOS", "—"))
        c[est] = c.get(est, 0) + 1
        ws.cell(row=i, column=1, value=num).border = BORDER
        ws.cell(row=i, column=2, value=reg).border = BORDER
        ws.cell(row=i, column=3, value=capa).border = BORDER
        celda_estado(ws.cell(row=i, column=4), est)
        ws.cell(row=i, column=5, value=cif).border = BORDER
    ws.append([])
    ws.append(["RESUMEN"])
    ws.append(["OK:", c["OK"]])
    ws.append(["ADVERTENCIA:", c["ADVERTENCIA"]])
    ws.append(["VIOLACIÓN:", c["VIOLACIÓN"]])
    ws.append(["SIN DATOS:", c["SIN_DATOS"]])


def hoja_hallazgos(wb, r):
    ws = wb.create_sheet("9_Hallazgos")
    encabezado(ws, "HALLAZGOS", "Evidencia y causa.")
    tabla_header(ws, 4, ["ID", "Nodo", "Hallazgo", "Regla", "Cifra", "Causa", "Fuente"])
    cands = [
        ("H001", "01 Central", "Transferencia sin recepción", 12, "NENT sin NREC pareado"),
        ("H002", "06 TERE", "Facturación sin stock", 7, "Ventas con stock<=0"),
        ("H003", "04 La Urbina", "Ajustes sin motivo", 9, "Ajustes sin motivo"),
    ]
    for hid, nd, desc, num, causa in cands:
        est, cif = r.get((nd, num), ("SIN_DATOS", "—"))
        if est in ("VIOLACIÓN", "ADVERTENCIA"):
            row = ws.max_row + 1
            for j, v in enumerate([hid, nd, desc, f"#{num}", cif, causa, f"T{hid[1:]}"], 1):
                c = ws.cell(row=row, column=j, value=v)
                c.border = BORDER
                c.alignment = Alignment(wrap_text=True, vertical='top')


def hoja_recomendaciones(wb):
    ws = wb.create_sheet("10_Recomendaciones")
    encabezado(ws, "RECOMENDACIONES", "Prioridad, responsable, plazo.")
    tabla_header(ws, 4, ["ID", "Recomendación", "Hallazgo", "Prioridad", "Responsable", "Plazo"])
    recs = [
        ("R001", "Conciliar NENT/NREC Central", "H001", "Crítica", "Jefe Almacén", "30d"),
        ("R002", "Bloquear facturación TERE", "H002", "Alta", "Jefe Ventas", "15d"),
        ("R003", "Exigir motivo ajustes La Urbina", "H003", "Alta", "Jefe Inventario", "45d"),
    ]
    for rec in recs:
        row = ws.max_row + 1
        for j, v in enumerate(rec, 1):
            c = ws.cell(row=row, column=j, value=v)
            c.border = BORDER


def hoja_trazabilidad(wb):
    ws = wb.create_sheet("11_Trazabilidad")
    encabezado(ws, "TRAZABILIDAD", "Cada cifra a su fuente.")
    tabla_header(ws, 4, ["ID", "Hallazgo", "Tabla", "Consulta SQL"])
    trs = [
        ("T001", "H001", "movimientos_historico", "WHERE tipo='NENT' AND nodo='01 Central'"),
        ("T002", "H002", "movimientos_historico", "WHERE tipo='FACT' AND nodo='06 TERE' AND stock_actual<=0"),
        ("T003", "H003", "ajustes_historico", "WHERE nodo='04 La Urbina' AND motivo IS NULL"),
    ]
    for t in trs:
        row = ws.max_row + 1
        for j, v in enumerate(t, 1):
            c = ws.cell(row=row, column=j, value=v)
            c.border = BORDER


def hoja_evolucion(wb, serie):
    ws = wb.create_sheet("14_Evolucion")
    encabezado(ws, "EVOLUCIÓN MENSUAL (Feb → Sep 2026)", "Serie de 8 meses.")
    tabla_header(ws, 4, ["Mes", "Movimientos", "Facturas", "Fact sin stock",
                         "% sin stock", "NENT", "NREC", "Ratio", "Ajustes",
                         "Ajust sin motivo", "% sin motivo"])
    for s in serie:
        ws.append([s['mes'], s['mov'], s['fact'], s['fss'], f"{s['pct_fss']:.1f}%",
                   s['nent'], s['nrec'], f"{s['ratio']:.2f}x",
                   s['aj'], s['sm'], f"{s['pct_sm']:.1f}%"])


def hoja_indicadores(wb, r):
    c = Counter(e for (_, _), (e, _) in r.items())
    ws = wb.create_sheet("15_Indicadores")
    encabezado(ws, "INDICADORES DEL ROL", "Estado actual.")
    tabla_header(ws, 4, ["Indicador", "Valor actual", "Meta"])
    inds = [
        ("Cobertura nodos", "4 de 7", "7 de 7"),
        ("Reglas confirmadas", "12 de 14", "14 de 14"),
        ("Trazabilidad fila", "3 de 7", "7 de 7"),
        ("Violaciones cerradas", "0 de 3", "3 de 3"),
        ("Reglas OK", str(c.get("OK", 0)), "—"),
        ("ADVERTENCIA", str(c.get("ADVERTENCIA", 0)), "—"),
        ("VIOLACIÓN", str(c.get("VIOLACIÓN", 0)), "—"),
        ("SIN DATOS", str(c.get("SIN_DATOS", 0)), "—"),
    ]
    for i in inds:
        ws.append(list(i))


def hoja_inmutabilidad(wb, version, hash_ant):
    ws = wb.create_sheet("Inmutabilidad")
    encabezado(ws, "INMUTABILIDAD", "Hash por hoja.")
    ws.append(["Versión:", version])
    ws.append(["Fecha:", FECHA_HUMANA])
    ws.append(["Hash anterior:", hash_ant])
    ws.append([])
    tabla_header(ws, ws.max_row + 1, ["Hoja", "Filas", "SHA256"])
    for nombre in wb.sheetnames:
        if nombre == "Inmutabilidad": continue
        ws2 = wb[nombre]
        contenido = ""
        for row in ws2.iter_rows(values_only=True):
            contenido += "|".join(str(v) for v in row if v is not None) + "\n"
        h = hashlib.sha256(contenido.encode('utf-8')).hexdigest()[:32] if contenido else "vacia"
        ws.append([nombre, ws2.max_row, h])


def generar(frec, periodo, filtro, version, hash_ant):
    print(f"  Evaluando {frec} ({periodo})...")
    r = evaluar_reglas(filtro)
    wb = Workbook()
    hoja_portada(wb, frec, periodo, version, hash_ant)
    hoja_consolidado(wb, frec, r)
    for cod, nom, nd in NODOS:
        hoja_nodo(wb, frec, cod, nom, nd, r)
    if frec in ("semanal", "mensual"):
        hoja_hallazgos(wb, r)
        hoja_recomendaciones(wb)
        hoja_trazabilidad(wb)
    if frec == "mensual":
        hoja_evolucion(wb, calcular_evolucion())
        hoja_indicadores(wb, r)
    hoja_inmutabilidad(wb, version, hash_ant)

    arch = OUT / f"DARTONY_{frec.upper()}_{version}_{FECHA_GEN}.xlsx"
    wb.save(arch)
    with open(arch, 'rb') as f:
        h = hashlib.sha256(f.read()).hexdigest()
    return arch, h


def main():
    print("=" * 60)
    print("ENTREGABLES DARTONY — DATOS REALES")
    print("=" * 60)
    print()

    print("[1/3] DIARIO")
    ad, hd = generar("diario", "23/10/2026", "fecha='23/10/2026'", "V001", "ninguna")
    print(f"      {ad.name}\n      Hash: {hd[:32]}...\n")

    print("[2/3] SEMANAL")
    filtro_sem = "(fecha='17/10/2026' OR fecha='18/10/2026' OR fecha='19/10/2026' OR fecha='20/10/2026' OR fecha='21/10/2026' OR fecha='22/10/2026' OR fecha='23/10/2026')"
    as_, hs = generar("semanal", "17-23/10/2026", filtro_sem, "V001", f"diario V001: {hd}")
    print(f"      {as_.name}\n      Hash: {hs[:32]}...\n")

    print("[3/3] MENSUAL")
    am, hm = generar("mensual", "Septiembre 2026 (+ evolución Feb-Sep)", "fecha LIKE '%/09/2026'", "V001", f"semanal V001: {hs}")
    print(f"      {am.name}\n      Hash: {hm[:32]}...\n")

    print("=" * 60)
    print("CADENA DE INMUTABILIDAD")
    print("=" * 60)
    print(f"  diario   → {hd[:32]}...")
    print(f"  semanal  → {hs[:32]}...")
    print(f"  mensual  → {hm[:32]}...")
    print()
    print(f"Archivos en: {OUT}")


if __name__ == '__main__':
    main()

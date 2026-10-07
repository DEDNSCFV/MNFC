"""
MNFC v0.2.0 - Capa 7 - Reportes desde StoreBase.

Genera archivos en libros/ (o en output_dir) y devuelve la ruta.

Funciones puras respecto al almacenamiento: reciben un StoreBase y
producen archivos. No dependen de la implementacion concreta
(SQLite o JSON) del almacenamiento.

Migrado de SCFV_DSR/scfv_dsr/contable/reportes_motor.py.
Adaptado para usar StoreBase en lugar de leer SQLite directamente.
"""

import csv
import calendar
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from .persistencia.base import StoreBase


def _timestamp_rango(periodo_id):
    """periodo_id = YYYY-MM -> (inicio_unix, fin_unix)."""
    año, mes = map(int, periodo_id.split("-"))
    inicio = int(datetime(año, mes, 1).timestamp())
    ultimo_dia = calendar.monthrange(año, mes)[1]
    fin = int(datetime(año, mes, ultimo_dia, 23, 59, 59).timestamp())
    return inicio, fin


def _leer_asientos(store, periodo_id):
    """Devuelve payloads dict de ASIENTO_REGISTRADO del periodo."""
    inicio, fin = _timestamp_rango(periodo_id)
    todos = store.obtener_por_tipo("ASIENTO_REGISTRADO")
    filtrados = [
        e["payload"] for e in todos
        if inicio <= e["timestamp"] <= fin and isinstance(e["payload"], dict)
    ]
    filtrados.sort(key=lambda a: a.get("timestamp", 0))
    return filtrados


def _saldos_mayor(asientos):
    """Agrega DEBE (+) y HABER (-) por cuenta."""
    saldos = {}
    for a in asientos:
        for p in a.get("partidas", []):
            cuenta = p.get("cuenta_codigo", "?")
            monto = float(p.get("monto", 0))
            signo = +1 if p.get("ubicacion") == "DEBE" else -1
            saldos[cuenta] = saldos.get(cuenta, 0.0) + signo * monto
    return saldos


def _directorio_salida(output_dir="libros"):
    d = Path(output_dir)
    d.mkdir(parents=True, exist_ok=True)
    return d


def generar_csv_diario(store, periodo_id, output_dir="libros"):
    """Genera el libro diario en CSV. Devuelve la ruta del archivo."""
    asientos = _leer_asientos(store, periodo_id)
    archivo = _directorio_salida(output_dir) / ("motor_diario_%s.csv" % periodo_id)
    with open(archivo, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Asiento ID", "Fecha", "Periodo",
                    "Total Debe", "Total Haber", "Correlation ID"])
        for a in asientos:
            w.writerow([
                a.get("id", ""),
                a.get("fecha", ""),
                a.get("periodo_id", ""),
                a.get("total_debe", 0),
                a.get("total_haber", 0),
                a.get("correlation_id", ""),
            ])
    return str(archivo)


def generar_csv_mayor(store, periodo_id, output_dir="libros"):
    """Genera el mayor por cuenta en CSV. Devuelve la ruta del archivo."""
    saldos = _saldos_mayor(_leer_asientos(store, periodo_id))
    archivo = _directorio_salida(output_dir) / ("motor_mayor_%s.csv" % periodo_id)
    with open(archivo, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Cuenta", "Saldo"])
        for cuenta in sorted(saldos.keys()):
            w.writerow([cuenta, saldos[cuenta]])
    return str(archivo)


def generar_csv_balance(store, periodo_id, output_dir="libros"):
    """
    Genera un balance por rubros en CSV.

    Clasificacion por primer digito del codigo de cuenta:
        1xxx -> ACTIVO
        2xxx -> PASIVO
        3xxx -> CAPITAL
        4xxx -> INGRESOS
        5xxx -> GASTOS
    """
    saldos = _saldos_mayor(_leer_asientos(store, periodo_id))

    activo = 0.0
    pasivo = 0.0
    capital = 0.0
    ingresos = 0.0
    gastos = 0.0

    for cuenta, saldo in saldos.items():
        if cuenta.startswith("1"):
            activo += saldo
        elif cuenta.startswith("2"):
            pasivo += saldo
        elif cuenta.startswith("3"):
            capital += saldo
        elif cuenta.startswith("4"):
            ingresos += saldo
        elif cuenta.startswith("5"):
            gastos += saldo

    archivo = _directorio_salida(output_dir) / ("motor_balance_%s.csv" % periodo_id)
    with open(archivo, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Rubro", "Saldo"])
        w.writerow(["ACTIVO", activo])
        w.writerow(["PASIVO", pasivo])
        w.writerow(["CAPITAL", capital])
        w.writerow(["INGRESOS", ingresos])
        w.writerow(["GASTOS", gastos])
        w.writerow(["RESULTADO", ingresos - gastos])
        w.writerow(["TOTAL ACTIVO", activo])
        w.writerow(["TOTAL PASIVO + CAPITAL + RESULTADO",
                    pasivo + capital + (ingresos - gastos)])
    return str(archivo)


def generar_pdf_diario(store, periodo_id, output_dir="libros"):
    """
    Genera el libro diario en PDF. Requiere la dependencia opcional fpdf.

    Si no esta instalada, lanza RuntimeError con mensaje explicito.
    """
    try:
        from fpdf import FPDF
    except ImportError:
        raise RuntimeError(
            "fpdf no instalado. Ejecutar: pip install fpdf"
        )

    asientos = _leer_asientos(store, periodo_id)
    archivo = _directorio_salida(output_dir) / ("motor_diario_%s.pdf" % periodo_id)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Libro Diario - %s" % periodo_id, ln=True, align="C")
    pdf.ln(5)
    pdf.cell(60, 8, "Asiento ID", 1)
    pdf.cell(30, 8, "Fecha", 1)
    pdf.cell(35, 8, "Total Debe", 1)
    pdf.cell(35, 8, "Total Haber", 1)
    pdf.ln()
    for a in asientos:
        pdf.cell(60, 6, str(a.get("id", ""))[:20], 1)
        pdf.cell(30, 6, str(a.get("fecha", "")), 1)
        pdf.cell(35, 6, str(a.get("total_debe", 0)), 1)
        pdf.cell(35, 6, str(a.get("total_haber", 0)), 1)
        pdf.ln()
    pdf.output(str(archivo))
    return str(archivo)

#!/usr/bin/env python3
"""
MNFC - CLI profesional con argparse.
Uso:
  mnfc version
  mnfc audit --detal 05_cua
  mnfc audit --consolidado
  mnfc contabilidad --detal 05_cua
  mnfc contabilidad --detal 05_cua --rebuild
  mnfc contabilidad --consolidado
  mnfc kpis
  mnfc autoauditoria
  mnfc resumen
"""
import argparse
import sys
import os
import subprocess
import sqlite3
from pathlib import Path

VERSION = "0.6.0-cli"
DETALES = ["04_la_urbina", "05_cua", "06_tere", "07_la_raiza", "07_palo_verde", "08_charallave"]
BASE = Path(__file__).parent


def cargar_config():
    import json
    try:
        with open(BASE / "config.json") as f:
            return json.load(f)
    except Exception:
        return {"db_path": "nodo_principal_cliente.db"}


def _run(script_name, args=None):
    script = BASE / script_name
    if not script.exists():
        print(f"[ERROR] No existe {script_name}", file=sys.stderr)
        sys.exit(1)
    cmd = [sys.executable, str(script)] + (args or [])
    try:
        subprocess.run(cmd, check=True, cwd=str(BASE))
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {script_name} codigo {e.returncode}", file=sys.stderr)
        sys.exit(e.returncode)


def cmd_version(args):
    config = cargar_config()
    print(f"MNFC v{VERSION}")
    print(f"Base de datos: {config.get('db_path', '?')}")
    db = BASE / config.get("db_path", "")
    if db.exists():
        con = sqlite3.connect(str(db))
        n = con.execute("SELECT COUNT(*) FROM inventario_nodo").fetchone()[0]
        a = con.execute("SELECT COUNT(*) FROM libro_diario").fetchone()[0]
        con.close()
        print(f"SKUs en inventario: {n:,}")
        print(f"Lineas en libro_diario: {a:,}")
    print(f"Detalles disponibles: {', '.join(DETALES)}")


def cmd_audit(args):
    _run("auditoria_360.py", [args.detal] if args.detal else None)


def cmd_contabilidad(args):
    args_script = []
    if args.detal:
        args_script.append(args.detal)
    if getattr(args, "rebuild", False):
        args_script.append("--rebuild")
    _run("contabilidad_perpetua.py", args_script if args_script else None)


def cmd_kpis(args):
    _run("kpis_hallazgos.py")


def cmd_autoauditoria(args):
    _run("autoauditoria.py")


def cmd_resumen(args):
    config = cargar_config()
    db = BASE / config.get("db_path", "")
    if not db.exists():
        print(f"[ERROR] No existe {db}", file=sys.stderr)
        sys.exit(1)
    con = sqlite3.connect(str(db))
    print("=" * 78)
    print(" MNFC - RESUMEN POR DETAL")
    print("=" * 78)
    print(f"{'DETAL':<20} | {'ASIENTOS':>9} | {'INGRESOS':>13} | {'UTILIDAD':>13}")
    print("-" * 78)
    total_det = 0
    for detal in DETALES:
        row = con.execute("""
            SELECT
                (SELECT COUNT(*) FROM libro_diario WHERE detal = ?) / 5,
                COALESCE((SELECT SUM(haber_cent) FROM libro_diario WHERE detal = ? AND cuenta_codigo = '4101'), 0),
                COALESCE((SELECT SUM(haber_cent) FROM libro_diario WHERE detal = ? AND cuenta_codigo = '4101'), 0)
                - COALESCE((SELECT SUM(debe_cent) FROM libro_diario WHERE detal = ? AND cuenta_codigo = '5101'), 0)
        """, (detal, detal, detal, detal)).fetchone()
        if row[0] > 0:
            print(f"{detal:<20} | {row[0]:>9,} | ${row[1]/100:>12,.2f} | ${row[2]/100:>12,.2f}")
            total_det += 1
    if total_det == 0:
        print("  (Sin contabilidad calculada. Ejecuta: mnfc contabilidad --consolidado)")
    print("=" * 78)
    con.close()


def main():
    parser = argparse.ArgumentParser(prog="mnfc", description="MNFC - Auditoria forense de inventario")
    parser.add_argument("--version", action="version", version=f"mnfc {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("version", help="Version y estado del motor")
    p.set_defaults(func=cmd_version)

    p = sub.add_parser("audit", help="Auditoria 360 (KPIs + COSO + FODA + 5S)")
    p.add_argument("--detal", choices=DETALES, help="Detal especifico")
    p.add_argument("--consolidado", action="store_true", help="Consolidado")
    p.set_defaults(func=cmd_audit)

    p = sub.add_parser("contabilidad", help="Contabilidad perpetua")
    p.add_argument("--detal", choices=DETALES, help="Detal especifico")
    p.add_argument("--consolidado", action="store_true", help="Consolidado")
    p.add_argument("--rebuild", action="store_true", help="Forzar recalculo (borra y reescribe)")
    p.set_defaults(func=cmd_contabilidad)

    p = sub.add_parser("kpis", help="KPIs y hallazgos automaticos")
    p.set_defaults(func=cmd_kpis)

    p = sub.add_parser("autoauditoria", help="Autoauditoria del motor")
    p.set_defaults(func=cmd_autoauditoria)

    p = sub.add_parser("resumen", help="Resumen rapido por detal")
    p.set_defaults(func=cmd_resumen)

    args = parser.parse_args()
    if hasattr(args, "consolidado") and args.consolidado:
        args.detal = None
    args.func(args)


if __name__ == "__main__":
    main()

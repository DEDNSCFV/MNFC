#!/usr/bin/env python3
"""Migra datos existentes: monto float -> monto_cent int.

Uso:
    python migrar_monto_a_cent.py <ruta.db>            # dry-run
    python migrar_monto_a_cent.py <ruta.db> --aplicar  # aplica + backup

Idempotente: si el payload ya tiene monto_cent, no toca nada.
Backup previo: <db>.bak_<timestamp>.
"""
import sqlite3
import shutil
import sys
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


def backup(db: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = db.with_name(f"{db.name}.bak_{ts}")
    shutil.copy2(db, bak)
    print(f"📦 Backup: {bak}")
    return bak


def convertir_linea(linea: dict) -> tuple[dict, bool]:
    """Convierte linea.monto (float) a linea.monto_cent (int)."""
    if "monto_cent" in linea:
        return linea, False
    if "monto" not in linea:
        return linea, False
    try:
        cent = int((Decimal(str(linea["monto"])) * 100).quantize(Decimal("1")))
    except (InvalidOperation, ValueError):
        return linea, False
    nueva = dict(linea)
    nueva["monto_cent"] = cent
    del nueva["monto"]
    return nueva, True


def convertir_payload(payload: dict) -> tuple[dict, int]:
    """Convierte un payload completo. Retorna (payload_nuevo, n_lineas_migradas)."""
    if not isinstance(payload, dict):
        return payload, 0
    if "partidas" not in payload:
        return payload, 0
    nuevo = dict(payload)
    lineas_nuevas = []
    n = 0
    for linea in nuevo["partidas"]:
        linea_nueva, cambio = convertir_linea(linea)
        lineas_nuevas.append(linea_nueva)
        if cambio:
            n += 1
    nuevo["partidas"] = lineas_nuevas

    # También migrar total_debe / total_haber si son float
    for campo in ("total_debe", "total_haber"):
        campo_cent = campo + "_cent"
        if campo_cent not in nuevo and campo in nuevo:
            try:
                nuevo[campo_cent] = int(
                    (Decimal(str(nuevo[campo])) * 100).quantize(Decimal("1"))
                )
            except (InvalidOperation, ValueError):
                pass

    return nuevo, n


def migrar(db: Path, dry_run: bool = True) -> None:
    con = sqlite3.connect(db)
    cur = con.cursor()
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tablas = [r[0] for r in cur.fetchall()]
    except sqlite3.DatabaseError as e:
        print(f"❌ No es BD SQLite válida: {e}")
        con.close()
        return

    total_filas = 0
    total_lineas = 0

    for tabla in tablas:
        if not tabla.startswith(("evento", "asiento", "ASIENTO")):
            continue
        try:
            cur.execute(f"SELECT rowid, payload FROM {tabla}")
        except sqlite3.OperationalError:
            continue
        filas = cur.fetchall()
        for rowid, payload_txt in filas:
            try:
                payload = json.loads(payload_txt) if isinstance(payload_txt, str) else payload_txt
            except (json.JSONDecodeError, TypeError):
                continue
            nuevo, n = convertir_payload(payload)
            if n > 0:
                total_filas += 1
                total_lineas += n
                if not dry_run:
                    nuevo_txt = json.dumps(nuevo, ensure_ascii=False)
                    cur.execute(
                        f"UPDATE {tabla} SET payload = ? WHERE rowid = ?",
                        (nuevo_txt, rowid),
                    )

    if not dry_run:
        con.commit()
        print(f"✅ Migradas {total_filas} filas, {total_lineas} líneas")
    else:
        print(f"🔍 DRY RUN: {total_filas} filas, {total_lineas} líneas a migrar")
        print("   Ejecutá con --aplicar para migrar.")

    con.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python migrar_monto_a_cent.py <ruta.db> [--aplicar]")
        sys.exit(1)
    db = Path(sys.argv[1]).expanduser()
    if not db.exists():
        print(f"❌ No existe: {db}")
        sys.exit(1)
    aplicar = "--aplicar" in sys.argv
    if aplicar:
        backup(db)
    migrar(db, dry_run=not aplicar)

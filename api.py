"""
MNFC - API REST con Flask.
Expone el motor como API JSON para integraciones.

Uso:
  python api.py
  curl http://localhost:5000/api/version
  curl http://localhost:5000/api/resumen
  curl http://localhost:5000/api/balance/05_cua
"""
import json
import os
import sqlite3
from flask import Flask, jsonify, request
from pathlib import Path

BASE = Path(__file__).parent
try:
    with open(BASE / "config.json") as f:
        CONFIG = json.load(f)
except Exception:
    CONFIG = {"db_path": "nodo_principal_cliente.db"}

DB_PATH = BASE / CONFIG.get("db_path", "nodo_principal_cliente.db")
DETALES = CONFIG.get("detalles_disponibles", [])
APP_VERSION = "0.7.0-api"

app = Flask(__name__)


def get_db():
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    return con


# ═══════════════════════════════════════════════════════════════════
# HEALTH & VERSION
# ═══════════════════════════════════════════════════════════════════
@app.route("/api/health", methods=["GET"])
def health():
    try:
        con = get_db()
        con.execute("SELECT 1")
        con.close()
        return jsonify({"status": "ok", "db": str(DB_PATH.name)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/version", methods=["GET"])
def version():
    con = get_db()
    skus = con.execute("SELECT COUNT(*) FROM inventario_nodo").fetchone()[0]
    asientos = con.execute("SELECT COUNT(*) FROM libro_diario").fetchone()[0]
    con.close()
    return jsonify({
        "version": APP_VERSION,
        "db_path": str(DB_PATH.name),
        "cliente": CONFIG.get("cliente_activo", "?"),
        "skus": skus,
        "asientos": asientos,
        "detalles_disponibles": DETALES,
        "detalles_pendientes": CONFIG.get("detalles_pendientes", []),
    })


# ═══════════════════════════════════════════════════════════════════
# RESUMEN
# ═══════════════════════════════════════════════════════════════════
@app.route("/api/resumen", methods=["GET"])
def resumen():
    con = get_db()
    out = []
    for detal in DETALES:
        row = con.execute("""
            SELECT
                (SELECT COUNT(*) FROM libro_diario WHERE detal = ?) / 5,
                COALESCE((SELECT SUM(haber_cent) FROM libro_diario WHERE detal = ? AND cuenta_codigo = '4101'), 0),
                COALESCE((SELECT SUM(debe_cent) FROM libro_diario WHERE detal = ? AND cuenta_codigo = '5101'), 0)
        """, (detal, detal, detal)).fetchone()
        asientos, ingresos, costos = row[0], row[1], row[2]
        out.append({
            "detal": detal,
            "asientos": asientos,
            "ingresos_cent": ingresos,
            "ingresos": ingresos / 100,
            "costos_cent": costos,
            "costos": costos / 100,
            "utilidad": (ingresos - costos) / 100,
        })
    con.close()
    return jsonify({"detalles": out})


# ═══════════════════════════════════════════════════════════════════
# BALANCE POR DETAL
# ═══════════════════════════════════════════════════════════════════
@app.route("/api/balance/<detal>", methods=["GET"])
def balance(detal):
    if detal not in DETALES:
        return jsonify({"error": f"detal no valido: {detal}", "validos": DETALES}), 400
    con = get_db()
    rows = con.execute("""
        SELECT pc.codigo, pc.nombre, pc.tipo,
               COALESCE(SUM(ld.debe_cent), 0) as debe,
               COALESCE(SUM(ld.haber_cent), 0) as haber
        FROM plan_cuentas pc
        LEFT JOIN libro_diario ld ON ld.cuenta_codigo = pc.codigo AND ld.detal = ?
        GROUP BY pc.codigo
        HAVING debe > 0 OR haber > 0
        ORDER BY pc.codigo
    """, (detal,)).fetchall()
    con.close()

    cuentas = [{
        "codigo": r["codigo"],
        "nombre": r["nombre"],
        "tipo": r["tipo"],
        "debe": r["debe"] / 100,
        "haber": r["haber"] / 100,
    } for r in rows]

    total_debe = sum(c["debe"] for c in cuentas)
    total_haber = sum(c["haber"] for c in cuentas)

    return jsonify({
        "detal": detal,
        "cuentas": cuentas,
        "total_debe": total_debe,
        "total_haber": total_haber,
        "partida_doble_ok": abs(total_debe - total_haber) < 0.01,
    })


# ═══════════════════════════════════════════════════════════════════
# ESTADO DE RESULTADOS POR DETAL
# ═══════════════════════════════════════════════════════════════════
@app.route("/api/resultados/<detal>", methods=["GET"])
def resultados(detal):
    if detal not in DETALES:
        return jsonify({"error": f"detal no valido: {detal}"}), 400
    con = get_db()
    rows = con.execute("""
        SELECT pc.codigo, pc.nombre, pc.tipo,
               COALESCE(SUM(ld.debe_cent), 0) as debe,
               COALESCE(SUM(ld.haber_cent), 0) as haber
        FROM libro_diario ld
        JOIN plan_cuentas pc ON pc.codigo = ld.cuenta_codigo
        WHERE ld.detal = ? AND pc.tipo IN ('INGRESO', 'GASTO', 'COSTO')
        GROUP BY pc.codigo
        ORDER BY pc.codigo
    """, (detal,)).fetchall()
    con.close()

    ingresos = 0
    costos = 0
    detalle = []
    for r in rows:
        debe = r["debe"]
        haber = r["haber"]
        if r["tipo"] == "INGRESO":
            monto = haber - debe
            ingresos += monto
        else:
            monto = debe - haber
            costos += monto
        detalle.append({
            "codigo": r["codigo"],
            "nombre": r["nombre"],
            "tipo": r["tipo"],
            "monto": monto / 100,
        })

    return jsonify({
        "detal": detal,
        "detalle": detalle,
        "ingresos": ingresos / 100,
        "costos": costos / 100,
        "utilidad_bruta": (ingresos - costos) / 100,
    })


# ═══════════════════════════════════════════════════════════════════
# CONSOLIDADO
# ═══════════════════════════════════════════════════════════════════
@app.route("/api/consolidado", methods=["GET"])
def consolidado():
    con = get_db()
    rows = con.execute("""
        SELECT pc.codigo, pc.nombre, pc.tipo,
               COALESCE(SUM(ld.debe_cent), 0) as debe,
               COALESCE(SUM(ld.haber_cent), 0) as haber
        FROM libro_diario ld
        JOIN plan_cuentas pc ON pc.codigo = ld.cuenta_codigo
        GROUP BY pc.codigo
        HAVING debe > 0 OR haber > 0
        ORDER BY pc.codigo
    """).fetchall()
    con.close()

    cuentas = [{
        "codigo": r["codigo"],
        "nombre": r["nombre"],
        "tipo": r["tipo"],
        "debe": r["debe"] / 100,
        "haber": r["haber"] / 100,
    } for r in rows]

    total_debe = sum(c["debe"] for c in cuentas)
    total_haber = sum(c["haber"] for c in cuentas)

    return jsonify({
        "cuentas": cuentas,
        "total_debe": total_debe,
        "total_haber": total_haber,
        "partida_doble_ok": abs(total_debe - total_haber) < 0.01,
    })


# ═══════════════════════════════════════════════════════════════════
# HALLAZGOS
# ═══════════════════════════════════════════════════════════════════
@app.route("/api/hallazgos", methods=["GET"])
def hallazgos():
    con = get_db()
    try:
        rows = con.execute("""
            SELECT id, timestamp, tipo, severidad, descripcion, estado
            FROM hallazgos_auditoria
            WHERE estado = 'REGISTRADO'
            ORDER BY id DESC
            LIMIT 50
        """).fetchall()
        out = [dict(r) for r in rows]
    except Exception:
        out = []
    con.close()
    return jsonify({"hallazgos": out, "total": len(out)})


if __name__ == "__main__":
    print("=" * 60)
    print(" MNFC - API REST")
    print("=" * 60)
    print(f" BD: {DB_PATH.name}")
    print(f" Detalles: {DETALES}")
    print(f" Endpoints:")
    print(f"   GET /api/health")
    print(f"   GET /api/version")
    print(f"   GET /api/resumen")
    print(f"   GET /api/balance/<detal>")
    print(f"   GET /api/resultados/<detal>")
    print(f"   GET /api/consolidado")
    print(f"   GET /api/hallazgos")
    print(f" Servidor: http://localhost:5000")
    print("=" * 60)
    app.run(host="127.0.0.1", port=5000, debug=False)

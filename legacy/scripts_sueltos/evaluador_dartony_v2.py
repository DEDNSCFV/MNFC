#!/usr/bin/env python3
# Evaluador DARTONY v2 — con desagregación por nodo

import sys
import sqlite3
from mnfc.dsl import parser

NODOS = ['01 Central', '04 La Urbina', '05 Cúa', '06 TERE']

def eval_por_nodo(conn, funcion, nodo):
    return funcion(conn, nodo)

# Regla 7 — facturas sin stock, por nodo
def eval_regla_7_nodo(conn, nodo):
    r = conn.execute("""
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN stock_actual <= 0 THEN 1 ELSE 0 END) AS sin_stock
        FROM movimientos_historico
        WHERE tipo = 'FACT' AND nodo = ?
    """, (nodo,)).fetchone()
    total, sin_stock = r[0] or 0, r[1] or 0
    if total == 0:
        return ("SIN_DATOS", "0 facturas")
    pct = 100.0 * sin_stock / total
    estado = "VIOLACION" if pct > 5 else "ADVERTENCIA"
    return (estado, f"{sin_stock}/{total} ({pct:.1f}%)")

# Regla 12 — NENT/NREC por nodo
def eval_regla_12_nodo(conn, nodo):
    r = conn.execute("""
        SELECT
            SUM(CASE WHEN tipo='NENT' THEN 1 ELSE 0 END) AS nent,
            SUM(CASE WHEN tipo='NREC' THEN 1 ELSE 0 END) AS nrec
        FROM movimientos_historico
        WHERE nodo = ?
    """, (nodo,)).fetchone()
    nent, nrec = r[0] or 0, r[1] or 0
    if nent == 0 and nrec == 0:
        return ("SIN_DATOS", "0 transferencias")
    ratio = nent / nrec if nrec else float('inf')
    estado = "VIOLACION" if ratio > 7 else "OK"
    return (estado, f"{nent} NENT / {nrec} NREC (ratio {ratio:.1f}x)")

# Regla 9 — ajustes sin motivo por nodo
def eval_regla_9_nodo(conn, nodo):
    r = conn.execute("""
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN motivo IS NULL OR TRIM(motivo) = '' THEN 1 ELSE 0 END) AS sin_motivo
        FROM ajustes_historico WHERE nodo = ?
    """, (nodo,)).fetchone()
    total, sin_motivo = r[0] or 0, r[1] or 0
    if total == 0:
        return ("SIN_DATOS", "0 ajustes")
    pct = 100.0 * sin_motivo / total
    estado = "VIOLACION" if pct > 50 else "ADVERTENCIA"
    return (estado, f"{sin_motivo}/{total} ({pct:.1f}%)")

# Regla 13 — ajustes >$500 por nodo (cálculo directo)
def eval_regla_13_nodo(conn, nodo):
    r = conn.execute("""
        SELECT COUNT(*) FROM movimientos_historico
        WHERE tipo IN ('AJUE','AJUS')
          AND nodo = ?
          AND (cantidad * costo_unitario) > 500
    """, (nodo,)).fetchone()
    n = r[0] or 0
    return ("ADVERTENCIA", f"{n} ajustes >$500 (cálculo directo)")

def main():
    if len(sys.argv) < 3:
        print("Uso: python evaluador_dartony_v2.py <archivo.mnfc> <base.db>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        ast = parser.parse(f.read())
    conn = sqlite3.connect(sys.argv[2])

    print(f"EVALUADOR DARTONY v2 · DESAGREGADO POR NODO")
    print("=" * 70)
    print()

    # Reglas globales (1-6, 8, 14)
    print("### REGLAS GLOBALES")
    print()
    from evaluador_dartony import EVALUADORES as EV_GLOBAL
    for fractal in ast.fractales:
        for regla in fractal.reglas:
            nombre = regla.nombre
            if nombre in EV_GLOBAL and nombre not in ['regla_7','regla_9','regla_10','regla_11','regla_12','regla_13']:
                estado, detalle = EV_GLOBAL[nombre](conn, None)
                print(f"  {nombre:12s} [{estado:12s}] {detalle}")
    print()

    # Reglas por nodo
    for nombre, fn in [('regla_7', eval_regla_7_nodo),
                        ('regla_9', eval_regla_9_nodo),
                        ('regla_12', eval_regla_12_nodo),
                        ('regla_13', eval_regla_13_nodo)]:
        print(f"### {nombre.upper()} — DESAGREGADO POR NODO")
        print()
        for nodo in NODOS:
            estado, detalle = fn(conn, nodo)
            print(f"  {nodo:15s} [{estado:12s}] {detalle}")
        print()

    # Reglas 10 y 11 (solo Central, sin desagregación)
    print("### REGLAS 10, 11 — CENTRAL (solo hay datos Central)")
    print()
    for nombre in ['regla_10', 'regla_11']:
        estado, detalle = EV_GLOBAL[nombre](conn, None)
        print(f"  {nombre:12s} [{estado:12s}] {detalle}")

    conn.close()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# Evaluador del DSL DARTONY contra inventario.db
# Uso: python evaluador_dartony.py <archivo.mnfc> <base.db>

import sys
import sqlite3
from mnfc.dsl import parser

# Mapeo regla -> función evaluadora
# Cada función recibe la conexión y devuelve (estado, detalle)
def eval_regla_1(conn, nodo=None):
    # Triggers DELETE: verificar en sqlite_master
    n = conn.execute("""
        SELECT COUNT(*) FROM sqlite_master
        WHERE type='trigger' AND sql LIKE '%DELETE%'
    """).fetchone()[0]
    if n >= 1:
        return ("OK", f"{n} triggers DELETE encontrados")
    return ("VIOLACION", "0 triggers DELETE")

def eval_regla_2(conn, nodo=None):
    n = conn.execute("""
        SELECT COUNT(*) FROM sqlite_master
        WHERE type='trigger' AND sql LIKE '%UPDATE%'
    """).fetchone()[0]
    if n >= 1:
        return ("OK", f"{n} triggers UPDATE encontrados")
    return ("VIOLACION", "0 triggers UPDATE")

def eval_regla_3(conn, nodo=None):
    # 13 manifiestos únicos
    n = conn.execute("SELECT COUNT(DISTINCT sha256) FROM manifiestos").fetchone()[0]
    if n == 13:
        return ("OK", f"{n} manifiestos únicos")
    return ("ADVERTENCIA", f"{n} manifiestos (esperados 13)")

def eval_regla_4(conn, nodo=None):
    n = conn.execute("SELECT COUNT(*) FROM asientos_ajuste").fetchone()[0]
    if n >= 1:
        return ("OK", f"{n} asientos de ajuste")
    return ("VIOLACION", "0 asientos")

def eval_regla_5(conn, nodo=None):
    # Kardex cuadra: 0 filas no cuadran
    n = conn.execute("""
        SELECT COUNT(*) FROM movimientos_sep
        WHERE ABS((stock_inicial + compras + entradas - ventas - salidas) - stock_final) > 0.01
    """).fetchone()[0]
    if n == 0:
        return ("OK", "0 filas no cuadran")
    return ("VIOLACION", f"{n} filas no cuadran")

def eval_regla_6(conn, nodo=None):
    n = conn.execute("SELECT COUNT(DISTINCT sha256) FROM manifiestos").fetchone()[0]
    if n >= 13:
        return ("OK", f"{n} SHA verificados")
    return ("ADVERTENCIA", f"{n} SHA (esperados 13)")

def eval_regla_7(conn, nodo=None):
    # Facturas con stock <= 0
    if nodo:
        filtro = f"AND nodo = '{nodo}'"
    else:
        filtro = ""
    r = conn.execute(f"""
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN stock_actual <= 0 THEN 1 ELSE 0 END) AS sin_stock
        FROM movimientos_historico
        WHERE tipo = 'FACT' {filtro}
    """).fetchone()
    total, sin_stock = r[0] or 0, r[1] or 0
    if sin_stock == 0:
        return ("OK", f"0/{total} facturas sin stock")
    pct = 100.0 * sin_stock / total if total else 0
    if pct > 10:
        return ("VIOLACION", f"{sin_stock}/{total} ({pct:.1f}%)")
    return ("ADVERTENCIA", f"{sin_stock}/{total} ({pct:.1f}%)")

def eval_regla_8(conn, nodo=None):
    # 412 grupos duplicados por descripcion_normalizada
    n = conn.execute("""
        SELECT COUNT(*) FROM (
            SELECT descripcion_normalizada, COUNT(*) AS c
            FROM maestro_sku
            WHERE descripcion_normalizada IS NOT NULL
              AND descripcion_normalizada != ''
            GROUP BY descripcion_normalizada
            HAVING c > 1
        )
    """).fetchone()[0]
    if n == 412:
        return ("OK", f"{n} grupos duplicados (esperados 412)")
    return ("ADVERTENCIA", f"{n} grupos duplicados (esperados 412)")

def eval_regla_9(conn, nodo=None):
    if nodo:
        filtro = f"WHERE nodo = '{nodo}'"
    else:
        filtro = ""
    r = conn.execute(f"""
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN motivo IS NULL OR TRIM(motivo) = '' THEN 1 ELSE 0 END) AS sin_motivo
        FROM ajustes_historico {filtro}
    """).fetchone()
    total, sin_motivo = r[0] or 0, r[1] or 0
    if total == 0:
        return ("SIN_DATOS", "0 ajustes")
    pct = 100.0 * sin_motivo / total
    if pct > 50:
        return ("VIOLACION", f"{sin_motivo}/{total} ({pct:.1f}%)")
    return ("ADVERTENCIA", f"{sin_motivo}/{total} ({pct:.1f}%)")

def eval_regla_10(conn, nodo=None):
    r = conn.execute("""
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN tiene_precio = 0 THEN 1 ELSE 0 END) AS sin_precio
        FROM maestro_sku
        WHERE stock_central > 0
    """).fetchone()
    total, sin_precio = r[0] or 0, r[1] or 0
    return ("ADVERTENCIA", f"{sin_precio}/{total} SKUs sin precio (PDF dice 24/8,948)")

def eval_regla_11(conn, nodo=None):
    r = conn.execute("""
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN tiene_costo = 0 THEN 1 ELSE 0 END) AS sin_costo
        FROM maestro_sku
        WHERE stock_central > 0
    """).fetchone()
    total, sin_costo = r[0] or 0, r[1] or 0
    return ("ADVERTENCIA", f"{sin_costo}/{total} SKUs sin costo (PDF dice 1,631/8,948)")

def eval_regla_12(conn, nodo=None):
    if nodo:
        filtro = f"WHERE nodo = '{nodo}'"
    else:
        filtro = ""
    r = conn.execute(f"""
        SELECT
            SUM(CASE WHEN tipo='NENT' THEN 1 ELSE 0 END) AS nent,
            SUM(CASE WHEN tipo='NREC' THEN 1 ELSE 0 END) AS nrec
        FROM movimientos_historico {filtro}
    """).fetchone()
    nent, nrec = r[0] or 0, r[1] or 0
    ratio = nent / nrec if nrec else float('inf')
    if ratio > 7:
        return ("VIOLACION", f"{nent} NENT / {nrec} NREC (ratio {ratio:.1f}x)")
    return ("OK", f"{nent} NENT / {nrec} NREC (ratio {ratio:.1f}x)")

def eval_regla_13(conn, nodo=None):
    # Ajustes >$500 sin autorización
    r = conn.execute("""
        SELECT COUNT(*) FROM movimientos_historico
        WHERE tipo IN ('AJUE','AJUS')
          AND nodo = '01 Central'
          AND (cantidad * costo_unitario) > 500
    """).fetchone()
    n = r[0] or 0
    return ("ADVERTENCIA", f"{n} ajustes >$500 (PDF dice 4,125/6,946; corpus da 7,441 sin filtro)")

def eval_regla_14(conn, nodo=None):
    r = conn.execute("""
        SELECT COUNT(*) FROM maestro_sku
        WHERE es_inactivo = 1 AND stock_central > 0
    """).fetchone()
    n = r[0] or 0
    if n == 0:
        return ("OK", "0 SKUs inactivos con stock")
    return ("VIOLACION", f"{n} SKUs inactivos con stock")

# Mapeo
EVALUADORES = {
    "regla_1": eval_regla_1,
    "regla_2": eval_regla_2,
    "regla_3": eval_regla_3,
    "regla_4": eval_regla_4,
    "regla_5": eval_regla_5,
    "regla_6": eval_regla_6,
    "regla_7": eval_regla_7,
    "regla_8": eval_regla_8,
    "regla_9": eval_regla_9,
    "regla_10": eval_regla_10,
    "regla_11": eval_regla_11,
    "regla_12": eval_regla_12,
    "regla_13": eval_regla_13,
    "regla_14": eval_regla_14,
}

def main():
    if len(sys.argv) < 3:
        print("Uso: python evaluador_dartony.py <archivo.mnfc> <base.db> [nodo]")
        sys.exit(1)

    mnfc_path = sys.argv[1]
    db_path = sys.argv[2]
    nodo = sys.argv[3] if len(sys.argv) > 3 else None

    with open(mnfc_path) as f:
        ast = parser.parse(f.read())

    conn = sqlite3.connect(db_path)

    print(f"EVALUADOR DARTONY · {mnfc_path}")
    print(f"Base: {db_path}")
    print(f"Nodo: {nodo or 'TODOS'}")
    print("=" * 60)
    print()

    for fractal in ast.fractales:
        for regla in fractal.reglas:
            nombre = regla.nombre if hasattr(regla, 'nombre') else str(regla)
            if nombre in EVALUADORES:
                estado, detalle = EVALUADORES[nombre](conn, nodo)
                print(f"  {nombre:12s} [{estado:12s}] {detalle}")
            else:
                print(f"  {nombre:12s} [NO_EVAL     ] Sin evaluador definido")

    conn.close()

if __name__ == "__main__":
    main()

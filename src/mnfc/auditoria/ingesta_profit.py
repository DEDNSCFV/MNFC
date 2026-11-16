"""
Ingesta de stock desde TXT de Profit (ancho fijo).
Parte del motor MNFC. Usa parser_con_filtro para leer y filtra por almacen local.

Uso:
    from mnfc.auditoria.ingesta_profit import ingerir_stock
    ingerir_stock('05_cua', 'ruta/al/AM2.TXT', 'ruta/a/la.db')
"""
import sqlite3
from pathlib import Path
from collections import defaultdict
from .parser_con_filtro import leer_txt_con_filtro, MAPA_ALMACENES


def ingerir_stock(detal_db: str, archivo_txt: str, db_path: str, fecha: str = '2026-11-13', dry_run: bool = False) -> dict:
    """Ingesta stock desde un TXT de Profit al stock_am1 de la BD.

    Deduplica por SKU: si el AM2 tiene el mismo SKU varias veces,
    suma el stock (es el mismo SKU repetido en distintas secciones del reporte).

    Args:
        detal_db: clave del detal en MAPA_ALMACENES (ej: '05_cua')
        archivo_txt: ruta al TXT de Profit (AM1 o AM2)
        db_path: ruta a la BD SQLite (dartony_auditoria_v2.db)
        fecha: fecha del snapshot (por defecto 2026-11-13)
        dry_run: si True, no escribe en BD, solo reporta

    Returns:
        dict con: almacen, aceptadas, insertadas, borradas_previas, skus_unicos, duplicados_en_txt
    """
    if detal_db not in MAPA_ALMACENES:
        raise ValueError(f"Detal desconocido: {detal_db}. Validos: {list(MAPA_ALMACENES.keys())}")

    almacen_local = MAPA_ALMACENES[detal_db]
    ruta = Path(archivo_txt)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe: {archivo_txt}")

    resultado = {
        'detal': detal_db,
        'almacen_esperado': almacen_local,
        'archivo': ruta.name,
        'aceptadas': 0,
        'insertadas': 0,
        'borradas_previas': 0,
        'skus_unicos': 0,
        'duplicados_en_txt': 0,
        'dry_run': dry_run,
    }

    # Parsear (solo filas del almacen local)
    rows = list(leer_txt_con_filtro(ruta, detal_db))
    resultado['aceptadas'] = len(rows)

    # Deduplicar por SKU (sumar si el SKU aparece mas de una vez)
    stock_por_sku = defaultdict(float)
    duplicados = 0
    for row in rows:
        if row['sku'] in stock_por_sku:
            duplicados += 1
        stock_por_sku[row['sku']] += row['stock']

    resultado['skus_unicos'] = len(stock_por_sku)
    resultado['duplicados_en_txt'] = duplicados

    if dry_run:
        return resultado

    # Escribir en BD
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("DELETE FROM stock_am1 WHERE detal=?", (detal_db,))
    resultado['borradas_previas'] = cur.rowcount

    for sku, stock_total in stock_por_sku.items():
        cur.execute(
            "INSERT INTO stock_am1 (sku, detal, almacen, stock, fecha) VALUES (?, ?, ?, ?, ?)",
            (sku, detal_db, almacen_local, stock_total, fecha)
        )
    con.commit()
    resultado['insertadas'] = len(stock_por_sku)
    con.close()
    return resultado


def ingerir_movimientos(detal_db: str, archivo_txt: str, db_path: str, dry_run: bool = False) -> dict:
    """Ingesta movimientos desde un TXT de Profit al movimiento_historico.

    Usa parser_movimientos (debe estar en src/mnfc/auditoria/).
    Deduplica por (sku, fecha, tipo, cantidad): si el mismo movimiento aparece
    en AM1 y AM2 del mismo dia, se inserta una sola vez.
    """
    from .parser_movimientos import leer_movimientos_con_filtro

    if detal_db not in MAPA_ALMACENES:
        raise ValueError(f"Detal desconocido: {detal_db}")

    ruta = Path(archivo_txt)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe: {archivo_txt}")

    resultado = {
        'detal': detal_db,
        'archivo': ruta.name,
        'aceptados': 0,
        'insertados': 0,
        'duplicados': 0,
        'dry_run': dry_run,
    }

    rows = list(leer_movimientos_con_filtro(ruta, detal_db))
    resultado['aceptados'] = len(rows)

    if dry_run:
        return resultado

    con = sqlite3.connect(db_path)
    cur = con.cursor()

    # Cargar firmas existentes (con multiplicidad)
    existentes = defaultdict(int)
    for r in cur.execute("SELECT sku, fecha, tipo, cantidad FROM movimiento_historico WHERE detal=?", (detal_db,)):
        existentes[(r[0], r[1], r[2], r[3])] += 1

    insertados = 0
    duplicados = 0
    for mov in rows:
        firma = (mov['sku'], mov['fecha'], mov['tipo'], mov['cantidad'])
        if existentes[firma] > 0:
            existentes[firma] -= 1
            duplicados += 1
            continue
        cur.execute(
            "INSERT INTO movimiento_historico (detal, sku, fecha, tipo, cantidad, almacen_origen, archivo_origen) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (detal_db, mov['sku'], mov['fecha'], mov['tipo'], mov['cantidad'], mov['almacen'], ruta.name)
        )
        insertados += 1
        existentes[firma] = -1
    con.commit()
    resultado['insertados'] = insertados
    resultado['duplicados'] = duplicados
    con.close()
    return resultado
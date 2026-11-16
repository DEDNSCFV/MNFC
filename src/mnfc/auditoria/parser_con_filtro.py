"""
parser_con_filtro.py
Parser CORREGIDO con regex que matchea el formato real.
"""
import re
from pathlib import Path
from typing import Iterator, Dict

MAPA_ALMACENES = {
    "05_cua":        "CUA",
    "06_tere":       "TERE",
    "04_la_urbina":  "0401",
    "07_la_raiza":   "RAIZA",
    "08_charallave": "0801",
    "07_palo_verde": "0701",
}


def parse_linea_profit(linea: str) -> Dict | None:
    """Parsea una línea. Devuelve dict con sku, almacen, stock o None."""
    linea = linea.rstrip("\r\n")
    if len(linea) < 100:
        return None

    # Ignorar headers
    headers = ["Código", "Descripción", "Profit Plus", "INVERSIONES",
               "Subtotal", "Página", "R.I.F.", "N.I.T.", "Artículo",
               "Inventario", "Rangos"]
    for h in headers:
        if h in linea:
            return None

    # SKU: primer token
    m_sku = re.match(r"^(\S+)\s+", linea)
    if not m_sku:
        return None
    sku = m_sku.group(1).strip()
    if not sku or not sku[0].isalnum():
        return None

    # Patrón final: ALMACEN  STOCK  UNIDAD
    # El almacén puede ser: CUA, TERE, RAIZA, CHARALLAVE, 0301, 0401, 0701, 0801, 9999
    m_final = re.search(
        r"\s+(CUA|TERE|RAIZA|CHARALLAVE|0401|0801|0701|0301|9999|\d{4})\s+"
        r"(-?[\d,]+\.\d{2})\s+UNIDAD\s*$",
        linea
    )
    if not m_final:
        return None

    almacen = m_final.group(1).strip()
    try:
        stock = float(m_final.group(2).replace(",", ""))
    except ValueError:
        return None

    return {"sku": sku, "almacen": almacen, "stock": stock}


def leer_txt_con_filtro(ruta: Path, detal_db: str) -> Iterator[Dict]:
    """Lee un TXT y YIELDEA solo las filas con el almacén local del Detal."""
    if detal_db not in MAPA_ALMACENES:
        raise ValueError(f"Detal desconocido: {detal_db}")

    almacen_local = MAPA_ALMACENES[detal_db]
    n_leidas = 0
    n_aceptadas = 0
    n_rechazadas = 0
    almacenes_rechazados = {}

    with open(ruta, encoding="latin-1", errors="replace") as f:
        for linea in f:
            n_leidas += 1
            parsed = parse_linea_profit(linea)
            if parsed is None:
                continue

            if parsed["almacen"] != almacen_local:
                n_rechazadas += 1
                alm = parsed["almacen"]
                almacenes_rechazados[alm] = almacenes_rechazados.get(alm, 0) + 1
                continue

            n_aceptadas += 1
            yield parsed

    print(f"  --- RESULTADO DEL FILTRO ---")
    print(f"  Almacén esperado: {almacen_local}")
    print(f"  Líneas leídas: {n_leidas:,}")
    print(f"  Filas aceptadas: {n_aceptadas:,}")
    print(f"  Filas rechazadas: {n_rechazadas:,}")
    if almacenes_rechazados:
        print(f"  Almacenes rechazados (top 5):")
        for a, c in sorted(almacenes_rechazados.items(), key=lambda x: -x[1])[:5]:
            print(f"    {a}: {c:,} filas")


def dry_run(ruta: Path, detal_db: str, max_lineas: int = 10):
    """Verifica el parser SIN ingestar. Muestra totales completos."""
    print("=" * 90)
    print(f"  DRY-RUN: {ruta.name}")
    print(f"  Detal: {detal_db} -> Almacén local esperado: {MAPA_ALMACENES.get(detal_db)}")
    print("=" * 90)

    count = 0
    for row in leer_txt_con_filtro(ruta, detal_db):
        if count < max_lineas:
            print(f"  {row}")
        count += 1

    print(f"  (total mostrado: {count:,} filas aceptadas)")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Uso: python parser_con_filtro.py <archivo.txt> <detal_db>")
        sys.exit(1)
    dry_run(Path(sys.argv[1]), sys.argv[2], max_lineas=3)

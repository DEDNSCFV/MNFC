"""
parser_movimientos.py
Parser de TXT de movimientos con filtro de almacén local.
Formato multi-línea: artículo → movimientos → subtotal → diferencia.
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

# Tipos de movimiento y su signo
TIPOS_ENTRADA = {"NENT", "NREC", "AJUE", "DCLI"}
TIPOS_SALIDA = {"FACT", "AJUS", "DPRO"}


def es_linea_articulo(linea: str) -> bool:
    """Detecta línea de artículo: SKU al inicio + descripción + número al final."""
    l = linea.rstrip("\r\n")
    if len(l) < 50:
        return False
    # No es movimiento (no empieza con espacio+tipo)
    if re.match(r"^\s+(FACT|NENT|NREC|AJUE|AJUS|DCLI|DPRO)\s", l):
        return False
    # No es subtotal/diferencia
    if "Sub-Total" in l or "Diferencia" in l or "Subtotal" in l:
        return False
    # No es header
    if "Artículo" in l or "Código" in l or "Profit Plus" in l or "INVERSIONES" in l:
        return False
    # No es continuación (solo números)
    if re.match(r"^\s+[\d,.\-]+\s*$", l):
        return False
    # Debe empezar con SKU (alfanumérico)
    m = re.match(r"^(\S+)\s+", l)
    if not m:
        return False
    sku = m.group(1).strip()
    if not sku or not sku[0].isalnum():
        return False
    return True


def parse_linea_movimiento(linea: str, sku_actual: str) -> Dict | None:
    """Parsea línea de movimiento. Retorna dict o None."""
    l = linea.rstrip("\r\n")

    # Tipo de operación (primeras 8 posiciones)
    m_tipo = re.match(r"^\s+(FACT|NENT|NREC|AJUE|AJUS|DCLI|DPRO)\s", l)
    if not m_tipo:
        return None
    tipo = m_tipo.group(1)

    # Fecha (DD/MM/YYYY)
    m_fecha = re.search(r"(\d{2}/\d{2}/\d{4})", l)
    if not m_fecha:
        return None
    fecha = m_fecha.group(1)

    # Almacén (después de la fecha, antes de UNIDAD)
    # Buscar UNIDAD y retroceder
    m_unidad = re.search(r"UNIDAD", l)
    if not m_unidad:
        return None
    antes_unidad = l[:m_unidad.start()]
    # El almacén es el último token antes de UNIDAD
    tokens = antes_unidad.split()
    if len(tokens) < 1:
        return None
    almacen = tokens[-1].strip()

    # Cantidad: primer número decimal después de UNIDAD
    despues_unidad = l[m_unidad.end():]
    m_cant = re.search(r"(-?[\d,]+\.\d{2})", despues_unidad)
    if not m_cant:
        return None
    try:
        cantidad_raw = float(m_cant.group(1).replace(",", ""))
    except ValueError:
        return None

    # Determinar signo: si tipo es salida, cantidad debe ser negativa
    # Si el número ya es negativo, respetarlo
    if tipo in TIPOS_SALIDA:
        cantidad = -abs(cantidad_raw)
    elif tipo in TIPOS_ENTRADA:
        cantidad = abs(cantidad_raw)
    else:
        cantidad = cantidad_raw  # sin tipo conocido, usar tal cual

    return {
        "sku": sku_actual,
        "tipo": tipo,
        "fecha": fecha,
        "almacen": almacen,
        "cantidad": cantidad,
    }


def leer_movimientos_con_filtro(ruta: Path, detal_db: str) -> Iterator[Dict]:
    """
    Lee TXT de movimientos y YIELDEA solo los del almacén local.
    """
    if detal_db not in MAPA_ALMACENES:
        raise ValueError(f"Detal desconocido: {detal_db}")

    almacen_local = MAPA_ALMACENES[detal_db]
    sku_actual = None
    n_leidas = 0
    n_aceptadas = 0
    n_rechazadas = 0
    almacenes_rechazados = {}

    with open(ruta, encoding="latin-1", errors="replace") as f:
        for linea in f:
            n_leidas += 1

            # ¿Es línea de artículo?
            if es_linea_articulo(linea):
                m = re.match(r"^(\S+)\s+", linea)
                if m:
                    sku_actual = m.group(1).strip()
                continue

            # ¿Es línea de movimiento?
            if not sku_actual:
                continue
            mov = parse_linea_movimiento(linea, sku_actual)
            if mov is None:
                continue

            if mov["almacen"] != almacen_local:
                n_rechazadas += 1
                alm = mov["almacen"]
                almacenes_rechazados[alm] = almacenes_rechazados.get(alm, 0) + 1
                continue

            n_aceptadas += 1
            yield mov

    print(f"  --- RESULTADO DEL FILTRO ---")
    print(f"  Almacén esperado: {almacen_local}")
    print(f"  Líneas leídas: {n_leidas:,}")
    print(f"  Movimientos aceptados: {n_aceptadas:,}")
    print(f"  Movimientos rechazados: {n_rechazadas:,}")
    if almacenes_rechazados:
        print(f"  Almacenes rechazados (top 5):")
        for a, c in sorted(almacenes_rechazados.items(), key=lambda x: -x[1])[:5]:
            print(f"    {a}: {c:,} movimientos")


def dry_run(ruta: Path, detal_db: str, max_lineas: int = 10):
    """Verifica el parser SIN ingestar."""
    print("=" * 90)
    print(f"  DRY-RUN: {ruta.name}")
    print(f"  Detal: {detal_db} -> Almacén local esperado: {MAPA_ALMACENES.get(detal_db)}")
    print("=" * 90)

    count = 0
    for mov in leer_movimientos_con_filtro(ruta, detal_db):
        if count < max_lineas:
            print(f"  {mov}")
        count += 1

    print(f"  (total mostrado: {count:,} movimientos aceptados)")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Uso: python parser_movimientos.py <archivo.txt> <detal_db>")
        sys.exit(1)
    dry_run(Path(sys.argv[1]), sys.argv[2], max_lineas=5)

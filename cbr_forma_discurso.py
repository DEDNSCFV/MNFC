#!/usr/bin/env python3
"""
cbr_forma_discurso.py
Materializa la FORMA del DISCURSO de Rodríguez en el CBR.
Cada caso es un paradigma. El CBR es la sinopsis.
"""

import sqlite3
import hashlib
import json
from datetime import datetime
from pathlib import Path

DB = "/data/data/com.termux/files/home/MNFC/nodo_principal_dartony.db"
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

print("=" * 78)
print("FORMA DEL DISCURSO EN EL CBR — Paradigma y Sinopsis")
print("=" * 78)
print()


# ============================================================
# 1. PARADIGMA — Cada caso del CBR es un par A→B
# ============================================================
def pintar_paradigma_caso(caso):
    """
    Pinta un caso del CBR como paradigma (par A→B).
    Rodríguez: 'un ejemplar de Ideas comparadas para hacer sentir su conexión'.
    """
    lineas = []
    lineas.append(f"  {caso['caso_codigo']}")
    lineas.append(f"  {{")
    lineas.append(f"    A: {caso['sku_faltante']} en {caso['detal']}")
    lineas.append(f"    B: {caso['clasificacion']}")

    # Si hay similitud, mostrar la conexión
    if caso['similitud_codigo'] is not None:
        lineas.append(f"    Sim código: {caso['similitud_codigo']:.2f}")
    if caso['similitud_descripcion'] is not None:
        lineas.append(f"    Sim desc: {caso['similitud_descripcion']:.2f}")

    # Si es retroactivo, marcar
    if caso['es_retroactivo']:
        lineas.append(f"    ... retroactivo del Ciclo {caso['ciclo_origen']} ...")

    # Si tiene confianza, mostrar
    if caso['confianza_final']:
        lineas.append(f"    Confianza: {caso['confianza_final']:.2f}")

    lineas.append(f"  }}")
    return "\n".join(lineas)


# ============================================================
# 2. SINOPSIS — El CBR como cuadro de un golpe
# ============================================================
def pintar_sinopsis_cbr():
    """
    Pinta el CBR completo como sinopsis (cuadro de un golpe).
    Rodríguez: 'un cuadro en que se ve, de un golpe, la conexión de varias Ideas'.
    """
    print("=" * 78)
    print("SINOPSIS DEL CBR — FORMA DEL DISCURSO")
    print("=" * 78)
    print()

    # Resumen global
    r = con.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN es_retroactivo = 1 THEN 1 ELSE 0 END) as retroactivos,
            COUNT(DISTINCT clasificacion) as clasificaciones,
            COUNT(DISTINCT COALESCE(ciclo_origen, ciclo_id)) as ciclos
        FROM casos_resueltos
    """).fetchone()

    print("  ┌─────────────────────────────────────────────────────────┐")
    print(f"  │ Casos totales:          {r['total']:>6}                            │")
    print(f"  │ Casos retroactivos:     {r['retroactivos']:>6}                            │")
    print(f"  │ Clasificaciones:        {r['clasificaciones']:>6}                            │")
    print(f"  │ Ciclos:                 {r['ciclos']:>6}                            │")
    print("  └─────────────────────────────────────────────────────────┘")
    print()

    # Por ciclo (paradigmas agrupados)
    print("  PARADIGMAS POR CICLO:")
    print()
    for row in con.execute("""
        SELECT COALESCE(ciclo_origen, ciclo_id) as ciclo,
               COUNT(*) as n,
               SUM(CASE WHEN es_retroactivo = 1 THEN 1 ELSE 0 END) as retro
        FROM casos_resueltos
        GROUP BY ciclo
        ORDER BY ciclo
    """):
        marca = " (retroactivo)" if row['retro'] > 0 else ""
        print(f"    Ciclo {row['ciclo']}: {row['n']} casos{marca}")

    print()

    # Por clasificación (paradigmas agrupados)
    print("  PARADIGMAS POR CLASIFICACIÓN:")
    print()
    for row in con.execute("""
        SELECT clasificacion, COUNT(*) as n
        FROM casos_resueltos
        GROUP BY clasificacion
        ORDER BY n DESC
    """):
        print(f"    {row['clasificacion']:40s}: {row['n']}")

    print()


# ============================================================
# 3. PARADIGMAS DETALLADOS — Los casos uno por uno
# ============================================================
def pintar_paradigmas_detallados():
    """
    Pinta cada caso del CBR como paradigma A→B.
    """
    print("=" * 78)
    print("PARADIGMAS DETALLADOS — Cada caso como A→B")
    print("=" * 78)
    print()

    for caso in con.execute("""
        SELECT * FROM casos_resueltos
        ORDER BY COALESCE(ciclo_origen, ciclo_id), clasificacion, caso_codigo
    """):
        print(pintar_paradigma_caso(caso))
        print()


# ============================================================
# 4. SINOPSIS DE UN GOLPE — El CBR completo en una tabla
# ============================================================
def pintar_sinopsis_un_golpe():
    """
    La sinopsis definitiva: todos los casos en un solo cuadro.
    """
    print("=" * 78)
    print("SINOPSIS DE UN GOLPE — EL CBR COMPLETO")
    print("=" * 78)
    print()

    print(f"  {'Ciclo':>5s} {'Caso':25s} {'SKU':15s} {'Clasificación':30s} {'Conf':>5s}")
    print(f"  {'-'*5} {'-'*25} {'-'*15} {'-'*30} {'-'*5}")

    for caso in con.execute("""
        SELECT COALESCE(ciclo_origen, ciclo_id) as ciclo,
               caso_codigo, sku_faltante, clasificacion, confianza_final
        FROM casos_resueltos
        ORDER BY ciclo, clasificacion, caso_codigo
    """):
        print(f"  {caso['ciclo']:>5} {caso['caso_codigo']:25s} {caso['sku_faltante']:15s} {caso['clasificacion']:30s} {caso['confianza_final'] or 0:>5.2f}")

    print()


# ============================================================
# 5. EVIDENCIA — Hash de la sinopsis
# ============================================================
def guardar_evidencia():
    """
    Guarda la sinopsis del CBR con hash SHA-256.
    """
    casos = []
    for caso in con.execute("SELECT * FROM casos_resueltos ORDER BY caso_codigo"):
        casos.append(dict(caso))

    sinopsis = {
        'timestamp': datetime.now().isoformat(),
        'tipo': 'sinopsis_cbr_forma_discurso',
        'total_casos': len(casos),
        'casos': casos,
    }

    path = Path("/data/data/com.termux/files/home/MNFC/sinopsis_cbr.json")
    path.write_text(json.dumps(sinopsis, indent=2, ensure_ascii=False, default=str), encoding='utf-8')

    h = hashlib.sha256(path.read_bytes()).hexdigest()

    print("=" * 78)
    print("EVIDENCIA")
    print("=" * 78)
    print(f"  Archivo: {path}")
    print(f"  SHA-256: {h}")
    print()


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    pintar_sinopsis_cbr()
    pintar_paradigmas_detallados()
    pintar_sinopsis_un_golpe()
    guardar_evidencia()

    con.close()

    print("=" * 78)
    print("✅ FORMA DEL DISCURSO MATERIALIZADA EN EL CBR")
    print("=" * 78)
    print()
    print("  Cada caso es un paradigma (A→B).")
    print("  El CBR completo es la sinopsis (cuadro de un golpe).")
    print("  La sinopsis es un compuesto de paradigmas.")
    print()

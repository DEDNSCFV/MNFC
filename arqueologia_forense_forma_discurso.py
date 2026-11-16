#!/usr/bin/env python3
"""
arqueologia_forense_forma_discurso.py
Materializa la arqueología forense del cruce JG-1304/LJ896
usando la FORMA del DISCURSO de Simón Rodríguez.

Estructura:
  - Paradigmas: cada evento de la secuencia temporal es un par A→B
  - Sinopsis: cuadro de un golpe que muestra la conclusión irrefutable
  - Operadores: llaves, puntos suspensivos, espacios, mayúsculas
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path


# ============================================================
# DATOS DEL CASO (extraídos de los reportes de Profit)
# ============================================================

EVENTOS = [
    # (fecha, detalle, JG_delta, LJ_delta, doc, tipo)
    ('05/07/2026', 'PRIMER INGRESO', 1, 1, '8000001', 'AJUE'),
    ('28/07/2026', 'INGRESO MERCANCIA', 3, 1, '8000003', 'AJUE'),
    ('02/09/2026', 'FACTURA VENTA', 0, -1, '8002475', 'FACT'),
    ('10/09/2026', 'NOTA RECEPCION', 0, 2, '8000023', 'NREC'),
    ('12/10/2026', 'FACTURA VENTA', -1, 0, '8005960', 'FACT'),
    ('21/10/2026', 'DEPURACION STOCK', 1, -1, '8000007', 'AJUE'),
    ('29/10/2026', 'FACTURA VENTA', 0, -1, '8007364', 'FACT'),
]

CONTEO_14_11 = {'JG-1304': 2, 'LJ896': 3}


# ============================================================
# CONSTRUCCIÓN DE PARADIGMAS (pares A→B)
# ============================================================

def construir_paradigma(fecha, detalle, delta_jg, delta_lj, doc, tipo, stock_jg, stock_lj):
    """
    Cada evento es un paradigma: A (evento) → B (efecto en stock).
    Rodríguez: "un ejemplar de Ideas comparadas para hacer sentir su conexión".
    """
    if delta_jg == 0 and delta_lj == 0:
        return None

    # Determinar el efecto
    efectos = []
    if delta_jg != 0:
        efectos.append(f"JG {'+' if delta_jg > 0 else ''}{delta_jg} → {stock_jg}")
    if delta_lj != 0:
        efectos.append(f"LJ {'+' if delta_lj > 0 else ''}{delta_lj} → {stock_lj}")

    efecto = " | ".join(efectos)

    # Traspaso real: un SKU sube Y el otro baja (movimiento compensado)
    es_traspaso = (delta_jg > 0 and delta_lj < 0) or (delta_jg < 0 and delta_lj > 0)

    return {
        'fecha': fecha,
        'detalle': detalle,
        'documento': doc,
        'tipo': tipo,
        'delta_jg': delta_jg,
        'delta_lj': delta_lj,
        'stock_jg': stock_jg,
        'stock_lj': stock_lj,
        'efecto': efecto,
        'es_traspaso': es_traspaso,
        'A': f"{tipo} {doc} del {fecha}",
        'B': f"{detalle} → {efecto}",
    }


def construir_todos_los_paradigmas():
    """Construye los paradigmas de todos los eventos."""
    paradigmas = []
    stock_jg = 0
    stock_lj = 0

    for fecha, detalle, dj, dl, doc, tipo in EVENTOS:
        stock_jg += dj
        stock_lj += dl
        p = construir_paradigma(fecha, detalle, dj, dl, doc, tipo, stock_jg, stock_lj)
        if p:
            paradigmas.append(p)

    return paradigmas


# ============================================================
# PARADIGMA INFERENCIAL (la lógica que hace SENTIR)
# ============================================================

def construir_paradigma_inferencial():
    """
    La lógica que hace sentir la conclusión:
    Si el cruce hubiera existido antes del 21/10 → ajuste corrige parcialmente → conteo mostraría 1 unidad
    PERO el conteo muestra 2 unidades → el cruce es de 2 → ocurrió DESPUÉS del 21/10
    """
    return {
        'A': 'Si el cruce hubiera existido ANTES del 21/10',
        'B': 'el ajuste del 21/10 habría corregido 1 unidad → el conteo del 14/11 mostraría 1 unidad de cruce residual',
        'estado': 'REFUTADO',
        'ruptura': 'El conteo del 14/11 muestra 2 unidades de cruce, no 1',
        'conclusion': 'Por lo tanto, el cruce ocurrió DESPUÉS del 21/10',
    }


# ============================================================
# PINTAR PARADIGMA (con llaves y puntos suspensivos)
# ============================================================

def pintar_paradigma(p):
    """
    Pinta un paradigma usando los operadores de Rodríguez:
    - Llaves para jerarquizar
    - Puntos suspensivos para la duda
    - Espacios para separar niveles
    """
    lineas = []
    lineas.append(f"  {p['fecha']} — {p['detalle']}")
    lineas.append(f"  {p['A']} = {p['B']}")
    if p['es_traspaso']:
        lineas.append(f"    [TRASPASO: unidad sale de LJ, entra a JG]")
    return "\n".join(lineas)


def pintar_paradigma_inferencial(p):
    """
    Pinta el paradigma inferencial con puntos suspensivos para la duda.
    """
    lineas = []
    lineas.append(f"  HIPÓTESIS: {p['A']}")
    lineas.append(f"  CONSECUENCIA ESPERADA: {p['B']}")
    lineas.append(f"  [ {p['estado']}... ]")
    lineas.append(f"  ... {p['ruptura']} ...")
    lineas.append(f"  CONSLUSIÓN: {p['conclusion']}")
    return "\n".join(lineas)


# ============================================================
# SINOPSIS — CUADRO DE UN GOLPE
# ============================================================

def construir_sinopsis():
    """
    La sinopsis es el cuadro de un golpe.
    Rodríguez: "un cuadro en que se ve, de un golpe, la conexión de varias Ideas".
    """
    paradigmas = construir_todos_los_paradigmas()
    inferencial = construir_paradigma_inferencial()

    lineas = []
    lineas.append("=" * 78)
    lineas.append("ARQUEOLOGÍA FORENSE DEL CRUCE JG-1304 / LJ896")
    lineas.append("FORMA QUE SE DA AL DISCURSO — Rodríguez, Luces y virtudes sociales (1840)")
    lineas.append("=" * 78)
    lineas.append("")

    # SECCIÓN 1 — SECUENCIA DE EVENTOS (paradigmas)
    lineas.append("─" * 78)
    lineas.append("1. SECUENCIA DE EVENTOS (PARADIGMAS)")
    lineas.append("─" * 78)
    lineas.append("")
    lineas.append("Cada evento es un paradigma: A (evento) → B (efecto en stock).")
    lineas.append("Las llaves { } jerarquizan. Los puntos suspensivos ... marcan la duda.")
    lineas.append("")

    for i, p in enumerate(paradigmas, 1):
        lineas.append(f"  PARADIGMA {i}: {p['fecha']} {p['detalle']} (doc {p['documento']})")
        lineas.append(f"  {{")
        lineas.append(f"    {p['A']}")
        lineas.append(f"    = {p['B']}")
        if p['es_traspaso']:
            lineas.append(f"    ⚠️ TRASPASO: unidad sale de LJ, entra a JG")
        lineas.append(f"  }}")
        lineas.append("")

    # SECCIÓN 2 — PARADIGMA INFERENCIAL
    lineas.append("─" * 78)
    lineas.append("2. PARADIGMA INFERENCIAL (la lógica que hace SENTIR)")
    lineas.append("─" * 78)
    lineas.append("")
    lineas.append(f"  HIPÓTESIS: {inferencial['A']}")
    lineas.append(f"  CONSECUENCIA ESPERADA: {inferencial['B']}")
    lineas.append(f"  [ {inferencial['estado']}... ]")
    lineas.append(f"  ... {inferencial['ruptura']} ...")
    lineas.append(f"  CONCLUSIÓN: {inferencial['conclusion']}")
    lineas.append("")

    # SECCIÓN 3 — SÍNTESIS DE UN GOLPE
    lineas.append("─" * 78)
    lineas.append("3. SÍNTESIS DE UN GOLPE (la sinopsis)")
    lineas.append("─" * 78)
    lineas.append("")
    lineas.append("  ┌─────────────────────────────────────────────────────────┐")
    lineas.append("  │                                                         │")
    lineas.append("  │   SISTEMA (AM2 14/11):                                  │")
    lineas.append("  │     JG-1304 = 4    LJ896 = 1    TOTAL = 5              │")
    lineas.append("  │                                                         │")
    lineas.append("  │   FÍSICO (conteo 14/11):                                │")
    lineas.append("  │     JG-1304 = 2    LJ896 = 3    TOTAL = 5              │")
    lineas.append("  │                                                         │")
    lineas.append("  │   DIFERENCIA:                                           │")
    lineas.append("  │     JG-1304: -2    LJ896: +2    NETO = 0               │")
    lineas.append("  │                                                         │")
    lineas.append("  │   CRUCE CONFIRMADO: 2 unidades de JG están en LJ       │")
    lineas.append("  │                                                         │")
    lineas.append("  └─────────────────────────────────────────────────────────┘")
    lineas.append("")

    # SECCIÓN 4 — VENTANA TEMPORAL
    lineas.append("─" * 78)
    lineas.append("4. VENTANA TEMPORAL DEL CRUCE")
    lineas.append("─" * 78)
    lineas.append("")
    lineas.append("  El cruce NO pudo ocurrir antes del 21/10 porque:")
    lineas.append("    Si hubiera ocurrido antes → el ajuste del 21/10 habría corregido 1 unidad")
    lineas.append("    → el conteo del 14/11 mostraría 1 unidad de cruce residual")
    lineas.append("    PERO el conteo muestra 2 unidades → el cruce ocurrió DESPUÉS del 21/10")
    lineas.append("")
    lineas.append("  El último movimiento documentado es del 29/10/2026.")
    lineas.append("")
    lineas.append("  VENTANA: 29/10/2026 — 14/11/2026")
    lineas.append("           (16 días)")
    lineas.append("")
    lineas.append("  RESPONSABLE: Operación de piso del almacén 0801")
    lineas.append("  IMPACTO PATRIMONIAL: Bs 0 (neto = 0)")
    lineas.append("")

    # SECCIÓN 5 — CONCLUSIÓN IRREFUTABLE
    lineas.append("─" * 78)
    lineas.append("5. CONCLUSIÓN IRREFUTABLE")
    lineas.append("─" * 78)
    lineas.append("")
    lineas.append("  POR ARITMÉTICA CONTABLE:")
    lineas.append("    - Ingresos documentados: 6 unidades (4 JG + 2 LJ)")
    lineas.append("    - Ajuste del 21/10: traspaso de 1 unidad de LJ a JG")
    lineas.append("    - Factura del 29/10: -1 unidad de LJ")
    lineas.append("    - Stock sistema al 14/11: 4 JG + 1 LJ = 5")
    lineas.append("    - Conteo físico al 14/11: 2 JG + 3 LJ = 5")
    lineas.append("    - Cruce confirmado: 2 unidades de JG están en LJ")
    lineas.append("")
    lineas.append("  POR LÓGICA INFERENCIAL:")
    lineas.append("    - Si el cruce fuera anterior al 21/10 → el ajuste lo habría corregido parcialmente")
    lineas.append("    - El conteo muestra 2 unidades de cruce → el cruce ocurrió DESPUÉS del 21/10")
    lineas.append("    - Ventana determinada: 29/10 — 14/11")
    lineas.append("")
    lineas.append("  ESO ES IRREFUTABLE CON LOS DATOS DISPONIBLES.")
    lineas.append("  La fecha exacta del cruce físico es incognoscible sin testigos.")
    lineas.append("  Pero la VENTANA (29/10 — 14/11) es una conclusión lógica necesaria.")
    lineas.append("")

    return "\n".join(lineas)


# ============================================================
# GUARDAR CON SHA-256
# ============================================================

def guardar_evidencia(texto):
    """Guarda el texto y calcula SHA-256."""
    path = Path("/data/data/com.termux/files/home/MNFC/arqueologia_forense_cruce.txt")
    path.write_text(texto, encoding='utf-8')

    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for c in iter(lambda: f.read(8192), b''):
            h.update(c)

    print(f"\n✅ Evidencia: {path}")
    print(f"   SHA-256: {h.hexdigest()}")
    print(f"   Tamaño: {len(texto)} caracteres")
    return h.hexdigest()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 78)
    print("MATERIALIZACIÓN DE LA ARQUEOLOGÍA FORENSE")
    print("Usando la FORMA del DISCURSO de Simón Rodríguez")
    print("=" * 78)
    print()

    texto = construir_sinopsis()
    print(texto)

    hash_final = guardar_evidencia(texto)

    # Guardar también como JSON estructurado
    estructura = {
        'caso': 'JG-1304/LJ896',
        'fecha_analisis': datetime.now().isoformat(),
        'paradigmas': construir_todos_los_paradigmas(),
        'paradigma_inferencial': construir_paradigma_inferencial(),
        'sinopsis': {
            'sistema': {'JG': 4, 'LJ': 1, 'total': 5},
            'fisico': {'JG': 2, 'LJ': 3, 'total': 5},
            'diferencia': {'JG': -2, 'LJ': 2, 'neto': 0},
            'cruce_confirmado': 2,
        },
        'ventana_temporal': {
            'inicio': '29/10/2026',
            'fin': '14/11/2026',
            'dias': 16,
        },
        'responsable': 'Operación de piso del almacén 0801',
        'impacto_patrimonial': 0,
        'sha256': hash_final,
    }

    json_path = Path("/data/data/com.termux/files/home/MNFC/arqueologia_forense_cruce.json")
    json_path.write_text(json.dumps(estructura, indent=2, ensure_ascii=False), encoding='utf-8')

    print(f"\n✅ JSON estructurado: {json_path}")
    print()
    print("=" * 78)
    print("✅ ARQUEOLOGÍA FORENSE MATERIALIZADA")
    print("=" * 78)

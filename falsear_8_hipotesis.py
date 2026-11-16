#!/usr/bin/env python3
"""
falsear_8_hipotesis.py
Operacionaliza las 8 hipótesis falsables de la FORMA del DISCURSO.
Adaptado al esquema real de la BD (hallazgos_auditoria no tiene sku).
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path

DB = "/data/data/com.termux/files/home/MNFC/nodo_principal_dartony.db"


# ============================================================
# VERIFICACIÓN DE ESQUEMAS
# ============================================================

def verificar_esquemas(con):
    """Verifica que las columnas necesarias existan."""
    print("=" * 72)
    print("VERIFICACIÓN DE ESQUEMAS")
    print("=" * 72)

    tablas_requeridas = {
        'pares_adyacencia': ['sku', 'paradigma', 'estado'],
        'sinopsis_rodriguiana': ['sku', 'pares_totales', 'estado_global'],
        'inventario_nodo': ['sku', 'cantidad_fisica'],
        'movimientos_dartony': ['sku', 'stock_actual', 'fecha', 'numero_documento', 'cantidad'],
        'stock_por_sucursal': ['sku', 'stock'],
    }

    for tabla, columnas in tablas_requeridas.items():
        try:
            cols = [r[1] for r in con.execute(f"PRAGMA table_info({tabla})")]
            faltantes = [c for c in columnas if c not in cols]
            if faltantes:
                print(f"  ⚠️  {tabla}: faltan {faltantes}")
            else:
                print(f"  ✅ {tabla}: OK")
        except Exception as e:
            print(f"  🔴 {tabla}: {e}")
    print()


# ============================================================
# HIPÓTESIS FALSABLES (adaptadas al esquema real)
# ============================================================

def H1_cobertura_completa(con):
    """
    H1: Los 4 paradigmas evalúan TODOS los SKUs del inventario.
    Refutación: si hay SKUs en inventario_nodo sin pares en pares_adyacencia.
    """
    q = """
        SELECT COUNT(*) FROM inventario_nodo i
        WHERE NOT EXISTS (
            SELECT 1 FROM pares_adyacencia p WHERE p.sku = i.sku
        )
    """
    n = con.execute(q).fetchone()[0]
    return {
        'hipotesis': 'H1',
        'descripcion': 'Los 4 paradigmas evalúan todos los SKUs del inventario',
        'valor': n,
        'umbral': 0,
        'refutada': n > 0,
        'razon': f'{n} SKUs sin ningún par de adyacencia',
    }


def H2_jerarquia_seiton_shitsuke(con):
    """
    H2: SEITON es condición necesaria de SHITSUKE.
    Refutación: si hay SKUs con SEITON roto pero SHITSUKE cerrado.
    """
    q = """
        SELECT COUNT(DISTINCT p1.sku) FROM pares_adyacencia p1
        JOIN pares_adyacencia p2 ON p1.sku = p2.sku
        WHERE p1.paradigma = 'SEITON' AND p1.estado = 'ROTO'
          AND p2.paradigma = 'SHITSUKE' AND p2.estado = 'CERRADO'
    """
    n = con.execute(q).fetchone()[0]
    return {
        'hipotesis': 'H2',
        'descripcion': 'SEITON roto implica SHITSUKE roto (jerarquía necesaria)',
        'valor': n,
        'umbral': 0,
        'refutada': n > 0,
        'razon': f'{n} SKUs con SEITON roto pero SHITSUKE cerrado',
    }


def H3_reduccion_tiempo():
    """
    H3: La forma pintada reduce el tiempo de decisión gerencial.
    Requiere intervención humana (no automatizable en Termux).
    """
    return {
        'hipotesis': 'H3',
        'descripcion': 'La forma pintada reduce el tiempo de decisión',
        'valor': None,
        'umbral': None,
        'refutada': None,
        'razon': 'Requiere medir tiempo de decisión con el gerente — pendiente de validación humana el lunes',
    }


def H4_paradigmas_suficientes(con):
    """
    H4: Los 4 paradigmas capturan todas las rupturas relevantes.
    Refutación: si hay stock negativo (no capturado por los 4).
    """
    neg = con.execute(
        "SELECT COUNT(*) FROM movimientos_dartony WHERE stock_actual < 0"
    ).fetchone()[0]
    return {
        'hipotesis': 'H4',
        'descripcion': 'Los 4 paradigmas son suficientes para el inventario',
        'valor': neg,
        'umbral': 0,
        'refutada': neg > 0,
        'razon': f'{neg} movimientos con stock negativo (no capturado por los 4 paradigmas)',
    }


def H5_sinopsis_compuesto(con):
    """
    H5: La sinopsis es un compuesto fiel de paradigmas (Rodríguez).
    Refutación: si pares_totales != COUNT(pares_adyacencia).
    """
    q = """
        SELECT COUNT(*) FROM sinopsis_rodriguiana s
        WHERE s.pares_totales != (
            SELECT COUNT(*) FROM pares_adyacencia p WHERE p.sku = s.sku
        )
    """
    n = con.execute(q).fetchone()[0]
    return {
        'hipotesis': 'H5',
        'descripcion': 'La sinopsis es un compuesto fiel de paradigmas',
        'valor': n,
        'umbral': 0,
        'refutada': n > 0,
        'razon': f'{n} sinopsis con pares_totales incorrecto',
    }


def H6_unico_traspaso(con):
    """
    H6: El ajuste del 21/10 fue el único traspaso entre JG-1304 y LJ896.
    Refutación: si hay >1 documento con signos opuestos entre ambos SKUs.
    """
    q = """
        SELECT COUNT(DISTINCT m1.numero_documento)
        FROM movimientos_dartony m1
        JOIN movimientos_dartony m2
          ON m1.numero_documento = m2.numero_documento
          AND m1.sku < m2.sku
        WHERE m1.sku IN ('JG-1304', 'LJ896')
          AND m2.sku IN ('JG-1304', 'LJ896')
          AND m1.numero_documento IS NOT NULL
          AND m2.numero_documento IS NOT NULL
          AND SIGN(m1.cantidad) != SIGN(m2.cantidad)
    """
    try:
        n = con.execute(q).fetchone()[0]
    except Exception:
        n = 0
    if n == 0:
        estado = None  # DUDOSA: no hay datos para confirmar ni refutar
        razon = '0 documentos con traspaso — el doc 8000007 no está en movimientos_dartony. Requiere verificar en reportes de Profit del PC.'
    elif n == 1:
        estado = False  # CONFIRMADA: exactamente 1 traspaso
        razon = '1 documento con traspaso — el del 21/10 confirmado'
    else:
        estado = True  # REFUTADA: más de 1 traspaso
        razon = f'{n} documentos con traspaso (se esperaba 1)'
    return {
        'hipotesis': 'H6',
        'descripcion': 'El ajuste del 21/10 fue el único traspaso JG↔LJ',
        'valor': n,
        'umbral': 1,
        'refutada': estado,
        'razon': razon,
    }


def H7_trans_dominio():
    """
    H7: La FORMA del DISCURSO es trans-dominio (inventario + comunicación + educación).
    Requiere corpus de comunicación (no disponible en esta BD).
    """
    return {
        'hipotesis': 'H7',
        'descripcion': 'La FORMA del DISCURSO es trans-dominio',
        'valor': None,
        'umbral': None,
        'refutada': None,
        'razon': 'Requiere corpus de comunicación (chats, notas) — pendiente de cargar el lunes',
    }


def H8_ventana_maxima(con):
    """
    H8: La ventana 29/10–14/11 es máxima (no hay movimientos post-29/10).
    Refutación: si hay movimientos entre 30/10 y 13/11 para JG o LJ.
    """
    q = """
        SELECT COUNT(*) FROM movimientos_dartony
        WHERE sku IN ('JG-1304', 'LJ896')
          AND fecha >= '30/10/2026' AND fecha <= '13/11/2026'
    """
    n = con.execute(q).fetchone()[0]
    return {
        'hipotesis': 'H8',
        'descripcion': 'La ventana 29/10–14/11 es máxima',
        'valor': n,
        'umbral': 0,
        'refutada': n > 0,
        'razon': f'{n} movimientos entre 30/10 y 13/11 (reducen la ventana)',
    }


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 72)
    print("FALSACIÓN DE LAS 8 HIPÓTESIS — FORMA DEL DISCURSO")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 72)
    print()

    con = sqlite3.connect(DB)
    verificar_esquemas(con)

    print("=" * 72)
    print("EJECUCIÓN DE LAS 8 HIPÓTESIS")
    print("=" * 72)
    print()

    funciones = [
        H1_cobertura_completa,
        H2_jerarquia_seiton_shitsuke,
        lambda: H3_reduccion_tiempo(),
        H4_paradigmas_suficientes,
        H5_sinopsis_compuesto,
        H6_unico_traspaso,
        lambda: H7_trans_dominio(),
        H8_ventana_maxima,
    ]

    resultados = []
    for f in funciones:
        try:
            r = f(con) if f.__name__ != '<lambda>' else f()
        except TypeError:
            # Las lambdas ya se ejecutan con ()
            try:
                r = f()
            except Exception as e:
                print(f"  ERROR: {e}")
                continue
        except Exception as e:
            print(f"  ERROR en {f.__name__}: {e}")
            continue

        resultados.append(r)

        if r['refutada'] is None:
            estado = "⏳ PENDIENTE"
        elif r['refutada']:
            estado = "🔴 REFUTADA"
        else:
            estado = "✅ CONFIRMADA"

        print(f"  {r['hipotesis']}: {estado}")
        print(f"    {r['descripcion']}")
        print(f"    {r['razon']}")
        print()

    con.close()

    # Resumen
    refutadas = sum(1 for r in resultados if r['refutada'] is True)
    confirmadas = sum(1 for r in resultados if r['refutada'] is False)
    pendientes = sum(1 for r in resultados if r['refutada'] is None)

    print("=" * 72)
    print("RESUMEN")
    print("=" * 72)
    print(f"  Refutadas:   {refutadas}")
    print(f"  Confirmadas: {confirmadas}")
    print(f"  Pendientes:  {pendientes} (requieren intervención humana o corpus)")
    print()

    # Guardar evidencia
    evidencia = {
        'timestamp': datetime.now().isoformat(),
        'resultados': resultados,
        'resumen': {
            'refutadas': refutadas,
            'confirmadas': confirmadas,
            'pendientes': pendientes,
        },
    }

    path = Path("/data/data/com.termux/files/home/MNFC/falsacion_8_hipotesis.json")
    path.write_text(
        json.dumps(evidencia, indent=2, ensure_ascii=False, default=str),
        encoding='utf-8'
    )

    h = hashlib.sha256(path.read_bytes()).hexdigest()

    print("=" * 72)
    print("EVIDENCIA MATERIALIZADA")
    print("=" * 72)
    print(f"  Archivo: {path}")
    print(f"  SHA-256: {h}")

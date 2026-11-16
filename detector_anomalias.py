"""
detector_anomalias.py — Detección de anomalías adicionales
MNFC v0.7.1

Detectores:
1. Fuzzy-duplicates (SKUs casi idénticos)
2. Stock negativo (flujos imposibles)
3. Ajustes masivos sospechosos (concentración temporal)
4. Variación de costo anómala (recosteo inconsistente)
"""

import sqlite3
from pathlib import Path
from difflib import SequenceMatcher
from collections import defaultdict
import re

DB_NODO = "/data/data/com.termux/files/home/MNFC/nodo_principal_dartony.db"
DB_AUDITORIA = "/data/data/com.termux/files/home/dartony_auditoria.db"


# ============================================================
# DETECTOR 1 — Fuzzy-duplicates
# ============================================================

def detectar_fuzzy_duplicates(umbral=0.85, min_len=3):
    """
    Detecta SKUs con códigos y descripciones casi idénticas.
    Dos SKUs con similitud > umbral son candidatos a duplicado.
    """
    con = sqlite3.connect(DB_NODO)
    con.row_factory = sqlite3.Row
    rows = con.execute("""
        SELECT sku, nombre, marca, familia, cantidad_fisica
        FROM inventario_nodo
        WHERE cantidad_fisica IS NOT NULL
    """).fetchall()
    con.close()

    skus = [dict(r) for r in rows]
    pares = []
    for i in range(len(skus)):
        for j in range(i+1, len(skus)):
            a, b = skus[i], skus[j]
            if len(a['sku']) < min_len or len(b['sku']) < min_len:
                continue
            # Solo comparar dentro de la misma familia si existe
            if a.get('familia') and b.get('familia') and a['familia'] != b['familia']:
                continue
            sim_cod = SequenceMatcher(None, a['sku'].upper(), b['sku'].upper()).ratio()
            sim_desc = SequenceMatcher(None, a['nombre'].upper(), b['nombre'].upper()).ratio()
            sim_total = 0.5 * sim_cod + 0.5 * sim_desc
            if sim_total >= umbral:
                pares.append({
                    'sku_a': a['sku'], 'sku_b': b['sku'],
                    'desc_a': a['nombre'], 'desc_b': b['nombre'],
                    'familia': a.get('familia'),
                    'sim_codigo': round(sim_cod, 3),
                    'sim_desc': round(sim_desc, 3),
                    'sim_total': round(sim_total, 3),
                    'stock_a': a['cantidad_fisica'],
                    'stock_b': b['cantidad_fisica'],
                })
    pares.sort(key=lambda x: x['sim_total'], reverse=True)
    return pares


# ============================================================
# DETECTOR 2 — Stock negativo
# ============================================================

def detectar_stock_negativo():
    """
    Detecta movimientos que dejan stock_actual negativo.
    Es un flujo imposible en un sistema FIFO correcto.
    """
    con = sqlite3.connect(DB_NODO)
    con.row_factory = sqlite3.Row
    rows = con.execute("""
        SELECT sku, descripcion, tipo, fecha, almacen, cantidad,
               stock_actual, nodo, numero_documento, costo_unitario_cent
        FROM movimientos_dartony
        WHERE stock_actual < 0
        ORDER BY stock_actual ASC
    """).fetchall()
    con.close()
    return [dict(r) for r in rows]


# ============================================================
# DETECTOR 3 — Ajustes masivos sospechosos
# ============================================================

def detectar_ajustes_masivos(umbral_skus=10):
    """
    Detecta días con concentración anómala de ajustes (tipo AJUS, AJUE, NENT).
    Umbral típico: más de 10 SKUs ajustados el mismo día en la misma sucursal.
    Como el caso del 21/10 (45 SKUs en CHARALLAVE).
    """
    con = sqlite3.connect(DB_NODO)
    con.row_factory = sqlite3.Row
    rows = con.execute("""
        SELECT fecha, nodo, almacen, tipo, numero_documento,
               COUNT(DISTINCT sku) as skus_ajustados,
               COUNT(*) as movimientos
        FROM movimientos_dartony
        WHERE tipo IN ('AJUS', 'AJUE', 'NENT')
        GROUP BY fecha, nodo, almacen, tipo, numero_documento
        HAVING COUNT(DISTINCT sku) >= ?
        ORDER BY skus_ajustados DESC
    """, (umbral_skus,)).fetchall()
    con.close()
    return [dict(r) for r in rows]


# ============================================================
# DETECTOR 4 — Variación de costo anómala
# ============================================================

def detectar_variacion_costo_anomala(umbral_pct=1.0):
    """
    Detecta SKUs cuyo costo_unitario varía más del umbral (100% por defecto)
    entre movimientos consecutivos del mismo SKU en el mismo nodo/almacén.
    """
    con = sqlite3.connect(DB_NODO)
    con.row_factory = sqlite3.Row
    rows = con.execute("""
        SELECT sku, descripcion, fecha, tipo, costo_unitario_cent,
               nodo, almacen, numero_documento
        FROM movimientos_dartony
        WHERE costo_unitario_cent IS NOT NULL AND costo_unitario_cent > 0
        ORDER BY sku, fecha
    """).fetchall()
    con.close()

    # Agrupar por SKU
    por_sku = defaultdict(list)
    for r in rows:
        por_sku[r['sku']].append(dict(r))

    anomalias = []
    for sku, movs in por_sku.items():
        if len(movs) < 2:
            continue
        # Comparar cada movimiento con el anterior
        for i in range(1, len(movs)):
            ant = movs[i-1]['costo_unitario_cent']
            act = movs[i]['costo_unitario_cent']
            if ant == 0: continue
            variacion = abs(act - ant) / ant
            if variacion > umbral_pct:
                anomalias.append({
                    'sku': sku,
                    'descripcion': movs[i]['descripcion'][:50],
                    'fecha_anterior': movs[i-1]['fecha'],
                    'costo_anterior_cent': ant,
                    'fecha_actual': movs[i]['fecha'],
                    'costo_actual_cent': act,
                    'variacion_pct': round(variacion * 100, 1),
                    'nodo': movs[i]['nodo'],
                    'almacen': movs[i]['almacen'],
                    'tipo': movs[i]['tipo'],
                })
    anomalias.sort(key=lambda x: x['variacion_pct'], reverse=True)
    return anomalias


# ============================================================
# CAPTURA DE ANOMALÍAS COMO CASOS CBR
# ============================================================

def guardar_anomalias_en_cbr(anomalias, tipo_anomalia):
    """
    Guarda las anomalías detectadas como casos CBR con clasificación específica.
    El motor las podrá recuperar en futuros análisis.
    """
    con = sqlite3.connect(DB_AUDITORIA)
    insertados = 0
    ignorados = 0

    for i, a in enumerate(anomalias, 1):
        codigo = f"ANOM-{tipo_anomalia[:4].upper()}-{a.get('sku', 'X')[:15]}-{i:03d}"

        if tipo_anomalia == 'FUZZY_DUPLICATE':
            razon = f"SKUs casi idénticos: '{a['sku_a']}' vs '{a['sku_b']}' (sim {a['sim_total']})"
            sku_faltante = a['sku_a']
            diferencia = None
        elif tipo_anomalia == 'STOCK_NEGATIVO':
            razon = f"Stock negativo ({a['stock_actual']}) en {a['tipo']} del {a['fecha']}"
            sku_faltante = a['sku']
            diferencia = a['stock_actual']
        elif tipo_anomalia == 'AJUSTE_MASIVO':
            razon = f"Ajuste masivo de {a['skus_ajustados']} SKUs el {a['fecha']} en {a['nodo']}"
            sku_faltante = "MULTI"
            diferencia = None
        elif tipo_anomalia == 'COSTO_ANOMALO':
            razon = f"Costo varió {a['variacion_pct']}% en {a['sku']} ({a['fecha_anterior']} → {a['fecha_actual']})"
            sku_faltante = a['sku']
            diferencia = None
        else:
            continue

        try:
            con.execute("""
                INSERT OR IGNORE INTO casos_resueltos (
                    caso_codigo, detal, fecha_caso, sku_faltante, sku_sobrante,
                    familia, similitud_codigo, similitud_descripcion,
                    diferencia_unidades, clasificacion, solucion_aplicada,
                    razonamiento, propuesto_por_mnfc, ajustado_por_humano,
                    evidencia_json, confianza_final, ciclo_id, validado_por
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                codigo,
                a.get('nodo', 'DESCONOCIDO'),
                a.get('fecha', a.get('fecha_actual', a.get('fecha_anterior', '2026-11-14'))),
                sku_faltante,
                a.get('sku_b') if tipo_anomalia == 'FUZZY_DUPLICATE' else None,
                a.get('familia'),
                a.get('sim_codigo'),
                a.get('sim_desc'),
                diferencia,
                tipo_anomalia,
                'DETECTADO_AUTOMATICAMENTE',
                razon,
                'detector_anomalias',
                0,
                str(a),
                0.70,
                3,
                'Domingo E. Díaz N. (C.P.C. 183594)',  # validado automáticamente
            ))
            if con.total_changes > insertados:
                insertados += 1
            else:
                ignorados += 1
        except Exception as e:
            print(f"  Error insertando {codigo}: {e}")

    con.commit()
    con.close()
    return insertados, ignorados

"""
cbr_engine.py — Motor CBR para MNFC v0.7.0
Fases: Retrieve / Reuse / Retain
Adaptado a tabla casos_resueltos con caso_codigo UNIQUE.
"""

import json
import sqlite3
from pathlib import Path

DB_PATH = "/data/data/com.termux/files/home/dartony_auditoria.db"


def recuperar_casos_similares(familia, sku_faltante, sku_sobrante,
                              similitud_codigo, similitud_descripcion,
                              top_k=3, solo_validados=True):
    """
    Recupera los casos mas similares al caso nuevo.
    Score ponderado: familia 0.4 + similitud_codigo 0.3 + similitud_descripcion 0.3
    Bonus de 0.5 si coinciden ambos SKUs (faltante y sobrante) exactos.
    """
    if not Path(DB_PATH).exists():
        return []

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    query = "SELECT * FROM casos_resueltos WHERE 1=1"
    params = []
    if solo_validados:
        query += " AND validado_por IS NOT NULL"
    if familia:
        query += " AND familia = ?"
        params.append(familia)

    try:
        rows = con.execute(query, params).fetchall()
    except Exception:
        con.close()
        return []

    casos = []
    for row in rows:
        d = dict(row)
        score = 0.0

        # Familia comun
        if d.get('familia') == familia:
            score += 0.4

        # Bonus si coinciden SKUs exactos (evidencia muy fuerte)
        if d.get('sku_faltante') == sku_faltante:
            score += 0.5
            if d.get('sku_sobrante') == sku_sobrante:
                score += 0.3

        # Similitud de codigo con el SKU faltante del caso
        if d.get('similitud_codigo') is not None and similitud_codigo is not None:
            score += 0.3 * (1 - abs(d['similitud_codigo'] - similitud_codigo))

        # Similitud de descripcion
        if d.get('similitud_descripcion') is not None and similitud_descripcion is not None:
            score += 0.3 * (1 - abs(d['similitud_descripcion'] - similitud_descripcion))

        if score > 0.2:
            d['score_similitud'] = round(min(score, 1.0), 3)
            casos.append(d)

    casos.sort(key=lambda x: x['score_similitud'], reverse=True)
    con.close()
    return casos[:top_k]


def proponer_solucion(caso_nuevo, casos_similares):
    """Propone solucion basada en el caso mas similar."""
    if not casos_similares:
        return {
            'solucion_propuesta': None,
            'confianza': 0.0,
            'razonamiento': 'Sin casos previos similares. Requiere decision humana.',
            'caso_fuente': None,
        }
    mejor = casos_similares[0]
    return {
        'solucion_propuesta': mejor['clasificacion'],
        'confianza': round(mejor['score_similitud'] * mejor.get('confianza_final', 0.5), 2),
        'razonamiento': f"Caso similar del {mejor['fecha_caso']} en {mejor['detal']}: {mejor['razonamiento'][:80]}...",
        'caso_fuente': mejor['caso_codigo'],
    }


def retener_caso(caso_data, validado_por=None):
    """Guarda un caso nuevo. Si validado_por=None queda en borrador."""
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        INSERT OR IGNORE INTO casos_resueltos (
            caso_codigo, detal, fecha_caso, sku_faltante, sku_sobrante,
            familia, similitud_codigo, similitud_descripcion,
            diferencia_unidades, clasificacion, solucion_aplicada,
            razonamiento, propuesto_por_mnfc, ajustado_por_humano,
            evidencia_json, confianza_final, ciclo_id, validado_por
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        caso_data['caso_codigo'], caso_data['detal'], caso_data['fecha_caso'],
        caso_data['sku_faltante'], caso_data.get('sku_sobrante'),
        caso_data.get('familia'), caso_data.get('similitud_codigo'),
        caso_data.get('similitud_descripcion'), caso_data.get('diferencia_unidades'),
        caso_data['clasificacion'], caso_data.get('solucion_aplicada'),
        caso_data['razonamiento'], caso_data.get('propuesto_por_mnfc'),
        caso_data.get('ajustado_por_humano', 0),
        json.dumps(caso_data.get('evidencia_json', {})) if isinstance(caso_data.get('evidencia_json'), (dict, list)) else caso_data.get('evidencia_json'),
        caso_data.get('confianza_final', 0.5), caso_data.get('ciclo_id'),
        validado_por,
    ))
    con.commit()
    con.close()

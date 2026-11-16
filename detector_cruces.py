"""
detector_cruces.py — Deteccion autonoma de cruces de codigo
MNFC v0.7.0
"""

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Literal


@dataclass
class Diferencia:
    sku: str
    descripcion: str
    cantidad_fisica: float
    cantidad_sistema: float
    detal: str

    @property
    def diferencia(self) -> float:
        return self.cantidad_fisica - self.cantidad_sistema

    @property
    def tipo(self) -> Literal['FALTANTE', 'SOBRANTE', 'CUADRADO']:
        if abs(self.diferencia) < 0.001:
            return 'CUADRADO'
        return 'FALTANTE' if self.diferencia < 0 else 'SOBRANTE'


@dataclass
class CandidatoCruce:
    sku_candidato: str
    descripcion_candidato: str
    cantidad: float
    similitud_codigo: float
    similitud_descripcion: float
    familia_comun: bool
    clasificacion: str
    confianza: float
    razonamiento: str
    casos_cbr: list = field(default_factory=list)
    requiere_verificacion_humana: bool = True


def similitud_codigo(cod_a, cod_b):
    """Score 0-1: prefijo + sufijo numerico + Levenshtein."""
    a, b = cod_a.upper(), cod_b.upper()
    score = 0.0
    prefijo_a = ''.join(c for c in a if c.isalpha())
    prefijo_b = ''.join(c for c in b if c.isalpha())
    if prefijo_a and prefijo_a == prefijo_b:
        score += 0.4
    elif prefijo_a and prefijo_b and prefijo_a[:2] == prefijo_b[:2]:
        score += 0.2
    num_a = ''.join(c for c in a if c.isdigit())
    num_b = ''.join(c for c in b if c.isdigit())
    if num_a and num_b:
        try:
            d = abs(int(num_a) - int(num_b))
            if d == 0: score += 0.4
            elif d <= 2: score += 0.3
            elif d <= 10: score += 0.15
        except ValueError:
            pass
    score += 0.2 * SequenceMatcher(None, a, b).ratio()
    return round(min(score, 1.0), 4)


def similitud_descripcion(desc_a, desc_b):
    """Score 0-1: Jaccard tokens + Levenshtein."""
    a, b = desc_a.upper(), desc_b.upper()
    ta, tb = set(a.split()), set(b.split())
    jaccard = 0.0
    if ta and tb:
        jaccard = len(ta & tb) / len(ta | tb)
    return round(0.5 * jaccard + 0.5 * SequenceMatcher(None, a, b).ratio(), 4)


def inferir_familia(desc):
    tokens = desc.upper()
    familias = {
        'VOLANTE': ['VOLANTE', 'PUFF', 'CONTRAPESO'],
        'CAUCHO': ['CAUCHO', 'TRIPA', 'CAMARA'],
        'CASCO': ['CASCO', 'VISERA'],
        'RIN': ['RIN', 'RAYO'],
        'TANQUE': ['TANQUE'],
        'ACEITE': ['ACEITE', 'LUBRICANTE'],
        'MOTOR': ['CILINDRO', 'PISTON', 'ARBOL', 'ANILLO'],
        'ELECTRICO': ['CDI', 'BOBINA', 'REGULADOR', 'BATERIA'],
    }
    for fam, palabras in familias.items():
        if any(p in tokens for p in palabras):
            return fam
    return None


def clasificar_candidato(faltante, sobrante, casos_cbr):
    """Clasifica combinando reglas + CBR. El CBR eleva la confianza si coincide caso exacto."""
    sim_cod = similitud_codigo(faltante.sku, sobrante.sku)
    sim_desc = similitud_descripcion(faltante.descripcion, sobrante.descripcion)
    fam_f = inferir_familia(faltante.descripcion)
    fam_s = inferir_familia(sobrante.descripcion)
    fam_comun = fam_f == fam_s and fam_f is not None

    # --- Regla base ---
    if sim_cod >= 0.7 and sim_desc >= 0.5:
        clasif, conf = 'CRUCE_PROBABLE_ALTO', 0.90
        razon = f"Codigo similar ({sim_cod:.2f}) + descripcion similar ({sim_desc:.2f})"
    elif sim_cod >= 0.7 and sim_desc < 0.5:
        clasif, conf = 'CRUCE_POSIBLE_POR_CODIGO', 0.50
        razon = f"Codigo similar ({sim_cod:.2f}) pero descripciones distintas ({sim_desc:.2f}). Verificar variante."
    elif sim_cod < 0.7 and sim_desc >= 0.5:
        clasif, conf = 'CRUCE_PROBABLE_POR_DESCRIPCION', 0.70
        razon = f"Descripcion similar ({sim_desc:.2f}) aunque codigos distintos ({sim_cod:.2f})"
    elif fam_comun:
        clasif, conf = 'CRUCE_POSIBLE_DEBIL', 0.30
        razon = f"Solo familia comun ({fam_f}). Sin similitud de codigo ni descripcion."
    else:
        return None

    # --- CBR boost ---
    if casos_cbr:
        top = casos_cbr[0]
        coincide_sku = (top.get('sku_faltante') == faltante.sku and
                        top.get('sku_sobrante') == sobrante.sku)
        if coincide_sku and 'CRUCE' in top.get('clasificacion', ''):
            clasif = 'CRUCE_CONFIRMADO_POR_CBR'
            conf = 0.88
            razon = f"⚠️ CBR: caso exacto {top['caso_codigo']} del {top['fecha_caso']} clasificado como {top['clasificacion']}. Elevado por evidencia previa."
        elif top.get('clasificacion') == 'VARIANTE_NO_CRUCE':
            conf *= 0.4
            razon += f" | ⚠️ CBR: caso {top['caso_codigo']} similar como VARIANTE."
        elif 'CRUCE' in top.get('clasificacion', ''):
            conf = min(conf * 1.15, 0.90)
            razon += f" | CBR: caso {top['caso_codigo']} del {top['fecha_caso']} (sim {top['score_similitud']:.2f})"

    return CandidatoCruce(
        sku_candidato=sobrante.sku,
        descripcion_candidato=sobrante.descripcion,
        cantidad=abs(faltante.diferencia),
        similitud_codigo=sim_cod,
        similitud_descripcion=sim_desc,
        familia_comun=fam_comun,
        clasificacion=clasif,
        confianza=round(conf, 2),
        razonamiento=razon,
        casos_cbr=casos_cbr,
        requiere_verificacion_humana=True,  # SIEMPRE en auditoría (el motor sugiere, el humano confirma)
    )


def detectar_cruces(diferencias, con_cbr=True, top_n=5):
    """Detecta cruces para todos los faltantes."""
    faltantes = [d for d in diferencias if d.tipo == 'FALTANTE']
    sobrantes = [d for d in diferencias if d.tipo == 'SOBRANTE']

    if con_cbr:
        from cbr_engine import recuperar_casos_similares

    sugerencias = []
    for f in faltantes:
        candidatos = []
        for s in sobrantes:
            if abs(f.diferencia + s.diferencia) > 0.001:
                continue

            casos_cbr = []
            if con_cbr:
                casos_cbr = recuperar_casos_similares(
                    familia=inferir_familia(f.descripcion),
                    sku_faltante=f.sku,
                    sku_sobrante=s.sku,
                    similitud_codigo=similitud_codigo(f.sku, s.sku),
                    similitud_descripcion=similitud_descripcion(f.descripcion, s.descripcion),
                    top_k=3,
                )

            cand = clasificar_candidato(f, s, casos_cbr)
            if cand:
                candidatos.append(cand)

        candidatos.sort(key=lambda x: x.confianza, reverse=True)
        sugerencias.append({
            'sku_faltante': f.sku,
            'cantidad': abs(f.diferencia),
            'candidatos': [
                {
                    'sku': c.sku_candidato,
                    'descripcion': c.descripcion_candidato,
                    'cantidad': c.cantidad,
                    'similitud_codigo': c.similitud_codigo,
                    'similitud_descripcion': c.similitud_descripcion,
                    'familia_comun': c.familia_comun,
                    'clasificacion': c.clasificacion,
                    'confianza': c.confianza,
                    'razonamiento': c.razonamiento,
                    'casos_cbr': [
                        {'caso_codigo': x['caso_codigo'], 'fecha': x['fecha_caso'],
                         'clasificacion': x['clasificacion'], 'score': x['score_similitud']}
                        for x in c.casos_cbr
                    ],
                    'requiere_verificacion_humana': c.requiere_verificacion_humana,
                }
                for c in candidatos[:top_n]
            ]
        })
    return sugerencias

"""
MNFC v0.2.0 - Capa 7 - Examinador de evidencia.

Panel de consulta. No decide. No autoriza. No camino critico.

Verifica tres niveles sobre una evidencia contable:
    1. nivel_linea     - coherencia de cada partida individual
    2. nivel_conjunto  - pertenencia de las cuentas al marco y universo
    3. examinar        - combinacion de los dos anteriores

Migrado de SCFV_DSR/scfv_dsr/contable/examinador.py.
Adaptado para importar del kernel MNFC en lugar de scfv_dsr.kernel.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from ..xnor import (
    NATURALEZAS_VALIDAS,
    MOVIMIENTOS_VALIDOS,
    ubicacion_booleana,
    ubicacion_gf2,
    ubicacion_signos,
)
from .reticulo import ReticuloCuentas


@dataclass
class Reporte:
    linea: dict = field(default_factory=dict)
    conjunto: dict = field(default_factory=dict)


def _nivel(ok: bool, hallazgos: list, detalles: dict = None) -> dict:
    return {"ok": ok, "hallazgos": hallazgos, "detalles": detalles or {}}


class ExaminadorEvidencia:
    def __init__(self, pcu: Mapping):
        self._pcu = dict(pcu)
        self._reticulo = ReticuloCuentas.desde_pcu(pcu)

    def examinar(self, evidencia: Mapping) -> Reporte:
        if not isinstance(evidencia, Mapping):
            raise TypeError(
                "examinar() espera Mapping, recibio "
                + type(evidencia).__name__
            )
        partidas = evidencia.get("partidas", []) or []
        marco = evidencia.get("marco_contable", "NIIF_Completas")
        linea = self.nivel_linea(partidas)
        cuentas = [
            p.get("cuenta_codigo") for p in partidas if p.get("cuenta_codigo")
        ]
        conjunto = self.nivel_conjunto(cuentas, marco=marco)
        return Reporte(linea=linea, conjunto=conjunto)

    def nivel_linea(self, partidas: list) -> dict:
        hallazgos = []
        detalles = {"n_partidas": len(partidas)}
        for i, p in enumerate(partidas):
            cc = p.get("cuenta_codigo")
            if not cc:
                hallazgos.append(
                    "partida[%d]: partida_incompleta (sin cuenta_codigo)" % i
                )
                continue
            if cc not in self._pcu:
                hallazgos.append(
                    "partida[%d]: cuenta_ausente '%s'" % (i, cc)
                )
                continue
            naturaleza = self._pcu[cc].get("naturaleza")
            if naturaleza not in NATURALEZAS_VALIDAS:
                hallazgos.append(
                    "partida[%d]: naturaleza_invalida '%s' en cuenta '%s'"
                    % (i, naturaleza, cc)
                )
                continue
            mov = p.get("movimiento")
            if mov not in MOVIMIENTOS_VALIDOS:
                hallazgos.append(
                    "partida[%d]: movimiento_invalido '%s'" % (i, mov)
                )
                continue
            b = ubicacion_booleana(naturaleza, mov)
            g = ubicacion_gf2(naturaleza, mov)
            s = ubicacion_signos(naturaleza, mov)
            if not (b == g == s):
                hallazgos.append(
                    "partida[%d]: XNOR_inconsistente b=%s g=%s s=%s"
                    % (i, b, g, s)
                )
                continue
            if "ubicacion" in p and p["ubicacion"] != b:
                hallazgos.append(
                    "partida[%d]: ubicacion_declarada '%s' != '%s'"
                    % (i, p["ubicacion"], b)
                )
        return _nivel(ok=not hallazgos, hallazgos=hallazgos, detalles=detalles)

    def nivel_conjunto(self, cuentas: Iterable, marco: str = None) -> dict:
        hallazgos = []
        cuentas = list(cuentas)
        detalles = {"n_cuentas": len(cuentas), "marco": marco}
        if marco is not None and marco not in self._reticulo.nombres():
            hallazgos.append("marco_ausente_en_pcu '%s'" % marco)
            return _nivel(ok=False, hallazgos=hallazgos, detalles=detalles)
        universo = self._reticulo.universo_set()
        C_marco = (
            self._reticulo.subconjunto(marco)
            if marco is not None else universo
        )
        for i, c in enumerate(cuentas):
            if c not in universo:
                hallazgos.append("cuenta[%d]: '%s' no en universo" % (i, c))
                continue
            if c not in C_marco:
                hallazgos.append(
                    "cuenta[%d]: '%s' no pertenece a marco '%s'" % (i, c, marco)
                )
        return _nivel(ok=not hallazgos, hallazgos=hallazgos, detalles=detalles)

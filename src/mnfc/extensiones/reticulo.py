"""
MNFC v0.2.0 - Capa 7 - Reticulo booleano de cuentas.

Estructura: (P(C), subset, union, interseccion, complemento, dif_simetrica).

NOTA FRACTAL: esta estructura es la misma algebra booleana que xnor.py,
aplicada al conjunto potencia de cuentas en lugar del conjunto {0,1}.
Misma ley, distinta escala. Autosimilitud verificable.

Sin dependencias de xnor.py ni mnfc.py. Solo stdlib.
Migrado desde SCFV_DSR/scfv_dsr/contable/reticulo.py.
"""
from typing import Iterable, Mapping


Cuenta = str
Subconjunto = frozenset


class ReticuloCuentas:
    """Reticulo booleano sobre el universo de cuentas C."""

    def __init__(self,
                 universo: Iterable[Cuenta],
                 subconjuntos: Mapping[str, Iterable[Cuenta]] | None = None):
        self._universo = frozenset(universo)
        self._subconjuntos = {}
        if subconjuntos is not None:
            for nombre, conjunto in subconjuntos.items():
                s = frozenset(conjunto)
                if not s <= self._universo:
                    fuera = s - self._universo
                    raise ValueError(
                        "subconjunto '%s' contiene cuentas fuera del universo: %s"
                        % (nombre, sorted(fuera))
                    )
                self._subconjuntos[nombre] = s

    @classmethod
    def desde_pcu(cls,
                  pcu: Mapping[str, Mapping],
                  clave: str = "marcos") -> "ReticuloCuentas":
        """Construye el reticulo desde un PCU: cada valor de 'clave' define un subconjunto."""
        universo = frozenset(pcu.keys())
        acumulador = {}
        for cuenta, meta in pcu.items():
            for v in meta.get(clave, []):
                acumulador.setdefault(v, set()).add(cuenta)
        return cls(universo, {k: frozenset(v) for k, v in acumulador.items()})

    # --- Universo y acceso ---
    def universo_set(self) -> Subconjunto:
        return self._universo

    def subconjunto(self, nombre: str) -> Subconjunto:
        if nombre not in self._subconjuntos:
            raise KeyError("subconjunto '%s' no existe" % nombre)
        return self._subconjuntos[nombre]

    def nombres(self) -> tuple:
        return tuple(sorted(self._subconjuntos.keys()))

    # --- Operaciones sobre nombres ---
    def union(self, *nombres: str) -> Subconjunto:
        resultado = frozenset()
        for n in nombres:
            resultado = resultado | self.subconjunto(n)
        return resultado

    def interseccion(self, *nombres: str) -> Subconjunto:
        if not nombres:
            return self._universo
        conjuntos = [self.subconjunto(n) for n in nombres]
        resultado = conjuntos[0]
        for c in conjuntos[1:]:
            resultado = resultado & c
        return resultado

    def complemento(self, nombre: str) -> Subconjunto:
        return self._universo - self.subconjunto(nombre)

    def diferencia_simetrica(self, a: str, b: str) -> Subconjunto:
        return self.subconjunto(a) ^ self.subconjunto(b)

    # --- Predicados ---
    def es_subconjunto(self, a: str, b: str) -> bool:
        return self.subconjunto(a) <= self.subconjunto(b)

    def es_particion(self, *nombres: str) -> bool:
        conjuntos = [self.subconjunto(n) for n in nombres]
        cubierto = frozenset()
        for c in conjuntos:
            cubierto = cubierto | c
        if cubierto != self._universo:
            return False
        for i, c1 in enumerate(conjuntos):
            for c2 in conjuntos[i + 1:]:
                if c1 & c2:
                    return False
        return True

    # --- Diagnostico ---
    def cuentas_sin_asignar(self) -> Subconjunto:
        cubierto = frozenset()
        for s in self._subconjuntos.values():
            cubierto = cubierto | s
        return self._universo - cubierto

    def cuentas_huerfanas(self) -> Subconjunto:
        return self.cuentas_sin_asignar()

    # --- Operaciones sobre conjuntos crudos ---
    def complemento_set(self, s: Iterable[Cuenta]) -> Subconjunto:
        return self._universo - frozenset(s)

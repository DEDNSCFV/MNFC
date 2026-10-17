"""MNFC DSL — Fase 3a · Semantic (validación de coherencia).

Recorre un Programa ya parseado y verifica coherencia interna:

- Unicidad de declaraciones (categorías, hechos, marcos, elementos,
  fractales, reglas por fractal).
- Referencias resueltas: toda categoría/hecho/marco citada debe estar
  declarada en el mismo Programa.
- Walk recursivo sobre condiciones y conjuntos.

No ejecuta reglas. No carga marcos reales. No valida contra registry.

Sin posición en el AST: el contexto es un path jerárquico legible.
Ejemplo: "FRACTAL ventas > REGLA r1 > GENERAR CONSECUENCIA #2 > fuente="

Sin dependencias externas. Solo stdlib.
"""

from typing import List, Set

from .parser import (
    Programa,
    Accion,
    CmpEscalar,
    HechoRef,
    NegBool,
    Conjuncion,
    Disyuncion,
    CategoriaRef,
    SetLiteral,
    Union,
    Inter,
    Diff,
    Complemento,
    Relacion,
)


class DSLSemanticError(Exception):
    """Error semántico del DSL. Incluye contexto jerárquico."""

    def __init__(self, mensaje: str, contexto: str = ""):
        self.mensaje = mensaje
        self.contexto = contexto
        if contexto:
            super().__init__(f"{contexto}: {mensaje}")
        else:
            super().__init__(mensaje)


def validar(programa: Programa) -> None:
    """Valida coherencia semántica. Lanza DSLSemanticError si falla."""
    _validar_declaraciones(programa)
    _validar_referencias(programa)


# ═════════════════════════════════════════════════════════════════════
# A · Unicidad de declaraciones
# ═════════════════════════════════════════════════════════════════════

def _validar_declaraciones(programa: Programa) -> None:
    _unicos([e.nombre for e in programa.elementos], "ELEMENTO")
    _unicos([c.nombre for c in programa.categorias], "CATEGORIA")
    _unicos(programa.hechos, "HECHO")
    _unicos(programa.marcos, "MARCO")
    _unicos([f.nombre for f in programa.fractales], "FRACTAL")
    for fractal in programa.fractales:
        _unicos(
            [r.nombre for r in fractal.reglas],
            "REGLA",
            contexto=f"FRACTAL {fractal.nombre}",
        )


def _unicos(nombres: List[str], tipo: str, contexto: str = "") -> None:
    vistos: Set[str] = set()
    for nombre in nombres:
        if nombre in vistos:
            raise DSLSemanticError(
                f"{tipo} '{nombre}' declarado dos veces", contexto
            )
        vistos.add(nombre)


# ═════════════════════════════════════════════════════════════════════
# B · Referencias resueltas
# ═════════════════════════════════════════════════════════════════════

def _validar_referencias(programa: Programa) -> None:
    elementos = {e.nombre for e in programa.elementos}
    categorias = {c.nombre for c in programa.categorias}
    hechos = set(programa.hechos)
    marcos = set(programa.marcos)

    # B.1 · Categoria.elemento debe existir
    for cat in programa.categorias:
        if cat.elemento not in elementos:
            raise DSLSemanticError(
                f"CATEGORIA '{cat.nombre}' referencia elemento "
                f"'{cat.elemento}' no declarado",
                f"CATEGORIA {cat.nombre}",
            )

    # B.2 · Walk de fractales
    for fractal in programa.fractales:
        ctx_fractal = f"FRACTAL {fractal.nombre}"
        for regla in fractal.reglas:
            ctx_regla = f"{ctx_fractal} > REGLA {regla.nombre}"
            _walk_cond(
                regla.condicion, categorias, hechos,
                f"{ctx_regla} > condición",
            )
            for i, accion in enumerate(regla.acciones, start=1):
                _validar_accion(
                    accion, categorias, marcos,
                    f"{ctx_regla} > GENERAR CONSECUENCIA #{i}",
                )


def _validar_accion(
    accion: Accion, categorias: Set[str],
    marcos: Set[str], contexto: str,
) -> None:
    if accion.categoria is not None:
        _walk_set(accion.categoria, categorias, f"{contexto} > categoria=")
    if accion.fuente is not None:
        if accion.fuente.marco not in marcos:
            raise DSLSemanticError(
                f"fuente cita marco '{accion.fuente.marco}' no declarado",
                f"{contexto} > fuente=",
            )


# ═════════════════════════════════════════════════════════════════════
# C · Walk de condiciones
# ═════════════════════════════════════════════════════════════════════

def _walk_cond(
    nodo, categorias: Set[str], hechos: Set[str], contexto: str,
) -> None:
    if nodo is None:
        return
    if isinstance(nodo, HechoRef):
        if nodo.nombre not in hechos:
            raise DSLSemanticError(
                f"hecho '{nodo.nombre}' citado pero no declarado",
                contexto,
            )
    elif isinstance(nodo, NegBool):
        _walk_cond(nodo.interno, categorias, hechos, contexto)
    elif isinstance(nodo, (Conjuncion, Disyuncion)):
        for p in nodo.partes:
            _walk_cond(p, categorias, hechos, contexto)
    elif isinstance(nodo, Relacion):
        _walk_set(nodo.izq, categorias, f"{contexto} > izq")
        _walk_set(nodo.der, categorias, f"{contexto} > der")
    elif isinstance(nodo, CmpEscalar):
        # izq/der son variables de evidencia en runtime. No se validan.
        return


# ═════════════════════════════════════════════════════════════════════
# D · Walk de conjuntos
# ═════════════════════════════════════════════════════════════════════

def _walk_set(nodo, categorias: Set[str], contexto: str) -> None:
    if nodo is None:
        return
    if isinstance(nodo, CategoriaRef):
        if nodo.nombre not in categorias:
            raise DSLSemanticError(
                f"categoría '{nodo.nombre}' citada pero no declarada",
                contexto,
            )
    elif isinstance(nodo, SetLiteral):
        for item in nodo.items:
            if item not in categorias:
                raise DSLSemanticError(
                    f"categoría '{item}' citada en conjunto pero no declarada",
                    contexto,
                )
    elif isinstance(nodo, (Union, Inter, Diff)):
        _walk_set(nodo.izq, categorias, f"{contexto} > izq")
        _walk_set(nodo.der, categorias, f"{contexto} > der")
    elif isinstance(nodo, Complemento):
        _walk_set(nodo.interno, categorias, f"{contexto} > interno")

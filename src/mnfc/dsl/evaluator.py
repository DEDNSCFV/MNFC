"""MNFC DSL — Fase 3b · Evaluator (ejecución del AST).

Recorre un Programa ya validado (parse + semantic) y ejecuta cada
regla cuya condición se cumpla contra un contexto de hechos/variables.

Produce PartidaAutorizada por cada cuenta resuelta. No persiste.
No cuadra. No ensambla Asiento. Eso es Fase 4.

Las operaciones contables y el Plan de Cuentas se INYECTAN:
- operaciones: dict {nombre: fn(contexto) -> float}.
- pcu: dict {cuenta: {naturaleza, marcos, nombre}}.

Sin marcos reales. Sin fiscal. Sin registry cargado desde disco.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

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
    Cita,
)
from ..extensiones.modelos import PartidaAutorizada
from ..extensiones.reticulo import ReticuloCuentas
from ..xnor import ubicacion_booleana


class DSLEvaluationError(Exception):
    """Error de evaluación del DSL. Incluye contexto jerárquico."""

    def __init__(self, mensaje: str, contexto: str = ""):
        self.mensaje = mensaje
        self.contexto = contexto
        if contexto:
            super().__init__(f"{contexto}: {mensaje}")
        else:
            super().__init__(mensaje)


@dataclass
class ResultadoAccion:
    """Una acción ejecutada con sus partidas resueltas."""
    fractal: str
    regla: str
    indice: int
    partidas: List[PartidaAutorizada]
    evidencia: Optional[str] = None


# ═════════════════════════════════════════════════════════════════════
# Punto de entrada
# ═════════════════════════════════════════════════════════════════════

def evaluar(
    programa: Programa,
    contexto: Dict[str, Any],
    pcu: Dict[str, Dict[str, Any]],
    operaciones: Dict[str, Callable],
    marco_contable: str,
    correlation_id: str = "",
) -> List[ResultadoAccion]:
    """Ejecuta el Programa contra contexto/pcu/operaciones."""
    reticulo = ReticuloCuentas.desde_pcu(pcu, clave="marcos")
    cuentas_marco = reticulo.subconjunto(marco_contable) \
        if marco_contable in reticulo.nombres() else frozenset()

    resultados: List[ResultadoAccion] = []

    for fractal in programa.fractales:
        for regla in fractal.reglas:
            ctx_regla = f"FRACTAL {fractal.nombre} > REGLA {regla.nombre}"
            if not evaluar_condicion(regla.condicion, contexto, ctx_regla):
                continue

            for i, accion in enumerate(regla.acciones, start=1):
                ctx_acc = f"{ctx_regla} > GENERAR CONSECUENCIA #{i}"
                partidas = evaluar_accion(
                    accion, contexto, pcu, reticulo, cuentas_marco,
                    operaciones, marco_contable, correlation_id, ctx_acc,
                )
                resultados.append(ResultadoAccion(
                    fractal=fractal.nombre,
                    regla=regla.nombre,
                    indice=i,
                    partidas=partidas,
                    evidencia=accion.evidencia,
                ))

    return resultados


# ═════════════════════════════════════════════════════════════════════
# Condiciones
# ═════════════════════════════════════════════════════════════════════

def evaluar_condicion(
    nodo, contexto: Dict[str, Any], ctx: str = "",
) -> bool:
    """Evalúa un nodo de condición contra el contexto. Devuelve bool."""
    if nodo is None:
        raise DSLEvaluationError("condición vacía", ctx)

    if isinstance(nodo, HechoRef):
        if nodo.nombre not in contexto:
            raise DSLEvaluationError(
                f"hecho '{nodo.nombre}' no presente en contexto", ctx
            )
        return bool(contexto[nodo.nombre])

    if isinstance(nodo, NegBool):
        return not evaluar_condicion(nodo.interno, contexto, ctx)

    if isinstance(nodo, Conjuncion):
        return all(evaluar_condicion(p, contexto, ctx) for p in nodo.partes)

    if isinstance(nodo, Disyuncion):
        return any(evaluar_condicion(p, contexto, ctx) for p in nodo.partes)

    if isinstance(nodo, Relacion):
        # ∈ / ⊆ : resuelve ambos lados como conjuntos y compara
        # Nota: requiere un retículo. En condiciones no lo inyectamos.
        # Si aparece acá, es error de uso: relación se resuelve en acciones.
        raise DSLEvaluationError(
            f"relación '{nodo.op}' en condición no soportada en Fase 3b", ctx
        )

    if isinstance(nodo, CmpEscalar):
        return _evaluar_cmp(nodo, contexto, ctx)

    raise DSLEvaluationError(
        f"nodo de condición inesperado: {type(nodo).__name__}", ctx
    )


def _evaluar_cmp(
    nodo: CmpEscalar, contexto: Dict[str, Any], ctx: str,
) -> bool:
    """Evalúa comparación escalar (izq op der)."""
    izq = _resolver_valor(nodo.izq, contexto, ctx)
    der = _resolver_valor(nodo.der, contexto, ctx)
    op = nodo.op
    try:
        if op == "==": return izq == der
        if op == "!=": return izq != der
        if op == ">":  return izq > der
        if op == "<":  return izq < der
        if op == ">=": return izq >= der
        if op == "<=": return izq <= der
    except TypeError as e:
        raise DSLEvaluationError(
            f"comparación '{op}' falla entre {type(izq).__name__} "
            f"y {type(der).__name__}: {e}", ctx
        )
    raise DSLEvaluationError(f"operador desconocido: {op}", ctx)


def _resolver_valor(ref: str, contexto: Dict[str, Any], ctx: str):
    """Convierte una referencia a valor concreto.

    Orden: contexto → número → string.
    """
    if ref in contexto:
        return contexto[ref]
    try:
        return float(ref)
    except (TypeError, ValueError):
        return ref


# ═════════════════════════════════════════════════════════════════════
# Conjuntos
# ═════════════════════════════════════════════════════════════════════

def evaluar_set(nodo, reticulo: ReticuloCuentas, ctx: str = "") -> frozenset:
    """Resuelve un nodo de conjunto a frozenset de cuentas."""
    if nodo is None:
        raise DSLEvaluationError("conjunto vacío", ctx)

    if isinstance(nodo, CategoriaRef):
        if nodo.nombre not in reticulo.nombres():
            raise DSLEvaluationError(
                f"subconjunto '{nodo.nombre}' no existe en el retículo", ctx
            )
        return reticulo.subconjunto(nodo.nombre)

    if isinstance(nodo, SetLiteral):
        # Literal: cada item es una categoría → unión de sus cuentas
        acumulado: frozenset = frozenset()
        for item in nodo.items:
            if item not in reticulo.nombres():
                raise DSLEvaluationError(
                    f"subconjunto '{item}' del literal no existe en el retículo",
                    ctx,
                )
            acumulado = acumulado | reticulo.subconjunto(item)
        return acumulado

    if isinstance(nodo, Union):
        return evaluar_set(nodo.izq, reticulo, ctx) | evaluar_set(nodo.der, reticulo, ctx)

    if isinstance(nodo, Inter):
        return evaluar_set(nodo.izq, reticulo, ctx) & evaluar_set(nodo.der, reticulo, ctx)

    if isinstance(nodo, Diff):
        return evaluar_set(nodo.izq, reticulo, ctx) - evaluar_set(nodo.der, reticulo, ctx)

    if isinstance(nodo, Complemento):
        return reticulo.universo_set() - evaluar_set(nodo.interno, reticulo, ctx)

    raise DSLEvaluationError(
        f"nodo de conjunto inesperado: {type(nodo).__name__}", ctx
    )


# ═════════════════════════════════════════════════════════════════════
# Acciones
# ═════════════════════════════════════════════════════════════════════

def evaluar_accion(
    accion: Accion,
    contexto: Dict[str, Any],
    pcu: Dict[str, Dict[str, Any]],
    reticulo: ReticuloCuentas,
    cuentas_marco: frozenset,
    operaciones: Dict[str, Callable],
    marco_contable: str,
    correlation_id: str,
    ctx: str,
) -> List[PartidaAutorizada]:
    """Ejecuta una acción y produce una PartidaAutorizada por cuenta."""
    # 1. Resolver operación → monto
    if not accion.operacion:
        raise DSLEvaluationError("acción sin 'operacion='", ctx)
    if accion.operacion not in operaciones:
        raise DSLEvaluationError(
            f"operación '{accion.operacion}' no está en el registry", ctx
        )
    try:
        monto = operaciones[accion.operacion](contexto)
    except Exception as e:
        raise DSLEvaluationError(
            f"operación '{accion.operacion}' falló: {e}", ctx
        ) from e
    if not isinstance(monto, (int, float)):
        raise DSLEvaluationError(
            f"operación '{accion.operacion}' retornó "
            f"{type(monto).__name__}, no número", ctx
        )
    monto = float(monto)

    # 2. Resolver movimiento
    if not accion.movimiento:
        raise DSLEvaluationError("acción sin 'movimiento='", ctx)

    # 3. Resolver categoría → cuentas
    if accion.categoria is None:
        raise DSLEvaluationError("acción sin 'categoria='", ctx)
    cuentas = evaluar_set(accion.categoria, reticulo, f"{ctx} > categoria=")
    if not cuentas:
        raise DSLEvaluationError(
            "categoria= se resolvió a conjunto vacío", ctx
        )

    # 4. Filtrar cuentas que aplican al marco (si el marco está cargado)
    if cuentas_marco:
        cuentas = cuentas & cuentas_marco
    if not cuentas:
        raise DSLEvaluationError(
            f"ninguna cuenta de categoria= aplica al marco '{marco_contable}'",
            ctx,
        )

    # 5. Construir PartidaAutorizada por cuenta
    norma_id = (
        f"{accion.fuente.marco}:{accion.fuente.seccion}"
        if accion.fuente else None
    )
    partidas: List[PartidaAutorizada] = []
    for cuenta in sorted(cuentas):
        if cuenta not in pcu:
            raise DSLEvaluationError(
                f"cuenta '{cuenta}' no está en el PCU", ctx
            )
        naturaleza = pcu[cuenta].get("naturaleza")
        if naturaleza not in ("DEUDORA", "ACREEDORA"):
            raise DSLEvaluationError(
                f"cuenta '{cuenta}' tiene naturaleza inválida: {naturaleza!r}",
                ctx,
            )
        ubicacion = ubicacion_booleana(naturaleza, accion.movimiento)
        partidas.append(PartidaAutorizada(
            cuenta_codigo=cuenta,
            cuenta_version=pcu[cuenta].get("version", ""),
            monto=monto,
            ubicacion=ubicacion,
            movimiento=accion.movimiento,
            norma_id=norma_id,
        ))

    return partidas

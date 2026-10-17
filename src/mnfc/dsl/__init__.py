"""MNFC DSL — Fases 2 + 3a + 3b + 4 + 5 + 6
Parser, validación semántica, evaluador, assembler, registry y
persistencia para la gramática v1.6.

API pública:
    parse(texto) -> Programa
    validar(programa) -> None
    evaluar(programa, contexto, pcu, operaciones, marco, corr) -> list[ResultadoAccion]
    ensamblar(resultados, contexto) -> list[Asiento]
    persistir(asientos, store, correlation_id, periodo_id, fecha) -> list[str]
    Registry, OperacionRegistrada
    DSLSyntaxError, DSLSemanticError, DSLEvaluationError,
    DSLAssemblyError, DSLRegistryError, DSLPersistenceError
    Programa, ResultadoAccion

Sin dependencias externas. Solo stdlib.
"""

from .parser import parse, Programa, DSLSyntaxError
from .semantic import validar, DSLSemanticError
from .evaluator import evaluar, ResultadoAccion, DSLEvaluationError
from .assembler import ensamblar, DSLAssemblyError
from .registry import Registry, OperacionRegistrada, DSLRegistryError
from .persistencia import persistir, DSLPersistenceError

__all__ = [
    "parse",
    "validar",
    "evaluar",
    "ensamblar",
    "persistir",
    "Registry",
    "OperacionRegistrada",
    "Programa",
    "ResultadoAccion",
    "DSLSyntaxError",
    "DSLSemanticError",
    "DSLEvaluationError",
    "DSLAssemblyError",
    "DSLRegistryError",
    "DSLPersistenceError",
]

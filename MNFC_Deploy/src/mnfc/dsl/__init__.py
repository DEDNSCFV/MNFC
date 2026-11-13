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

from .assembler import DSLAssemblyError, ensamblar
from .evaluator import DSLEvaluationError, ResultadoAccion, evaluar
from .parser import DSLSyntaxError, Programa, parse
from .persistencia import DSLPersistenceError, persistir
from .registry import DSLRegistryError, OperacionRegistrada, Registry
from .semantic import DSLSemanticError, validar

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

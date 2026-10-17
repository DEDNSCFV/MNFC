"""MNFC DSL — Fases 2 + 3a + 3b + 4 + 5
Parser, validación semántica, evaluador, assembler y registry
para la gramática v1.6.

API pública:
    parse(texto) -> Programa
    validar(programa) -> None
    evaluar(programa, contexto, pcu, operaciones, marco, corr) -> list[ResultadoAccion]
    ensamblar(resultados, contexto) -> list[Asiento]
    Registry, OperacionRegistrada
    DSLSyntaxError, DSLSemanticError, DSLEvaluationError,
    DSLAssemblyError, DSLRegistryError
    Programa, ResultadoAccion

Sin dependencias externas. Solo stdlib.
"""

from .parser import parse, Programa, DSLSyntaxError
from .semantic import validar, DSLSemanticError
from .evaluator import evaluar, ResultadoAccion, DSLEvaluationError
from .assembler import ensamblar, DSLAssemblyError
from .registry import Registry, OperacionRegistrada, DSLRegistryError

__all__ = [
    "parse",
    "validar",
    "evaluar",
    "ensamblar",
    "Registry",
    "OperacionRegistrada",
    "Programa",
    "ResultadoAccion",
    "DSLSyntaxError",
    "DSLSemanticError",
    "DSLEvaluationError",
    "DSLAssemblyError",
    "DSLRegistryError",
]

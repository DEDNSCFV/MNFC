"""MNFC DSL — Fases 2 + 3a + 3b
Parser, validación semántica y evaluador para la gramática v1.6.

API pública:
    parse(texto) -> Programa
    validar(programa) -> None
    evaluar(programa, contexto, pcu, operaciones, marco, corr) -> list[ResultadoAccion]
    DSLSyntaxError, DSLSemanticError, DSLEvaluationError
    Programa, ResultadoAccion

Sin dependencias externas. Solo stdlib.
"""

from .parser import parse, Programa, DSLSyntaxError
from .semantic import validar, DSLSemanticError
from .evaluator import evaluar, ResultadoAccion, DSLEvaluationError

__all__ = [
    "parse",
    "validar",
    "evaluar",
    "Programa",
    "ResultadoAccion",
    "DSLSyntaxError",
    "DSLSemanticError",
    "DSLEvaluationError",
]

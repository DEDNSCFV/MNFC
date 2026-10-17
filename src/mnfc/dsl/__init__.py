"""MNFC DSL — Fases 2 + 3a + 3b + 4
Parser, validación semántica, evaluador y assembler para la
gramática v1.6.

API pública:
    parse(texto) -> Programa
    validar(programa) -> None
    evaluar(programa, contexto, pcu, operaciones, marco, corr) -> list[ResultadoAccion]
    ensamblar(resultados, contexto) -> list[Asiento]
    DSLSyntaxError, DSLSemanticError, DSLEvaluationError, DSLAssemblyError
    Programa, ResultadoAccion

Sin dependencias externas. Solo stdlib.
"""

from .parser import parse, Programa, DSLSyntaxError
from .semantic import validar, DSLSemanticError
from .evaluator import evaluar, ResultadoAccion, DSLEvaluationError
from .assembler import ensamblar, DSLAssemblyError

__all__ = [
    "parse",
    "validar",
    "evaluar",
    "ensamblar",
    "Programa",
    "ResultadoAccion",
    "DSLSyntaxError",
    "DSLSemanticError",
    "DSLEvaluationError",
    "DSLAssemblyError",
]

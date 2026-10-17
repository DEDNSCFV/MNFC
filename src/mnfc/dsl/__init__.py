"""MNFC DSL — Fases 2 + 3a
Parser (Fase 2) y validación semántica (Fase 3a) para la gramática v1.6.

API pública:
    parse(texto: str, archivo: str = "<input>") -> Programa
    validar(programa: Programa) -> None
    DSLSyntaxError
    DSLSemanticError

Uso:
    from mnfc.dsl import parse, validar, DSLSyntaxError, DSLSemanticError

    try:
        ast = parse(texto)
        validar(ast)
    except DSLSyntaxError as e:
        print("sintaxis:", e)
    except DSLSemanticError as e:
        print("semántica:", e)

Sin dependencias externas. Solo stdlib.
"""

from .parser import parse, Programa, DSLSyntaxError
from .semantic import validar, DSLSemanticError

__all__ = [
    "parse",
    "validar",
    "Programa",
    "DSLSyntaxError",
    "DSLSemanticError",
]

"""
MNFC DSL — Fase 2
Parser para la gramática v1.6.

API pública:
    parse(texto: str, archivo: str = "<input>") -> Programa
    DSLSyntaxError

Uso:
    from mnfc.dsl import parse, DSLSyntaxError

    try:
        ast = parse(texto_scfv)
    except DSLSyntaxError as e:
        print(e)

Sin dependencias externas. Solo stdlib.
"""

from .parser import parse, Programa, DSLSyntaxError

__all__ = ["parse", "Programa", "DSLSyntaxError"]

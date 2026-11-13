#!/usr/bin/env python3
"""Agrega la regla #18 al DSL."""
from pathlib import Path
import sys

dsl = Path.home() / "MNFC" / "dartony_17_reglas.mnfc"
texto = dsl.read_text(encoding='utf-8')

if 'regla_18' in texto:
    print("Regla #18 ya existe.")
    sys.exit(0)

texto = texto.replace(
    'regla_17 : "Coherencia bimonetaria";',
    'regla_17 : "Coherencia bimonetaria";\n  regla_18 : "No duplicar movimientos";'
)
texto = texto.replace(
    'HECHO violacion_17;',
    'HECHO violacion_17;\nHECHO violacion_18;'
)
texto = texto.replace(
    'REGLA regla_17:\n    SI violacion_17 ENTONCES GENERAR CONSECUENCIA (categoria = categoria(violacion_17), operacion = violacion_regla_17, movimiento = DISMINUYE, fuente = PokaYoke:17, evidencia = regla_17_log);',
    'REGLA regla_17:\n    SI violacion_17 ENTONCES GENERAR CONSECUENCIA (categoria = categoria(violacion_17), operacion = violacion_regla_17, movimiento = DISMINUYE, fuente = PokaYoke:17, evidencia = regla_17_log);\n  REGLA regla_18:\n    SI violacion_18 ENTONCES GENERAR CONSECUENCIA (categoria = categoria(violacion_18), operacion = violacion_regla_18, movimiento = DISMINUYE, fuente = PokaYoke:18, evidencia = regla_18_log);'
)

dsl.write_text(texto, encoding='utf-8')
print("Regla #18 agregada al DSL.")

sys.path.insert(0, str(Path.home() / "MNFC/src"))
from mnfc.dsl import parser
ast = parser.parse(texto)
print(f"Reglas en el DSL: {len(ast.fractales[0].reglas)}")

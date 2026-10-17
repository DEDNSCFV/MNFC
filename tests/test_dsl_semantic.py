"""Tests de validación semántica del DSL (Fase 3a).

Verifican que src/mnfc/dsl/semantic.py detecta:
- Declaraciones duplicadas.
- Referencias no resueltas (categorías, hechos, marcos, elementos).
- Casos válidos completos.

Solo validación de coherencia. No ejecuta reglas ni carga marcos reales.
"""
import pytest
from mnfc.dsl import parse, validar, DSLSemanticError


# ═════════════════════════════════════════════════════════════════════
# Fixtures
# ═════════════════════════════════════════════════════════════════════

DSL_VALIDO_MINIMO = 'DSL_VERSION "1.6";'

DSL_VALIDO_COMPLETO = '''
DSL_VERSION "1.6";
ELEMENTOS { activo : "Recurso"; pasivo; patrimonio; }
MARCOS { PYMES; NIIF_Completas; BA_VEN_NIF; }
CATEGORIA inventarios = elemento: activo; universal: VERDADERO;
CATEGORIA ppe = elemento: activo; universal: FALSO;
HECHO activo_es_venta;
HECHO economia_hiperinflacionaria;
FRACTAL ventas:
    REGLA venta_simple:
        SI activo_es_venta
        ENTONCES GENERAR CONSECUENCIA(categoria=categoria(inventarios), operacion=suma_montos, movimiento=AUMENTA, fuente=PYMES:S23.1);
'''


# ═════════════════════════════════════════════════════════════════════
# A · Validación de declaraciones (unicidad)
# ═════════════════════════════════════════════════════════════════════

class TestUnicidadDeclaraciones:

    def test_categoria_duplicada(self):
        src = '''
        DSL_VERSION "1.6";
        ELEMENTOS { activo; }
        CATEGORIA x = elemento: activo; universal: VERDADERO;
        CATEGORIA x = elemento: activo; universal: FALSO;
        '''
        with pytest.raises(DSLSemanticError, match="CATEGORIA 'x' declarado dos veces"):
            validar(parse(src))

    def test_hecho_duplicado(self):
        src = '''
        DSL_VERSION "1.6";
        HECHO activo;
        HECHO activo;
        '''
        with pytest.raises(DSLSemanticError, match="HECHO 'activo' declarado dos veces"):
            validar(parse(src))

    def test_marco_duplicado(self):
        src = '''
        DSL_VERSION "1.6";
        MARCOS { PYMES; PYMES; }
        '''
        with pytest.raises(DSLSemanticError, match="MARCO 'PYMES' declarado dos veces"):
            validar(parse(src))

    def test_elemento_duplicado(self):
        src = '''
        DSL_VERSION "1.6";
        ELEMENTOS { activo; activo; }
        '''
        with pytest.raises(DSLSemanticError, match="ELEMENTO 'activo' declarado dos veces"):
            validar(parse(src))

    def test_fractal_duplicado(self):
        src = '''
        DSL_VERSION "1.6";
        HECHO h;
        MARCOS { PYMES; }
        FRACTAL f: REGLA r1: SI h ENTONCES GENERAR CONSECUENCIA(operacion=op, movimiento=AUMENTA, fuente=PYMES:S1);
        FRACTAL f: REGLA r2: SI h ENTONCES GENERAR CONSECUENCIA(operacion=op, movimiento=AUMENTA, fuente=PYMES:S1);
        '''
        with pytest.raises(DSLSemanticError, match="FRACTAL 'f' declarado dos veces"):
            validar(parse(src))

    def test_regla_duplicada_en_fractal(self):
        src = '''
        DSL_VERSION "1.6";
        HECHO h;
        MARCOS { PYMES; }
        FRACTAL f:
            REGLA r: SI h ENTONCES GENERAR CONSECUENCIA(operacion=op, movimiento=AUMENTA, fuente=PYMES:S1);
            REGLA r: SI h ENTONCES GENERAR CONSECUENCIA(operacion=op, movimiento=AUMENTA, fuente=PYMES:S1);
        '''
        with pytest.raises(DSLSemanticError, match="REGLA 'r' declarado dos veces"):
            validar(parse(src))

    def test_regla_mismo_nombre_en_fractales_distintos_ok(self):
        """Misma regla en fractales distintos es válido."""
        src = '''
        DSL_VERSION "1.6";
        HECHO h;
        MARCOS { PYMES; }
        FRACTAL f1: REGLA r: SI h ENTONCES GENERAR CONSECUENCIA(operacion=op, movimiento=AUMENTA, fuente=PYMES:S1);
        FRACTAL f2: REGLA r: SI h ENTONCES GENERAR CONSECUENCIA(operacion=op, movimiento=AUMENTA, fuente=PYMES:S1);
        '''
        validar(parse(src))  # no raise


# ═════════════════════════════════════════════════════════════════════
# B · Referencias resueltas en acciones
# ═════════════════════════════════════════════════════════════════════

class TestReferenciasAcciones:

    def _programa_con_accion(self, args):
        return f'''
        DSL_VERSION "1.6";
        ELEMENTOS {{ activo; }}
        MARCOS {{ PYMES; }}
        CATEGORIA inv = elemento: activo; universal: VERDADERO;
        HECHO h;
        FRACTAL f:
            REGLA r: SI h
            ENTONCES GENERAR CONSECUENCIA({args});
        '''

    def test_categoria_no_declarada_en_accion(self):
        src = self._programa_con_accion(
            'categoria=categoria(noexiste), operacion=op, movimiento=AUMENTA, fuente=PYMES:S1'
        )
        with pytest.raises(DSLSemanticError, match="categoría 'noexiste' citada pero no declarada"):
            validar(parse(src))

    def test_marco_no_declarado_en_fuente(self):
        src = self._programa_con_accion(
            'categoria=categoria(inv), operacion=op, movimiento=AUMENTA, fuente=NO_DECLARADO:S1'
        )
        with pytest.raises(DSLSemanticError, match="marco 'NO_DECLARADO' no declarado"):
            validar(parse(src))

    def test_categoria_declarada_ok(self):
        src = self._programa_con_accion(
            'categoria=categoria(inv), operacion=op, movimiento=AUMENTA, fuente=PYMES:S1'
        )
        validar(parse(src))  # no raise

    def test_set_literal_con_categoria_no_declarada(self):
        src = self._programa_con_accion(
            'categoria={inv, noexiste}, operacion=op, movimiento=AUMENTA, fuente=PYMES:S1'
        )
        with pytest.raises(DSLSemanticError, match="categoría 'noexiste' citada en conjunto"):
            validar(parse(src))

    def test_union_con_categoria_no_declarada(self):
        src = self._programa_con_accion(
            'categoria=categoria(inv) ∪ categoria(fantasma), operacion=op, movimiento=AUMENTA, fuente=PYMES:S1'
        )
        with pytest.raises(DSLSemanticError, match="categoría 'fantasma'"):
            validar(parse(src))

    def test_complemento_con_categoria_no_declarada(self):
        src = self._programa_con_accion(
            'categoria=¬ categoria(fantasma), operacion=op, movimiento=AUMENTA, fuente=PYMES:S1'
        )
        with pytest.raises(DSLSemanticError, match="categoría 'fantasma'"):
            validar(parse(src))


# ═════════════════════════════════════════════════════════════════════
# C · Condiciones y conjuntos
# ═════════════════════════════════════════════════════════════════════

class TestCondiciones:

    def _programa_con_condicion(self, condicion):
        return f'''
        DSL_VERSION "1.6";
        ELEMENTOS {{ activo; }}
        MARCOS {{ PYMES; }}
        CATEGORIA a = elemento: activo; universal: VERDADERO;
        CATEGORIA b = elemento: activo; universal: VERDADERO;
        HECHO h1;
        HECHO h2;
        FRACTAL f:
            REGLA r: SI {condicion}
            ENTONCES GENERAR CONSECUENCIA(operacion=op, movimiento=AUMENTA, fuente=PYMES:S1);
        '''

    def test_hecho_no_declarado(self):
        with pytest.raises(DSLSemanticError, match="hecho 'no_existe' citado pero no declarado"):
            validar(parse(self._programa_con_condicion("no_existe")))

    def test_hecho_declarado_ok(self):
        validar(parse(self._programa_con_condicion("h1")))

    def test_conjuncion_ambos_declarados_ok(self):
        validar(parse(self._programa_con_condicion("h1 Y h2")))

    def test_conjuncion_con_no_declarado(self):
        with pytest.raises(DSLSemanticError, match="hecho 'no_existe'"):
            validar(parse(self._programa_con_condicion("h1 Y no_existe")))

    def test_disyuncion_con_no_declarado(self):
        with pytest.raises(DSLSemanticError, match="hecho 'no_existe'"):
            validar(parse(self._programa_con_condicion("h1 O no_existe")))

    def test_negacion_de_hecho_declarado(self):
        validar(parse(self._programa_con_condicion("NO h1")))

    def test_negacion_de_hecho_no_declarado(self):
        with pytest.raises(DSLSemanticError, match="hecho 'no_existe'"):
            validar(parse(self._programa_con_condicion("NO no_existe")))

    def test_relacion_con_categoria_no_declarada(self):
        with pytest.raises(DSLSemanticError, match="categoría 'fantasma'"):
            validar(parse(self._programa_con_condicion(
                "categoria(a) ⊆ categoria(fantasma)"
            )))

    def test_relacion_con_ambas_declaradas(self):
        validar(parse(self._programa_con_condicion(
            "categoria(a) ⊆ categoria(b)"
        )))

    def test_comparacion_no_valida_hechos(self):
        """CmpEscalar.izq/der son variables de evidencia en runtime."""
        validar(parse(self._programa_con_condicion("monto > 100")))


# ═════════════════════════════════════════════════════════════════════
# D · Casos válidos completos
# ═════════════════════════════════════════════════════════════════════

class TestCasosValidos:

    def test_programa_minimo(self):
        validar(parse(DSL_VALIDO_MINIMO))

    def test_programa_completo(self):
        validar(parse(DSL_VALIDO_COMPLETO))

    def test_categoria_referencia_elemento_declarado(self):
        src = '''
        DSL_VERSION "1.6";
        ELEMENTOS { activo; }
        CATEGORIA x = elemento: activo; universal: VERDADERO;
        '''
        validar(parse(src))

    def test_fractal_sin_categorias_ni_hechos_solo_operacion(self):
        src = '''
        DSL_VERSION "1.6";
        MARCOS { PYMES; }
        HECHO h;
        FRACTAL f:
            REGLA r: SI h
            ENTONCES GENERAR CONSECUENCIA(operacion=suma_montos, movimiento=AUMENTA, fuente=PYMES:S1);
        '''
        validar(parse(src))


# ═════════════════════════════════════════════════════════════════════
# E · Errores específicos de referencia de elementos
# ═════════════════════════════════════════════════════════════════════

class TestReferenciaElemento:

    def test_categoria_con_elemento_no_declarado(self):
        src = '''
        DSL_VERSION "1.6";
        ELEMENTOS { pasivo; }
        CATEGORIA x = elemento: activo; universal: VERDADERO;
        '''
        with pytest.raises(DSLSemanticError, match="referencia elemento 'activo' no declarado"):
            validar(parse(src))

    def test_categoria_con_elemento_declarado(self):
        src = '''
        DSL_VERSION "1.6";
        ELEMENTOS { activo; }
        CATEGORIA x = elemento: activo; universal: VERDADERO;
        '''
        validar(parse(src))


# ═════════════════════════════════════════════════════════════════════
# F · Integración: parse + validar
# ═════════════════════════════════════════════════════════════════════

class TestIntegracion:

    def test_parse_ok_pero_validar_falla(self):
        """Sintaxis correcta, semántica incorrecta."""
        src = '''
        DSL_VERSION "1.6";
        HECHO h;
        MARCOS { PYMES; }
        FRACTAL f:
            REGLA r: SI h
            ENTONCES GENERAR CONSECUENCIA(categoria=categoria(fantasma), operacion=op, movimiento=AUMENTA, fuente=PYMES:S1);
        '''
        prog = parse(src)  # no raise
        with pytest.raises(DSLSemanticError):
            validar(prog)

    def test_parse_falla_no_llega_a_validar(self):
        """Sintaxis incorrecta: el error es de sintaxis, no de semántica."""
        from mnfc.dsl import DSLSyntaxError
        with pytest.raises(DSLSyntaxError):
            parse('DSL_VERSION "1.6" sin punto y coma')

    def test_error_incluye_contexto_jerarquico(self):
        src = '''
        DSL_VERSION "1.6";
        HECHO h;
        MARCOS { PYMES; }
        FRACTAL ventas:
            REGLA r1: SI h
            ENTONCES GENERAR CONSECUENCIA(categoria=categoria(fantasma), operacion=op, movimiento=AUMENTA, fuente=PYMES:S1);
        '''
        try:
            validar(parse(src))
            assert False, "debería haber lanzado"
        except DSLSemanticError as e:
            assert "FRACTAL ventas" in str(e)
            assert "REGLA r1" in str(e)

    def test_error_hecho_incluye_contexto(self):
        src = '''
        DSL_VERSION "1.6";
        FRACTAL f:
            REGLA r: SI fantasma
            ENTONCES GENERAR CONSECUENCIA(operacion=op, movimiento=AUMENTA, fuente=X:S1);
        '''
        # Nota: falla por hecho primero (se valida condición antes que acciones)
        try:
            validar(parse(src))
            assert False
        except DSLSemanticError as e:
            assert "FRACTAL f" in str(e)
            assert "REGLA r" in str(e)
            assert "fantasma" in str(e)

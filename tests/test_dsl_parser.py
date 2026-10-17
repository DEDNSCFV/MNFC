"""Tests del parser DSL de MNFC — Fase 2.5

Verifican que src/mnfc/dsl/parser.py cumple la gramática v1.6.

Sintaxis de acción correcta:
  operacion=suma_montos          (identificador bare, sin comillas)
  movimiento=AUMENTA|DISMINUYE   (keyword bare)
  categoria={x, y} | categoria=categoria(x)
  fuente=PYMES:S23.1             (marco:seccion)

Sintaxis DSR rechazada por diseño (§0):
  operacion="suma_montos"        (string) → DSLSyntaxError
  movimiento="AUMENTA"           (string) → DSLSyntaxError
  cuenta="110101"                (cuenta concreta) → DSLSyntaxError

Fix DSL-PARSER-001 aplicado (2026-10-16): section_atom acepta
NUMBER con punto. Citas con múltiples niveles son parseables.

Solo parseo sintáctico. No validan semántica ni cargan marcos.
"""
import pytest
from mnfc.dsl import parse, Programa, DSLSyntaxError


DSL_MINIMO = 'DSL_VERSION "1.6";'

DSL_ELEMENTOS = '''
DSL_VERSION "1.6";
ELEMENTOS {
    activo : "Recurso controlado";
    pasivo;
    patrimonio;
}
'''

DSL_MARCOS = '''
DSL_VERSION "1.6";
MARCOS {
    PYMES;
    NIIF_Completas;
    BA_VEN_NIF;
}
'''

DSL_CATEGORIA = '''
DSL_VERSION "1.6";
CATEGORIA inventarios = elemento: activo; universal: VERDADERO;
CATEGORIA ppe = elemento: activo; universal: FALSO;
'''

DSL_HECHO = '''
DSL_VERSION "1.6";
HECHO activo_es_venta;
HECHO economia_hiperinflacionaria;
'''

DSL_FRACTAL_MINIMO = '''
DSL_VERSION "1.6";
FRACTAL venta:
    REGLA venta_simple:
        SI activo_es_venta
        ENTONCES GENERAR CONSECUENCIA(operacion=suma_montos, movimiento=AUMENTA, fuente=PYMES:S23.1);
'''


class TestHappyPath:
    def test_dsl_minimo_parsea(self):
        prog = parse(DSL_MINIMO)
        assert isinstance(prog, Programa)
        assert prog.version == "1.6"

    def test_elementos_vacios(self):
        prog = parse('DSL_VERSION "1.6"; ELEMENTOS {}')
        assert prog.elementos == []

    def test_elementos_con_contenido(self):
        prog = parse(DSL_ELEMENTOS)
        assert len(prog.elementos) == 3
        nombres = [e.nombre for e in prog.elementos]
        assert "activo" in nombres
        assert "pasivo" in nombres
        assert "patrimonio" in nombres

    def test_elemento_con_descripcion(self):
        prog = parse(DSL_ELEMENTOS)
        activo = next(e for e in prog.elementos if e.nombre == "activo")
        assert activo.descripcion == "Recurso controlado"

    def test_marcos(self):
        prog = parse(DSL_MARCOS)
        assert len(prog.marcos) == 3
        assert "PYMES" in prog.marcos
        assert "NIIF_Completas" in prog.marcos
        assert "BA_VEN_NIF" in prog.marcos

    def test_categorias(self):
        prog = parse(DSL_CATEGORIA)
        assert len(prog.categorias) == 2
        inv = next(c for c in prog.categorias if c.nombre == "inventarios")
        assert inv.elemento == "activo"
        assert inv.universal is True

    def test_categoria_universal_falso(self):
        prog = parse(DSL_CATEGORIA)
        ppe = next(c for c in prog.categorias if c.nombre == "ppe")
        assert ppe.universal is False

    def test_hechos(self):
        prog = parse(DSL_HECHO)
        assert len(prog.hechos) == 2
        assert "activo_es_venta" in prog.hechos

    def test_fractal_minimo(self):
        prog = parse(DSL_FRACTAL_MINIMO)
        assert len(prog.fractales) == 1
        assert prog.fractales[0].nombre == "venta"

    def test_fractal_con_regla(self):
        prog = parse(DSL_FRACTAL_MINIMO)
        assert len(prog.fractales[0].reglas) == 1

    def test_programa_completo(self):
        src = """
        DSL_VERSION "1.6";
        ELEMENTOS { activo; pasivo; patrimonio; }
        MARCOS { PYMES; NIIF_Completas; BA_VEN_NIF; }
        CATEGORIA inventarios = elemento: activo; universal: VERDADERO;
        CATEGORIA ppe = elemento: activo; universal: FALSO;
        HECHO activo_es_venta;
        HECHO economia_hiperinflacionaria;
        """
        prog = parse(src)
        assert len(prog.elementos) == 3
        assert len(prog.marcos) == 3
        assert len(prog.categorias) == 2
        assert len(prog.hechos) == 2

    def test_multiple_fractales(self):
        src = '''
        DSL_VERSION "1.6";
        FRACTAL ventas: REGLA r1: SI activo ENTONCES GENERAR CONSECUENCIA(operacion=op1, movimiento=AUMENTA, fuente=PYMES:S23.1);
        FRACTAL compras: REGLA r2: SI pasivo ENTONCES GENERAR CONSECUENCIA(operacion=op2, movimiento=DISMINUYE, fuente=NIC:S16.4);
        '''
        assert len(parse(src).fractales) == 2


class TestCondiciones:
    def _regla_con(self, condicion):
        return f'''
        DSL_VERSION "1.6";
        FRACTAL f: REGLA r: SI {condicion}
            ENTONCES GENERAR CONSECUENCIA(operacion=op, movimiento=AUMENTA, fuente=PYMES:S1.1);
        '''

    def test_hecho_simple(self):
        assert parse(self._regla_con("activo_es_venta")).fractales[0].reglas[0].condicion is not None

    def test_comparacion_igual(self):
        assert parse(self._regla_con("marco == NIIF")).fractales[0].reglas[0].condicion.op == "=="

    def test_comparacion_distinto(self):
        assert parse(self._regla_con("marco != NIIF")).fractales[0].reglas[0].condicion.op == "!="

    def test_comparacion_mayor_igual(self):
        assert parse(self._regla_con("monto >= 1000")).fractales[0].reglas[0].condicion.op == ">="

    def test_comparacion_con_string(self):
        assert parse(self._regla_con('marco == "NIIF"')).fractales[0].reglas[0].condicion.der == "NIIF"

    def test_comparacion_con_numero(self):
        assert parse(self._regla_con("monto > 100.5")).fractales[0].reglas[0].condicion.der == "100.5"

    def test_conjuncion_y(self):
        cond = parse(self._regla_con("activo_es_venta Y economia_hiperinflacionaria")).fractales[0].reglas[0].condicion
        assert hasattr(cond, "partes") and len(cond.partes) == 2

    def test_disyuncion_o(self):
        cond = parse(self._regla_con("activo_es_venta O economia_hiperinflacionaria")).fractales[0].reglas[0].condicion
        assert hasattr(cond, "partes") and len(cond.partes) == 2

    def test_negacion_no(self):
        cond = parse(self._regla_con("NO activo_es_venta")).fractales[0].reglas[0].condicion
        assert hasattr(cond, "interno")

    def test_parentesis_agrupa(self):
        assert parse(self._regla_con("[activo Y [pasivo O patrimonio]]")).fractales[0].reglas[0].condicion is not None


class TestErrores:
    def test_sin_dsl_version(self):
        with pytest.raises(DSLSyntaxError):
            parse('ELEMENTOS {}')

    def test_sin_punto_y_coma(self):
        with pytest.raises(DSLSyntaxError):
            parse('DSL_VERSION "1.6"')

    def test_string_sin_cerrar(self):
        with pytest.raises(DSLSyntaxError) as exc:
            parse('DSL_VERSION "1.6;')
        assert "string" in str(exc.value).lower()

    def test_eof_prematuro(self):
        with pytest.raises(DSLSyntaxError):
            parse('DSL_VERSION "1.6"; FRACTAL')

    def test_caracter_inesperado(self):
        with pytest.raises(DSLSyntaxError):
            parse('DSL_VERSION "1.6"; @')

    def test_falta_parentesis_en_categoria(self):
        with pytest.raises(DSLSyntaxError):
            parse('''
            DSL_VERSION "1.6";
            FRACTAL f: REGLA r: SI categoria inventarios
                ENTONCES GENERAR CONSECUENCIA(operacion=op, movimiento=AUMENTA, fuente=PYMES:S1.1);
            ''')

    def test_error_incluye_linea(self):
        with pytest.raises(DSLSyntaxError) as exc:
            parse('DSL_VERSION "1.6";\n@')
        assert exc.value.linea >= 1

    def test_error_incluye_archivo(self):
        with pytest.raises(DSLSyntaxError) as exc:
            parse('DSL_VERSION "1.6"; @', archivo="test.mnfc")
        assert "test.mnfc" in str(exc.value)

    def test_entrada_vacia(self):
        with pytest.raises(DSLSyntaxError):
            parse('')

    def test_solo_whitespace(self):
        with pytest.raises(DSLSyntaxError):
            parse('   \n\t  \n')


class TestAdversarios:
    def test_comentarios_ignorados(self):
        src = '# comentario\nDSL_VERSION "1.6";  # otro\n'
        assert parse(src).version == "1.6"

    def test_whitespace_variado(self):
        assert parse('DSL_VERSION\t\t"1.6"\n\n;').version == "1.6"

    def test_identificador_con_underscore(self):
        prog = parse('DSL_VERSION "1.6"; HECHO activo_es_venta_ordinaria;')
        assert "activo_es_venta_ordinaria" in prog.hechos

    def test_numero_negativo(self):
        prog = parse('''
        DSL_VERSION "1.6";
        FRACTAL f: REGLA r: SI monto > -100
            ENTONCES GENERAR CONSECUENCIA(operacion=op, movimiento=AUMENTA, fuente=PYMES:S1.1);
        ''')
        assert prog.fractales[0].reglas[0].condicion.der == "-100"


class TestSintaxisDSRRechazada:
    def test_operacion_con_string_rechazada(self):
        with pytest.raises(DSLSyntaxError):
            parse('''
            DSL_VERSION "1.6";
            FRACTAL f: REGLA r: SI activo
                ENTONCES GENERAR CONSECUENCIA(operacion="suma_montos", movimiento=AUMENTA, fuente=PYMES:S1.1);
            ''')

    def test_movimiento_con_string_rechazado(self):
        with pytest.raises(DSLSyntaxError):
            parse('''
            DSL_VERSION "1.6";
            FRACTAL f: REGLA r: SI activo
                ENTONCES GENERAR CONSECUENCIA(operacion=op, movimiento="AUMENTA", fuente=PYMES:S1.1);
            ''')

    def test_cuenta_rechazada(self):
        with pytest.raises(DSLSyntaxError):
            parse('''
            DSL_VERSION "1.6";
            FRACTAL f: REGLA r: SI activo
                ENTONCES GENERAR CONSECUENCIA(cuenta="110101", operacion=op, movimiento=AUMENTA, fuente=PYMES:S1.1);
            ''')


class TestArqueologiaCitasReales:
    def _cita(self, fuente):
        src = f'''
        DSL_VERSION "1.6";
        FRACTAL f: REGLA r: SI activo
            ENTONCES GENERAR CONSECUENCIA(operacion=op, movimiento=AUMENTA, fuente={fuente});
        '''
        return parse(src).fractales[0].reglas[0].acciones[0].fuente

    @pytest.mark.parametrize("cita,sec", [
        ("PYMES:S13.4", "S13.4"),
        ("PYMES:S17.9", "S17.9"),
        ("PYMES:S17.17", "S17.17"),
        ("PYMES:S17.27", "S17.27"),
        ("PYMES:S18.9", "S18.9"),
        ("PYMES:S18.20", "S18.20"),
        ("PYMES:S18.24", "S18.24"),
        ("PYMES:S19.22", "S19.22"),
        ("PYMES:S19.24", "S19.24"),
        ("PYMES:S20.9", "S20.9"),
        ("PYMES:S20.11", "S20.11"),
        ("PYMES:S21.10", "S21.10"),
        ("PYMES:S21.15", "S21.15"),
        ("PYMES:S23", "S23"),
        ("PYMES:S24.4", "S24.4"),
        ("PYMES:S24.5", "S24.5"),
        ("PYMES:S30.9", "S30.9"),
        ("PYMES:S30.13", "S30.13"),
        ("PYMES:S31.11", "S31.11"),
        ("PYMES:S31.12", "S31.12"),
    ])
    def test_cita_pymes(self, cita, sec):
        f = self._cita(cita)
        assert f.marco == "PYMES" and f.seccion == sec

    @pytest.mark.parametrize("cita,marco,sec", [
        ("NIC:S16.43", "NIC", "S16.43"),
        ("NIC:S36.12", "NIC", "S36.12"),
        ("NIIF:S15.31", "NIIF", "S15.31"),
    ])
    def test_cita_niif_simple(self, cita, marco, sec):
        f = self._cita(cita)
        assert f.marco == marco and f.seccion == sec

    @pytest.mark.parametrize("cita,sec", [
        ("BA_VEN_NIF:S8.11", "S8.11"),
        ("BA_VEN_NIF:S8", "S8"),
        ("BA_VEN_NIF:S11", "S11"),
    ])
    def test_cita_ba_ven_nif(self, cita, sec):
        f = self._cita(cita)
        assert f.marco == "BA_VEN_NIF" and f.seccion == sec


class TestFixDSLParser001:
    def _cita(self, fuente):
        src = f'''
        DSL_VERSION "1.6";
        FRACTAL f: REGLA r: SI activo
            ENTONCES GENERAR CONSECUENCIA(operacion=op, movimiento=AUMENTA, fuente={fuente});
        '''
        return parse(src).fractales[0].reglas[0].acciones[0].fuente

    def test_digits_punto_digits(self):
        f = self._cita("PYMES:23.1")
        assert f.seccion == "23.1"

    def test_seccion_con_dos_puntos(self):
        f = self._cita("PYMES:S23.1.2")
        assert f.seccion == "S23.1.2"

    def test_cita_niif_completa(self):
        f = self._cita("NIC:S16.4.3")
        assert f.marco == "NIC" and f.seccion == "S16.4.3"

    def test_cita_niif_con_inciso(self):
        f = self._cita("NIIF:S9.1.2")
        assert f.marco == "NIIF" and f.seccion == "S9.1.2"

    def test_cita_nic_con_inciso(self):
        f = self._cita("NIC:S16.4.3")
        assert f.seccion == "S16.4.3"

    def test_cita_pymes_numerica(self):
        f = self._cita("PYMES:17.17")
        assert f.seccion == "17.17"


class TestConjuntos:
    def _regla_con(self, condicion):
        return f'''
        DSL_VERSION "1.6";
        FRACTAL f: REGLA r: SI {condicion}
            ENTONCES GENERAR CONSECUENCIA(operacion=op, movimiento=AUMENTA, fuente=PYMES:S1.1);
        '''

    def test_categoria_ref_pertenencia(self):
        assert parse(self._regla_con('categoria(inventarios) ∈ categoria(activos)')).fractales[0].reglas[0].condicion.op == "∈"

    def test_subconjunto(self):
        assert parse(self._regla_con('categoria(inventarios) ⊆ categoria(activos)')).fractales[0].reglas[0].condicion.op == "⊆"

    def test_union(self):
        cond = parse(self._regla_con('categoria(a) ⊆ categoria(b) ∪ categoria(c)')).fractales[0].reglas[0].condicion
        assert hasattr(cond.der, "izq") and hasattr(cond.der, "der")

    def test_interseccion(self):
        assert hasattr(parse(self._regla_con('categoria(a) ⊆ categoria(b) ∩ categoria(c)')).fractales[0].reglas[0].condicion.der, "izq")

    def test_diferencia(self):
        assert hasattr(parse(self._regla_con('categoria(a) ⊆ categoria(b) ∖ categoria(c)')).fractales[0].reglas[0].condicion.der, "izq")

    def test_complemento(self):
        assert hasattr(parse(self._regla_con('categoria(a) ⊆ ¬ categoria(b)')).fractales[0].reglas[0].condicion.der, "interno")

    def test_literal_conjunto(self):
        cond = parse(self._regla_con('categoria(a) ⊆ {x, y, z}')).fractales[0].reglas[0].condicion
        assert hasattr(cond.der, "items") and len(cond.der.items) == 3

    def test_parentesis_conjuntos(self):
        assert parse(self._regla_con('(categoria(a) ∪ categoria(b)) ⊆ categoria(c)')).fractales[0].reglas[0].condicion is not None


class TestAcciones:
    def _acc(self, args):
        src = f'''
        DSL_VERSION "1.6";
        FRACTAL f: REGLA r: SI activo
            ENTONCES GENERAR CONSECUENCIA({args});
        '''
        return parse(src).fractales[0].reglas[0].acciones[0]

    def test_accion_completa(self):
        acc = self._acc('categoria={activos}, operacion=suma_montos, movimiento=AUMENTA, fuente=PYMES:S23.1')
        assert acc.operacion == "suma_montos"
        assert acc.movimiento == "AUMENTA"
        assert acc.fuente is not None

    def test_accion_solo_operacion(self):
        assert self._acc('operacion=op, movimiento=AUMENTA, fuente=NIC:S16').operacion == "op"

    def test_operacion_bare_no_string(self):
        acc = self._acc('operacion=suma_montos, movimiento=AUMENTA, fuente=PYMES:S1.1')
        assert acc.operacion == "suma_montos"
        assert isinstance(acc.operacion, str)

    def test_cita_seccion_simple(self):
        acc = self._acc('operacion=op, movimiento=AUMENTA, fuente=PYMES:23')
        assert acc.fuente.marco == "PYMES" and acc.fuente.seccion == "23"

    def test_cita_seccion_ident(self):
        acc = self._acc('operacion=op, movimiento=AUMENTA, fuente=PYMES:S23')
        assert acc.fuente.seccion == "S23"

    def test_cita_seccion_ident_punto_digits(self):
        acc = self._acc('operacion=op, movimiento=AUMENTA, fuente=PYMES:S23.1')
        assert acc.fuente.seccion == "S23.1"

    def test_cita_ba_ven_nif(self):
        acc = self._acc('operacion=op, movimiento=AUMENTA, fuente=BA_VEN_NIF:S8.11')
        assert acc.fuente.marco == "BA_VEN_NIF" and acc.fuente.seccion == "S8.11"

    def test_movimiento_aumenta(self):
        assert self._acc('operacion=op, movimiento=AUMENTA, fuente=PYMES:S1.1').movimiento == "AUMENTA"

    def test_movimiento_disminuye(self):
        assert self._acc('operacion=op, movimiento=DISMINUYE, fuente=PYMES:S1.1').movimiento == "DISMINUYE"

    def test_categoria_set_literal(self):
        assert self._acc('categoria={x, y}, operacion=op, movimiento=AUMENTA, fuente=PYMES:S1.1').categoria is not None

    def test_categoria_ref(self):
        assert self._acc('categoria=categoria(x), operacion=op, movimiento=AUMENTA, fuente=PYMES:S1.1').categoria is not None

    def test_multiples_acciones_por_regla(self):
        src = '''
        DSL_VERSION "1.6";
        FRACTAL f: REGLA r: SI activo
            ENTONCES
                GENERAR CONSECUENCIA(operacion=op1, movimiento=AUMENTA, fuente=PYMES:S1.1)
                GENERAR CONSECUENCIA(operacion=op2, movimiento=DISMINUYE, fuente=PYMES:S2.2);
        '''
        assert len(parse(src).fractales[0].reglas[0].acciones) == 2

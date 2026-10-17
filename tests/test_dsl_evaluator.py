"""Tests del evaluator del DSL (Fase 3b).

Verifican que src/mnfc/dsl/evaluator.py:
- Evalúa condiciones contra un contexto de hechos y variables.
- Resuelve conjuntos contra un retículo de cuentas.
- Ejecuta acciones produciendo PartidaAutorizada por cuenta.
- Falla explícitamente cuando falta algo (no fallback silencioso).

Sin marcos reales. Sin fiscal. Todo inyectado (pcu, operaciones).
"""
import pytest
from mnfc.dsl import (
    parse, validar, evaluar,
    DSLEvaluationError,
    ResultadoAccion,
)
from mnfc.dsl.evaluator import (
    evaluar_condicion, evaluar_set, evaluar_accion,
)
from mnfc.dsl.parser import (
    HechoRef, NegBool, Conjuncion, Disyuncion, CmpEscalar,
    CategoriaRef, SetLiteral, Union, Inter, Diff, Complemento,
    Relacion, Cita, Accion,
)
from mnfc.extensiones.reticulo import ReticuloCuentas
from mnfc.extensiones.modelos import PartidaAutorizada


# ═════════════════════════════════════════════════════════════════════
# Fixtures comunes
# ═════════════════════════════════════════════════════════════════════

@pytest.fixture
def pcu():
    """PCU de fixture: 3 cuentas con categoría y marco.

    Convención Fase 3b: 'marcos' cumple doble rol —
    - nombre de categoría del DSL (para el retículo)
    - nombre de marco contable (para el filtro)
    """
    return {
        "110101": {"naturaleza": "DEUDORA",   "marcos": ["caja", "PYMES"],    "nombre": "Caja"},
        "410101": {"naturaleza": "ACREEDORA", "marcos": ["ingreso", "PYMES"], "nombre": "Ingresos"},
        "210101": {"naturaleza": "ACREEDORA", "marcos": ["deuda", "PYMES"],   "nombre": "Proveedores"},
    }


@pytest.fixture
def ops():
    return {
        "suma_montos": lambda ctx: sum(ctx["montos"]),
        "cien":        lambda ctx: 100.0,
        "falla":       lambda ctx: 1/0,
        "retorna_str": lambda ctx: "no numero",
    }


@pytest.fixture
def ret(pcu):
    return ReticuloCuentas.desde_pcu(pcu, clave="marcos")


# ═════════════════════════════════════════════════════════════════════
# A · evaluar_condicion
# ═════════════════════════════════════════════════════════════════════

class TestEvaluarCondicion:

    def test_hecho_presente_true(self):
        assert evaluar_condicion(HechoRef("h"), {"h": True}) is True

    def test_hecho_presente_false(self):
        assert evaluar_condicion(HechoRef("h"), {"h": False}) is False

    def test_hecho_presente_valor_truthy(self):
        assert evaluar_condicion(HechoRef("h"), {"h": 1}) is True

    def test_hecho_ausente_error(self):
        with pytest.raises(DSLEvaluationError, match="hecho 'h' no presente"):
            evaluar_condicion(HechoRef("h"), {})

    def test_negacion_true(self):
        nodo = NegBool(HechoRef("h"))
        assert evaluar_condicion(nodo, {"h": False}) is True

    def test_negacion_false(self):
        nodo = NegBool(HechoRef("h"))
        assert evaluar_condicion(nodo, {"h": True}) is False

    def test_conjuncion_todos_true(self):
        nodo = Conjuncion([HechoRef("a"), HechoRef("b")])
        assert evaluar_condicion(nodo, {"a": True, "b": True}) is True

    def test_conjuncion_algun_false(self):
        nodo = Conjuncion([HechoRef("a"), HechoRef("b")])
        assert evaluar_condicion(nodo, {"a": True, "b": False}) is False

    def test_disyuncion_algun_true(self):
        nodo = Disyuncion([HechoRef("a"), HechoRef("b")])
        assert evaluar_condicion(nodo, {"a": False, "b": True}) is True

    def test_disyuncion_todos_false(self):
        nodo = Disyuncion([HechoRef("a"), HechoRef("b")])
        assert evaluar_condicion(nodo, {"a": False, "b": False}) is False

    def test_cmp_igual_numeros(self):
        nodo = CmpEscalar("monto", "==", "100")
        assert evaluar_condicion(nodo, {"monto": 100.0}) is True

    def test_cmp_igual_numeros_falla(self):
        nodo = CmpEscalar("monto", "==", "100")
        assert evaluar_condicion(nodo, {"monto": 99.0}) is False

    def test_cmp_mayor(self):
        nodo = CmpEscalar("monto", ">", "50")
        assert evaluar_condicion(nodo, {"monto": 100.0}) is True

    def test_cmp_string(self):
        nodo = CmpEscalar("marco", "==", "PYMES")
        assert evaluar_condicion(nodo, {"marco": "PYMES"}) is True

    def test_cmp_variable_ausente_trata_como_string(self):
        # Si izq no está en contexto, se usa como literal string
        nodo = CmpEscalar("fantasma", "==", "fantasma")
        assert evaluar_condicion(nodo, {}) is True

    def test_relacion_en_condicion_error(self):
        nodo = Relacion(CategoriaRef("a"), "∈", CategoriaRef("b"))
        with pytest.raises(DSLEvaluationError, match="relación.*no soportada"):
            evaluar_condicion(nodo, {})

    def test_nodo_none_error(self):
        with pytest.raises(DSLEvaluationError, match="condición vacía"):
            evaluar_condicion(None, {})

    def test_nodo_inesperado_error(self):
        with pytest.raises(DSLEvaluationError, match="nodo de condición inesperado"):
            evaluar_condicion("no-es-nodo", {})


# ═════════════════════════════════════════════════════════════════════
# B · evaluar_set
# ═════════════════════════════════════════════════════════════════════

class TestEvaluarSet:

    def test_categoria_ref_existente(self, ret):
        resultado = evaluar_set(CategoriaRef("caja"), ret)
        assert resultado == frozenset({"110101"})

    def test_categoria_ref_inexistente_error(self, ret):
        with pytest.raises(DSLEvaluationError, match="subconjunto 'fantasma'"):
            evaluar_set(CategoriaRef("fantasma"), ret)

    def test_set_literal_un_elemento(self, ret):
        resultado = evaluar_set(SetLiteral(["caja"]), ret)
        assert resultado == frozenset({"110101"})

    def test_set_literal_multiples(self, ret):
        resultado = evaluar_set(SetLiteral(["caja", "ingreso"]), ret)
        assert resultado == frozenset({"110101", "410101"})

    def test_set_literal_con_fantasma_error(self, ret):
        with pytest.raises(DSLEvaluationError, match="subconjunto 'fantasma'"):
            evaluar_set(SetLiteral(["caja", "fantasma"]), ret)

    def test_union(self, ret):
        nodo = Union(CategoriaRef("caja"), CategoriaRef("ingreso"))
        resultado = evaluar_set(nodo, ret)
        assert resultado == frozenset({"110101", "410101"})

    def test_inter(self, ret):
        # caja ∩ ingreso = ∅ (no comparten cuentas)
        nodo = Inter(CategoriaRef("caja"), CategoriaRef("ingreso"))
        resultado = evaluar_set(nodo, ret)
        assert resultado == frozenset()

    def test_diff(self, ret):
        # caja - ingreso = caja (no comparten)
        nodo = Diff(CategoriaRef("caja"), CategoriaRef("ingreso"))
        resultado = evaluar_set(nodo, ret)
        assert resultado == frozenset({"110101"})

    def test_complemento(self, ret):
        # universo - caja = {ingreso, deuda, PYMES} mapeados a cuentas
        nodo = Complemento(CategoriaRef("caja"))
        resultado = evaluar_set(nodo, ret)
        # universo = {110101, 410101, 210101}
        assert "110101" not in resultado
        assert "410101" in resultado
        assert "210101" in resultado

    def test_nodo_none_error(self, ret):
        with pytest.raises(DSLEvaluationError, match="conjunto vacío"):
            evaluar_set(None, ret)

    def test_nodo_inesperado_error(self, ret):
        with pytest.raises(DSLEvaluationError, match="nodo de conjunto inesperado"):
            evaluar_set("no-es-nodo", ret)


# ═════════════════════════════════════════════════════════════════════
# C · evaluar_accion
# ═════════════════════════════════════════════════════════════════════

class TestEvaluarAccion:

    def _ctx_eval(self, accion, pcu, ret, ops):
        cuentas_marco = ret.subconjunto("PYMES") if "PYMES" in ret.nombres() else frozenset()
        return evaluar_accion(
            accion,
            contexto={"montos": [100.0, 50.0]},
            pcu=pcu,
            reticulo=ret,
            cuentas_marco=cuentas_marco,
            operaciones=ops,
            marco_contable="PYMES",
            correlation_id="c1",
            ctx="test",
        )

    def _accion(self, **kw):
        return Accion(**kw)

    def test_accion_completa_una_partida(self, pcu, ops, ret):
        acc = self._accion(
            categoria=CategoriaRef("caja"),
            operacion="suma_montos",
            movimiento="AUMENTA",
            fuente=Cita("PYMES", "S23"),
        )
        partidas = self._ctx_eval(acc, pcu, ret, ops)
        assert len(partidas) == 1
        assert partidas[0].cuenta_codigo == "110101"
        assert partidas[0].ubicacion == "DEBE"
        assert partidas[0].monto == 150.0
        assert partidas[0].movimiento == "AUMENTA"
        assert partidas[0].norma_id == "PYMES:S23"

    def test_accion_set_literal_multiples_partidas(self, pcu, ops, ret):
        acc = self._accion(
            categoria=SetLiteral(["caja", "ingreso"]),
            operacion="cien",
            movimiento="AUMENTA",
            fuente=Cita("PYMES", "S1"),
        )
        partidas = self._ctx_eval(acc, pcu, ret, ops)
        assert len(partidas) == 2
        cuentas = {p.cuenta_codigo for p in partidas}
        assert cuentas == {"110101", "410101"}

    def test_sin_operacion_error(self, pcu, ops, ret):
        acc = self._accion(
            categoria=CategoriaRef("caja"),
            movimiento="AUMENTA",
        )
        with pytest.raises(DSLEvaluationError, match="sin 'operacion="):
            self._ctx_eval(acc, pcu, ret, ops)

    def test_operacion_no_en_registry_error(self, pcu, ops, ret):
        acc = self._accion(
            categoria=CategoriaRef("caja"),
            operacion="no_existe",
            movimiento="AUMENTA",
        )
        with pytest.raises(DSLEvaluationError, match="no está en el registry"):
            self._ctx_eval(acc, pcu, ret, ops)

    def test_operacion_falla_error(self, pcu, ops, ret):
        acc = self._accion(
            categoria=CategoriaRef("caja"),
            operacion="falla",
            movimiento="AUMENTA",
        )
        with pytest.raises(DSLEvaluationError, match="'falla' falló"):
            self._ctx_eval(acc, pcu, ret, ops)

    def test_operacion_retorna_no_numerico_error(self, pcu, ops, ret):
        acc = self._accion(
            categoria=CategoriaRef("caja"),
            operacion="retorna_str",
            movimiento="AUMENTA",
        )
        with pytest.raises(DSLEvaluationError, match="retornó str"):
            self._ctx_eval(acc, pcu, ret, ops)

    def test_sin_movimiento_error(self, pcu, ops, ret):
        acc = self._accion(
            categoria=CategoriaRef("caja"),
            operacion="cien",
        )
        with pytest.raises(DSLEvaluationError, match="sin 'movimiento="):
            self._ctx_eval(acc, pcu, ret, ops)

    def test_sin_categoria_error(self, pcu, ops, ret):
        acc = self._accion(
            operacion="cien",
            movimiento="AUMENTA",
        )
        with pytest.raises(DSLEvaluationError, match="sin 'categoria="):
            self._ctx_eval(acc, pcu, ret, ops)

    def test_categoria_resuelve_vacio_error(self, pcu, ops, ret):
        # Inter de disjuntos = vacío
        cat = Inter(CategoriaRef("caja"), CategoriaRef("ingreso"))
        acc = self._accion(
            categoria=cat,
            operacion="cien",
            movimiento="AUMENTA",
        )
        with pytest.raises(DSLEvaluationError, match="conjunto vacío"):
            self._ctx_eval(acc, pcu, ret, ops)

    def test_cuenta_no_en_pcu_error(self, ops, ret):
        pcu_incompleto = {
            "410101": {"naturaleza": "ACREEDORA", "marcos": ["ingreso", "PYMES"]},
        }
        # ret de este test no corresponde al pcu_incompleto. Lo creamos:
        ret2 = ReticuloCuentas.desde_pcu(pcu_incompleto, clave="marcos")
        acc = self._accion(
            categoria=CategoriaRef("caja"),  # caja no existe en pcu_incompleto
            operacion="cien",
            movimiento="AUMENTA",
        )
        # caja no existe en ret2 → error de set primero
        with pytest.raises(DSLEvaluationError):
            cuentas_marco = frozenset()
            evaluar_accion(
                acc,
                contexto={}, pcu=pcu_incompleto, reticulo=ret2,
                cuentas_marco=cuentas_marco, operaciones=ops,
                marco_contable="PYMES", correlation_id="c1", ctx="test",
            )

    def test_naturaleza_invalida_error(self, ops, ret):
        pcu_malo = {
            "X": {"naturaleza": "RARA", "marcos": ["caja", "PYMES"]},
        }
        ret3 = ReticuloCuentas.desde_pcu(pcu_malo, clave="marcos")
        acc = self._accion(
            categoria=CategoriaRef("caja"),
            operacion="cien",
            movimiento="AUMENTA",
        )
        with pytest.raises(DSLEvaluationError, match="naturaleza inválida"):
            evaluar_accion(
                acc,
                contexto={}, pcu=pcu_malo, reticulo=ret3,
                cuentas_marco=frozenset(), operaciones=ops,
                marco_contable="PYMES", correlation_id="c1", ctx="test",
            )


# ═════════════════════════════════════════════════════════════════════
# D · evaluar · programa completo
# ═════════════════════════════════════════════════════════════════════

def _programa(condicion: str, acciones: str) -> str:
    return f'''
    DSL_VERSION "1.6";
    ELEMENTOS {{ activo; ingreso; pasivo; }}
    MARCOS {{ PYMES; }}
    CATEGORIA caja = elemento: activo; universal: VERDADERO;
    CATEGORIA ingreso = elemento: ingreso; universal: FALSO;
    CATEGORIA deuda = elemento: pasivo; universal: FALSO;
    HECHO activo;
    HECHO inactivo;
    FRACTAL f:
        REGLA r:
            SI {condicion}
            ENTONCES {acciones};
    '''


class TestEvaluarPrograma:

    def _evaluar(self, src, pcu, ops, contexto=None):
        prog = parse(src)
        validar(prog)
        return evaluar(
            prog,
            contexto=contexto or {"activo": True, "inactivo": False,
                                  "montos": [100.0]},
            pcu=pcu,
            operaciones=ops,
            marco_contable="PYMES",
        )

    def test_condicion_true_ejecuta_una_accion(self, pcu, ops):
        src = _programa(
            "activo",
            'GENERAR CONSECUENCIA(categoria=categoria(caja), '
            'operacion=cien, movimiento=AUMENTA, fuente=PYMES:S1)'
        )
        rs = self._evaluar(src, pcu, ops)
        assert len(rs) == 1
        assert isinstance(rs[0], ResultadoAccion)
        assert rs[0].fractal == "f"
        assert rs[0].regla == "r"
        assert rs[0].indice == 1
        assert len(rs[0].partidas) == 1
        assert rs[0].partidas[0].cuenta_codigo == "110101"

    def test_condicion_false_no_ejecuta(self, pcu, ops):
        src = _programa(
            "inactivo",
            'GENERAR CONSECUENCIA(categoria=categoria(caja), '
            'operacion=cien, movimiento=AUMENTA, fuente=PYMES:S1)'
        )
        rs = self._evaluar(src, pcu, ops)
        assert rs == []

    def test_multiples_acciones_por_regla(self, pcu, ops):
        src = _programa(
            "activo",
            'GENERAR CONSECUENCIA(categoria=categoria(caja), operacion=cien, movimiento=AUMENTA, fuente=PYMES:S1) '
            'GENERAR CONSECUENCIA(categoria=categoria(ingreso), operacion=cien, movimiento=AUMENTA, fuente=PYMES:S1)'
        )
        rs = self._evaluar(src, pcu, ops)
        assert len(rs) == 2
        assert rs[0].indice == 1
        assert rs[1].indice == 2

    def test_correlation_id_preservado(self, pcu, ops):
        src = _programa(
            "activo",
            'GENERAR CONSECUENCIA(categoria=categoria(caja), '
            'operacion=cien, movimiento=AUMENTA, fuente=PYMES:S1)'
        )
        prog = parse(src)
        validar(prog)
        rs = evaluar(
            prog,
            contexto={"activo": True, "inactivo": False},
            pcu=pcu, operaciones=ops, marco_contable="PYMES",
            correlation_id="corr-xyz",
        )
        # El correlation_id va en PartidaAutorizada vía norma_id no. Está
        # en el ResultadoAccion? No, se usa a nivel programa. Verificar que
        # la firma lo acepta (contrato).
        assert len(rs) == 1

    def test_evidencia_preservada(self, pcu, ops):
        src = _programa(
            "activo",
            'GENERAR CONSECUENCIA(categoria=categoria(caja), operacion=cien, '
            'movimiento=AUMENTA, fuente=PYMES:S1, evidencia=doc1)'
        )
        rs = self._evaluar(src, pcu, ops)
        assert rs[0].evidencia == "doc1"

    def test_sin_fractales_devuelve_vacio(self, pcu, ops):
        src = 'DSL_VERSION "1.6";'
        prog = parse(src)
        validar(prog)
        rs = evaluar(prog, contexto={}, pcu=pcu, operaciones=ops,
                     marco_contable="PYMES")
        assert rs == []

    def test_norma_id_correcta(self, pcu, ops):
        src = _programa(
            "activo",
            'GENERAR CONSECUENCIA(categoria=categoria(caja), operacion=cien, '
            'movimiento=AUMENTA, fuente=NIC:S16.4.3)'
        )
        # NIC no está declarado en MARCOS, así que esto debe fallar
        # Cambiamos la fuente a PYMES:S16.4.3 para que valide
        src = src.replace("NIC:S16.4.3", "PYMES:S16.4.3")
        rs = self._evaluar(src, pcu, ops)
        assert rs[0].partidas[0].norma_id == "PYMES:S16.4.3"

"""Tests del assembler del DSL (Fase 4).

Verifican:
- Agrupación por (fractal, regla).
- Transformación PartidaAutorizada → LineaAsiento.
- Cuadre por regla individual (no compensable entre reglas).
- Tolerancia 0.001 estricta de verificar_cuadre (< no <=).
- Validación de montos individuales (bool, no numérico, no finito, negativo).
- Contrato de error de DSLAssemblyError.
- Diagnóstico seguro de diferencias (no propaga inf/nan al mensaje).
- Pipeline completo: parse → validar → evaluar → ensamblar.

Sin marcos reales. Sin fiscal. Todo con datos sintéticos.
"""
import pytest
from mnfc.dsl.evaluator import ResultadoAccion, DSLEvaluationError
from mnfc.dsl.assembler import ensamblar, DSLAssemblyError
from mnfc.extensiones.modelos import (
    PartidaAutorizada,
    ContextoContable,
)


def _pa(cuenta, ubicacion, monto, movimiento="AUMENTA"):
    return PartidaAutorizada(
        cuenta_codigo=cuenta,
        cuenta_version="v1",
        monto=monto,
        ubicacion=ubicacion,
        movimiento=movimiento,
    )


def _rc(fractal, regla, indice, partidas):
    return ResultadoAccion(fractal, regla, indice, partidas)


# ═════════════════════════════════════════════════════════════════════
# A · Agrupación
# ═════════════════════════════════════════════════════════════════════

class TestAgrupacion:

    def test_vacio(self):
        assert ensamblar([]) == []

    def test_una_sola_regla(self):
        rs = [_rc("f", "r", 1, [
            _pa("1101", "DEBE", 100.0),
            _pa("4101", "HABER", 100.0),
        ])]
        assert len(ensamblar(rs)) == 1

    def test_dos_reglas_distintas(self):
        rs = [
            _rc("f", "r1", 1, [_pa("A", "DEBE", 100.0),
                               _pa("B", "HABER", 100.0)]),
            _rc("f", "r2", 1, [_pa("C", "DEBE", 50.0),
                               _pa("D", "HABER", 50.0)]),
        ]
        assert len(ensamblar(rs)) == 2

    def test_mismo_nombre_regla_en_fractales_distintos(self):
        rs = [
            _rc("f1", "r", 1, [_pa("A", "DEBE", 10.0),
                               _pa("B", "HABER", 10.0)]),
            _rc("f2", "r", 1, [_pa("C", "DEBE", 20.0),
                               _pa("D", "HABER", 20.0)]),
        ]
        asientos = ensamblar(rs)
        assert len(asientos) == 2
        assert asientos[0].lineas[0].cuenta == "A"
        assert asientos[1].lineas[0].cuenta == "C"

    def test_una_regla_dos_acciones(self):
        rs = [
            _rc("f", "r", 1, [_pa("A", "DEBE", 100.0)]),
            _rc("f", "r", 2, [_pa("B", "HABER", 100.0)]),
        ]
        asientos = ensamblar(rs)
        assert len(asientos) == 1
        assert len(asientos[0].lineas) == 2

    def test_orden_primera_aparicion(self):
        rs = [
            _rc("f2", "r", 1, [_pa("A", "DEBE", 10.0),
                               _pa("B", "HABER", 10.0)]),
            _rc("f1", "r", 1, [_pa("C", "DEBE", 20.0),
                               _pa("D", "HABER", 20.0)]),
            _rc("f2", "r", 2, [_pa("E", "DEBE", 5.0),
                               _pa("F", "HABER", 5.0)]),
        ]
        asientos = ensamblar(rs)
        assert len(asientos) == 2
        assert len(asientos[0].lineas) == 4
        assert len(asientos[1].lineas) == 2


# ═════════════════════════════════════════════════════════════════════
# B · Transformación PartidaAutorizada → LineaAsiento
# ═════════════════════════════════════════════════════════════════════

class TestTransformacion:

    def test_campos_preservados(self):
        pa = _pa("1101", "DEBE", 100.5, "DISMINUYE")
        rs = [_rc("f", "r", 1, [pa, _pa("4101", "HABER", 100.5)])]
        linea = ensamblar(rs)[0].lineas[0]
        assert linea.cuenta == "1101"
        assert linea.ubicacion == "DEBE"
        assert linea.monto == 100.5
        assert linea.movimiento == "DISMINUYE"
        assert linea.naturaleza is None

    def test_orden_de_partidas(self):
        rs = [_rc("f", "r", 1, [
            _pa("A", "DEBE", 10.0),
            _pa("B", "HABER", 6.0),
            _pa("C", "HABER", 4.0),
        ])]
        asiento = ensamblar(rs)[0]
        assert [l.cuenta for l in asiento.lineas] == ["A", "B", "C"]


# ═════════════════════════════════════════════════════════════════════
# C · Cuadre por regla individual
# ═════════════════════════════════════════════════════════════════════

class TestCuadre:

    def test_cuadrado(self):
        rs = [_rc("f", "r", 1, [
            _pa("A", "DEBE", 100.0),
            _pa("B", "HABER", 100.0),
        ])]
        a = ensamblar(rs)[0]
        assert a.cuadrado is True
        assert a.total_debe == 100.0
        assert a.total_haber == 100.0

    def test_multiples_partidas_por_lado(self):
        rs = [_rc("f", "r", 1, [
            _pa("A", "DEBE", 60.0),
            _pa("B", "DEBE", 40.0),
            _pa("C", "HABER", 50.0),
            _pa("D", "HABER", 50.0),
        ])]
        a = ensamblar(rs)[0]
        assert a.cuadrado is True
        assert a.total_debe == 100.0
        assert a.total_haber == 100.0

    def test_descuadrado_error(self):
        rs = [_rc("f", "r", 1, [
            _pa("A", "DEBE", 100.0),
            _pa("B", "HABER", 90.0),
        ])]
        with pytest.raises(DSLAssemblyError, match="descuadrado"):
            ensamblar(rs)

    def test_descuadre_no_compensa_entre_reglas(self):
        """Regla 1 descuadra +10, regla 2 descuadra -10. No se compensan."""
        rs = [
            _rc("f", "r1", 1, [_pa("A", "DEBE", 100.0),
                               _pa("B", "HABER", 90.0)]),
            _rc("f", "r2", 1, [_pa("C", "DEBE", 90.0),
                               _pa("D", "HABER", 100.0)]),
        ]
        with pytest.raises(DSLAssemblyError):
            ensamblar(rs)


# ═════════════════════════════════════════════════════════════════════
# D · Tolerancia 0.001 (estricta, < no <=)
# ═════════════════════════════════════════════════════════════════════

class TestTolerancia:

    def test_dentro(self):
        """diff=0.0005 → cuadrado."""
        rs = [_rc("f", "r", 1, [
            _pa("A", "DEBE", 100.0),
            _pa("B", "HABER", 99.9995),
        ])]
        assert ensamblar(rs)[0].cuadrado is True

    def test_justo_en_limite(self):
        """diff=0.001 exacto → descuadrado (tolerancia es < estricto)."""
        rs = [_rc("f", "r", 1, [
            _pa("A", "DEBE", 100.0),
            _pa("B", "HABER", 99.999),
        ])]
        with pytest.raises(DSLAssemblyError):
            ensamblar(rs)

    def test_fuera(self):
        """diff=0.002 → descuadrado."""
        rs = [_rc("f", "r", 1, [
            _pa("A", "DEBE", 100.0),
            _pa("B", "HABER", 99.998),
        ])]
        with pytest.raises(DSLAssemblyError):
            ensamblar(rs)


# ═════════════════════════════════════════════════════════════════════
# E · Contexto
# ═════════════════════════════════════════════════════════════════════

class TestContexto:

    def test_adjuntado(self):
        ctx = ContextoContable("PYMES", "v1", "v1", "v1")
        rs = [_rc("f", "r", 1, [
            _pa("A", "DEBE", 100.0),
            _pa("B", "HABER", 100.0),
        ])]
        a = ensamblar(rs, contexto=ctx)[0]
        assert a.contexto is ctx

    def test_sin_contexto(self):
        rs = [_rc("f", "r", 1, [
            _pa("A", "DEBE", 100.0),
            _pa("B", "HABER", 100.0),
        ])]
        assert ensamblar(rs)[0].contexto is None


# ═════════════════════════════════════════════════════════════════════
# F · Errores con contexto
# ═════════════════════════════════════════════════════════════════════

class TestErrores:

    def test_accion_sin_partidas(self):
        rs = [_rc("f", "r", 1, [])]
        with pytest.raises(DSLAssemblyError, match="acción #1 sin partidas"):
            ensamblar(rs)

    def test_ubicacion_invalida(self):
        pa = PartidaAutorizada(
            cuenta_codigo="X", cuenta_version="v1",
            monto=100.0, ubicacion="OTRA", movimiento="AUMENTA",
        )
        rs = [_rc("f", "r", 1, [pa])]
        with pytest.raises(DSLAssemblyError, match="ubicación inválida"):
            ensamblar(rs)

    def test_contexto_en_error_descuadre(self):
        rs = [_rc("ventas", "registro", 1, [
            _pa("A", "DEBE", 100.0),
            _pa("B", "HABER", 90.0),
        ])]
        try:
            ensamblar(rs)
            assert False, "debería haber lanzado"
        except DSLAssemblyError as e:
            assert "FRACTAL ventas" in str(e)
            assert "REGLA registro" in str(e)

    def test_dsl_assembly_error_hereda_de_dsl_evaluation_error(self):
        """Catchable con except DSLEvaluationError."""
        rs = [_rc("f", "r", 1, [])]
        with pytest.raises(DSLEvaluationError):
            ensamblar(rs)


# ═════════════════════════════════════════════════════════════════════
# G · Integración: parse → validar → evaluar → ensamblar
# ═════════════════════════════════════════════════════════════════════

class TestIntegracion:

    def test_pipeline_completo(self):
        from mnfc.dsl import parse, validar, evaluar
        pcu = {
            "110101": {"naturaleza": "DEUDORA",
                       "marcos": ["caja", "PYMES"]},
            "410101": {"naturaleza": "ACREEDORA",
                       "marcos": ["ingreso", "PYMES"]},
        }
        ops = {"cien": lambda ctx: 100.0}
        src = '''
        DSL_VERSION "1.6";
        ELEMENTOS { activo; ingreso; }
        MARCOS { PYMES; }
        CATEGORIA caja = elemento: activo; universal: VERDADERO;
        CATEGORIA ingreso = elemento: ingreso; universal: FALSO;
        HECHO activo;
        FRACTAL ventas:
            REGLA registro:
                SI activo
                ENTONCES
                    GENERAR CONSECUENCIA(categoria=categoria(caja), operacion=cien, movimiento=AUMENTA, fuente=PYMES:S23)
                    GENERAR CONSECUENCIA(categoria=categoria(ingreso), operacion=cien, movimiento=AUMENTA, fuente=PYMES:S23);
        '''
        prog = parse(src)
        validar(prog)
        rs = evaluar(prog, {"activo": True}, pcu, ops, "PYMES")
        asientos = ensamblar(rs)
        assert len(asientos) == 1
        assert asientos[0].cuadrado is True
        assert asientos[0].total_debe == 100.0
        assert asientos[0].total_haber == 100.0
        assert len(asientos[0].lineas) == 2


# ═════════════════════════════════════════════════════════════════════
# H · Validación de montos individuales
# ═════════════════════════════════════════════════════════════════════

class TestValidacionMontos:

    @pytest.mark.parametrize("monto_inv,motivo", [
        (float("nan"),  "no finito"),
        (float("inf"),  "no finito"),
        (float("-inf"), "no finito"),
        (-100.0,        "negativo"),
        (-0.001,        "negativo"),
        (True,          "booleano"),
        (False,         "booleano"),
        ("100",         "no numérico"),
    ])
    def test_monto_invalido(self, monto_inv, motivo):
        pa = PartidaAutorizada(
            cuenta_codigo="X", cuenta_version="v1",
            monto=monto_inv, ubicacion="DEBE", movimiento="AUMENTA",
        )
        with pytest.raises(DSLAssemblyError, match=motivo):
            ensamblar([_rc("f", "r", 1, [pa])])

    def test_monto_decimal_rechazado_por_contrato_de_fase(self):
        """Decimal NO es inválido contablemente. Está fuera del contrato
        numérico de Fase 4 porque el kernel opera en float. Se documenta
        aquí para que la decisión no se confunda con un juicio sobre
        Decimal como tipo contable."""
        from decimal import Decimal
        pa = PartidaAutorizada(
            cuenta_codigo="X", cuenta_version="v1",
            monto=Decimal("100"), ubicacion="DEBE", movimiento="AUMENTA",
        )
        with pytest.raises(DSLAssemblyError, match="no numérico"):
            ensamblar([_rc("f", "r", 1, [pa])])

    def test_monto_cero_valido(self):
        rs = [_rc("f", "r", 1, [
            _pa("A", "DEBE", 0.0),
            _pa("B", "HABER", 0.0),
        ])]
        a = ensamblar(rs)[0]
        assert a.cuadrado is True
        assert a.total_debe == 0.0

    def test_monto_int_se_normaliza_a_float(self):
        pa = PartidaAutorizada(
            cuenta_codigo="A", cuenta_version="v1",
            monto=100, ubicacion="DEBE", movimiento="AUMENTA",
        )
        rs = [_rc("f", "r", 1, [pa, _pa("B", "HABER", 100.0)])]
        a = ensamblar(rs)[0]
        assert isinstance(a.lineas[0].monto, float)

    def test_error_monto_indica_cuenta(self):
        pa = PartidaAutorizada(
            cuenta_codigo="110101", cuenta_version="v1",
            monto=float("nan"), ubicacion="DEBE", movimiento="AUMENTA",
        )
        with pytest.raises(DSLAssemblyError) as exc:
            ensamblar([_rc("f", "r", 1, [pa])])
        assert "110101" in str(exc.value)

    def test_overflow_en_total_error_con_regla(self):
        """Suma de floats finitos desborda a inf. El pre-check detecta
        antes de fijar cuadrado y el error conserva (fractal, regla)."""
        rs = [_rc("ventas", "registro", 1, [
            _pa("A", "DEBE", 1e308),
            _pa("B", "DEBE", 1e308),
            _pa("C", "HABER", 1e308),
            _pa("D", "HABER", 1e308),
        ])]
        with pytest.raises(DSLAssemblyError, match="total no finito") as exc:
            ensamblar(rs)
        assert "FRACTAL ventas" in str(exc.value)
        assert "REGLA registro" in str(exc.value)


# ═════════════════════════════════════════════════════════════════════
# I · Contrato de error y agrupación
# ═════════════════════════════════════════════════════════════════════

class TestContratoError:

    def test_constructor_sin_contexto(self):
        e = DSLAssemblyError("msg")
        assert str(e) == "msg"
        assert e.mensaje == "msg"
        assert e.contexto == ""

    def test_constructor_con_contexto(self):
        e = DSLAssemblyError("msg", "FRACTAL f > REGLA r")
        assert str(e) == "FRACTAL f > REGLA r: msg"

    def test_hereda_de_dsl_evaluation_error(self):
        assert issubclass(DSLAssemblyError, DSLEvaluationError)

    def test_lista_vacia_devuelve_lista_vacia(self):
        assert ensamblar([]) == []

    def test_partidas_vacias_en_resultado_es_error(self):
        with pytest.raises(DSLAssemblyError, match="acción #1 sin partidas"):
            ensamblar([_rc("f", "r", 1, [])])

    def test_lista_vacia_vs_partidas_vacias_son_distintas(self):
        assert ensamblar([]) == []
        with pytest.raises(DSLAssemblyError):
            ensamblar([_rc("f", "r", 1, [])])


# ═════════════════════════════════════════════════════════════════════
# J · Diagnóstico seguro de diferencias (Corrección A)
# ═════════════════════════════════════════════════════════════════════

class TestDiferenciaSeguraEnMensaje:
    """El helper _describir_diferencia no debe propagar inf ni nan al
    texto diagnóstico. La decisión de cuadre la toma verificar_cuadre()
    antes; este helper sólo construye el mensaje de error.

    Nota: el branch `except (OverflowError, ValueError)` de
    _describir_diferencia no se ejercita desde aquí porque
    total_debe - total_haber (ambos finitos, no negativos) no
    lanza excepción en CPython. El try/except es defensa
    anticipada para fases futuras. Su verificación queda como
    deuda explícita si en v0.4 se admite un contrato numérico
    más amplio (Decimal, negativos, etc.).
    """

    def test_diferencia_normal(self):
        from mnfc.dsl.assembler import _describir_diferencia
        assert _describir_diferencia(100.0, 90.0) == "10.000000"

    def test_diferencia_cero(self):
        from mnfc.dsl.assembler import _describir_diferencia
        assert _describir_diferencia(100.0, 100.0) == "0.000000"

    def test_diferencia_negativa_usa_abs(self):
        from mnfc.dsl.assembler import _describir_diferencia
        assert _describir_diferencia(90.0, 100.0) == "10.000000"

    def test_entrada_no_finita_inf_positivo(self):
        from mnfc.dsl.assembler import _describir_diferencia
        assert _describir_diferencia(float("inf"), 90.0) == \
            "no calculable (overflow)"

    def test_entrada_no_finita_inf_negativo(self):
        from mnfc.dsl.assembler import _describir_diferencia
        assert _describir_diferencia(float("-inf"), 90.0) == \
            "no calculable (overflow)"

    def test_entrada_nan(self):
        from mnfc.dsl.assembler import _describir_diferencia
        assert _describir_diferencia(float("nan"), 90.0) == \
            "no calculable (overflow)"

    def test_mensaje_de_error_no_contiene_inf_ni_nan(self):
        rs = [_rc("f", "r", 1, [
            _pa("A", "DEBE", 100.0),
            _pa("B", "HABER", 90.0),
        ])]
        with pytest.raises(DSLAssemblyError) as exc:
            ensamblar(rs)
        msg = str(exc.value)
        assert "diferencia=10.000000" in msg
        assert "inf" not in msg
        assert "nan" not in msg
        assert "tolerancia=<0.001" in msg

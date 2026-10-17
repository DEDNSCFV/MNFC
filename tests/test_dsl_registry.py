"""Tests del registry del DSL (Fase 5).

Verifican:
- Registro de operaciones con metadatos.
- Orden de validación del contrato de registrar().
- Rechazo de duplicados, tipo inválido, nombre inválido, fuente/
  descripcion de tipo incorrecto, fn no callable.
- Estado intacto ante error (sin estado parcial).
- to_dict() devuelve copia (mutarla no afecta el registry).
- Integración con evaluator verificando resultado observable.

Sin marcos reales. Sin fiscal. Todo sintético.
"""
import pytest
from mnfc.dsl.registry import (
    Registry,
    OperacionRegistrada,
    DSLRegistryError,
    TIPOS_VALIDOS,
)


def _fn_suma(ctx):
    return sum(ctx["montos"])


def _fn_cien(ctx):
    return 100.0


def _op(nombre, fn=None, tipo="ley", fuente=None, descripcion=None):
    """Helper para construir OperacionRegistrada en tests.

    F5-R4: usa 'is not None' para no sustituir callables que
    evalúan a False por _fn_cien.
    """
    return OperacionRegistrada(
        nombre=nombre,
        fn=fn if fn is not None else _fn_cien,
        tipo=tipo,
        fuente=fuente,
        descripcion=descripcion,
    )


# ═════════════════════════════════════════════════════════════════════
# A · Registro básico
# ═════════════════════════════════════════════════════════════════════

class TestRegistro:

    def test_vacio(self):
        r = Registry()
        assert len(r) == 0
        assert r.listar() == []

    def test_una_operacion(self):
        r = Registry()
        r.registrar(_op("suma", _fn_suma))
        assert len(r) == 1
        assert r.contiene("suma") is True

    def test_varias_operaciones(self):
        r = Registry()
        r.registrar(_op("suma", _fn_suma))
        r.registrar(_op("cien", _fn_cien))
        assert len(r) == 2

    def test_con_metadatos(self):
        r = Registry()
        r.registrar(_op(
            "suma", _fn_suma, tipo="ley",
            fuente="PYMES:S23", descripcion="Suma montos"
        ))
        op = r.obtener("suma")
        assert op.tipo == "ley"
        assert op.fuente == "PYMES:S23"
        assert op.descripcion == "Suma montos"

    def test_registrar_es_una_sola_escritura(self):
        """F5-R7: propiedad estructural. Una única mutación de estado
        (inserción en _ops). No existe _orden (sin estructura paralela)."""
        r = Registry()
        r.registrar(_op("a", _fn_suma))
        assert list(r._ops.keys()) == ["a"]
        assert not hasattr(r, "_orden")


# ═════════════════════════════════════════════════════════════════════
# B · Validaciones del contrato de registrar()
# ═════════════════════════════════════════════════════════════════════

class TestValidaciones:

    def test_duplicado_error(self):
        r = Registry()
        r.registrar(_op("suma", _fn_suma))
        with pytest.raises(DSLRegistryError, match="ya registrada"):
            r.registrar(_op("suma", _fn_cien))

    def test_duplicado_conserva_original(self):
        """F5-R6: duplicado no altera el registro original."""
        r = Registry()
        r.registrar(_op("suma", _fn_suma, tipo="ley"))
        with pytest.raises(DSLRegistryError):
            r.registrar(_op("suma", _fn_cien, tipo="norma"))
        assert r.obtener("suma").tipo == "ley"
        assert r.obtener("suma").fn is _fn_suma
        assert len(r) == 1

    @pytest.mark.parametrize("tipo_inv", [
        "otro", "", "LEY", "Compuesta", "ley ", " ley"
    ])
    def test_tipo_str_invalido(self, tipo_inv):
        r = Registry()
        with pytest.raises(DSLRegistryError, match="tipo inválido"):
            r.registrar(_op("x", tipo=tipo_inv))

    @pytest.mark.parametrize("tipo_inv", [
        None, [], {}, 42, 3.14, object(), True
    ])
    def test_tipo_no_str_rechazado(self, tipo_inv):
        """F5-R3: tipo no-str no debe propagar TypeError de frozenset."""
        r = Registry()
        with pytest.raises(DSLRegistryError, match="tipo debe ser str"):
            r.registrar(_op("x", tipo=tipo_inv))

    @pytest.mark.parametrize("tipo_val", sorted(TIPOS_VALIDOS))
    def test_tipo_valido_aceptado(self, tipo_val):
        r = Registry()
        r.registrar(_op("x", tipo=tipo_val))
        assert r.obtener("x").tipo == tipo_val

    @pytest.mark.parametrize("nombre_inv", ["", " ", "   ", "\t", "\n", " \t\n "])
    def test_nombre_vacio_o_espacios_rechazado(self, nombre_inv):
        """F5-R1: nombre no vacío, no solo espacios."""
        r = Registry()
        with pytest.raises(DSLRegistryError, match="nombre no puede"):
            r.registrar(_op(nombre_inv))

    @pytest.mark.parametrize("nombre_inv", [None, 42, [], {}, object()])
    def test_nombre_no_str_rechazado(self, nombre_inv):
        """F5-R1: nombre debe ser str."""
        r = Registry()
        with pytest.raises(DSLRegistryError, match="nombre debe ser str"):
            r.registrar(OperacionRegistrada(nombre_inv, _fn_cien))

    @pytest.mark.parametrize("fuente_inv", [42, [], {}, 3.14, object(), True])
    def test_fuente_invalida(self, fuente_inv):
        """F5-R2: fuente str o None."""
        r = Registry()
        with pytest.raises(DSLRegistryError, match="fuente debe ser"):
            r.registrar(_op("x", fuente=fuente_inv))

    @pytest.mark.parametrize("desc_inv", [42, [], {}, 3.14, object(), True])
    def test_descripcion_invalida(self, desc_inv):
        """F5-R2: descripcion str o None."""
        r = Registry()
        with pytest.raises(DSLRegistryError, match="descripcion debe ser"):
            r.registrar(_op("x", descripcion=desc_inv))

    def test_fuente_none_aceptada(self):
        r = Registry()
        r.registrar(_op("x", fuente=None))
        assert r.obtener("x").fuente is None

    def test_descripcion_none_aceptada(self):
        r = Registry()
        r.registrar(_op("x", descripcion=None))
        assert r.obtener("x").descripcion is None

    def test_fn_no_callable(self):
        r = Registry()
        with pytest.raises(DSLRegistryError, match="fn no es callable"):
            r.registrar(OperacionRegistrada("x", "no-callable"))

    def test_tipo_no_operacion_registrada(self):
        r = Registry()
        with pytest.raises(DSLRegistryError, match="se esperaba"):
            r.registrar("no-es-operacion")

    def test_estado_intacto_tras_multiples_errores(self):
        """F5-R6: ningún error de validación deja estado parcial."""
        r = Registry()
        r.registrar(_op("suma", _fn_suma))
        for intento in [
            lambda: r.registrar(_op("suma", _fn_cien)),
            lambda: r.registrar(_op("nueva", tipo="otro")),
            lambda: r.registrar(_op("", _fn_cien)),
            lambda: r.registrar(_op("nueva", fuente=42)),
        ]:
            with pytest.raises(DSLRegistryError):
                intento()
        assert len(r) == 1
        assert [op.nombre for op in r.listar()] == ["suma"]
        assert r.obtener("suma").fn is _fn_suma


# ═════════════════════════════════════════════════════════════════════
# C · Obtener
# ═════════════════════════════════════════════════════════════════════

class TestObtener:

    def test_ausente_error(self):
        r = Registry()
        with pytest.raises(DSLRegistryError, match="no está en el registry"):
            r.obtener("fantasma")

    def test_ausente_mensaje_incluye_nombre(self):
        r = Registry()
        with pytest.raises(DSLRegistryError) as exc:
            r.obtener("suma_fantasma")
        assert "suma_fantasma" in str(exc.value)


# ═════════════════════════════════════════════════════════════════════
# D · contiene / __contains__
# ═════════════════════════════════════════════════════════════════════

class TestContiene:

    def test_contiene_existente(self):
        r = Registry()
        r.registrar(_op("suma", _fn_suma))
        assert r.contiene("suma") is True

    def test_contiene_ausente(self):
        r = Registry()
        assert r.contiene("x") is False

    def test_in_operator(self):
        r = Registry()
        r.registrar(_op("suma", _fn_suma))
        assert "suma" in r
        assert "x" not in r


# ═════════════════════════════════════════════════════════════════════
# E · listar
# ═════════════════════════════════════════════════════════════════════

class TestListar:

    def test_vacio(self):
        assert Registry().listar() == []

    def test_orden_de_registro(self):
        r = Registry()
        r.registrar(_op("b", tipo="ley"))
        r.registrar(_op("a", tipo="norma"))
        r.registrar(_op("c", tipo="compuesta"))
        nombres = [op.nombre for op in r.listar()]
        assert nombres == ["b", "a", "c"]


# ═════════════════════════════════════════════════════════════════════
# F · to_dict
# ═════════════════════════════════════════════════════════════════════

class TestToDict:

    def test_vacio(self):
        assert Registry().to_dict() == {}

    def test_forma_correcta(self):
        r = Registry()
        r.registrar(_op("suma", _fn_suma))
        r.registrar(_op("cien", _fn_cien))
        d = r.to_dict()
        assert set(d.keys()) == {"suma", "cien"}
        assert d["suma"] is _fn_suma
        assert d["cien"] is _fn_cien

    def test_sin_metadatos(self):
        r = Registry()
        r.registrar(_op("suma", _fn_suma, tipo="norma", fuente="X:1"))
        d = r.to_dict()
        assert isinstance(d["suma"], type(_fn_suma))
        assert not hasattr(d["suma"], "tipo")

    def test_mutar_dict_no_afecta_registry(self):
        """F5-R5: el dict devuelto es independiente del estado interno."""
        r = Registry()
        r.registrar(_op("suma", _fn_suma))
        d = r.to_dict()
        d["suma"] = lambda ctx: 999.0
        d["nueva"] = lambda ctx: 1.0
        assert r.obtener("suma").fn is _fn_suma
        assert len(r) == 1
        assert "nueva" not in r
        d2 = r.to_dict()
        assert d2["suma"] is _fn_suma
        assert "nueva" not in d2


# ═════════════════════════════════════════════════════════════════════
# G · __len__
# ═════════════════════════════════════════════════════════════════════

class TestLen:

    def test_vacio(self):
        assert len(Registry()) == 0

    def test_varios(self):
        r = Registry()
        r.registrar(_op("a"))
        r.registrar(_op("b"))
        r.registrar(_op("c"))
        assert len(r) == 3


# ═════════════════════════════════════════════════════════════════════
# H · Integración con evaluator (cierra F5-R8 al ejecutarse)
# ═════════════════════════════════════════════════════════════════════

class TestIntegracionConEvaluator:

    def test_registry_pasa_a_evaluar_y_produce_montos_esperados(self):
        """Verifica el resultado observable: cuentas, ubicaciones y
        montos exactos, no solo cantidad de resultados."""
        from mnfc.dsl import parse, validar, evaluar

        pcu = {
            "110101": {"naturaleza": "DEUDORA",
                       "marcos": ["caja", "PYMES"]},
            "410101": {"naturaleza": "ACREEDORA",
                       "marcos": ["ingreso", "PYMES"]},
        }
        r = Registry()
        r.registrar(_op("suma", _fn_suma, tipo="norma",
                        fuente="PYMES:S23"))

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
                    GENERAR CONSECUENCIA(categoria=categoria(caja), operacion=suma, movimiento=AUMENTA, fuente=PYMES:S23)
                    GENERAR CONSECUENCIA(categoria=categoria(ingreso), operacion=suma, movimiento=AUMENTA, fuente=PYMES:S23);
        '''
        prog = parse(src)
        validar(prog)
        resultados = evaluar(
            prog,
            {"activo": True, "montos": [100.0, 50.0]},
            pcu, r.to_dict(), "PYMES",
        )
        assert len(resultados) == 2
        p1 = resultados[0].partidas[0]
        assert p1.cuenta_codigo == "110101"
        assert p1.ubicacion == "DEBE"
        assert p1.monto == 150.0
        assert p1.norma_id == "PYMES:S23"
        p2 = resultados[1].partidas[0]
        assert p2.cuenta_codigo == "410101"
        assert p2.ubicacion == "HABER"
        assert p2.monto == 150.0
        assert p2.norma_id == "PYMES:S23"

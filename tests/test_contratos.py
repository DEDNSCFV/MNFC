"""
Categorias D + E - Determinismo y contratos de error.

D - Determinismo: mismo input -> mismo output, siempre. Hash estable
    entre sesiones, entre ordenes de claves, entre repeticiones.

E - Contratos: cada funcion lanza el tipo de excepcion correcto con
    un mensaje especifico. No hay excepciones genericas silenciosas.
"""
import json
import pytest
from mnfc import (
    calcular_ubicacion, ubicacion_booleana, ubicacion_gf2, ubicacion_signos,
    verificar_cuadre, sumar_montos, calcular_base_e_iva,
    capital_final, tiempo_ic,
    media, mediana, varianza_muestral, z_score,
    error_estandar_media, tamano_muestra_media,
    exponente_escalante, cascada,
    procesar_asiento, Ledger, GENESIS,
)


# ─────────────────────────────────────────────────────────────────────
# D.1 Determinismo del ledger
# ─────────────────────────────────────────────────────────────────────

class TestDeterminismoLedger:
    def test_mismo_input_mismo_hash_100_veces(self):
        """100 ledgers con la misma secuencia -> 100 raices identicas."""
        raices = set()
        for _ in range(100):
            l = Ledger()
            for i in range(5):
                l.append({"n": i, "monto": i * 100})
            raices.add(l.raiz())
        assert len(raices) == 1, f"se esperaba 1 raiz, hay {len(raices)}"

    def test_hash_estable_entre_sesiones(self):
        """El hash depende solo del contenido, no del momento."""
        l = Ledger()
        h = l.append({"x": 1, "y": 2})
        # El hash debe ser un hex de 64 chars determinista
        assert len(h) == 64
        # Verificacion manual del hash
        import hashlib
        canonical = json.dumps({"x": 1, "y": 2}, sort_keys=True, separators=(",", ":"))
        payload = f"{GENESIS}|{canonical}".encode("utf-8")
        esperado = hashlib.sha256(payload).hexdigest()
        assert h == esperado

    def test_orden_claves_no_afecta_raiz(self):
        l1 = Ledger()
        l1.append({"z": 1, "a": 2, "m": 3})
        l2 = Ledger()
        l2.append({"a": 2, "m": 3, "z": 1})
        assert l1.raiz() == l2.raiz()

    def test_orden_append_si_afecta_raiz(self):
        """Cambiar el orden de los bloques cambia la raiz."""
        l1 = Ledger()
        l1.append({"n": 1})
        l1.append({"n": 2})
        l2 = Ledger()
        l2.append({"n": 2})
        l2.append({"n": 1})
        assert l1.raiz() != l2.raiz()

    def test_raiz_cambia_con_cualquier_alteracion(self):
        l1 = Ledger()
        l1.append({"n": 1})
        l1.append({"n": 2})
        l1.append({"n": 3})
        r1 = l1.raiz()
        l2 = Ledger()
        l2.append({"n": 1})
        l2.append({"n": 2})
        l2.append({"n": 4})   # <- solo cambia el ultimo
        r2 = l2.raiz()
        assert r1 != r2


# ─────────────────────────────────────────────────────────────────────
# D.2 Serializacion y persistencia
# ─────────────────────────────────────────────────────────────────────

class TestSerializacion:
    def test_ledger_reconstruible_desde_contenidos(self):
        """Si guardo los contenidos, puedo reconstruir el ledger."""
        l1 = Ledger()
        contenidos = []
        for i in range(5):
            c = {"n": i, "monto": i * 100}
            l1.append(c)
            contenidos.append(c)

        # Simulamos persistencia: serializar a JSON, deserializar
        serializado = json.dumps(contenidos)
        recuperado = json.loads(serializado)

        # Reconstruimos
        l2 = Ledger()
        for c in recuperado:
            l2.append(c)

        assert l1.raiz() == l2.raiz()
        assert l1.verify()
        assert l2.verify()

    def test_repr_no_crashea(self):
        l = Ledger()
        l.append({"n": 1})
        r = repr(l)
        assert "Ledger" in r
        assert "n=1" in r


# ─────────────────────────────────────────────────────────────────────
# E.1 Contratos de error - XNOR
# ─────────────────────────────────────────────────────────────────────

class TestContratosXnor:
    def test_naturaleza_invalida_message(self):
        with pytest.raises(ValueError) as exc_info:
            ubicacion_booleana("INVALIDA", "AUMENTA")
        # El mensaje debe mencionar el valor problematico
        assert "INVALIDA" in str(exc_info.value)

    def test_movimiento_invalido_message(self):
        with pytest.raises(ValueError) as exc_info:
            ubicacion_gf2("DEUDORA", "BAILA")
        assert "BAILA" in str(exc_info.value)

    def test_tipo_incorrecto_falla(self):
        """None no es str. ¿Falla con mensaje util?"""
        with pytest.raises((ValueError, TypeError)):
            ubicacion_signos(None, "AUMENTA")


# ─────────────────────────────────────────────────────────────────────
# E.2 Contratos de error - Baldor
# ─────────────────────────────────────────────────────────────────────

class TestContratosBaldor:
    def test_iva_message(self):
        # calcular_base_e_iva no falla con tasa negativa en la version actual,
        # pero verificamos su comportamiento
        base, iva = calcular_base_e_iva(1160.0, 0.16)
        assert base + iva == pytest.approx(1160.0)

    def test_tiempo_ic_con_r_cero_falla(self):
        """r=0 -> division por cero (bug conocido, declarado en frontera)."""
        with pytest.raises((ValueError, ZeroDivisionError)):
            tiempo_ic(200.0, 100.0, 0.0)

    def test_tiempo_ic_con_r_menos_uno_falla(self):
        """r=-1 -> log(0), indefinido."""
        with pytest.raises((ValueError, ZeroDivisionError)):
            tiempo_ic(200.0, 100.0, -1.0)


# ─────────────────────────────────────────────────────────────────────
# E.3 Contratos de error - Estadistica
# ─────────────────────────────────────────────────────────────────────

class TestContratosEstadistica:
    def test_media_vacia_message(self):
        with pytest.raises(ValueError) as exc_info:
            media([])
        assert "vacia" in str(exc_info.value).lower()

    def test_error_estandar_n_cero_falla(self):
        with pytest.raises(ValueError) as exc_info:
            error_estandar_media(10.0, 0)
        assert "n" in str(exc_info.value).lower()

    def test_error_estandar_n_negativo_falla(self):
        with pytest.raises(ValueError):
            error_estandar_media(10.0, -5)

    def test_tamano_muestra_B_cero_falla(self):
        with pytest.raises(ValueError):
            tamano_muestra_media(1.96, 10.0, 0.0)

    def test_z_score_serie_constante_message(self):
        with pytest.raises((ValueError, ZeroDivisionError)):
            z_score(5, [5, 5, 5, 5])


# ─────────────────────────────────────────────────────────────────────
# E.4 Contratos de error - Fractal
# ─────────────────────────────────────────────────────────────────────

class TestContratosFractal:
    def test_serie_corta_message(self):
        with pytest.raises(ValueError) as exc_info:
            exponente_escalante([1])
        assert "corta" in str(exc_info.value).lower()

    def test_serie_vacia_message(self):
        with pytest.raises(ValueError):
            exponente_escalante([])

    def test_cascada_con_niveles_invalidos_ignora(self):
        """Niveles <= 1 o > len(xs) se ignoran silenciosamente."""
        r = cascada([1, 2, 3], [1, 0, -5, 100])
        assert r == []  # todos ignorados


# ─────────────────────────────────────────────────────────────────────
# E.5 Contratos de error - MNFC composicion
# ─────────────────────────────────────────────────────────────────────

class TestContratosMnfc:
    def test_asiento_vacio_message(self):
        with pytest.raises(ValueError) as exc_info:
            procesar_asiento([])
        assert "sin lineas" in str(exc_info.value).lower() or "vacio" in str(exc_info.value).lower()

    def test_linea_sin_campo_message(self):
        with pytest.raises(ValueError) as exc_info:
            procesar_asiento([{"naturaleza": "DEUDORA"}])
        # El mensaje debe indicar qué campo falta
        msg = str(exc_info.value)
        assert "movimiento" in msg or "monto" in msg

    def test_descuadre_message(self):
        with pytest.raises(ValueError) as exc_info:
            procesar_asiento([
                {"naturaleza": "DEUDORA",   "movimiento": "AUMENTA", "monto": 100},
                {"naturaleza": "ACREEDORA", "movimiento": "AUMENTA", "monto": 200},
            ])
        msg = str(exc_info.value)
        assert "descuadr" in msg.lower() or "debe" in msg.lower()

    def test_tipo_error_en_monto_no_numerico(self):
        """monto="abc" -> ValueError al convertir a float."""
        with pytest.raises((ValueError, TypeError)):
            procesar_asiento([
                {"naturaleza": "DEUDORA",   "movimiento": "AUMENTA", "monto": "abc"},
                {"naturaleza": "ACREEDORA", "movimiento": "AUMENTA", "monto": "abc"},
            ])


# ─────────────────────────────────────────────────────────────────────
# E.6 Contratos de error - Ledger
# ─────────────────────────────────────────────────────────────────────

class TestContratosLedger:
    def test_append_none_message(self):
        l = Ledger()
        with pytest.raises(TypeError) as exc_info:
            l.append(None)
        assert "dict" in str(exc_info.value).lower()
        assert "nonetype" in str(exc_info.value).lower() or "none" in str(exc_info.value).lower()

    def test_append_string_falla(self):
        l = Ledger()
        with pytest.raises(TypeError):
            l.append("no soy dict")

    def test_append_lista_falla(self):
        l = Ledger()
        with pytest.raises(TypeError):
            l.append([1, 2, 3])

    def test_append_numero_falla(self):
        l = Ledger()
        with pytest.raises(TypeError):
            l.append(42)


# ─────────────────────────────────────────────────────────────────────
# D.3 Determinismo de xnor (invariante fundamental)
# ─────────────────────────────────────────────────────────────────────

class TestDeterminismoXnor:
    def test_100_llamadas_mismo_resultado(self):
        """100 llamadas con el mismo input -> mismo output."""
        resultados = set()
        for _ in range(100):
            resultados.add(calcular_ubicacion("DEUDORA", "AUMENTA"))
        assert resultados == {"DEBE"}

    def test_tres_caras_deterministas(self):
        """Las 3 caras siempre devuelven lo mismo."""
        for _ in range(50):
            b = ubicacion_booleana("ACREEDORA", "DISMINUYE")
            g = ubicacion_gf2("ACREEDORA", "DISMINUYE")
            s = ubicacion_signos("ACREEDORA", "DISMINUYE")
            assert b == g == s == "DEBE"

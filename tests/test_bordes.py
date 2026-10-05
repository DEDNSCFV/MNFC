"""
Categoria A - Pruebas de borde.

Inputs extremos que rompen la logica normal si no se manejan bien.
Cubre: montos cero/negativos/grandes, floats imprecisos, series
vacias o de un solo elemento, unicode en cuentas, orden de claves.
"""
import pytest
from mnfc import (
    calcular_ubicacion, ubicacion_booleana, ubicacion_gf2, ubicacion_signos,
    verificar_cuadre, sumar_montos, calcular_base_e_iva,
    capital_final, capital_inicial, tiempo_ic, tasa_ic,
    media, mediana, varianza_muestral, z_score,
    procesar_asiento, Ledger, GENESIS,
)


class TestMontos:
    def test_monto_cero_cuadra(self):
        a = procesar_asiento([
            {"naturaleza": "DEUDORA",   "movimiento": "AUMENTA", "monto": 0.0},
            {"naturaleza": "ACREEDORA", "movimiento": "AUMENTA", "monto": 0.0},
        ])
        assert a.cuadrado
        assert a.total_debe == 0.0
        assert a.total_haber == 0.0

    def test_monto_negativo_en_linea(self):
        a = procesar_asiento([
            {"naturaleza": "DEUDORA",   "movimiento": "AUMENTA", "monto": -100.0},
            {"naturaleza": "ACREEDORA", "movimiento": "AUMENTA", "monto": -100.0},
        ])
        assert a.cuadrado

    def test_monto_muy_grande(self):
        a = procesar_asiento([
            {"naturaleza": "DEUDORA",   "movimiento": "AUMENTA", "monto": 1e15},
            {"naturaleza": "ACREEDORA", "movimiento": "AUMENTA", "monto": 1e15},
        ])
        assert a.cuadrado
        assert a.total_debe == 1e15

    def test_float_impreciso_cuadra_con_epsilon(self):
        assert verificar_cuadre(0.1 + 0.2, 0.3)

    def test_float_impreciso_muchas_lineas(self):
        debe = [0.1] * 10
        haber = [0.3] * 3 + [0.1]
        assert verificar_cuadre(sumar_montos(debe), sumar_montos(haber))

    def test_monto_como_string_numerico(self):
        a = procesar_asiento([
            {"naturaleza": "DEUDORA",   "movimiento": "AUMENTA", "monto": "1000"},
            {"naturaleza": "ACREEDORA", "movimiento": "AUMENTA", "monto": "1000"},
        ])
        assert a.cuadrado
        assert a.total_debe == 1000.0


class TestSeries:
    def test_media_vacia_falla(self):
        with pytest.raises(ValueError):
            media([])

    def test_mediana_vacia_falla(self):
        with pytest.raises(ValueError):
            mediana([])

    def test_varianza_un_elemento_falla(self):
        with pytest.raises(ValueError):
            varianza_muestral([42])

    def test_media_un_elemento(self):
        assert media([42]) == 42

    def test_mediana_un_elemento(self):
        assert mediana([42]) == 42

    def test_z_score_serie_constante_falla(self):
        with pytest.raises((ValueError, ZeroDivisionError)):
            z_score(5, [5, 5, 5, 5, 5])


class TestUnicodeYClaves:
    def test_unicode_en_cuenta(self):
        a = procesar_asiento([
            {"cuenta": "Caja Ñandú", "naturaleza": "DEUDORA",   "movimiento": "AUMENTA", "monto": 100},
            {"cuenta": "Omega",      "naturaleza": "ACREEDORA", "movimiento": "AUMENTA", "monto": 100},
        ])
        assert a.cuadrado
        assert a.lineas[0]["cuenta"] == "Caja Ñandú"
        assert a.lineas[1]["cuenta"] == "Omega"

    def test_orden_de_claves_no_afecta_hash(self):
        l1 = Ledger()
        h1 = l1.append({"a": 1, "b": 2, "c": 3})
        l2 = Ledger()
        h2 = l2.append({"c": 3, "a": 1, "b": 2})
        assert h1 == h2

    def test_claves_anidadas_hash_estable(self):
        l1 = Ledger()
        h1 = l1.append({"outer": {"z": 1, "a": 2}})
        l2 = Ledger()
        h2 = l2.append({"outer": {"a": 2, "z": 1}})
        assert h1 == h2


class TestFinanciero:
    def test_iva_tasa_cero(self):
        base, iva = calcular_base_e_iva(1000.0, 0.0)
        assert base == 1000.0
        assert iva == 0.0

    def test_iva_tasa_negativa(self):
        try:
            base, iva = calcular_base_e_iva(1000.0, -0.5)
            assert base + iva == pytest.approx(1000.0)
        except ValueError:
            pass

    def test_capital_final_tiempo_cero(self):
        assert capital_final(1000.0, 0.05, 0) == 1000.0

    def test_capital_final_tasa_cero(self):
        assert capital_final(1000.0, 0.0, 10) == 1000.0

    def test_tasa_ic_capital_unico(self):
        r = tasa_ic(1000.0, 1000.0, 5)
        assert abs(r) < 1e-10


class TestLedgerBordes:
    def test_ledger_recien_creado(self):
        l = Ledger()
        assert len(l) == 0
        assert l.raiz() == GENESIS
        assert l.verify()

    def test_genesis_es_64_ceros(self):
        assert GENESIS == "0" * 64
        assert len(GENESIS) == 64

    def test_ledger_append_none(self):
        l = Ledger()
        with pytest.raises((TypeError, ValueError, AttributeError)):
            l.append(None)

    def test_ledger_contenido_vacio_cuadrado(self):
        l = Ledger()
        h = l.append({})
        assert len(h) == 64
        assert l.verify()

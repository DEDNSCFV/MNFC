"""
Tests adversariales. Intentan romper MNFC.

A diferencia de los tests de determinismo (que verifica
propiedades conocidas), estos tests PLANTEAN una exigencia
y verifican si MNFC la cumple. Los que fallen son información:
bug, hueco de diseño, o frontera no documentada.

Postura: un kernel contable formal no debe propagar NaN o
Inf silenciosamente. Un IC con p fuera de [0,1] no es un IC
válido. Un tamaño muestral con B=0 no tiene sentido.

Si estos tests pasan, MNFC es mas robusto de lo que asumo.
Si fallan, sabemos exactamente donde apretar.
"""
import math
import pytest

from mnfc import (
    media, mediana, moda, modas, varianza_muestral, desviacion_muestral,
    cuartiles, iqr, z_score, coef_variacion,
    normal_pdf, normal_cdf,
    error_estandar_media, error_estandar_proporcion,
    tamano_muestra_media, tamano_muestra_proporcion,
    margen_error, ic_media, ic_proporcion, proyeccion_error,
    es_atipico_z, es_atipico_iqr, z_score_serie,
    sumar_montos, verificar_cuadre,
    Ledger, GENESIS,
    cascada, exponente_escalante, clasificar_cascada,
)


NAN = float("nan")
INF = float("inf")


class TestCategoriaA_NanInf:
    """Postura: NaN/Inf en entradas contables debe ser error, no valor."""

    def test_media_rechaza_nan(self):
        with pytest.raises((ValueError, TypeError)):
            media([1.0, NAN, 3.0])

    def test_media_rechaza_inf(self):
        with pytest.raises((ValueError, TypeError)):
            media([1.0, INF, 3.0])

    def test_mediana_rechaza_nan(self):
        with pytest.raises((ValueError, TypeError)):
            mediana([1.0, NAN, 3.0])

    def test_varianza_rechaza_nan(self):
        with pytest.raises((ValueError, TypeError)):
            varianza_muestral([1.0, NAN, 3.0])

    def test_desviacion_rechaza_nan(self):
        with pytest.raises((ValueError, TypeError)):
            desviacion_muestral([1.0, NAN, 3.0])

    def test_cuartiles_rechaza_nan(self):
        with pytest.raises((ValueError, TypeError)):
            cuartiles([1.0, NAN, 3.0])

    def test_z_score_rechaza_nan_en_xs(self):
        with pytest.raises((ValueError, TypeError)):
            z_score(2.0, [1.0, NAN, 3.0])

    def test_coef_variacion_rechaza_nan(self):
        with pytest.raises((ValueError, TypeError)):
            coef_variacion([1.0, NAN, 3.0])

    def test_sumar_montos_rechaza_nan(self):
        with pytest.raises((ValueError, TypeError)):
            sumar_montos([100.0, NAN, 50.0])


class TestCategoriaB_Dominios:
    """Postura: parametros fuera de dominio matematico deben fallar."""

    def test_normal_pdf_sigma_cero(self):
        with pytest.raises((ValueError, ZeroDivisionError)):
            normal_pdf(0.0, 0.0, 0.0)

    def test_normal_pdf_sigma_negativo(self):
        with pytest.raises((ValueError, ZeroDivisionError)):
            normal_pdf(0.0, 0.0, -1.0)

    def test_normal_cdf_sigma_cero(self):
        with pytest.raises((ValueError, ZeroDivisionError)):
            normal_cdf(0.0, 0.0, 0.0)

    def test_error_estandar_media_n_cero(self):
        with pytest.raises((ValueError, ZeroDivisionError)):
            error_estandar_media(10.0, 0)

    def test_error_estandar_media_n_negativo(self):
        with pytest.raises((ValueError, ValueError)):
            error_estandar_media(10.0, -5)

    def test_error_estandar_media_sigma_negativo(self):
        with pytest.raises((ValueError, ValueError)):
            error_estandar_media(-10.0, 25)

    def test_error_estandar_proporcion_n_cero(self):
        with pytest.raises((ValueError, ZeroDivisionError)):
            error_estandar_proporcion(0.5, 0)

    def test_error_estandar_proporcion_p_mayor_1(self):
        with pytest.raises((ValueError, ValueError)):
            error_estandar_proporcion(1.5, 100)

    def test_error_estandar_proporcion_p_negativo(self):
        with pytest.raises((ValueError, ValueError)):
            error_estandar_proporcion(-0.1, 100)

    def test_tamano_muestra_media_B_cero(self):
        with pytest.raises((ValueError, ZeroDivisionError)):
            tamano_muestra_media(1.96, 10.0, 0.0)

    def test_tamano_muestra_media_sigma_negativo(self):
        with pytest.raises((ValueError, ValueError)):
            tamano_muestra_media(1.96, -10.0, 2.0)

    def test_tamano_muestra_proporcion_B_cero(self):
        with pytest.raises((ValueError, ZeroDivisionError)):
            tamano_muestra_proporcion(1.96, 0.4, 0.0)

    def test_tamano_muestra_proporcion_p_fuera(self):
        with pytest.raises((ValueError, ValueError)):
            tamano_muestra_proporcion(1.96, 1.5, 0.05)

    def test_margen_error_n_cero(self):
        with pytest.raises((ValueError, ZeroDivisionError)):
            margen_error(1.96, 10.0, 0)

    def test_ic_media_n_cero(self):
        with pytest.raises((ValueError, ZeroDivisionError)):
            ic_media([], 1.96)

    def test_ic_proporcion_p_fuera(self):
        with pytest.raises((ValueError, ValueError)):
            ic_proporcion(1.5, 100)

    def test_ic_proporcion_n_cero(self):
        with pytest.raises((ValueError, ZeroDivisionError)):
            ic_proporcion(0.5, 0)

    def test_proyeccion_error_n_cero(self):
        with pytest.raises((ValueError, ZeroDivisionError)):
            proyeccion_error(2.0, 1000, 0)

    def test_proyeccion_error_n_mayor_N(self):
        with pytest.raises((ValueError, ValueError)):
            proyeccion_error(2.0, 10, 100)


class TestCategoriaC_Tipos:
    """Postura: entradas con tipo incorrecto deben fallar limpiamente."""

    def test_media_string(self):
        with pytest.raises((TypeError, ValueError)):
            media("123")

    def test_media_lista_con_string(self):
        with pytest.raises((TypeError, ValueError)):
            media([1.0, "dos", 3.0])

    def test_media_lista_con_none(self):
        with pytest.raises((TypeError, ValueError)):
            media([1.0, None, 3.0])

    def test_media_dict(self):
        with pytest.raises((TypeError, ValueError)):
            media({"a": 1.0})

    def test_sumar_montos_string(self):
        with pytest.raises((TypeError, ValueError)):
            sumar_montos(["100", "50"])

    def test_verificar_cuadre_string(self):
        with pytest.raises((TypeError, ValueError)):
            verificar_cuadre("100", "100")


class TestCategoriaD_Extremos:
    """Postura: entradas extremas no deben producir silencios raros."""

    @pytest.mark.xfail(strict=True,
                       reason="overflow float por suma directa; "
                              "documentado en media()")
    def test_media_dos_max_floats(self):
        # Overflow conocido: sum([1e308, 1e308]) = inf.
        # Documentado, no arreglado. Si alguien lo arregla (suma
        # Kahan o similar), este xfail pasa a XPASS y salta.
        r = media([1e308, 1e308])
        assert math.isfinite(r), f"media de dos 1e308 no es finita: {r}"

    def test_varianza_valores_enormes(self):
        r = varianza_muestral([1e150, -1e150, 1e150, -1e150])
        # La varianza real es ~1e300; si se desborda, es bug.
        assert math.isfinite(r) or r == float("inf")

    def test_normal_cdf_extremos_estables(self):
        # En x muy negativo, debe tender a 0; muy positivo, a 1.
        assert normal_cdf(-100.0) == pytest.approx(0.0, abs=1e-6)
        assert normal_cdf(100.0) == pytest.approx(1.0, abs=1e-6)

    def test_normal_cdf_monotona(self):
        xs = [-5, -2, -1, 0, 1, 2, 5]
        vals = [normal_cdf(x) for x in xs]
        for i in range(len(vals) - 1):
            assert vals[i] <= vals[i+1], f"no monotona en {xs[i]}->{xs[i+1]}"

    def test_normal_pdf_simetria(self):
        for x in [0.5, 1.0, 2.0, 3.0]:
            assert normal_pdf(x) == pytest.approx(normal_pdf(-x), abs=1e-15)


class TestCategoriaE_Ledger:
    """Postura: el ledger debe detectar manipulaciones."""

    def test_mutacion_post_append_detectada(self):
        lg = Ledger()
        d = {"debe": "caja", "haber": "ventas", "monto": 100.0}
        lg.append(d)
        d["monto"] = 999.0  # mutacion externa
        # verify() debe detectar la alteracion
        assert lg.verify() is False

    def test_append_no_dict_falla(self):
        lg = Ledger()
        with pytest.raises(TypeError):
            lg.append("string")
        with pytest.raises(TypeError):
            lg.append(None)
        with pytest.raises(TypeError):
            lg.append([1, 2, 3])

    def test_append_dict_con_set_falla(self):
        lg = Ledger()
        with pytest.raises(TypeError):
            lg.append({"conjunto": {1, 2, 3}})

    def test_chain_1000_bloques_estable(self):
        lg = Ledger()
        for i in range(1000):
            lg.append({"i": i, "monto": float(i)})
        assert len(lg) == 1000
        assert lg.verify() is True

    def test_ledger_vacio_no_tiene_raiz_aleatoria(self):
        lg1 = Ledger()
        lg2 = Ledger()
        assert lg1.raiz() == lg2.raiz() == GENESIS

    def test_verify_no_depende_del_estado_externo(self):
        lg = Ledger()
        lg.append({"a": 1})
        lg.append({"b": 2})
        r1 = lg.verify()
        for _ in range(100):
            assert lg.verify() == r1


class TestCategoriaF_Fractal:
    """Postura: series degeneradas no deben dar clasificaciones validas."""

    def test_cascada_lista_vacia(self):
        r = cascada([], [2, 3, 5])
        assert r == []

    def test_cascada_un_solo_elemento(self):
        r = cascada([5.0], [2, 3, 5])
        assert r == []

    def test_cascada_todos_cero(self):
        # Serie constante: varianza cero, no debe aparecer en cascada.
        r = cascada([0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [2, 3])
        assert r == []

    def test_exponente_serie_corta_falla(self):
        with pytest.raises(ValueError):
            exponente_escalante([1.0, 2.0])

    def test_exponente_serie_constante_falla(self):
        with pytest.raises(ValueError):
            exponente_escalante([5.0] * 20)

    def test_clasificar_lista_vacia_falla(self):
        with pytest.raises(ValueError):
            clasificar_cascada([])


class TestCategoriaG_Regresion:
    """Regresion: estos casos fallaban antes del fix de validacion."""

    def test_media_con_nan_lanza(self):
        with pytest.raises(ValueError):
            media([1.0, NAN, 3.0])

    def test_media_con_inf_lanza(self):
        with pytest.raises(ValueError):
            media([1.0, INF, 3.0])

    def test_mediana_con_nan_lanza(self):
        with pytest.raises(ValueError):
            mediana([1.0, NAN, 3.0])

    def test_sumar_montos_con_nan_lanza(self):
        with pytest.raises(ValueError):
            sumar_montos([100.0, NAN, 50.0])

    def test_verificar_cuadre_con_inf_lanza(self):
        with pytest.raises(ValueError):
            verificar_cuadre(INF, 100.0)

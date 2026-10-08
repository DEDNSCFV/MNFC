"""
Tests de determinismo del kernel MNFC (capas 0-6).

Objetivo: verificar empiricamente que el kernel es puro: misma entrada,
misma salida, siempre. No se testean extensiones (capa 7) porque
generan UUID y timestamps por diseno.

Ejes verificados:
    1. Idempotencia: dos llamadas con mismo input -> mismo output.
    2. Orden-independencia: agregaciones -> permutar la entrada no cambia.
    3. Ledger determinista: misma cadena -> mismo hash raiz.
    4. Constantes del kernel inmutables tras importacion.

Sin random, sin time. Solo permutaciones deterministas.
"""

import pytest

from mnfc import (
    # Capa 0
    calcular_ubicacion, ubicacion_booleana, ubicacion_gf2, ubicacion_signos,
    # Capa 1
    ley_de_signos, sumar_montos, verificar_cuadre,
    # Capa 2
    media, mediana, moda, modas, varianza_muestral, desviacion_muestral,
    cuartiles, iqr, z_score, coef_variacion,
    normal_pdf, normal_cdf, z_critico_90, z_critico_95, z_critico_99,
    error_estandar_media, error_estandar_proporcion,
    tamano_muestra_media, tamano_muestra_proporcion,
    limite_control_media, margen_error, ic_media, ic_proporcion,
    proyeccion_error, ic_una_cola_sup, ic_una_cola_inf,
    es_atipico_z, es_atipico_iqr, z_score_serie,
    stock_seguridad, pronostico_media_movil,
    # Capa 3
    cascada, exponente_escalante, clasificar_cascada, reporte_cascada,
    # Capa 6
    Ledger, GENESIS,
)


XS = [3.0, 5.0, 4.0, 6.0, 10.0, 5.0, 6.0, 9.0, 2.0, 8.0]
XS_POS = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]


class TestIdempotencia:
    """Dos llamadas identicas -> mismo resultado (==)."""

    def test_media(self):
        assert media(XS) == media(XS)

    def test_mediana(self):
        assert mediana(XS) == mediana(XS)

    def test_moda(self):
        assert moda(XS) == moda(XS)

    def test_modas(self):
        assert modas(XS) == modas(XS)

    def test_varianza(self):
        assert varianza_muestral(XS) == varianza_muestral(XS)

    def test_desviacion(self):
        assert desviacion_muestral(XS) == desviacion_muestral(XS)

    def test_cuartiles(self):
        assert cuartiles(XS) == cuartiles(XS)

    def test_iqr(self):
        assert iqr(XS) == iqr(XS)

    def test_z_score(self):
        assert z_score(5.0, XS) == z_score(5.0, XS)

    def test_coef_variacion(self):
        assert coef_variacion(XS) == coef_variacion(XS)

    def test_normal_pdf(self):
        assert normal_pdf(0.0) == normal_pdf(0.0)
        assert normal_pdf(1.96, 0.0, 1.0) == normal_pdf(1.96, 0.0, 1.0)

    def test_normal_cdf(self):
        assert normal_cdf(0.0) == normal_cdf(0.0)
        assert normal_cdf(1.96) == normal_cdf(1.96)
        assert normal_cdf(-2.5) == normal_cdf(-2.5)

    def test_z_criticos_constantes(self):
        assert z_critico_90() == z_critico_90()
        assert z_critico_95() == z_critico_95()
        assert z_critico_99() == z_critico_99()

    def test_error_estandar(self):
        assert error_estandar_media(10.0, 25) == error_estandar_media(10.0, 25)
        assert error_estandar_proporcion(0.4, 100) == error_estandar_proporcion(0.4, 100)

    def test_tamanos_muestra(self):
        assert tamano_muestra_media(1.96, 10.0, 2.0) == tamano_muestra_media(1.96, 10.0, 2.0)
        assert tamano_muestra_proporcion(1.96, 0.4, 0.05) == tamano_muestra_proporcion(1.96, 0.4, 0.05)

    def test_limite_control(self):
        assert limite_control_media(XS) == limite_control_media(XS)

    def test_margen_error(self):
        assert margen_error(1.96, 10.0, 25) == margen_error(1.96, 10.0, 25)

    def test_ic_media(self):
        assert ic_media(XS) == ic_media(XS)

    def test_ic_proporcion(self):
        assert ic_proporcion(0.4, 100) == ic_proporcion(0.4, 100)

    def test_proyeccion_error(self):
        assert proyeccion_error(2.0, 1000, 100) == proyeccion_error(2.0, 1000, 100)

    def test_ic_una_cola(self):
        assert ic_una_cola_sup(XS, 1.645) == ic_una_cola_sup(XS, 1.645)
        assert ic_una_cola_inf(XS, 1.645) == ic_una_cola_inf(XS, 1.645)

    def test_atipicos(self):
        assert es_atipico_z(20.0, XS) == es_atipico_z(20.0, XS)
        assert es_atipico_iqr(20.0, XS) == es_atipico_iqr(20.0, XS)

    def test_z_score_serie(self):
        assert z_score_serie(XS) == z_score_serie(XS)

    def test_stock_seguridad(self):
        assert stock_seguridad(1.645, 2.0, 5.0) == stock_seguridad(1.645, 2.0, 5.0)

    def test_pronostico_media_movil(self):
        assert pronostico_media_movil(XS, 3) == pronostico_media_movil(XS, 3)

    def test_capa3_fractal(self):
        assert cascada(XS, [1, 2, 4]) == cascada(XS, [1, 2, 4])
        assert exponente_escalante(XS) == exponente_escalante(XS)
        assert clasificar_cascada(XS) == clasificar_cascada(XS)
        assert reporte_cascada(XS) == reporte_cascada(XS)


def _permutaciones_deterministas(xs):
    """Devuelve 3 permutaciones fijas de xs, sin random."""
    n = len(xs)
    return [
        list(reversed(xs)),                              # invertida
        xs[n//2:] + xs[:n//2],                            # rotada
        [xs[i] for i in (0, 2, 4, 6, 8, 1, 3, 5, 7, 9)],  # intercalada fija
    ]


class TestOrdenIndependencia:
    """Agregaciones que no dependen del orden de la entrada."""

    def test_media(self):
        base = media(XS)
        for p in _permutaciones_deterministas(XS):
            assert media(p) == base

    def test_mediana(self):
        base = mediana(XS)
        for p in _permutaciones_deterministas(XS):
            assert mediana(p) == base

    def test_varianza(self):
        base = varianza_muestral(XS)
        for p in _permutaciones_deterministas(XS):
            assert varianza_muestral(p) == base

    def test_desviacion(self):
        base = desviacion_muestral(XS)
        for p in _permutaciones_deterministas(XS):
            assert desviacion_muestral(p) == base

    def test_cuartiles(self):
        base = cuartiles(XS)
        for p in _permutaciones_deterministas(XS):
            assert cuartiles(p) == base

    def test_iqr(self):
        base = iqr(XS)
        for p in _permutaciones_deterministas(XS):
            assert iqr(p) == base

    def test_modas_orden_independiente(self):
        # modas() devuelve lista; comparamos como conjunto ordenado.
        base = sorted(modas(XS))
        for p in _permutaciones_deterministas(XS):
            assert sorted(modas(p)) == base



class TestLedgerDeterminista:
    """Misma cadena de bloques -> mismo hash raiz."""

    ASIENTOS = [
        {"debe": "caja", "haber": "ventas", "monto": 100.0},
        {"debe": "caja", "haber": "ventas", "monto": 250.5},
        {"debe": "gasto", "haber": "caja", "monto": 40.0},
    ]

    def _construir(self):
        lg = Ledger()
        for a in self.ASIENTOS:
            lg.append(a)
        return lg

    def test_raiz_estable(self):
        r1 = self._construir().raiz()
        r2 = self._construir().raiz()
        assert r1 == r2

    def test_hashes_individuales_estables(self):
        h1 = [self._construir()._hashes[i] for i in range(3)]
        h2 = [self._construir()._hashes[i] for i in range(3)]
        assert h1 == h2

    def test_verify_siempre_true(self):
        assert self._construir().verify() is True
        assert self._construir().verify() is True

    def test_ledger_vacio_raiz_genesis(self):
        lg = Ledger()
        assert lg.raiz() == GENESIS
        assert lg.verify() is True
        assert len(lg) == 0

    def test_ledger_100_repeticiones(self):
        """100 repeticiones -> 100 veces el mismo hash raiz."""
        ref = self._construir().raiz()
        for _ in range(100):
            assert self._construir().raiz() == ref


class TestConstantesInmutables:
    """Las constantes del kernel no se mutan tras importacion."""

    def test_naturalezas_validas(self):
        from mnfc import NATURALEZAS_VALIDAS, MOVIMIENTOS_VALIDOS
        assert NATURALEZAS_VALIDAS == ("DEUDORA", "ACREEDORA")
        assert MOVIMIENTOS_VALIDOS == ("AUMENTA", "DISMINUYE")

    def test_ubicacion_estable(self):
        # calcular_ubicacion debe dar el mismo resultado tras muchas llamadas
        esperado = calcular_ubicacion("DEUDORA", "AUMENTA")
        for _ in range(50):
            assert calcular_ubicacion("DEUDORA", "AUMENTA") == esperado

    def test_xnor_cuatro_casos_estables(self):
        casos = [
            ("DEUDORA",   "AUMENTA"),
            ("DEUDORA",   "DISMINUYE"),
            ("ACREEDORA", "AUMENTA"),
            ("ACREEDORA", "DISMINUYE"),
        ]
        ref = {c: calcular_ubicacion(*c) for c in casos}
        for _ in range(50):
            for c in casos:
                assert calcular_ubicacion(*c) == ref[c]


class TestSensibilidadAlOrden:
    """
    Las funciones de capa 3 (fractal) son SENSIBLES al orden de la
    serie por diseno: miden autosimilitud de una serie temporal.

    cascada() agrupa bloques consecutivos: xs[i:i+k]. Si se permuta
    la serie, cambian los bloques, cambia la varianza agregada, cambia
    beta. Es una propiedad matematica, no un bug.

    Estos tests DOCUMENTAN y BLOQUEAN esa sensibilidad. Si alguien
    refactoriza cascada() para ser orden-independiente, estos tests
    fallan y obligan a revisar la decision.
    """

    def test_cascada_sensible_al_orden(self):
        """cascada() con serie invertida da distinto resultado."""
        a = cascada(XS, [2, 3, 5])
        b = cascada(list(reversed(XS)), [2, 3, 5])
        assert a != b

    def test_exponente_sensible_al_orden(self):
        """exponente_escalante() cambia con el orden de la serie."""
        a = exponente_escalante(XS)
        b = exponente_escalante(list(reversed(XS)))
        # No exigimos un valor concreto, solo que cambie.
        assert a != b

    def test_clasificar_no_es_invariante(self):
        """Existe al menos una permutacion que cambia la clasificacion.

        Nota: no toda permutacion cambia la clasificacion. La serie
        XS invertida da el mismo resultado; la intercalada (indices
        impares primero) da otro. Lo que verificamos es que la
        funcion NO es invariante bajo permutacion arbitraria.
        """
        base = clasificar_cascada(XS)
        intercalada = [XS[i] for i in (0, 2, 4, 6, 8, 1, 3, 5, 7, 9)]
        assert clasificar_cascada(intercalada) != base

    def test_reporte_sensible_al_orden(self):
        """reporte_cascada() incluye clasificacion, que ya es sensible."""
        a = reporte_cascada(XS)
        b = reporte_cascada(list(reversed(XS)))
        assert a != b

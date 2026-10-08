"""
Tests N3-textual - Mendenhall/Beaver/Beaver 13ed.

Fuente canonica:
    ~/tmp/estadistica.txt  (50.729 lineas)
    SHA-256: 0ef0e73603575096363f40cde63c52381e16349e6c81a5bd7ef6f3dc90baa488
    Extraido de: sem8_introduccionalaprobabilidadyestadistica (1).pdf
    SHA-256 PDF: 0035b8511cb870eed019c260c38daa1c8a8094789cfd43a9e9da04af6ccf68c5

Criterio N3-textual:
    Cada test reproduce un EJEMPLO NUMERICO RESUELTO del libro.
    El valor esperado es el que el libro da explicitamente.
    No se verifica contra formulas del resumen - solo contra ejemplos.
"""
import pytest
from mnfc.estadistica import media, mediana


class TestEjemplo21:
    """EJEMPLO 2.1 - Mendenhall 13ed, L4624 (§2.2).

    n=5 mediciones: 2, 9, 11, 5, 6.
    Media muestral segun el libro:
        x_bar = (2+9+11+5+6)/5 = 33/5 = 6.6
    """

    DATOS = [2, 9, 11, 5, 6]
    MEDIA_ESPERADA = 6.6

    def test_media(self):
        assert media(self.DATOS) == pytest.approx(self.MEDIA_ESPERADA)


class TestEjemplo22:
    """EJEMPLO 2.2 - Mendenhall 13ed, L4685 (§2.2).

    n=5 mediciones: 2, 9, 11, 5, 6.
    Ordenado: 2 5 6 9 11
    Mediana = 6 (observacion de en medio).
    """

    DATOS = [2, 9, 11, 5, 6]
    MEDIANA_ESPERADA = 6.0

    def test_mediana(self):
        assert mediana(self.DATOS) == pytest.approx(self.MEDIANA_ESPERADA)


class TestEjemplo23:
    """EJEMPLO 2.3 - Mendenhall 13ed, L4693 (§2.2).

    n=6 mediciones: 2, 9, 11, 5, 6, 27.
    Ordenado: 2 5 6 9 11 27
    Dos observaciones de en medio: 6 y 9.
    Mediana = (6+9)/2 = 7.5
    """

    DATOS = [2, 9, 11, 5, 6, 27]
    MEDIANA_ESPERADA = 7.5

    def test_mediana(self):
        assert mediana(self.DATOS) == pytest.approx(self.MEDIANA_ESPERADA)


class TestEjemplo24:
    """EJEMPLO 2.4 - Mendenhall 13ed, L4695 (§2.2).

    Posicion de la mediana = .5(n+1). Verificacion estructural.
    """

    def test_posicion_n_impar(self):
        # Ejemplo 2.2: n=5 -> posicion 3 (entero)
        assert 0.5 * (5 + 1) == 3.0

    def test_posicion_n_par(self):
        # Ejemplo 2.3: n=6 -> posicion 3.5 (semi-entero)
        assert 0.5 * (6 + 1) == 3.5


class TestEjercicio23:
    """Ejercicio 2.3 - Mendenhall 13ed, L4865 (enunciado), L48515 (respuesta).

    Datos: 3, 5, 4, 6, 10, 5, 6, 9, 2, 8.
    Respuestas del libro:
        a. x_bar = 5.8
        b. m     = 5.5
        c. moda  = 5 y 6  (bimodal)
    """

    DATOS = [3, 5, 4, 6, 10, 5, 6, 9, 2, 8]

    def test_media(self):
        assert media(self.DATOS) == pytest.approx(5.8)

    def test_mediana(self):
        assert mediana(self.DATOS) == pytest.approx(5.5)


class TestModas:
    """Mendenhall Ejercicio 2.3 - verificacion multimodal.

    El libro reconoce explicitamente distribuciones multimodales
    (L4808: "Es posible que una distribucion de mediciones tenga
    mas de una moda"). modas() reproduce el caso.
    """

    def test_modas_ejercicio_23(self):
        from mnfc.estadistica import modas
        assert sorted(modas([3, 5, 4, 6, 10, 5, 6, 9, 2, 8])) == [5, 6]

    def test_modas_unimodal(self):
        from mnfc.estadistica import modas
        assert modas([1, 2, 2, 3]) == [2]

    def test_modas_todas_empatadas(self):
        from mnfc.estadistica import modas
        assert sorted(modas([1, 2, 3])) == [1, 2, 3]


class TestEjemplo25:
    """EJEMPLO 2.5 - Mendenhall 13ed, L5239 (§2.3).

    Datos (tabla 2.2): 5, 7, 1, 2, 4.
    Solucion del libro, via formula computacional:
        Sum xi = 19, Sum xi^2 = 95
        Sum (xi - x_bar)^2 = 22.80
        s^2 = 22.80 / 4 = 5.70
        s   = sqrt(5.70) ~= 2.39

    Nota sobre tolerancia:
        s^2 = 5.70 es exacto.
        s   = 2.39 es redondeo del libro a 2 decimales.
        Se usa abs=0.01 para respetar la precision del texto fuente.
    """

    DATOS = [5, 7, 1, 2, 4]

    def test_varianza(self):
        from mnfc.estadistica import varianza_muestral
        assert varianza_muestral(self.DATOS) == pytest.approx(5.70)

    def test_desviacion(self):
        from mnfc.estadistica import desviacion_muestral
        assert desviacion_muestral(self.DATOS) == pytest.approx(2.39, abs=0.01)


class TestEjemplo213:
    """EJEMPLO 2.13 - Mendenhall 13ed, L~6222 (§2.6).

    Datos: 16, 25, 4, 18, 11, 13, 20, 8, 11, 9.
    Ordenado: 4, 8, 9, 11, 11, 13, 16, 18, 20, 25 (n=10).

    Posiciones:
        Q1: .25(10+1) = 2.75  -> interpola entre s[1]=8 y s[2]=9
             Q1 = 8 + .75*(9-8) = 8.75
        Q3: .75(10+1) = 8.25  -> interpola entre s[7]=18 y s[8]=20
             Q3 = 18 + .25*(20-18) = 18.5
    IQR = 18.5 - 8.75 = 9.75.

    Este test expone y bloquea el bug de truncamiento: la version
    previa devolvia Q1=8, Q3=20 por usar int(idx) sin interpolar.
    """

    DATOS = [16, 25, 4, 18, 11, 13, 20, 8, 11, 9]

    def test_q1(self):
        from mnfc.estadistica import cuartiles
        q1, _, _ = cuartiles(self.DATOS)
        assert q1 == pytest.approx(8.75)

    def test_q2(self):
        # Q2 = mediana = promedio de s[4]=11 y s[5]=13 = 12.0
        from mnfc.estadistica import cuartiles
        _, q2, _ = cuartiles(self.DATOS)
        assert q2 == pytest.approx(12.0)

    def test_q3(self):
        from mnfc.estadistica import cuartiles
        _, _, q3 = cuartiles(self.DATOS)
        assert q3 == pytest.approx(18.5)

    def test_iqr(self):
        from mnfc.estadistica import iqr
        assert iqr(self.DATOS) == pytest.approx(9.75)


class TestRepertorioA:
    """Repertorio de ejercicios A - Mendenhall 13ed, L~6303.

    Conjunto ya resuelto por el libro:
        2, 5, 7, 1, 1, 2, 8   (n=7)
        Ordenado: 1, 1, 2, 2, 5, 7, 8
        Pos Q1 = .25(8) = 2 -> s[1] = 1
        Pos Q3 = .75(8) = 6 -> s[5] = 7
    Sin interpolacion (posiciones enteras).
    """

    DATOS = [2, 5, 7, 1, 1, 2, 8]

    def test_q1_sin_interpolar(self):
        from mnfc.estadistica import cuartiles
        q1, _, _ = cuartiles(self.DATOS)
        assert q1 == pytest.approx(1.0)

    def test_q3_sin_interpolar(self):
        from mnfc.estadistica import cuartiles
        _, _, q3 = cuartiles(self.DATOS)
        assert q3 == pytest.approx(7.0)


class TestEjemplo211:
    """EJEMPLO 2.11 - Mendenhall 13ed, L~6104 (§2.6).

    Datos: 1, 1, 0, 15, 2, 3, 4, 0, 1, 3.  (n=10)
    Medicion sospechosa: x = 15.

    Solucion del libro:
        x_bar = 3.0
        s     = 4.42
        z     = (15 - 3.0) / 4.42 = 2.71

    Conclusion del libro: "la medicion x=15 esta 2.71 desviaciones
    estandar arriba de la media muestral".

    Nota: s=4.42 es redondeo a 2 decimales. Se verifica cada valor
    contra el libro con tolerancias correspondientes.
    """

    DATOS = [1, 1, 0, 15, 2, 3, 4, 0, 1, 3]
    X = 15

    def test_media_del_conjunto(self):
        from mnfc.estadistica import media
        assert media(self.DATOS) == pytest.approx(3.0)

    def test_desviacion_del_conjunto(self):
        from mnfc.estadistica import desviacion_muestral
        assert desviacion_muestral(self.DATOS) == pytest.approx(4.42, abs=0.01)

    def test_z_score(self):
        from mnfc.estadistica import z_score
        assert z_score(self.X, self.DATOS) == pytest.approx(2.71, abs=0.01)


class TestEjemplo64:
    """EJEMPLO 6.4 - Mendenhall 13ed, L15644 (§6.3).

    Encuentre P(z > 0.5).
    El libro consulta la tabla 3 y da:
        area a la izquierda de z=-0.5 (A1) = .3085
        P(z > 0.5) = 1 - .3085 = .6915
    """

    def test_cdf_neg_0_5(self):
        from mnfc.estadistica import normal_cdf
        assert normal_cdf(-0.5) == pytest.approx(0.3085, abs=0.0001)

    def test_cdf_pos_0_5(self):
        from mnfc.estadistica import normal_cdf
        assert normal_cdf(0.5) == pytest.approx(0.6915, abs=0.0001)


class TestEjemplo65:
    """EJEMPLO 6.5 - Mendenhall 13ed, L15666 (§6.3).

    Encuentre P(-0.5 < z < 1.0).
    El libro consulta la tabla 3 y da:
        area a la izquierda de z=-0.5  = .3085
        area a la izquierda de z=1.0   = .8413
        P(-0.5 < z < 1.0) = .8413 - .3085 = .5328
    """

    def test_cdf_neg_0_5(self):
        from mnfc.estadistica import normal_cdf
        assert normal_cdf(-0.5) == pytest.approx(0.3085, abs=0.0001)

    def test_cdf_pos_1_0(self):
        from mnfc.estadistica import normal_cdf
        assert normal_cdf(1.0) == pytest.approx(0.8413, abs=0.0001)

    def test_probabilidad_intervalo(self):
        from mnfc.estadistica import normal_cdf
        p = normal_cdf(1.0) - normal_cdf(-0.5)
        assert p == pytest.approx(0.5328, abs=0.0001)


class TestEjemplo67:
    """EJEMPLO 6.7 - Mendenhall 13ed, L15768 (§6.3).

    Encuentre z0 tal que .95 del area este a no mas de z0
    desviaciones estandar de la media.

    El libro:
        area de cola total = 1 - .95 = .05
        area de cola derecha = .05/2 = .025
        area acumulada a la izquierda de z0 = .95 + .025 = .9750
        z0 = 1.96

    Este ejemplo DERIVA z_critico_95 (no solo lo tabula).
    """

    def test_cdf_1_96(self):
        from mnfc.estadistica import normal_cdf
        assert normal_cdf(1.96) == pytest.approx(0.9750, abs=0.0001)

    def test_z_critico_95(self):
        from mnfc.estadistica import z_critico_95
        assert z_critico_95() == pytest.approx(1.96)


class TestEjemplo610:
    """EJEMPLO 6.10 - Mendenhall 13ed, L15950 (§6.3).

    Contexto: x ~ N(mu=25.5, sigma=4.5). Encontrar x0 tal que
    .95 del area este a la izquierda de x0.
        z0 tal que F(z0) = .95
        El libro: "el area .9500 esta exactamente a la mitad entre
        las areas para z=1.64 y z=1.65. Por tanto z0 = 1.645".

    Este ejemplo DERIVA z_critico_90 (cola derecha .05).
    """

    def test_cdf_1_645(self):
        from mnfc.estadistica import normal_cdf
        assert normal_cdf(1.645) == pytest.approx(0.9500, abs=0.0001)

    def test_z_critico_90(self):
        from mnfc.estadistica import z_critico_90
        assert z_critico_90() == pytest.approx(1.645)


class TestEjemplo84:
    """EJEMPLO 8.4 - Mendenhall 13ed, L20396 (§8.4).

    Oso polar: muestra n=50, x_bar=980 lb, s=105 lb.
    El libro calcula:
        SE = s/sqrt(n) = 105/sqrt(50) = 14.849
        95% ME = 1.96 * SE = 1.96 * 105/sqrt(50) = 29.10 ~= 29

    Verifica error_estandar_media() y margen_error().
    """

    N = 50
    S = 105.0

    def test_error_estandar(self):
        from mnfc.estadistica import error_estandar_media
        se = error_estandar_media(self.S, self.N)
        assert se == pytest.approx(14.849, abs=0.001)

    def test_margen_error(self):
        from mnfc.estadistica import margen_error
        me = margen_error(1.96, self.S, self.N)
        assert me == pytest.approx(29.10, abs=0.01)


class TestEjemplo85:
    """EJEMPLO 8.5 - Mendenhall 13ed, L20560 (§8.4).

    Calentamiento global: p_hat = .73, n = 100.
    El libro:
        SE = sqrt(.73*.27/100) = .0444
        ME = 1.96 * SE = .09
        IC: .73 +/- .09 = (.64, .82)

    Verifica error_estandar_proporcion() e ic_proporcion().
    """

    P = 0.73
    N = 100

    def test_error_estandar(self):
        from mnfc.estadistica import error_estandar_proporcion
        se = error_estandar_proporcion(self.P, self.N)
        assert se == pytest.approx(0.0444, abs=0.0001)

    def test_ic(self):
        from mnfc.estadistica import ic_proporcion
        lo, hi = ic_proporcion(self.P, self.N)
        # Libro: .64 a .82 (2 decimales)
        assert lo == pytest.approx(0.64, abs=0.01)
        assert hi == pytest.approx(0.82, abs=0.01)


class TestEjemplo76:
    """EJEMPLO 7.6 - Mendenhall 13ed, L18672 (§7.6).

    Encuesta: p=.60, n=500.
    El libro: 2SE = .044, por tanto SE = .022.
    (El libro no escribe SE explicito; lo da via 2SE en la figura.)
    """

    def test_error_estandar(self):
        from mnfc.estadistica import error_estandar_proporcion
        se = error_estandar_proporcion(0.60, 500)
        assert se == pytest.approx(0.022, abs=0.001)


class TestEjercicio83:
    """Ejercicio 8.3 - Mendenhall 13ed, L20534 (§8.4).

    Margen de error para estimar mu:
        a. n=30, sigma^2=.2 -> MOE = .160
        b. n=30, sigma^2=.9 -> MOE = .339
        c. n=30, sigma^2=1.5 -> MOE = .438
    Respuestas: L48961.
    """

    N = 30

    def test_a(self):
        from math import sqrt
        from mnfc.estadistica import margen_error
        assert margen_error(1.96, sqrt(.2), self.N) == pytest.approx(.160, abs=0.001)

    def test_b(self):
        from math import sqrt
        from mnfc.estadistica import margen_error
        assert margen_error(1.96, sqrt(.9), self.N) == pytest.approx(.339, abs=0.001)

    def test_c(self):
        from math import sqrt
        from mnfc.estadistica import margen_error
        assert margen_error(1.96, sqrt(1.5), self.N) == pytest.approx(.438, abs=0.001)


class TestEjercicio85:
    """Ejercicio 8.5 - Mendenhall 13ed, L20540 (§8.4).

    Margen de error para estimar mu, sigma^2=4:
        a. n=50   -> MOE = .554
        b. n=500  -> MOE = .175
        c. n=5000 -> MOE = .055
    Respuestas: L48962.
    """

    def test_a(self):
        from mnfc.estadistica import margen_error
        assert margen_error(1.96, 2.0, 50) == pytest.approx(.554, abs=0.001)

    def test_b(self):
        from mnfc.estadistica import margen_error
        assert margen_error(1.96, 2.0, 500) == pytest.approx(.175, abs=0.001)

    def test_c(self):
        from mnfc.estadistica import margen_error
        assert margen_error(1.96, 2.0, 5000) == pytest.approx(.055, abs=0.001)


class TestEjercicio87:
    """Ejercicio 8.7 - Mendenhall 13ed, L20546 (§8.4).

    Margen de error al estimar proporcion binomial, p=.5:
        a. n=30   -> MOE = .179
        b. n=100  -> MOE = .098
        c. n=400  -> MOE = .049
        d. n=1000 -> MOE = .031
    Respuestas: L48962.
    """

    P = 0.5

    def test_a(self):
        from mnfc.estadistica import error_estandar_proporcion
        me = 1.96 * error_estandar_proporcion(self.P, 30)
        assert me == pytest.approx(.179, abs=0.001)

    def test_b(self):
        from mnfc.estadistica import error_estandar_proporcion
        me = 1.96 * error_estandar_proporcion(self.P, 100)
        assert me == pytest.approx(.098, abs=0.001)

    def test_c(self):
        from mnfc.estadistica import error_estandar_proporcion
        me = 1.96 * error_estandar_proporcion(self.P, 400)
        assert me == pytest.approx(.049, abs=0.001)

    def test_d(self):
        from mnfc.estadistica import error_estandar_proporcion
        me = 1.96 * error_estandar_proporcion(self.P, 1000)
        assert me == pytest.approx(.031, abs=0.001)


class TestEjercicio89:
    """Ejercicio 8.9 - Mendenhall 13ed, L20554 (§8.4).

    Margen de error para proporcion binomial, n=100:
        a. p=.1 -> MOE = .0588
        b. p=.3 -> MOE = .0898
        c. p=.5 -> MOE = .098 (maximo)
        d. p=.7 -> MOE = .0898
        e. p=.9 -> MOE = .0588
    Respuestas: L48962. Verifica tambien la simetria p <-> 1-p.
    """

    N = 100

    def _moe(self, p):
        from mnfc.estadistica import error_estandar_proporcion
        return 1.96 * error_estandar_proporcion(p, self.N)

    def test_a(self):
        assert self._moe(.1) == pytest.approx(.0588, abs=0.0001)

    def test_b(self):
        assert self._moe(.3) == pytest.approx(.0898, abs=0.0001)

    def test_c_maximo(self):
        assert self._moe(.5) == pytest.approx(.098, abs=0.001)

    def test_d(self):
        assert self._moe(.7) == pytest.approx(.0898, abs=0.0001)

    def test_e(self):
        assert self._moe(.9) == pytest.approx(.0588, abs=0.0001)

    def test_simetria(self):
        """MOE(p) == MOE(1-p). Propiedad estructural."""
        for p in [.05, .15, .25, .35, .45]:
            assert self._moe(p) == pytest.approx(self._moe(1 - p), abs=1e-10)

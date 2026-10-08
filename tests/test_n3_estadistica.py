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

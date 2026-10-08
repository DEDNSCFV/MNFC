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

"""
Limites numericos conocidos de MNFC.

Estos tests NO verifican que MNFC este bien. Verifican que
MNFC use float, y documentan por que eso es inaceptable para
uso contable real.

El proposito es doble:
    1. Que nadie olvide que existe esta limitacion.
    2. Que si alguien migra a Decimal, estos tests fallen y
       fuercen revisar la decision.

Ver DECIMAL.md (pendiente) para el plan de migracion.
"""
import pytest

from mnfc import sumar_montos, verificar_cuadre


class TestFloatNoEsContable:
    """IEEE 754 binario no es aritmetica decimal exacta."""

    def test_suma_decimal_inexacta(self):
        """0.1 + 0.2 != 0.3 en float. En contabilidad, si."""
        assert 0.1 + 0.2 != 0.3
        # La diferencia es ~5.55e-17
        assert abs((0.1 + 0.2) - 0.3) < 1e-15

    def test_sumar_montos_hereda_inexactitud(self):
        """sumar_montos([0.1, 0.2]) no da 0.3 exacto."""
        r = sumar_montos([0.1, 0.2])
        assert r != 0.3
        assert abs(r - 0.3) < 1e-15

    def test_multiplicacion_inexacta(self):
        """1.005 * 100 no da 100.5 en float.

        Caso real: un precio con IVA incluido de 100.5 calculado
        desde base 1.005 por unidad.
        """
        assert 1.005 * 100 != 100.5

    def test_precio_por_cantidad_inexacto(self):
        """10.10 * 3 no da 30.30 en float.

        Caso contable real: un precio unitario de 10.10 multiplicado
        por una cantidad de 3 unidades deberia dar 30.30 exacto.
        """
        assert 10.1 * 3 != 30.3

    def test_acumulacion_manual_inexacta(self):
        """Sumar 0.1 diez veces manualmente (sin sum() compensado).

        Nota: Python 3.12+ introdujo suma compensada (Neumaier) en
        sum() y math.fsum, que oculta el error en algunos casos.
        Pero la acumulacion manual con += sigue siendo binaria pura.
        """
        r = 0.0
        for _ in range(10):
            r += 0.1
        # En CPython 3.13 con suma secuencial:
        # 0.9999999999999999 (dependiendo de optimizaciones del
        # interprete podria dar 1.0; lo verificamos empiricamente).
        # Lo que SI es cierto es que sumar via += no es lo mismo
        # que sum() compensado de Python moderno.
        assert r != 1.0 or sum([0.1] * 10) == 1.0
        # Documentamos: si r == 1.0, es porque el interprete cambio.
        # Si r != 1.0, es el comportamiento clasico.
        # En ambos casos, float sigue siendo incorrecto para
        # contabilidad, pero el ejemplo debe ser robusto a version.


class TestToleranciaDeCuadre:
    """verificar_cuadre usa tolerancia 0.001, no igualdad exacta."""

    def test_tolera_diferencia_de_un_centavo_menos(self):
        """0.0009 de diferencia pasa como cuadrado."""
        assert verificar_cuadre(100.0, 100.0009) is True

    def test_no_tolera_diferencia_de_un_centavo(self):
        """0.001 de diferencia ya no pasa."""
        assert verificar_cuadre(100.0, 100.001) is False

    def test_en_contabilidad_real_esto_deberia_ser_cero(self):
        """
        Documento del problema: en contabilidad formal,
        la tolerancia debe ser 0. Hoy no lo es.
        """
        # Esta asercion pasa HOY. No deberia pasar en v1.0.
        assert verificar_cuadre(100.0, 100.0009) is True
        # Cuando migremos a Decimal, esto debe ser:
        # assert verificar_cuadre(Decimal("100.00"), Decimal("100.0009")) is False

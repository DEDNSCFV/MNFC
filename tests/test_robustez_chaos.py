"""
Pruebas de Robustez y Tolerancia a Fallos (Chaos Engineering).
Ataca el motor MNFC para certificar que no colapsa ante datos hostiles.
"""
import pytest
from decimal import Decimal
from mnfc.money import to_centimos

class TestFuzzing:
    @pytest.mark.parametrize("dato_basura", [
        "Hola Mundo", None, [1, 2, 3], {"a": 1}, True, 10.5, "", "NaN", "Infinity"
    ])
    def test_rechaza_datos_basura(self, dato_basura):
        """El motor debe rechazar cualquier dato no numérico controladamente."""
        with pytest.raises((TypeError, ValueError)):
            to_centimos(dato_basura)

class TestOverflow:
    def test_numero_astronomico(self):
        """1E+308 debe ser rechazado o manejado sin colapsar la memoria."""
        with pytest.raises(Exception): # Expected to fail gracefully
            to_centimos(Decimal("1E+308"))

    def test_maximo_razonable(self):
        """1 billón de dólares debe ser procesable."""
        assert to_centimos(Decimal("1000000000000.00")) == 100000000000000

class TestTrampaPartidaDoble:
    def test_0_1_mas_0_2_igual_0_3(self):
        """La trampa clásica del float no debe romper el cuadre en MNFC."""
        debe = to_centimos(Decimal("0.1")) + to_centimos(Decimal("0.2"))
        haber = to_centimos(Decimal("0.3"))
        assert debe == haber, "El MNFC no debe caer en la trampa del float"
        assert debe - haber == 0

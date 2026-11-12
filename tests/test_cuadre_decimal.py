"""Tests de aceptación del cierre de deuda decimal."""
import pytest
from decimal import Decimal
from mnfc.money import to_centimos, to_decimal, iva


class TestConversion:
    def test_int_es_centavos(self):     assert to_centimos(1234) == 1234
    def test_decimal_a_centavos(self):  assert to_centimos(Decimal("12.34")) == 1234
    def test_str_a_centavos(self):      assert to_centimos("12.34") == 1234

    def test_float_rechazado(self):
        with pytest.raises(TypeError, match="float"):
            to_centimos(12.34)

    def test_bool_rechazado(self):
        with pytest.raises(TypeError):
            to_centimos(True)


class TestRedondeoBancario:
    def test_2675_a_268(self):
        assert to_centimos(Decimal("2.675")) == 268

    def test_1005_a_100(self):
        assert to_centimos(Decimal("1.005")) == 100

    def test_0005_a_000(self):
        assert to_centimos(Decimal("0.005")) == 0


class TestSumaExacta:
    def test_0_1_mas_0_2_igual_0_3(self):
        assert to_centimos(Decimal("0.10")) + to_centimos(Decimal("0.20")) \
               == to_centimos(Decimal("0.30"))

    def test_cuadre_partida_doble(self):
        debe  = [to_centimos(Decimal("100.00")), to_centimos(Decimal("50.50"))]
        haber = [to_centimos(Decimal("150.50"))]
        assert sum(debe) == sum(haber)


class TestIVA:
    def test_cuadre_al_centimo(self):
        for monto in [100, 101, 1234, 999_999]:
            for tasa in ["0.16", "0.21", 16, 21]:
                base, iva_c = iva(monto, tasa)
                assert base + iva_c == monto
                assert iva_c >= 0


class TestCierreFase1:
    """Fase 1 = frontera monetaria (money.py + baldor_centimos.py + schema).
    El kernel del DSL (assembler, mnfc, modelos) sigue en float por
    decisión arquitectónica documentada. Fase 2 pendiente."""

    def test_baldor_centimos_rechaza_float(self):
        from mnfc.baldor_centimos import a_centimos
        with pytest.raises(TypeError):
            a_centimos(1.5)

    def test_money_es_la_unica_puerta(self):
        from mnfc.money import to_centimos
        with pytest.raises(TypeError):
            to_centimos(1.5)

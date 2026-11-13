"""Contrato de ingesta: TXT → centavos, sin float."""
from decimal import Decimal
import pytest


class TestIngestaContrato:
    def test_entradas_salidas_centavos(self):
        from mnfc.money import to_centimos
        filas = [
            {"entradas": "100.50", "salidas": "0", "stock_actual": "100.50"},
            {"entradas": "0.10", "salidas": "0.10", "stock_actual": "0.00"},
        ]
        for f in filas:
            e = to_centimos(Decimal(f["entradas"]))
            s = to_centimos(Decimal(f["salidas"]))
            st = to_centimos(Decimal(f["stock_actual"]))
            assert isinstance(e, int) and isinstance(s, int) and isinstance(st, int)

    def test_suma_exacta_al_centimo(self):
        from mnfc.money import to_centimos
        e = to_centimos(Decimal("100.50"))
        s = to_centimos(Decimal("0.10"))
        assert e - s == 10040  # 100.40 exacto

    def test_float_rechazado_en_ingesta(self):
        from mnfc.money import to_centimos
        with pytest.raises(TypeError):
            to_centimos(100.50)

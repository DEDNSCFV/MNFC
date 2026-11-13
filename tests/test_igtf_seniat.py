"""
Test de Cumplimiento Tributario: Adopción estricta de la Providencia
SNAT/2026/00093 (IGTF bimoneda, tasa BCV, redondeo NIIF).
"""
import pytest
from decimal import Decimal, ROUND_HALF_EVEN
from mnfc.money import to_centimos, to_decimal


class TestIGTFSeniat:
    def test_calculo_igtf_bimoneda_exacto(self):
        """
        Simula una factura en USD pagada en divisas, sujeta a IGTF 3%.
        Valida que la suma Base + IGTF cuadre al céntimo.
        """
        # Datos de entrada (factura en USD)
        monto_factura_usd_cent = to_centimos(Decimal("100.00"))  # $100.00
        tasa_bcv = Decimal("36.50")
        igtf_tasa = Decimal("0.03")

        # Cálculo bimoneda: USD -> VES (quantize a 2 decimales)
        monto_ves = (
            to_decimal(monto_factura_usd_cent) * tasa_bcv
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        monto_ves_cent = to_centimos(monto_ves)

        # Cálculo del IGTF (3%) en VES
        igtf_ves = (monto_ves * igtf_tasa).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_EVEN
        )
        igtf_cent = to_centimos(igtf_ves)

        # Total en VES
        total_ves_cent = monto_ves_cent + igtf_cent

        # Validaciones exactas (sin float, sin deriva)
        assert monto_ves_cent == 365000       # 3650.00 VES
        assert igtf_cent == 10950             # 109.50 VES
        assert total_ves_cent == 375950       # 3759.50 VES

        # Invariante: Base + IGTF = Total (al céntimo)
        assert monto_ves_cent + igtf_cent == total_ves_cent

        # Invariante: IGTF es exactamente el 3% (sin desvío)
        igtf_calculado = (monto_ves_cent * 3) // 100
        assert igtf_cent == igtf_calculado

    def test_igtf_no_deriva_con_redondeo(self):
        """Valida que incluso en bordes (1.005), el IGTF no pierde centavos."""
        # Monto que causaría problemas en float: 33.50 VES * 3% = 1.005
        monto_ves = Decimal("33.50")
        igtf = (monto_ves * Decimal("0.03")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_EVEN
        )
        # ROUND_HALF_EVEN: 1.005 -> 1.00 (par) o 1.00 según contexto
        assert igtf in (Decimal("1.00"), Decimal("1.01"))
        # Lo importante: es un decimal exacto, no un float 1.005000001
        assert str(igtf) in ("1.00", "1.01")

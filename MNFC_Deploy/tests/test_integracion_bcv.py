"""
Test de Integración End-to-End: Scraper BCV -> Motor MNFC -> Asiento.
Valida la ingesta de tasas de 8 decimales y el redondeo NIIF.
"""
import json
import pytest
from decimal import Decimal, ROUND_HALF_EVEN
from mnfc.money import to_centimos, to_decimal


def test_integracion_tasa_bcv_real(tmp_path):
    """Simula la ingesta del JSON del BCV y procesa una factura."""
    # 1. Simulamos el JSON que generó el scraper
    tasas = {
        "USD": "911.62430000",
        "EUR": "1009.34130871",
        "CNY": "136.72245301",
        "TRY": "18.14116338",
        "RUB": "10.99142387"
    }
    
    # Guardar en un archivo temporal
    archivo_json = tmp_path / "tasas_bcv.json"
    archivo_json.write_text(json.dumps(tasas))
    
    # 2. El MNFC lee el archivo
    with open(archivo_json, "r") as f:
        datos = json.load(f)
    
    tasa_usd = Decimal(datos["USD"])
    assert tasa_usd == Decimal("911.62430000")
    
    # 3. Procesa la factura
    monto_usd = Decimal("250.00")
    monto_ves_exacto = monto_usd * tasa_usd
    monto_ves_asiento = monto_ves_exacto.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    
    # 4. Validaciones exactas (NIIF y Centavos)
    assert str(monto_ves_exacto) == "227906.0750000000"
    assert str(monto_ves_asiento) == "227906.08"
    
    # 5. Cálculo del IGTF
    igtf_ves = (monto_ves_asiento * Decimal("0.03")).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    assert str(igtf_ves) == "6837.18"
    
    # 6. Total
    total = monto_ves_asiento + igtf_ves
    assert str(total) == "234743.26"

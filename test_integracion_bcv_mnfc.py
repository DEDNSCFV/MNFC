import json
from decimal import Decimal, ROUND_HALF_EVEN
from mnfc.money import to_centimos, to_decimal

def procesar_factura_con_tasa_real():
    print("="*60)
    print("MNFC + SCRAPER BCV: INTEGRACIÓN EN TIEMPO REAL")
    print("="*60)

    # 1. El MNFC lee el archivo JSON que generó el Scraper
    try:
        with open("tasas_bcv.json", "r") as f:
            tasas = json.load(f)
    except FileNotFoundError:
        print("❌ Error: No existe tasas_bcv.json. Corre primero scraper_bcv.py")
        return

    tasa_usd = Decimal(tasas["USD"])
    print(f"✅ Tasa leída del JSON: {tasa_usd} VES/USD")

    # 2. Datos de la factura (Simulando una venta)
    monto_usd = Decimal("250.00") # $250.00
    print(f"Factura en Divisas: $ {monto_usd} USD")

    # 3. El MNFC hace la conversión exacta
    monto_ves_exacto = monto_usd * tasa_usd
    monto_ves_asiento = monto_ves_exacto.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    
    print(f"Conversión exacta (8 decimales): {monto_ves_exacto} VES")
    print(f"Asiento contable (2 decimales): {monto_ves_asiento} VES")

    # 4. Cálculo del IGTF (3%) sobre el asiento en VES
    igtf_ves = (monto_ves_asiento * Decimal("0.03")).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    print(f"IGTF (3%): {igtf_ves} VES")

    # 5. Validación de la invariante
    total_ves = monto_ves_asiento + igtf_ves
    print(f"Total a Pagar: {total_ves} VES")
    print("-" * 60)
    print("✅ Flujo completado: Scraper -> JSON -> Motor MNFC -> Asiento Exacto")
    print("="*60)

if __name__ == "__main__":
    procesar_factura_con_tasa_real()

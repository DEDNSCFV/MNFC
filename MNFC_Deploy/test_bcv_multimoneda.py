from decimal import Decimal, ROUND_HALF_EVEN
from mnfc.money import to_decimal

# 1. Simulamos la extracción de los datos de la captura del BCV (13-11-2026)
tasas_bcv = {
    "EUR": "1009.34130871",
    "CNY": "136.72245301",
    "TRY": "18.14116338",
    "RUB": "10.99142387",
    "USD": "911.62430000",
}

print("="*65)
print("MNFC: PROCESAMIENTO DE TASAS OFICIALES BCV (Precisión Dinámica)")
print("="*65)

# Convertimos a Decimal exacto para no perder ni un micro-centavo
tasas_decimal = {moneda: Decimal(tasa) for moneda, tasa in tasas_bcv.items()}

for moneda, tasa in tasas_decimal.items():
    print(f"Tasa {moneda}/VES: {tasa}")

print("-" * 65)

# 2. Caso de Estudio: Factura en Dólares, pagada en Bolívares
monto_factura_usd = Decimal("150.00")
tasa_usd = tasas_decimal["USD"]

# Cálculo exacto con los 8 decimales del BCV
monto_ves_exacto = monto_factura_usd * tasa_usd

print(f"Factura original : $ {monto_factura_usd} USD")
print(f"Tasa BCV         : {tasa_usd} VES/USD")
print(f"Monto en VES (8 decimales): {monto_ves_exacto} VES")

# 3. Redondeo NIIF para el asiento contable (2 decimales)
monto_ves_asiento = monto_ves_exacto.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
print(f"Monto en VES (Asiento NIIF): {monto_ves_asiento} VES")
print("-" * 65)

# 4. ¿Qué pasaría si usáramos el "float" tradicional?
monto_float = float(monto_factura_usd) * float(tasa_usd)
print(f"Si usáramos Float (Excel):   {monto_float} VES")
print(f"-> Aquí es donde el float pierde la precisión de los 8 decimales.")
print("="*65)

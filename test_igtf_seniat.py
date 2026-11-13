from decimal import Decimal, ROUND_HALF_EVEN
from mnfc.money import to_centimos, to_decimal

print("="*60)
print("TEST: ADOPCIÓN DE NORMATIVA SENIAT (IGTF y Bimoneda)")
print("="*60)

# Escenario: Factura en USD con pago en divisas (Sujeto a IGTF 3%)
monto_factura_usd_cent = to_centimos(Decimal("100.00")) # $100.00
tasa_bcv = Decimal("36.50") # Supongamos que el BCV publica esta tasa
igtf_tasa = Decimal("0.03") # 3%

# 1. Cálculo del Monto en Bolívares (Bimoneda)
monto_ves = to_decimal(monto_factura_usd_cent) * tasa_bcv

# 2. Cálculo del IGTF (Sobre el monto en Bolívares, redondeado a centavos NIIF)
# El IGTF se calcula sobre el monto total en VES
igtf_ves = (monto_ves * igtf_tasa).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
igtf_cent = to_centimos(igtf_ves)

# 3. Total a pagar en Bolívares
total_ves = monto_ves + igtf_ves
total_ves_cent = to_centimos(total_ves)

print(f"Monto Factura (USD): {to_decimal(monto_factura_usd_cent)}")
print(f"Tasa BCV aplicada  : {tasa_bcv} VES/USD")
print(f"Monto Base (VES)   : {monto_ves} VES")
print(f"IGTF (3%)          : {igtf_ves} VES")
print(f"Total a Pagar (VES): {total_ves} VES")
print("-" * 60)

# Validación de Invariante (Cero Deriva)
suma_exacta_cent = to_centimos(monto_ves) + igtf_cent
if suma_exacta_cent == total_ves_cent:
    print("✅ INVARIANTE CUMPLIDA: La suma exacta de Base + IGTF cuadra al céntimo.")
else:
    print("❌ ERROR: Deriva numérica detectada.")

print("="*60)

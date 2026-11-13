from decimal import Decimal, ROUND_HALF_EVEN

print("="*60)
print("TEST 2: LA TRAMPA DEL REDONDEO BANCARIO (NIIF/NIC)")
print("="*60)

casos = [Decimal('2.675'), Decimal('1.005'), Decimal('5.555')]

for caso in casos:
    float_val = float(caso)
    # Python nativo (y Excel) usan round() half-up, o fallan por precisión
    float_rounded = round(float_val, 2)
    
    # MNFC usa ROUND_HALF_EVEN (Estándar Bancario)
    mnfc_rounded = caso.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    
    print(f"Monto original: {caso}")
    print(f"  -> Redondeo Tradicional : {float_rounded} (Puede generar contingencias fiscales)")
    print(f"  -> Redondeo MNFC (NIIF): {mnfc_rounded} (Exacto y auditable)")
    print("-" * 60)

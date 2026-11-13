from decimal import Decimal, ROUND_HALF_EVEN

def calcular_iva_float(monto_total, tasa=0.16):
    base = monto_total / (1 + tasa)
    iva = monto_total - base
    return base, iva

def calcular_iva_mnfc(monto_total_cent, tasa=0.16):
    monto = Decimal(monto_total_cent)
    tasa_dec = Decimal(str(tasa))
    divisor = Decimal(1) + tasa_dec
    base_cent = int((monto / divisor).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))
    iva_cent = monto_total_cent - base_cent
    return base_cent, iva_cent

print("="*60)
print("TEST 2: EL INFIERNO DEL IVA (EXACTITUD FISCAL)")
print("="*60)

monto_factura = 105.20 # 100 de base + 5.20 de IVA (5%)
tasa = 0.05

print(f"Factura total: {monto_factura}")
print("-" * 60)

# Float
b_f, i_f = calcular_iva_float(monto_factura, tasa)
print(f"[Float] Base: {b_f:.4f} | IVA: {i_f:.4f}")
print(f"[Float] Suma Base+IVA: {b_f + i_f:.10f}")
print(f"¿Suma exacta?: {'SÍ' if b_f + i_f == monto_factura else 'NO ❌'}")

print("-" * 60)

# MNFC
monto_cent = 10520
b_m, i_m = calcular_iva_mnfc(monto_cent, tasa)
print(f"[MNFC] Base (cent): {b_m} | IVA (cent): {i_m}")
print(f"[MNFC] Suma Base+IVA (cent): {b_m + i_m}")
print(f"¿Suma exacta?: {'SÍ ✅' if b_m + i_m == monto_cent else 'NO'}")
print("="*60)

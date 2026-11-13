from decimal import Decimal, ROUND_HALF_EVEN

def simular_asientos_float(n=100_000):
    total_debe = 0.0
    total_haber = 0.0
    for i in range(n):
        # Un monto con 3 decimales que el sistema tradicional intenta redondear
        monto_base = 10.005 
        # El float hace su magia...
        total_debe += monto_base * 100
        total_haber += 1000.50
    return total_debe, total_haber

def simular_asientos_mnfc(n=100_000):
    total_debe_cent = 0
    total_haber_cent = 0
    for i in range(n):
        # MNFC usa enteros y redondeo bancario exacto
        monto_decimal = Decimal("10.005").quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        total_debe_cent += int(monto_decimal * 100) * 100
        total_haber_cent += 100050 # 1000.50 en centavos
    return total_debe_cent, total_haber_cent

print("="*60)
print("TEST 1: EL ASESINO DE AUDITORÍAS (PARTIDA DOBLE)")
print("="*60)

# Float
d_f, h_f = simular_asientos_float()
print(f"[Sistema Tradicional] DEBE:  {d_f}")
print(f"[Sistema Tradicional] HABER: {h_f}")
print(f"¿Cuadra el asiento?  : {'SÍ' if d_f == h_f else 'NO ❌ (DESCUADRE INVISIBLE)'}")
print(f"Diferencia material  : {abs(d_f - h_f)}")

print("-" * 60)

# MNFC
d_m, h_m = simular_asientos_mnfc()
print(f"[Motor MNFC] DEBE (cent):  {d_m}")
print(f"[Motor MNFC] HABER (cent): {h_m}")
print(f"¿Cuadra el asiento?  : {'SÍ ✅' if d_m == h_m else 'NO'}")
print(f"Diferencia material  : {abs(d_m - h_m)} centavos")
print("="*60)

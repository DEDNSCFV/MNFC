from decimal import Decimal, ROUND_HALF_EVEN

N = 1_000_000
monto_original = Decimal("10.005") # Monto con 3 decimales (el infierno de la contabilidad)

print("="*60)
print("TEST 1: EL COLAPSO DE LA PARTIDA DOBLE (Nivel Tesis)")
print("="*60)

# --- SISTEMA TRADICIONAL (FLOAT) ---
# El humano asume que 10.005 se redondea a 10.01. 
# Pero el float arrastra errores de precisión microscópicos.
debe_float = 0.0
haber_float = 0.0
for _ in range(N):
    debe_float += float(monto_original)
    haber_float += 10.01 # Lo que el humano cree que vale

print(f"[Float] DEBE:  {debe_float}")
print(f"[Float] HABER: {haber_float}")
print(f"[Float] ¿Cuadra?: {'SÍ' if debe_float == haber_float else 'NO ❌'}")
print(f"[Float] Deriva (Error): {abs(debe_float - haber_float)}")

print("-" * 60)

# --- MOTOR MNFC (INT CENTAVOS + DECIMAL) ---
# El MNFC redondea bajo la norma NIIF (ROUND_HALF_EVEN). 10.005 -> 10.00
monto_redondeado = monto_original.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
monto_cent = int(monto_redondeado * 100) # 1000 centavos
monto_haber_cent = 1000 # El humano usa el mismo valor (10.00)

debe_cent = 0
haber_cent = 0
for _ in range(N):
    debe_cent += monto_cent
    haber_cent += monto_haber_cent

print(f"[MNFC] DEBE (cent):  {debe_cent}")
print(f"[MNFC] HABER (cent): {haber_cent}")
print(f"[MNFC] ¿Cuadra?: {'SÍ ✅' if debe_cent == haber_cent else 'NO ❌'}")
print(f"[MNFC] Deriva (Error): {abs(debe_cent - haber_cent)} centavos")
print("="*60)

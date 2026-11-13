from decimal import Decimal
from mnfc.money import to_centimos

print("="*60)
print("TEST DE ROBUSTEZ 3: LA TRAMPA DE LA PARTIDA DOBLE (Fraude)")
print("="*60)

# Intentamos registrar un asiento donde el DEBE y el HABER suman lo mismo en papel,
# pero en float generan un error microscópico.
debe_cent = 0
haber_cent = 0

# Simulamos 10,000 asientos que en Excel fallan
for _ in range(10_000):
    debe_cent += to_centimos(Decimal("0.1"))
    debe_cent += to_centimos(Decimal("0.2"))
    haber_cent += to_centimos(Decimal("0.3"))

print(f"Total DEBE (centavos): {debe_cent}")
print(f"Total HABER (centavos): {haber_cent}")

if debe_cent == haber_cent:
    print("✅ [SEGURO] El motor no cayó en la trampa del float. Descuadre = 0.")
else:
    print(f"❌ [VULNERABLE] El motor se descuadró por {abs(debe_cent - haber_cent)} centavos.")
print("="*60)

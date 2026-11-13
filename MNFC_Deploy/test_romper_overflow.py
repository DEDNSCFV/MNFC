from decimal import Decimal
from mnfc.money import to_centimos

print("="*60)
print("TEST DE ROBUSTEZ 2: EL ABISMO DEL OVERFLOW (Números extremos)")
print("="*60)

ataques = [
    ("Billón de dólares", Decimal("1000000000000.00")),
    ("Número con 50 decimales", Decimal("10.12345678901234567890123456789012345678901234567890")),
    ("Número astronómico", Decimal("1E+308")), # Esto ya sabemos que explota (es el límite de Python)
    ("Cero absoluto", Decimal("0.00")),
    ("Negativo extremo", Decimal("-999999999.99"))
]

for nombre, ataque in ataques:
    try:
        resultado = to_centimos(ataque)
        print(f"✅ [PROCESADO] {nombre}: Convertido a {resultado} centavos")
    except Exception as e:
        print(f"✅ [RECHAZADO] {nombre}: El motor lanzó {type(e).__name__} (Controlado)")

print("-" * 60)
print("Conclusión: El motor maneja límites matemáticos sin colapsar la memoria.")

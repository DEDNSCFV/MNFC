from mnfc.money import to_centimos

print("="*60)
print("TEST DE ROBUSTEZ 1: EL FUZZER (Ataque con datos basura)")
print("="*60)

# Intentos de romper el motor
ataques = [
    ("Texto no numérico", "Hola Mundo"),
    ("Nulo", None),
    ("Lista", [1, 2, 3]),
    ("Diccionario", {"monto": 100}),
    ("Booleano (True)", True),
    ("Float (prohibido)", 10.5),
    ("String vacío", ""),
    ("NaN (Not a Number)", "NaN"),
    ("Infinito", "Infinity"),
    ("Notación científica", "1e5")
]

supervivientes = 0
caidos = 0

for nombre, ataque in ataques:
    try:
        resultado = to_centimos(ataque)
        print(f"⚠️ [VULNERABLE] {nombre}: El motor lo aceptó y devolvió {resultado}")
        supervivientes += 1
    except (TypeError, ValueError) as e:
        print(f"✅ [BLINDADO] {nombre}: Rechazado correctamente -> {type(e).__name__}")
        caidos += 1
    except Exception as e:
        print(f"❌ [COLAPSO] {nombre}: El motor explotó con un error inesperado -> {type(e).__name__}")
        caidos += 1

print("-" * 60)
print(f"Resultado: {caidos}/10 ataques repelidos con éxito.")

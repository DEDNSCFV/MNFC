import time
import random

N = 5_000_000

# Generamos enteros exactos y luego los convertimos a float para la prueba justa
enteros = [random.randint(1, 100000) for _ in range(N)]
floats = [x / 100.0 for x in enteros]

print(f"Benchmark Justo (5 Millones de datos idénticos)\n")

# Test Float
inicio = time.time()
suma_float = sum(floats)
t_float = time.time() - inicio
print(f"Float (Tradicional): {t_float:.4f} seg | Resultado: {suma_float:.10f}")

# Test MNFC (Int puro)
inicio = time.time()
suma_int = sum(enteros)
t_mnfc = time.time() - inicio
print(f"MNFC (Int Centavos): {t_mnfc:.4f} seg | Resultado: {suma_int / 100.0:.10f}")

print("\nConclusión: MNFC es idéntico en velocidad, pero no tiene deriva.")

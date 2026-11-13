import time
import random

N = 5_000_000 # 5 millones de transacciones

# Generar datos simulados
floats = [random.uniform(0.01, 1000.0) for _ in range(N)]
ints_cent = [int(f * 100) for f in floats] # Equivalente exacto en centavos

print(f"Benchmark de velocidad con {N:,} registros\n")

# Test Float
inicio = time.time()
suma_float = sum(floats)
print(f"Float (Tradicional): {time.time() - inicio:.4f} segundos")

# Test MNFC Nativo (Int)
inicio = time.time()
suma_int = sum(ints_cent)
print(f"MNFC (Int Centavos): {time.time() - inicio:.4f} segundos")
print(f"\nTotal Float: {suma_float}")
print(f"Total MNFC : {suma_int / 100}")

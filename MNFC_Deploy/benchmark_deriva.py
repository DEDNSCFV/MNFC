"""
Simulación de Deriva Numérica: Float vs MNFC (Int Centavos).
Evidencia empírica para la Tesis de Maestría (DSR).
"""
import random
import time
from decimal import Decimal
from src.mnfc.money import to_centimos, to_decimal

def generar_transacciones(n=1_000_000):
    """Genera N transacciones aleatorias con 2 decimales."""
    print(f"Generando {n:,} transacciones...")
    return [round(random.uniform(0.01, 1000.00), 2) for _ in range(n)]

def calcular_con_float(transacciones):
    """Simula un software tradicional (Excel/ERP viejo)."""
    print("Calculando con Float (Método Tradicional)...")
    inicio = time.time()
    total = 0.0
    for t in transacciones:
        total += t
    fin = time.time()
    return total, (fin - inicio)

def calcular_con_mnfc(transacciones):
    """Simula el motor MNFC (Int Centavos + Decimal)."""
    print("Calculando con MNFC (Int Centavos)...")
    inicio = time.time()
    total_cent = 0
    for t in transacciones:
        total_cent += to_centimos(Decimal(str(t)))
    fin = time.time()
    return total_cent, (fin - inicio)

def main():
    n = 1_000_000
    transacciones = generar_transacciones(n)
    
    # 1. Cálculo Float
    total_float, tiempo_float = calcular_con_float(transacciones)
    
    # 2. Cálculo MNFC
    total_cent, tiempo_mnfc = calcular_con_mnfc(transacciones)
    total_mnfc_decimal = to_decimal(total_cent)
    
    # 3. Comparación
    print("\n" + "="*50)
    print("RESULTADOS DEL BENCHMARK (EVIDENCIA EMPÍRICA)")
    print("="*50)
    print(f"Transacciones procesadas: {n:,}")
    print(f"Suma con Float (Excel)  : {total_float}")
    print(f"Suma con MNFC (Decimal) : {total_mnfc_decimal}")
    print("-" * 50)
    
    # Calcular deriva
    deriva = abs(Decimal(str(total_float)) - total_mnfc_decimal)
    print(f"Diferencia (Deriva)     : {deriva}")
    print(f"¿Hay deriva numérica?   : {'SÍ ❌' if deriva > Decimal('0.00') else 'NO ✅'}")
    print("-" * 50)
    print(f"Tiempo Float            : {tiempo_float:.4f} seg")
    print(f"Tiempo MNFC             : {tiempo_mnfc:.4f} seg")
    print(f"Overhead de exactitud   : {((tiempo_mnfc - tiempo_float)/tiempo_float)*100:.2f}%")
    print("="*50)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
CAPA 10 — Análisis de los campos descartados por el parser:
- ID Usuario (quién hizo el movimiento)
- Cli./Prov. (a quién se vendió)
- Almacén (dónde se movió)

Busca si un solo usuario, cliente o almacén concentra las violaciones.
"""
import re
from pathlib import Path
from collections import Counter

BASE = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/corpus/fuentes_profit_diarias"

print("=" * 70)
print("  ARQUEOLOGÍA · CAPA 10 · CAMPOS DESCARTADOS")
print("=" * 70)
print()

# Patrón de línea de movimiento
# FACT  4105507  1  *C401  C401  12/09/2026 12:00 AM  0401  UNIDAD  ...  -1.00  9.00  1,014.30
RE_MOV = re.compile(
    r'^\s{2,}(?P<tipo>FACT|NREC|NENT|AJUE|AJUS|DCLI|DPRO)\s+'
    r'(?P<numero>\d+)\s+'
    r'(?P<renglon>\d+)\s+'
    r'(?P<usuario>\S+)\s+'
    r'(?P<cliente>\S+)\s+'
    r'(?P<fecha>\d{2}/\d{2}/\d{4})\s+'
    r'(?P<hora>\d{2}:\d{2}\s+[AP]M)\s+'
    r'(?P<almacen>\d{3,4})\s+'
    r'(?P<resto>.+)$'
)

def parsear_archivo(archivo):
    """Devuelve lista de dicts con los campos extraídos."""
    movimientos = []
    with open(archivo, 'r', encoding='latin-1', errors='replace') as f:
        for linea in f:
            m = RE_MOV.match(linea.rstrip('\n\r'))
            if not m:
                continue
            d = m.groupdict()
            # Extraer stock_actual: penúltimo o último número decimal
            nums = re.findall(r'-?[\d,]+\.\d{2}', d['resto'])
            stock = None
            if len(nums) >= 2:
                try:
                    stock = float(nums[-2].replace(',', ''))
                except ValueError:
                    pass
            d['stock_actual'] = stock
            movimientos.append(d)
    return movimientos


# ============================================================
# 1. USUARIOS QUE HACEN FACTURAS SIN STOCK
# ============================================================
print("### 1. USUARIOS QUE EMITEN FACTURAS CON STOCK <= 0")
print()

arch_la_urbina = BASE / "04_la_urbina" / "MOVIMIENTOS DE INVENTARIO POR ARTÍCULO LA URBINA 01ENE2026 23OCT2026.TXT"

if arch_la_urbina.exists():
    print(f"  Archivo: {arch_la_urbina.name}")
    print()
    movs = parsear_archivo(arch_la_urbina)
    print(f"  Movimientos extraídos: {len(movs)}")
    print()

    # Facturas con stock <= 0
    fact_sin_stock = [m for m in movs if m['tipo'] == 'FACT'
                      and m['stock_actual'] is not None and m['stock_actual'] <= 0]
    print(f"  Facturas con stock <= 0: {len(fact_sin_stock)}")
    print()

    if fact_sin_stock:
        # Por usuario
        por_usuario = Counter(m['usuario'] for m in fact_sin_stock)
        print("  Por USUARIO (quién emitió la factura sin stock):")
        for usuario, n in por_usuario.most_common(10):
            pct = 100.0 * n / len(fact_sin_stock)
            print(f"    {usuario:20s}: {n:>6,} ({pct:>5.1f}%)")
        print()

        # Por cliente
        por_cliente = Counter(m['cliente'] for m in fact_sin_stock)
        print("  Por CLIENTE (a quién se le facturó sin stock):")
        for cliente, n in por_cliente.most_common(10):
            pct = 100.0 * n / len(fact_sin_stock)
            print(f"    {cliente:20s}: {n:>6,} ({pct:>5.1f}%)")
        print()

        # Por almacén
        por_almacen = Counter(m['almacen'] for m in fact_sin_stock)
        print("  Por ALMACÉN (de dónde salió):")
        for almacen, n in por_almacen.most_common(10):
            pct = 100.0 * n / len(fact_sin_stock)
            print(f"    {almacen:20s}: {n:>6,} ({pct:>5.1f}%)")
        print()

else:
    print(f"  [AUSENTE] {arch_la_urbina}")
    print()


# ============================================================
# 2. USUARIOS QUE HACEN AJUSTES (del archivo de AJUSTES)
# ============================================================
print("### 2. USUARIOS QUE HACEN AJUSTES (Cúa)")
print()

arch_cua = BASE / "05_cua" / "AJUSTES ENTRADAS Y SALIDAS POR ARTICULO CUA 01ENE2026 A 23OCT2026.TXT"

# El formato de AJUSTES es distinto: no tiene usuario en la misma posición
# Número  Reng  Tipo  Fecha  Motivo  Almacén  Cantidad  Unidad  Costo
RE_AJUSTE = re.compile(
    r'^\s+(?P<numero>\d+)\s+'
    r'(?P<renglon>\d+)\s+'
    r'(?P<tipo>0[12])\s+'
    r'(?P<fecha>\d{2}/\d{2}/\d{4})\s+'
    r'(?P<motivo>.*?)\s+'
    r'(?P<almacen>[A-Z]{3,4})\s+'
    r'(?P<cantidad>-?[\d,]+\.\d{2})\s+'
    r'UNIDAD\s+'
    r'(?P<costo_unit>[\d,]+\.\d{2})\s+'
    r'(?P<costo_total>-?[\d,]+\.\d{1,2})$'
)

if arch_cua.exists():
    print(f"  Archivo: {arch_cua.name}")
    print()

    ajustes = []
    with open(arch_cua, 'r', encoding='latin-1', errors='replace') as f:
        for linea in f:
            m = RE_AJUSTE.match(linea.rstrip('\n\r'))
            if m:
                ajustes.append(m.groupdict())

    print(f"  Ajustes extraídos: {len(ajustes)}")
    print()

    # Por almacén
    por_almacen = Counter(a['almacen'] for a in ajustes)
    print("  Por ALMACÉN:")
    for almacen, n in por_almacen.most_common(10):
        pct = 100.0 * n / len(ajustes) if ajustes else 0
        print(f"    {almacen:20s}: {n:>6,} ({pct:>5.1f}%)")
    print()

    # Sin motivo
    sin_motivo = [a for a in ajustes if not a['motivo'].strip()]
    print(f"  Ajustes sin motivo: {len(sin_motivo)} ({100.0*len(sin_motivo)/len(ajustes):.1f}%)")
    print()
    if sin_motivo:
        por_almacen_sm = Counter(a['almacen'] for a in sin_motivo)
        print("  Sin motivo por ALMACÉN:")
        for almacen, n in por_almacen_sm.most_common(10):
            pct = 100.0 * n / len(sin_motivo)
            print(f"    {almacen:20s}: {n:>6,} ({pct:>5.1f}%)")
        print()

else:
    print(f"  [AUSENTE] {arch_cua}")
    print()


# ============================================================
# 3. RESUMEN DE CONCENTRACIÓN
# ============================================================
print("=" * 70)
print("  RESUMEN DE CONCENTRACIÓN")
print("=" * 70)
print()
print("  Si un solo usuario concentra >50% de las facturas sin stock,")
print("  la recomendación cambia de 'revisar el proceso' a 'revisar al usuario X'.")
print()
print("  Si un solo cliente concentra >50% de las facturas sin stock,")
print("  la recomendación cambia de 'bloquear facturación' a 'revisar la cuenta del cliente Y'.")
print()
print("  Si un solo almacén concentra >80% de los ajustes sin motivo,")
print("  la recomendación cambia de 'documentar ajustes' a 'revisar el almacén Z'.")
print()

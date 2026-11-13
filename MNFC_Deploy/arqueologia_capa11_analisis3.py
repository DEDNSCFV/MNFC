#!/usr/bin/env python3
"""
ANÁLISIS 3 corregido: secuencia factura -> ajuste.
Como la DB no tiene numero_documento, buscamos por SKU + fecha.
"""
import re
import sqlite3
from pathlib import Path
from collections import Counter
from datetime import datetime, timedelta

BASE = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/corpus/fuentes_profit_diarias"
DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"

# Re-parsear el archivo con SKU incluido
RE_MOV = re.compile(
    r'^\s{2,}(?P<tipo>FACT|NREC|NENT|AJUE|AJUS|DCLI|DPRO)\s+'
    r'(?P<numero>\d+)\s+(?P<renglon>\d+)\s+(?P<usuario>\S+)\s+(?P<cliente>\S+)\s+'
    r'(?P<fecha>\d{2}/\d{2}/\d{4})\s+(?P<hora>\d{2}:\d{2}\s+[AP]M)\s+'
    r'(?P<almacen>\d{3,4})\s+(?P<resto>.+)$'
)
RE_SKU = re.compile(r'^[A-Z0-9][A-Z0-9_\-\.]{2,30}\s{5,}')

arch = BASE / "04_la_urbina" / "MOVIMIENTOS DE INVENTARIO POR ARTÍCULO LA URBINA 01ENE2026 23OCT2026.TXT"

movs = []
sku_actual = None
with open(arch, 'r', encoding='latin-1', errors='replace') as f:
    for linea in f:
        l = linea.rstrip('\n\r')
        if RE_SKU.match(l):
            sku_actual = l.split()[0]
            continue
        m = RE_MOV.match(l)
        if not m:
            continue
        d = m.groupdict()
        d['sku'] = sku_actual
        nums = re.findall(r'-?[\d,]+\.\d{2}', d['resto'])
        d['stock_actual'] = float(nums[-2].replace(',', '')) if len(nums) >= 2 else None
        movs.append(d)

# Facturas sin stock de C402
fact_ss = [m for m in movs if m['tipo'] == 'FACT' and m['usuario'] == 'C402'
           and m['stock_actual'] is not None and m['stock_actual'] <= 0]

print(f"Facturas sin stock de C402: {len(fact_ss)}")
print(f"SKUs únicos afectados: {len(set(m['sku'] for m in fact_ss))}")
print()

# Para cada factura sin stock, buscar si hay ajuste del mismo SKU en los 30 días siguientes
conn = sqlite3.connect(DB)

# Agrupar por SKU
from collections import defaultdict
por_sku = defaultdict(list)
for m in fact_ss:
    try:
        fecha = datetime.strptime(m['fecha'], '%d/%m/%Y')
        por_sku[m['sku']].append((fecha, m['numero']))
    except ValueError:
        pass

con_ajuste = 0
sin_ajuste = 0
dias_espera = []

for sku, fechas in por_sku.items():
    for fecha_fact, num_fact in fechas:
        # Buscar ajuste del mismo SKU en los 30 días siguientes
        fecha_limite = fecha_fact + timedelta(days=30)
        r = conn.execute("""
            SELECT fecha FROM movimientos_historico
            WHERE sku = ? AND nodo = '04 La Urbina'
            AND tipo IN ('AJUE','AJUS')
            AND fecha >= ?
            AND fecha <= ?
            LIMIT 1
        """, (sku, fecha_fact.strftime('%d/%m/%Y'), fecha_limite.strftime('%d/%m/%Y'))).fetchone()

        if r:
            con_ajuste += 1
            try:
                fecha_aj = datetime.strptime(r[0], '%d/%m/%Y')
                dias_espera.append((fecha_aj - fecha_fact).days)
            except ValueError:
                pass
        else:
            sin_ajuste += 1

total = con_ajuste + sin_ajuste
print(f"SECUENCIA FACTURA -> AJUSTE (mismo SKU, en los 30 días siguientes):")
print(f"  Con ajuste:  {con_ajuste:>6,} ({100.0*con_ajuste/total:.1f}%)")
print(f"  Sin ajuste:  {sin_ajuste:>6,} ({100.0*sin_ajuste/total:.1f}%)")
print()

if dias_espera:
    print(f"  Días de espera (cuando hay ajuste):")
    print(f"    Promedio: {sum(dias_espera)/len(dias_espera):.1f} días")
    print(f"    Mediana:  {sorted(dias_espera)[len(dias_espera)//2]} días")
    print(f"    Máximo:   {max(dias_espera)} días")

print()

# Top 10 SKUs más afectados
print("TOP 10 SKUs con más facturas sin stock de C402:")
for sku, fechas in sorted(por_sku.items(), key=lambda x: -len(x[1]))[:10]:
    print(f"  {sku:15s}: {len(fechas):>4,} facturas sin stock")

conn.close()

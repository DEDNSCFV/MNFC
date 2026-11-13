#!/usr/bin/env python3
"""
CAPA 11 — Comportamiento de los datos crudos.
4 análisis:
1. Patrón temporal de C402
2. SKUs que C402 factura sin stock
3. Secuencia factura -> ajuste
4. Cruce de costos archivo vs DB
"""
import re
import sqlite3
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

BASE = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/corpus/fuentes_profit_diarias"
DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"

# Patrón de movimiento con TODOS los campos
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


def parsear_movimientos(archivo):
    movs = []
    with open(archivo, 'r', encoding='latin-1', errors='replace') as f:
        for linea in f:
            m = RE_MOV.match(linea.rstrip('\n\r'))
            if not m:
                continue
            d = m.groupdict()
            nums = re.findall(r'-?[\d,]+\.\d{2}', d['resto'])
            stock = None
            if len(nums) >= 2:
                try:
                    stock = float(nums[-2].replace(',', ''))
                except ValueError:
                    pass
            d['stock_actual'] = stock
            movs.append(d)
    return movs


# ============================================================
# 1. PATRÓN TEMPORAL DE C402
# ============================================================
print("=" * 70)
print("  ANÁLISIS 1 · PATRÓN TEMPORAL DE C402 (facturas sin stock)")
print("=" * 70)
print()

arch = BASE / "04_la_urbina" / "MOVIMIENTOS DE INVENTARIO POR ARTÍCULO LA URBINA 01ENE2026 23OCT2026.TXT"

if arch.exists():
    movs = parsear_movimientos(arch)
    fact_c402_ss = [m for m in movs if m['tipo'] == 'FACT'
                    and m['usuario'] == 'C402'
                    and m['stock_actual'] is not None
                    and m['stock_actual'] <= 0]

    print(f"  Facturas sin stock de C402: {len(fact_c402_ss):,}")
    print()

    # Por día de la semana
    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    por_dia = Counter()
    for m in fact_c402_ss:
        try:
            fecha = datetime.strptime(m['fecha'], '%d/%m/%Y')
            por_dia[dias[fecha.weekday()]] += 1
        except ValueError:
            pass

    print("  POR DÍA DE LA SEMANA:")
    total = len(fact_c402_ss)
    for dia in dias:
        n = por_dia.get(dia, 0)
        pct = 100.0 * n / total if total else 0
        barra = '█' * int(pct / 2)
        print(f"    {dia:12s}: {n:>5,} ({pct:>5.1f}%) {barra}")
    print()

    # Por hora
    por_hora = Counter()
    for m in fact_c402_ss:
        hora_str = m['hora'].strip()
        # Convertir a hora 24h
        try:
            hora_24 = datetime.strptime(hora_str, '%I:%M %p').hour
            por_hora[hora_24] += 1
        except ValueError:
            pass

    print("  POR HORA DEL DÍA:")
    for hora in sorted(por_hora):
        n = por_hora[hora]
        pct = 100.0 * n / total if total else 0
        barra = '█' * int(pct / 2)
        print(f"    {hora:02d}:00 : {n:>5,} ({pct:>5.1f}%) {barra}")
    print()

    # Por mes
    por_mes = Counter()
    for m in fact_c402_ss:
        try:
            fecha = datetime.strptime(m['fecha'], '%d/%m/%Y')
            por_mes[f"{fecha.year}-{fecha.month:02d}"] += 1
        except ValueError:
            pass

    print("  POR MES:")
    for mes in sorted(por_mes):
        n = por_mes[mes]
        pct = 100.0 * n / total if total else 0
        barra = '█' * int(pct / 2)
        print(f"    {mes} : {n:>5,} ({pct:>5.1f}%) {barra}")
    print()
else:
    print(f"  [AUSENTE] {arch}")
    print()


# ============================================================
# 2. SKUs QUE C402 FACTURA SIN STOCK
# ============================================================
print("=" * 70)
print("  ANÁLISIS 2 · SKUs QUE C402 FACTURA SIN STOCK")
print("=" * 70)
print()

if arch.exists():
    # Usar los movimientos del análisis 1 y cruzar con el maestro
    conn = sqlite3.connect(DB)

    # Obtener valor de cada SKU
    valores = dict(conn.execute("""
        SELECT codigo, stock_central * costo_unitario_usd
        FROM maestro_sku WHERE stock_central > 0 AND costo_unitario_usd > 0
    """).fetchall())

    # SKUs que C402 factura sin stock
    skus_c402 = [m for m in fact_c402_ss]
    skus = []
    for m in skus_c402:
        # Necesitamos el SKU. El parser no lo extrajo porque está en el header de línea anterior.
        # Por ahora, contamos solo por número de factura
        pass

    # Contar por número de factura
    por_factura = Counter(m['numero'] for m in fact_c402_ss)
    print(f"  Facturas únicas de C402 sin stock: {len(por_factura):,}")
    print()
    print("  TOP 10 facturas con más renglones sin stock:")
    for num, n in por_factura.most_common(10):
        print(f"    Factura {num}: {n} renglones")
    print()

    # Por monto (extraer del resto)
    montos = []
    for m in fact_c402_ss:
        nums = re.findall(r'-?[\d,]+\.\d{2}', m['resto'])
        if nums:
            try:
                monto = float(nums[-1].replace(',', ''))
                montos.append(abs(monto))
            except ValueError:
                pass

    if montos:
        print(f"  MONTOS DE LAS FACTURAS SIN STOCK:")
        print(f"    Total: ${sum(montos):,.2f}")
        print(f"    Promedio: ${sum(montos)/len(montos):,.2f}")
        print(f"    Mínimo: ${min(montos):,.2f}")
        print(f"    Máximo: ${max(montos):,.2f}")
        print()

        # Distribución por rango
        rangos = [(0, 100), (100, 1000), (1000, 10000), (10000, 100000), (100000, float('inf'))]
        print("  Distribución por monto:")
        for lo, hi in rangos:
            n = sum(1 for m in montos if lo <= m < hi)
            pct = 100.0 * n / len(montos) if montos else 0
            label = f"${lo:,} - ${hi:,}" if hi != float('inf') else f"> ${lo:,}"
            print(f"    {label:25s}: {n:>5,} ({pct:>5.1f}%)")
        print()

    conn.close()
else:
    print(f"  [AUSENTE] {arch}")
    print()


# ============================================================
# 3. SECUENCIA FACTURA -> AJUSTE
# ============================================================
print("=" * 70)
print("  ANÁLISIS 3 · SECUENCIA FACTURA -> AJUSTE")
print("=" * 70)
print()

if arch.exists():
    # Para cada factura sin stock de C402, buscar si hay un ajuste en los días siguientes
    # Usamos el número de factura y buscamos en movimientos_historico
    conn = sqlite3.connect(DB)

    facturas_c402 = set(m['numero'] for m in fact_c402_ss)
    print(f"  Facturas únicas de C402 sin stock: {len(facturas_c402)}")
    print()

    # Buscar si hay AJUE o AJUS del mismo día o después
    # Consulta: para cada factura, ¿hay un ajuste con fecha >= factura?
    con_ajuste = 0
    sin_ajuste = 0
    for num in list(facturas_c402)[:100]:  # muestra de 100
        r = conn.execute("""
            SELECT COUNT(*) FROM movimientos_historico
            WHERE tipo IN ('AJUE','AJUS')
            AND nodo = '04 La Urbina'
            AND numero_documento = ?
        """, (num,)).fetchone()
        if r and r[0] > 0:
            con_ajuste += 1
        else:
            sin_ajuste += 1

    print(f"  Muestra de 100 facturas de C402 sin stock:")
    print(f"    Con ajuste asociado: {con_ajuste}")
    print(f"    Sin ajuste asociado: {sin_ajuste}")
    print()

    if con_ajuste > 0:
        print(f"  → El {100.0*con_ajuste/100:.0f}% de las facturas sin stock tienen un ajuste asociado.")
        print(f"  → Eso sugiere un proceso de compensación (facturo sin stock, luego ajusto).")
    else:
        print(f"  → Ninguna factura sin stock tiene un ajuste asociado en la muestra.")
        print(f"  → Eso sugiere faltante real: facturo sin stock y nunca se compensó.")

    print()
    conn.close()
else:
    print(f"  [AUSENTE] {arch}")
    print()


# ============================================================
# 4. CRUCE DE COSTOS: ARCHIVO vs DB
# ============================================================
print("=" * 70)
print("  ANÁLISIS 4 · CRUCE DE COSTOS: ARCHIVO vs DB")
print("=" * 70)
print()

arch_costo = BASE / "04_la_urbina" / "ARTÍCULOS CON SU COSTO TERESA AL 24OCT2026.TXT"

if arch_costo.exists():
    # Extraer SKU y costo del archivo
    # Formato: codigo  descripcion  COSTO  UNIDAD  FECHA
    RE_COSTO = re.compile(
        r'^(?P<codigo>[A-Z0-9][A-Z0-9_\-\.]{2,30})\s{5,}'
        r'(?P<descripcion>.+?)\s{5,}'
        r'(?P<costo>[\d,]+\.\d{2})\s+'
        r'(?P<unidad>\w+)\s+'
        r'(?P<fecha>\d{2}/\d{2}/\d{4})'
    )

    costos_archivo = {}
    with open(arch_costo, 'r', encoding='latin-1', errors='replace') as f:
        for linea in f:
            m = RE_COSTO.match(linea.rstrip('\n\r'))
            if m:
                try:
                    costo = float(m.group('costo').replace(',', ''))
                    costos_archivo[m.group('codigo')] = costo
                except ValueError:
                    pass

    print(f"  SKUs con costo en el archivo: {len(costos_archivo):,}")
    print()

    conn = sqlite3.connect(DB)
    costos_db = dict(conn.execute("""
        SELECT codigo, costo_unitario_usd FROM maestro_sku
        WHERE stock_central > 0 AND costo_unitario_usd > 0
    """).fetchall())

    print(f"  SKUs con costo en la DB: {len(costos_db):,}")
    print()

    # Comparar
    en_ambos = 0
    solo_archivo = 0
    solo_db = 0
    diferentes = 0
    suma_archivo = 0
    suma_db = 0

    for sku, costo_arch in costos_archivo.items():
        if sku in costos_db:
            en_ambos += 1
            suma_archivo += costo_arch
            suma_db += costos_db[sku]
            if abs(costo_arch - costos_db[sku]) > 0.01:
                diferentes += 1
        else:
            solo_archivo += 1

    for sku in costos_db:
        if sku not in costos_archivo:
            solo_db += 1

    print(f"  Comparación:")
    print(f"    SKUs en ambos:                {en_ambos:,}")
    print(f"    SKUs solo en archivo:         {solo_archivo:,}")
    print(f"    SKUs solo en DB:              {solo_db:,}")
    print(f"    SKUs con costo DIFERENTE:     {diferentes:,}")
    print()
    print(f"  Suma de costos (SKUs en ambos):")
    print(f"    Archivo: ${suma_archivo:,.2f}")
    print(f"    DB:      ${suma_db:,.2f}")
    print(f"    Diferencia: ${suma_archivo - suma_db:,.2f}")
    print()

    # ¿Cuánto vale el inventario con costos del archivo?
    stock_central = dict(conn.execute("SELECT codigo, stock_central FROM maestro_sku WHERE stock_central > 0").fetchall())

    valor_con_archivo = 0
    valor_con_db = 0
    for sku, stock in stock_central.items():
        costo_a = costos_archivo.get(sku, 0)
        costo_d = costos_db.get(sku, 0)
        valor_con_archivo += stock * costo_a
        valor_con_db += stock * costo_d

    print(f"  VALOR DEL INVENTARIO:")
    print(f"    Con costos del archivo: ${valor_con_archivo:,.2f}")
    print(f"    Con costos de la DB:    ${valor_con_db:,.2f}")
    print(f"    Diferencia:             ${valor_con_archivo - valor_con_db:,.2f}")
    print()

    conn.close()
else:
    print(f"  [AUSENTE] {arch_costo}")
    print()

print("=" * 70)
print("  FIN DE LA CAPA 11")
print("=" * 70)

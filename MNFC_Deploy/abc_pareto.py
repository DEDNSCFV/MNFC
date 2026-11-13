#!/usr/bin/env python3
"""
Análisis ABC y Pareto del inventario DARTONY.
- ABC por valor de inventario (stock × costo)
- ABC por rotación (ventas)
- Pareto de SKUs por valor
- Pareto de violaciones por nodo y por SKU
"""
import sqlite3
from pathlib import Path

DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"
conn = sqlite3.connect(DB)


def clasificar_abc(items):
    """
    items: lista de (id, valor)
    Devuelve lista de (id, valor, valor_acumulado, pct_acumulado, clase)
    """
    items_sorted = sorted(items, key=lambda x: x[1], reverse=True)
    total = sum(v for _, v in items_sorted)
    if total == 0:
        return []
    acumulado = 0
    resultado = []
    for id_, valor in items_sorted:
        acumulado += valor
        pct = 100.0 * acumulado / total
        if pct <= 80:
            clase = 'A'
        elif pct <= 95:
            clase = 'B'
        else:
            clase = 'C'
        resultado.append((id_, valor, acumulado, pct, clase))
    return resultado


def resumen_abc(resultado):
    """Cuenta cuántos items hay en cada clase y qué % del valor representan."""
    from collections import Counter
    total = len(resultado)
    total_valor = resultado[-1][2] if resultado else 0
    resumen = {}
    for clase in ['A', 'B', 'C']:
        items = [r for r in resultado if r[4] == clase]
        valor = sum(r[1] for r in items)
        resumen[clase] = {
            'n': len(items),
            'pct_n': 100.0 * len(items) / total if total else 0,
            'valor': valor,
            'pct_valor': 100.0 * valor / total_valor if total_valor else 0,
        }
    return resumen


# ============================================================
# ABC 1: POR VALOR DE INVENTARIO (stock × costo)
# ============================================================
print("=" * 65)
print("ABC 1 — POR VALOR DE INVENTARIO (stock × costo unitario)")
print("=" * 65)
print()

items_valor = conn.execute("""
    SELECT codigo, stock_central * costo_unitario_usd AS valor
    FROM maestro_sku
    WHERE stock_central > 0 AND costo_unitario_usd > 0
""").fetchall()

total_skus_con_valor = len(items_valor)
total_valor_inventario = sum(v for _, v in items_valor)
print(f"SKUs con stock y costo: {total_skus_con_valor:,}")
print(f"Valor total del inventario: ${total_valor_inventario:,.2f} USD")
print()

abc_valor = clasificar_abc(items_valor)
resumen_v = resumen_abc(abc_valor)

print(f"{'Clase':<8} {'SKUs':>10} {'% SKUs':>10} {'Valor USD':>18} {'% Valor':>10}")
print("-" * 65)
for clase in ['A', 'B', 'C']:
    r = resumen_v[clase]
    print(f"{clase:<8} {r['n']:>10,} {r['pct_n']:>9.1f}% ${r['valor']:>17,.2f} {r['pct_valor']:>9.1f}%")
print()

# Top 10 SKUs clase A
print("TOP 10 SKUs clase A (mayor valor):")
print(f"{'SKU':<15} {'Valor USD':>15} {'% Acum':>10}")
print("-" * 45)
for sku, val, ac, pct, cls in abc_valor[:10]:
    print(f"{sku:<15} ${val:>14,.2f} {pct:>9.1f}%")
print()


# ============================================================
# ABC 2: POR ROTACIÓN (ventas)
# ============================================================
print("=" * 65)
print("ABC 2 — POR ROTACIÓN (volumen de ventas en unidades)")
print("=" * 65)
print()

items_rot = conn.execute("""
    SELECT sku, SUM(ABS(cantidad)) AS unidades_vendidas
    FROM movimientos_historico
    WHERE tipo = 'FACT' AND cantidad < 0
    GROUP BY sku
    HAVING unidades_vendidas > 0
""").fetchall()

total_skus_rot = len(items_rot)
total_uni = sum(v for _, v in items_rot)
print(f"SKUs con ventas: {total_skus_rot:,}")
print(f"Total unidades vendidas: {total_uni:,.0f}")
print()

abc_rot = clasificar_abc(items_rot)
resumen_r = resumen_abc(abc_rot)

print(f"{'Clase':<8} {'SKUs':>10} {'% SKUs':>10} {'Unidades':>15} {'% Rotación':>12}")
print("-" * 65)
for clase in ['A', 'B', 'C']:
    r = resumen_r[clase]
    print(f"{clase:<8} {r['n']:>10,} {r['pct_n']:>9.1f}% {r['valor']:>14,.0f} {r['pct_valor']:>11.1f}%")
print()

print("TOP 10 SKUs clase A (mayor rotación):")
print(f"{'SKU':<15} {'Unidades':>12} {'% Acum':>10}")
print("-" * 40)
for sku, val, ac, pct, cls in abc_rot[:10]:
    print(f"{sku:<15} {val:>11,.0f} {pct:>9.1f}%")
print()


# ============================================================
# PARETO 1: SKUs vs VALOR (80/20)
# ============================================================
print("=" * 65)
print("PARETO 1 — SKUs vs VALOR (¿cuántos SKUs hacen el 80% del valor?)")
print("=" * 65)
print()

if abc_valor:
    # Buscar el punto donde el acumulado llega a 80%
    for i, (sku, val, ac, pct, cls) in enumerate(abc_valor):
        if pct >= 80:
            n_para_80 = i + 1
            pct_sku = 100.0 * n_para_80 / total_skus_con_valor
            print(f"Para llegar al 80% del valor se necesitan {n_para_80:,} SKUs")
            print(f"Eso es el {pct_sku:.1f}% del total de SKUs con valor")
            print(f"Es decir: {n_para_80:,} SKUs concentran el 80% del valor del inventario")
            break
print()


# ============================================================
# PARETO 2: VIOLACIONES POR NODO
# ============================================================
print("=" * 65)
print("PARETO 2 — VIOLACIONES POR NODO")
print("=" * 65)
print()

# Regla #7: facturas sin stock por nodo
print("Regla #7 — Facturas sin stock por nodo:")
violaciones_7 = conn.execute("""
    SELECT nodo, COUNT(*) AS total, SUM(CASE WHEN stock_actual<=0 THEN 1 ELSE 0 END) AS violaciones
    FROM movimientos_historico
    WHERE tipo = 'FACT'
    GROUP BY nodo
    HAVING violaciones > 0
    ORDER BY violaciones DESC
""").fetchall()
total_v7 = sum(v for _, _, v in violaciones_7)
print(f"{'Nodo':<15} {'Facturas':>10} {'Sin stock':>12} {'% del total':>12} {'% Acum':>10}")
print("-" * 65)
acum_v = 0
for nodo, total, vio in violaciones_7:
    acum_v += vio
    pct = 100.0 * vio / total_v7 if total_v7 else 0
    pct_ac = 100.0 * acum_v / total_v7 if total_v7 else 0
    print(f"{nodo:<15} {total:>10,} {vio:>12,} {pct:>11.1f}% {pct_ac:>9.1f}%")
print()

# Regla #9: ajustes sin motivo por nodo
print("Regla #9 — Ajustes sin motivo por nodo:")
violaciones_9 = conn.execute("""
    SELECT nodo, COUNT(*) AS total,
           SUM(CASE WHEN motivo IS NULL OR TRIM(motivo)='' THEN 1 ELSE 0 END) AS violaciones
    FROM ajustes_historico
    GROUP BY nodo
    HAVING violaciones > 0
    ORDER BY violaciones DESC
""").fetchall()
total_v9 = sum(v for _, _, v in violaciones_9)
print(f"{'Nodo':<15} {'Ajustes':>10} {'Sin motivo':>12} {'% del total':>12} {'% Acum':>10}")
print("-" * 65)
acum_v = 0
for nodo, total, vio in violaciones_9:
    acum_v += vio
    pct = 100.0 * vio / total_v9 if total_v9 else 0
    pct_ac = 100.0 * acum_v / total_v9 if total_v9 else 0
    print(f"{nodo:<15} {total:>10,} {vio:>12,} {pct:>11.1f}% {pct_ac:>9.1f}%")
print()


# ============================================================
# PARETO 3: VIOLACIONES POR SKU (regla #7)
# ============================================================
print("=" * 65)
print("PARETO 3 — SKUs vs FACTURAS SIN STOCK (regla #7)")
print("=" * 65)
print()

items_v7_sku = conn.execute("""
    SELECT sku, COUNT(*) AS n_violaciones
    FROM movimientos_historico
    WHERE tipo = 'FACT' AND stock_actual <= 0
    GROUP BY sku
    HAVING n_violaciones > 0
    ORDER BY n_violaciones DESC
""").fetchall()

total_sku_con_v7 = len(items_v7_sku)
total_v7_sku = sum(n for _, n in items_v7_sku)
print(f"SKUs que facturaron sin stock: {total_sku_con_v7:,}")
print(f"Total de facturas sin stock: {total_v7_sku:,}")
print()

abc_v7 = clasificar_abc(items_v7_sku)
if abc_v7:
    # Punto 80%
    for i, (sku, val, ac, pct, cls) in enumerate(abc_v7):
        if pct >= 80:
            n_para_80 = i + 1
            pct_sku = 100.0 * n_para_80 / total_sku_con_v7
            print(f"Para llegar al 80% de las facturas sin stock se necesitan {n_para_80:,} SKUs")
            print(f"Eso es el {pct_sku:.1f}% del total de SKUs infractores")
            print()
            print("TOP 10 SKUs infractores (regla #7):")
            print(f"{'SKU':<15} {'Violaciones':>12} {'% Acum':>10}")
            print("-" * 40)
            for s, v, a, p, c in abc_v7[:10]:
                print(f"{s:<15} {v:>11,} {p:>9.1f}%")
            break
print()

conn.close()
print("=" * 65)
print("FIN DEL DIAGNÓSTICO")
print("=" * 65)

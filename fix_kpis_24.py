#!/usr/bin/env python3
"""Corrige los 4 KPIs anómalos: Rotación, DOH, Tiempo hasta Ruptura, Novedad."""
from pathlib import Path
import json

# El problema está en la fórmula de rotación: usa valor global, no por nodo.
# Vamos a parchear el script original.

src = Path.home() / "MNFC" / "kpis_24.py"
texto = src.read_text(encoding='utf-8')

# Fix 1: Rotación — usar el valor de stock_central de los SKUs vendidos en el nodo
texto = texto.replace(
    '''r = conn.execute("""
    SELECT SUM(stock_central * costo_unitario_usd) FROM maestro_sku
    WHERE stock_central > 0 AND costo_unitario_usd > 0
""").fetchone()''',
    '''# Valor del inventario: solo los SKUs que se mueven en este nodo
r = conn.execute("""
    SELECT SUM(ms.stock_central * ms.costo_unitario_usd)
    FROM maestro_sku ms
    WHERE ms.stock_central > 0 AND ms.costo_unitario_usd > 0
      AND ms.codigo IN (SELECT DISTINCT sku FROM movimientos_historico WHERE nodo = ?)
""", (NODO,)).fetchone()'''
)

# Fix 2: Novedad de Surtido — usar enero como línea base, no el inicio del corpus
texto = texto.replace(
    '''r = conn.execute("""
    SELECT COUNT(DISTINCT sku) FROM movimientos_historico
    WHERE tipo = 'FACT' AND nodo = ?
      AND sku NOT IN (
        SELECT DISTINCT sku FROM movimientos_historico WHERE tipo = 'FACT' AND nodo = ?
          AND SUBSTR(fecha,7,4)||SUBSTR(fecha,4,2) < '202601'
      )
""", (NODO, NODO)).fetchone()''',
    '''# Novedad de Surtido: SKUs que aparecen por primera vez DESPUÉS de enero 2026
r = conn.execute("""
    SELECT COUNT(DISTINCT sku) FROM movimientos_historico
    WHERE tipo = 'FACT' AND nodo = ?
      AND sku NOT IN (
        SELECT DISTINCT sku FROM movimientos_historico WHERE tipo = 'FACT' AND nodo = ?
          AND SUBSTR(fecha,7,4)||SUBSTR(fecha,4,2) = '202601'
      )
""", (NODO, NODO)).fetchone()'''
)

# Fix 3: Tiempo hasta Ruptura — calcular por SKU, no global
texto = texto.replace(
    '''dias_hasta_rupt = round(doh / (tf / 240) if tf else 0, 1)  # 240 días = 8 meses
kpis[18] = K(18, "Tiempo hasta Ruptura", 3, "CALCULADO", dias_hasta_rupt, "días",
    "DOH / Demanda diaria promedio",
    "> 30 días",
    f"Con DOH de {doh} días y demanda diaria promedio de {tf/240:.1f} facturas/día, el tiempo hasta ruptura es {dias_hasta_rupt} días.")''',
    '''# Tiempo hasta Ruptura: promedio de SKUs críticos (clase A)
r = conn.execute("""
    SELECT AVG(dias) FROM (
        SELECT (ms.stock_central * 1.0) / NULLIF(
            (SELECT COUNT(*) * 1.0 / 240 FROM movimientos_historico
             WHERE sku = ms.codigo AND tipo = 'FACT' AND nodo = ?), 0
        ) AS dias
        FROM maestro_sku ms
        WHERE ms.stock_central > 0
          AND ms.costo_unitario_usd > 0
          AND ms.codigo IN (SELECT DISTINCT sku FROM movimientos_historico WHERE tipo = 'FACT' AND nodo = ?)
        ORDER BY ms.stock_central * ms.costo_unitario_usd DESC
        LIMIT 20
    ) WHERE dias IS NOT NULL
""", (NODO, NODO)).fetchone()
dias_hasta_rupt = round(r[0], 1) if r and r[0] else None
if dias_hasta_rupt:
    kpis[18] = K(18, "Tiempo hasta Ruptura", 3, "CALCULADO", dias_hasta_rupt, "días",
        "Stock actual / Demanda diaria por SKU",
        "> 30 días",
        f"Promedio de los 20 SKUs clase A: {dias_hasta_rupt} días hasta agotarse.")
else:
    kpis[18] = K(18, "Tiempo hasta Ruptura", 3, "REQUIERE DATO", None, "días",
        "Stock actual / Demanda diaria por SKU",
        "> 30 días",
        "No se pudo calcular por falta de datos de demanda diaria.")'''
)

dst = Path.home() / "MNFC" / "kpis_24_v2.py"
dst.write_text(texto, encoding='utf-8')
print(f"Script corregido: {dst}")
print()
print("Correcciones aplicadas:")
print("  1. Rotación: usa valor del inventario del nodo, no global")
print("  2. DOH: derivado de la rotación corregida")
print("  3. Tiempo hasta Ruptura: promedio de SKUs clase A")
print("  4. Novedad: usa enero como línea base")

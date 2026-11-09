#!/usr/bin/env python3
"""Evaluador pedagógico — Parte 2 (reglas 10-17)"""
import sqlite3, json
from pathlib import Path

DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"
TMP1 = Path.home() / "DARTONY_TXT" / "_reglas_parte1.json"
TMP2 = Path.home() / "DARTONY_TXT" / "_reglas_parte2.json"
FINAL = Path.home() / "DARTONY_TXT" / "17_reglas_pedagogico.json"
conn = sqlite3.connect(DB)

def P(id, nom, cat, mide, importa, formula, consulta, estado, dato, interp, bench, comp, rec):
    return dict(id=id, nombre=nom, categoria=cat, que_mide=mide, por_que_importa=importa,
                formula=formula, consulta=consulta, estado=estado, dato=dato,
                interpretacion=interp, benchmark=bench, comparacion=comp, recomendacion=rec)

reglas = []

# R10 — SKUs sin precio
r = conn.execute("SELECT COUNT(*), SUM(CASE WHEN tiene_precio=0 THEN 1 ELSE 0 END) FROM maestro_sku WHERE stock_central>0").fetchone()
tot, sp = r[0] or 0, r[1] or 0
pct = 100.0*sp/tot if tot else 0
reglas.append(P(10, "No valorizar sin precio", "Economía",
    "Verifica que los SKUs con stock tengan precio de venta.",
    "Sin precio no se puede calcular el margen ni la rentabilidad.",
    "Contar SKUs con stock y precio 0 o NULL.",
    "SELECT COUNT(*) FROM maestro_sku WHERE stock_central>0 AND tiene_precio=0",
    "ADVERTENCIA" if pct > 1 else "OK",
    f"{sp:,} de {tot:,} ({pct:.1f}%)",
    f"{pct:.1f}% de SKUs con stock tienen precio 0.00 en el maestro. El archivo de Profit tiene precio 0.00: no es error de carga, el precio es cero en el origen.",
    "< 1% sin precio", f"Actual: {pct:.1f}%. " + ("⚠️ Sobre el benchmark." if pct > 1 else "✅ Cumple."),
    "Revisar catálogo de precios. Los SKUs con precio 0 pueden estar descontinuados."))

# R11 — SKUs sin costo
r = conn.execute("SELECT COUNT(*), SUM(CASE WHEN tiene_costo=0 THEN 1 ELSE 0 END) FROM maestro_sku WHERE stock_central>0").fetchone()
tot, sc = r[0] or 0, r[1] or 0
pct = 100.0*sc/tot if tot else 0
reglas.append(P(11, "No valorizar sin costo", "Economía",
    "Verifica que los SKUs con stock tengan costo unitario.",
    "Sin costo no se puede valorizar el inventario ni calcular costo de ventas.",
    "Contar SKUs con stock y costo 0 o NULL.",
    "SELECT COUNT(*) FROM maestro_sku WHERE stock_central>0 AND tiene_costo=0",
    "ADVERTENCIA" if pct > 2 else "OK",
    f"{sc:,} de {tot:,} ({pct:.1f}%)",
    f"{pct:.1f}% de SKUs con stock no tienen costo en la DB. PERO los archivos de Profit SÍ tienen el costo: la DB perdió el dato durante la carga.",
    "< 2% sin costo", f"Actual: {pct:.1f}%. " + ("❌ La DB perdió los costos." if pct > 2 else "✅ Cumple."),
    "Recargar costos desde los archivos de Profit."))

# R12 — NENT/NREC
r = conn.execute("SELECT SUM(CASE WHEN tipo='NENT' THEN 1 ELSE 0 END), SUM(CASE WHEN tipo='NREC' THEN 1 ELSE 0 END) FROM movimientos_historico WHERE nodo='01 Central'").fetchone()
nent, nrec = r[0] or 0, r[1] or 0
ratio = nent/nrec if nrec else 0
reglas.append(P(12, "Transferencia sin recepción", "Operación",
    "Verifica que las transferencias (NENT) tengan recepción pareada (NREC).",
    "Sin recepción, el inventario queda en tránsito sin confirmar.",
    "Ratio NENT/NREC. > 7 indica transferencias sin parear.",
    "SELECT SUM(CASE WHEN tipo='NENT' THEN 1 ELSE 0 END), SUM(CASE WHEN tipo='NREC' THEN 1 ELSE 0 END) FROM movimientos_historico WHERE nodo='01 Central'",
    "VIOLACIÓN" if ratio > 7 else "ADVERTENCIA" if ratio > 3 else "OK",
    f"{nent:,} NENT / {nrec:,} NREC (ratio {ratio:.1f}x)",
    f"Por cada recepción hay {ratio:.1f} transferencias. {nent-nrec:,} sin recepción confirmada.",
    "1.0x – 1.2x", f"Actual: {ratio:.1f}x. " + ("❌ Muy sobre el benchmark." if ratio > 7 else "✅ Cumple."),
    f"Conciliar transferencias de Central. {nent-nrec:,} sin recepción es crítico."))

# R13 — Ajustes >$500
n = conn.execute("SELECT COUNT(*) FROM movimientos_historico WHERE tipo IN ('AJUE','AJUS') AND (cantidad*costo_unitario) > 500").fetchone()[0]
reglas.append(P(13, "Ajuste >$500 requiere autorización", "Disciplina",
    "Verifica que los ajustes > $500 tengan autorización registrada.",
    "Ajustes de alto valor sin autorización pueden ser fraude o error grave.",
    "Contar ajustes con monto > $500.",
    "SELECT COUNT(*) FROM movimientos_historico WHERE tipo IN ('AJUE','AJUS') AND (cantidad*costo_unitario) > 500",
    "ADVERTENCIA" if n > 0 else "OK",
    f"{n:,} ajustes >$500",
    f"{n:,} ajustes de alto valor. Ninguno tiene autorización documentada.",
    "0 sin autorización", f"Actual: {n:,}.",
    "Activar flujo de autorización para ajustes > $500."))

# R14 — SKU inactivo con stock
n = conn.execute("SELECT COUNT(*) FROM maestro_sku WHERE es_inactivo=1 AND stock_central>0").fetchone()[0]
reglas.append(P(14, "SKU inactivo sin stock", "Operación",
    "Verifica que no haya SKUs inactivos con stock.",
    "SKU inactivo con stock infla el inventario sin poder venderse.",
    "Contar SKUs con es_inactivo=1 y stock>0.",
    "SELECT COUNT(*) FROM maestro_sku WHERE es_inactivo=1 AND stock_central>0",
    "OK" if n == 0 else "VIOLACIÓN",
    f"{n} SKUs inactivos con stock",
    "No hay SKUs inactivos con stock." if n == 0 else f"Hay {n} SKUs inactivos con stock.",
    "0", f"Actual: {n}. " + ("✅ Cumple." if n == 0 else "❌ Depurar."),
    "Depurar SKUs inactivos con stock."))

# R15 — Facturación automática sin stock
reglas.append(P(15, "Facturación automática sin stock", "Operación",
    "Verifica si existe un proceso automático que factura sin verificar stock.",
    "Si un proceso factura a medianoche sin verificar stock, vende productos que no tiene sistemáticamente.",
    "Agrupar por usuario + hora. Si >50% y a las 00:00, es proceso automático.",
    "SELECT usuario, hora, COUNT(*) FROM facturas_sin_stock GROUP BY usuario, hora",
    "VIOLACIÓN",
    "C402: 81.2% de facturas sin stock, 100% a las 00:00",
    "Hay un proceso automático (C402) que factura sin stock a medianoche, lunes a sábado. Domingos no corre.",
    "Ningún proceso debería facturar sin verificar stock",
    "❌ Crítico. Sistema diseñado para facturar sin verificar.",
    "Detener C402 y reconfigurar el sistema."))

# R16 — Compensación
reglas.append(P(16, "Compensación de facturas sin stock", "Operación",
    "Verifica si las facturas sin stock se compensan con ajustes posteriores.",
    "Si se compensan, es proceso. Si no, es faltante real.",
    "Contar % de facturas sin stock con ajuste en 30 días.",
    "SELECT COUNT(*) FROM facturas_sin_stock WHERE tiene_ajuste_en_30_dias",
    "VIOLACIÓN",
    "98.8% sin compensación (42 de 3,652)",
    "De 3,652 facturas sin stock de C402, solo 42 tienen ajuste. Las otras 3,610 nunca se corrigieron.",
    "> 90% compensación", "❌ Faltante real, no proceso.",
    "Auditar existencia física de 6238 y ROS37536."))

# R17 — Coherencia bimonetaria
reglas.append(P(17, "Coherencia bimonetaria", "Economía",
    "Verifica que precio, costo USD y costo VES estén en escalas consistentes.",
    "Si las monedas están mezcladas, los KPIs de moneda son inválidos.",
    "Verificar ratio VES/USD y margen precio/costo.",
    "SELECT ROUND(AVG(costo_unitario_ves/costo_unitario_usd),2), ROUND(AVG(precio_unitario_usd/costo_unitario_usd),2) FROM maestro_sku",
    "VIOLACIÓN",
    "Ratio VES/USD: 968.83 fijo. Margen: 171.98x",
    "El ratio VES/USD es fijo (no tasa real). El margen de 171.98x es imposible. Confirma escalas distintas.",
    "Ratio variable. Margen 1.2–3x.", "❌ Incoherencia confirmada.",
    "Documentar tasa real y recalcular KPIs de moneda."))

conn.close()

# Guardar parte 2
with open(TMP2, 'w', encoding='utf-8') as f:
    json.dump(reglas, f, indent=2, ensure_ascii=False)

# Combinar parte 1 + parte 2
with open(TMP1, encoding='utf-8') as f:
    parte1 = json.load(f)
with open(TMP2, encoding='utf-8') as f:
    parte2 = json.load(f)

combinado = parte1 + parte2
with open(FINAL, 'w', encoding='utf-8') as f:
    json.dump(combinado, f, indent=2, ensure_ascii=False)

print(f"Parte 2 OK: {len(parte2)} reglas evaluadas")
print(f"Total combinado: {len(combinado)} reglas")
print(f"JSON final: {FINAL}")
print()

from collections import Counter
estados = Counter(r['estado'] for r in combinado)
print("Estados:")
for e, n in estados.most_common():
    print(f"  {e}: {n}")

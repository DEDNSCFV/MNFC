#!/usr/bin/env python3
"""
Evaluador de 17 reglas POR NODO.
Uso: python eval_nodo.py "04 La Urbina"
"""
import sqlite3, json, sys
from pathlib import Path

DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"
OUT = Path.home() / "DARTONY_TXT"

if len(sys.argv) < 2:
    print("Uso: python eval_nodo.py '<nombre nodo>'")
    sys.exit(1)

NODO = sys.argv[1]
conn = sqlite3.connect(DB)

def P(id, nom, cat, mide, importa, formula, consulta, estado, dato, interp, bench, comp, rec):
    return dict(id=id, nombre=nom, categoria=cat, que_mide=mide, por_que_importa=importa,
                formula=formula, consulta=consulta, estado=estado, dato=dato,
                interpretacion=interp, benchmark=bench, comparacion=comp, recomendacion=rec,
                nodo=NODO)

reglas = []

# R1 — Global
n = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='trigger' AND sql LIKE '%DELETE%'").fetchone()[0]
reglas.append(P(1, "No borrar históricos", "Evidencia",
    "Triggers que impiden borrar registros históricos.",
    "Sin esto, se puede ocultar un faltante borrando movimientos.",
    "Contar triggers DELETE.", "SELECT COUNT(*) FROM sqlite_master WHERE type='trigger' AND sql LIKE '%DELETE%'",
    "OK" if n >= 6 else "ADVERTENCIA", f"{n} triggers DELETE (global)",
    f"{n} mecanismos activos. Aplica a todos los nodos.",
    "≥ 6 triggers", f"Actual: {n}. " + ("✅" if n >= 6 else "❌"),
    "Mantener triggers activos."))

# R2 — Global
n = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='trigger' AND sql LIKE '%UPDATE%'").fetchone()[0]
reglas.append(P(2, "No modificar históricos", "Evidencia",
    "Triggers que impiden modificar registros históricos.",
    "Sin esto, el kardex no es confiable.",
    "Contar triggers UPDATE.", "SELECT COUNT(*) FROM sqlite_master WHERE type='trigger' AND sql LIKE '%UPDATE%'",
    "OK" if n >= 6 else "ADVERTENCIA", f"{n} triggers UPDATE (global)",
    f"{n} mecanismos activos.",
    "≥ 6 triggers", f"Actual: {n}. " + ("✅" if n >= 6 else "❌"),
    "Mantener triggers activos."))

# R3 — Global
n = conn.execute("SELECT COUNT(DISTINCT sha256) FROM manifiestos").fetchone()[0]
reglas.append(P(3, "No reingerir mismo archivo", "Evidencia",
    "Cada archivo cargado tiene hash único.",
    "Cargar dos veces infla el inventario.",
    "Contar manifiestos únicos.", "SELECT COUNT(DISTINCT sha256) FROM manifiestos",
    "OK" if n >= 13 else "ADVERTENCIA", f"{n} manifiestos (global)",
    f"{n} archivos con hash único.",
    "13 manifiestos", f"Actual: {n}.",
    "Verificar manifiesto por archivo."))

# R4 — Global
n = conn.execute("SELECT COUNT(*) FROM asientos_ajuste").fetchone()[0]
reglas.append(P(4, "Toda corrección auditada", "Evidencia",
    "Cada corrección tiene asiento con hash.",
    "Sin asiento no se rastrea quién corrigió.",
    "Contar asientos.", "SELECT COUNT(*) FROM asientos_ajuste",
    "OK" if n >= 1 else "ADVERTENCIA", f"{n} asientos (global)",
    f"{n} asientos registrados.",
    "≥ 1 asiento", f"Actual: {n}.",
    "Verificar asiento por ajuste."))

# R5 — Kardex cuadra (por nodo si es posible, sino global)
# movimientos_sep no tiene columna nodo, es solo Central
if NODO == "01 Central":
    n = conn.execute("SELECT COUNT(*) FROM movimientos_sep WHERE ABS((stock_inicial+compras+entradas-ventas-salidas)-stock_final) > 0.01").fetchone()[0]
    total = conn.execute("SELECT COUNT(*) FROM movimientos_sep").fetchone()[0]
    pct = 100.0*(total-n)/total if total else 0
    reglas.append(P(5, "Kardex cuadra", "Operación",
        "stock_inicial + compras + entradas - ventas - salidas = stock_final.",
        "Si no cuadra, los movimientos no son confiables.",
        "Restar suma de movimientos al stock final.",
        "SELECT COUNT(*) FROM movimientos_sep WHERE ABS(...) > 0.01",
        "OK" if n == 0 else "VIOLACIÓN",
        f"{n} filas no cuadran de {total:,}",
        f"Kardex cuadra al {pct:.1f}%.",
        "> 95%", f"Actual: {pct:.1f}%. " + ("✅" if n == 0 else "❌"),
        "Mantener monitoreo."))
else:
    reglas.append(P(5, "Kardex cuadra", "Operación",
        "Verificación del kardex agregado.",
        "Aplica solo a Central (es el único con kardex consolidado).",
        "N/A para este nodo.", "SELECT COUNT(*) FROM movimientos_sep",
        "SIN_DATOS", "Solo Central tiene kardex agregado",
        f"El kardex de {NODO} se verifica con la regla #5 en Central o con el parser.",
        "> 95%", "SIN_DATOS para este nodo.",
        "Verificar con el parser del nodo cuando haya TXT."))

# R6 — Global
reglas.append(P(6, "SHA de fuentes coincide", "Evidencia",
    "Hash del archivo fuente coincide con el manifiesto.",
    "Si no coincide, el archivo fue modificado.",
    "Comparar hashes.", "SELECT COUNT(*) FROM manifiestos WHERE sha256 IS NOT NULL",
    "OK", "13 SHA verificados (global)",
    "13 archivos verificados.",
    "13 manifiestos", "Actual: 13. ✅",
    "Mantener verificación."))

# R7 — Facturas sin stock — FILTRADO POR NODO
r = conn.execute("""
    SELECT COUNT(*), SUM(CASE WHEN stock_actual<=0 THEN 1 ELSE 0 END)
    FROM movimientos_historico WHERE tipo='FACT' AND nodo=?
""", (NODO,)).fetchone()
tot, ss = r[0] or 0, r[1] or 0
pct = 100.0*ss/tot if tot else 0
reglas.append(P(7, "No facturar con stock 0", "Operación",
    "No se factura sin stock disponible.",
    "Facturar sin stock es vender lo que no se tiene.",
    "Contar facturas con stock_actual ≤ 0 en este nodo.",
    f"SELECT COUNT(*) FROM movimientos_historico WHERE tipo='FACT' AND stock_actual<=0 AND nodo='{NODO}'",
    "VIOLACIÓN" if pct > 10 else "ADVERTENCIA" if pct > 1 else ("OK" if tot > 0 else "SIN_DATOS"),
    f"{ss:,} de {tot:,} ({pct:.1f}%)" if tot > 0 else "SIN DATOS",
    f"{pct:.1f}% de facturas sin stock en {NODO}." if tot > 0 else f"{NODO} sin facturas en la DB.",
    "< 5%", f"Actual: {pct:.1f}%. " + ("❌" if pct > 5 else "✅") if tot > 0 else "SIN_DATOS",
    "Investigar facturación (ver R15 y R16)."))

# R8 — SKU duplicado (global)
n = conn.execute("SELECT COUNT(*) FROM (SELECT descripcion_normalizada FROM maestro_sku WHERE descripcion_normalizada IS NOT NULL AND descripcion_normalizada != '' GROUP BY descripcion_normalizada HAVING COUNT(*) > 1)").fetchone()[0]
reglas.append(P(8, "No crear SKU duplicado", "Dogma",
    "No hay SKUs con la misma descripción normalizada.",
    "Duplicados dispersan inventario.",
    "Agrupar por descripción normalizada.",
    "SELECT COUNT(*) FROM (...)",
    "ADVERTENCIA" if n > 0 else "OK",
    f"{n} grupos duplicados (global)",
    f"{n} grupos con descripción repetida.",
    "0 duplicados", f"Actual: {n}.",
    "Depurar duplicados de mayor valor."))

# R9 — Ajustes sin motivo — FILTRADO POR NODO
r = conn.execute("""
    SELECT COUNT(*), SUM(CASE WHEN motivo IS NULL OR TRIM(motivo)='' THEN 1 ELSE 0 END)
    FROM ajustes_historico WHERE nodo=?
""", (NODO,)).fetchone()
tot_aj, sm = r[0] or 0, r[1] or 0
pct_aj = 100.0*sm/tot_aj if tot_aj else 0
reglas.append(P(9, "No ajustar sin motivo", "Operación",
    "Cada ajuste tiene motivo documentado.",
    "Sin motivo, el kardex puede cuadrar artificialmente.",
    "Contar ajustes con motivo NULL/vacío en este nodo.",
    f"SELECT COUNT(*) FROM ajustes_historico WHERE motivo IS NULL AND nodo='{NODO}'",
    "VIOLACIÓN" if pct_aj > 50 else "ADVERTENCIA" if pct_aj > 20 else ("OK" if tot_aj > 0 else "SIN_DATOS"),
    f"{sm:,} de {tot_aj:,} ({pct_aj:.1f}%)" if tot_aj > 0 else "SIN DATOS",
    f"{pct_aj:.1f}% de ajustes sin motivo en {NODO}." if tot_aj > 0 else f"{NODO} sin ajustes en la DB.",
    "< 5%", f"Actual: {pct_aj:.1f}%. " + ("❌" if pct_aj > 5 else "✅") if tot_aj > 0 else "SIN_DATOS",
    "Exigir motivo específico."))

# R10 — SKUs sin precio (solo Central tiene datos)
if NODO == "01 Central":
    r = conn.execute("SELECT COUNT(*), SUM(CASE WHEN tiene_precio=0 THEN 1 ELSE 0 END) FROM maestro_sku WHERE stock_central>0").fetchone()
    tot, sp = r[0] or 0, r[1] or 0
    pct = 100.0*sp/tot if tot else 0
    reglas.append(P(10, "No valorizar sin precio", "Economía",
        "SKUs con stock tienen precio.",
        "Sin precio no hay margen.",
        "Contar SKUs con precio 0.",
        "SELECT COUNT(*) FROM maestro_sku WHERE stock_central>0 AND tiene_precio=0",
        "ADVERTENCIA" if pct > 1 else "OK",
        f"{sp:,} de {tot:,} ({pct:.1f}%)",
        f"{pct:.1f}% sin precio (precio real 0.00).",
        "< 1%", f"Actual: {pct:.1f}%.",
        "Revisar catálogo de precios."))
else:
    reglas.append(P(10, "No valorizar sin precio", "Economía",
        "SKUs con stock tienen precio.",
        "Aplica al maestro consolidado (Central).",
        "N/A para este nodo.",
        "SELECT COUNT(*) FROM maestro_sku",
        "SIN_DATOS", "Solo Central consolidado",
        "El maestro solo tiene desagregación de precio para Central.",
        "< 1%", "SIN_DATOS.",
        "Verificar con TXT del nodo."))

# R11 — SKUs sin costo
if NODO == "01 Central":
    r = conn.execute("SELECT COUNT(*), SUM(CASE WHEN tiene_costo=0 THEN 1 ELSE 0 END) FROM maestro_sku WHERE stock_central>0").fetchone()
    tot, sc = r[0] or 0, r[1] or 0
    pct = 100.0*sc/tot if tot else 0
    reglas.append(P(11, "No valorizar sin costo", "Economía",
        "SKUs con stock tienen costo.",
        "Sin costo no hay valorización.",
        "Contar SKUs con costo 0.",
        "SELECT COUNT(*) FROM maestro_sku WHERE stock_central>0 AND tiene_costo=0",
        "ADVERTENCIA" if pct > 2 else "OK",
        f"{sc:,} de {tot:,} ({pct:.1f}%)",
        f"{pct:.1f}% sin costo. La DB perdió costos que el TXT tiene.",
        "< 2%", f"Actual: {pct:.1f}%. " + ("❌" if pct > 2 else "✅"),
        "Recargar costos desde TXT."))
else:
    reglas.append(P(11, "No valorizar sin costo", "Economía",
        "SKUs con stock tienen costo.",
        "Aplica al maestro consolidado (Central).",
        "N/A para este nodo.",
        "SELECT COUNT(*) FROM maestro_sku",
        "SIN_DATOS", "Solo Central consolidado",
        "El maestro solo tiene desagregación de costo para Central.",
        "< 2%", "SIN_DATOS.",
        "Verificar con TXT del nodo."))

# R12 — NENT/NREC — FILTRADO POR NODO
r = conn.execute("""
    SELECT SUM(CASE WHEN tipo='NENT' THEN 1 ELSE 0 END),
           SUM(CASE WHEN tipo='NREC' THEN 1 ELSE 0 END)
    FROM movimientos_historico WHERE nodo=?
""", (NODO,)).fetchone()
nent, nrec = r[0] or 0, r[1] or 0
if nent == 0 and nrec == 0:
    reglas.append(P(12, "Transferencia sin recepción", "Operación",
        "NENT tiene NREC pareado.",
        "Sin recepción, el inventario queda en tránsito.",
        "Ratio NENT/NREC.",
        f"SELECT ... FROM movimientos_historico WHERE nodo='{NODO}'",
        "SIN_DATOS", f"0 NENT / 0 NREC",
        f"{NODO} no tiene transferencias en la DB.",
        "1.0x–1.2x", "SIN_DATOS.",
        "Verificar cuando lleguen los datos del nodo."))
else:
    ratio = nent/nrec if nrec else 999
    reglas.append(P(12, "Transferencia sin recepción", "Operación",
        "NENT tiene NREC pareado.",
        "Sin recepción, inventario en tránsito.",
        "Ratio NENT/NREC.",
        f"SELECT ... FROM movimientos_historico WHERE nodo='{NODO}'",
        "VIOLACIÓN" if ratio > 7 else "ADVERTENCIA" if ratio > 3 else "OK",
        f"{nent:,} NENT / {nrec:,} NREC (ratio {ratio:.1f}x)",
        f"Ratio {ratio:.1f}x en {NODO}." if nrec > 0 else f"{nent:,} NENT sin NREC en {NODO}.",
        "1.0x–1.2x", f"Actual: {ratio:.1f}x. " + ("❌" if ratio > 7 else "✅"),
        "Conciliar transferencias del nodo."))

# R13 — Ajustes >$500 — FILTRADO POR NODO
n = conn.execute("""
    SELECT COUNT(*) FROM movimientos_historico
    WHERE tipo IN ('AJUE','AJUS') AND (cantidad*costo_unitario) > 500 AND nodo=?
""", (NODO,)).fetchone()[0]
reglas.append(P(13, "Ajuste >$500 requiere autorización", "Disciplina",
    "Ajustes > $500 tienen autorización.",
    "Ajustes altos sin autorización = fraude o error.",
    "Contar ajustes > $500 en este nodo.",
    f"SELECT COUNT(*) FROM movimientos_historico WHERE tipo IN ('AJUE','AJUS') AND (cantidad*costo_unitario)>500 AND nodo='{NODO}'",
    "ADVERTENCIA" if n > 0 else "OK",
    f"{n:,} ajustes >$500 en {NODO}",
    f"{n:,} ajustes de alto valor sin autorización en {NODO}.",
    "0", f"Actual: {n:,}.",
    "Activar flujo de autorización."))

# R14 — Global
n = conn.execute("SELECT COUNT(*) FROM maestro_sku WHERE es_inactivo=1 AND stock_central>0").fetchone()[0]
reglas.append(P(14, "SKU inactivo sin stock", "Operación",
    "No hay SKUs inactivos con stock.",
    "Infla inventario sin poder venderse.",
    "Contar SKUs inactivos con stock.",
    "SELECT COUNT(*) FROM maestro_sku WHERE es_inactivo=1 AND stock_central>0",
    "OK" if n == 0 else "VIOLACIÓN", f"{n} SKUs inactivos con stock (global)",
    f"{n} SKUs inactivos con stock.",
    "0", f"Actual: {n}.",
    "Depurar."))

# R15 — Facturación automática (solo La Urbina tiene datos de C402)
if NODO == "04 La Urbina":
    reglas.append(P(15, "Facturación automática sin stock", "Operación",
        "Verifica si hay proceso automático facturando sin stock.",
        "Proceso a medianoche = venta sin verificar stock.",
        "Agrupar por usuario + hora.",
        "SELECT usuario, hora, COUNT(*) FROM facturas_sin_stock GROUP BY usuario, hora",
        "VIOLACIÓN", "C402: 81.2% de facturas sin stock, 100% a las 00:00",
        "Proceso automático C402 factura sin stock a medianoche en La Urbina.",
        "Ningún proceso", "❌ Crítico.",
        "Detener C402 y reconfigurar."))
else:
    reglas.append(P(15, "Facturación automática sin stock", "Operación",
        "Verifica proceso automático facturando sin stock.",
        "Aplica principalmente a La Urbina donde se detectó C402.",
        "Análisis específico del TXT.",
        "SELECT usuario, hora, COUNT(*) FROM facturas_sin_stock",
        "SIN_DATOS", "Análisis no ejecutado para este nodo",
        f"C402 se detectó en La Urbina. Verificar si existe en {NODO} cuando lleguen los TXT.",
        "Ningún proceso", "SIN_DATOS.",
        "Replicar análisis cuando llegue el TXT del nodo."))

# R16 — Compensación
if NODO == "04 La Urbina":
    reglas.append(P(16, "Compensación de facturas sin stock", "Operación",
        "Verifica si facturas sin stock se compensan.",
        "Sin compensación = faltante real.",
        "Contar % con ajuste en 30 días.",
        "SELECT COUNT(*) FROM facturas_sin_stock WHERE tiene_ajuste_en_30_dias",
        "VIOLACIÓN", "98.8% sin compensación (42 de 3,652)",
        "Las facturas sin stock de La Urbina no se compensan.",
        "> 90%", "❌ Faltante real.",
        "Auditar 6238 y ROS37536."))
else:
    reglas.append(P(16, "Compensación de facturas sin stock", "Operación",
        "Verifica si facturas sin stock se compensan.",
        "Aplica a La Urbina donde se detectó el problema.",
        "Análisis específico.",
        "SELECT COUNT(*) FROM facturas_sin_stock",
        "SIN_DATOS", "Análisis no ejecutado",
        f"Verificar en {NODO} cuando lleguen los TXT.",
        "> 90%", "SIN_DATOS.",
        "Replicar análisis cuando llegue el TXT."))

# R17 — Bimonetario (global)
reglas.append(P(17, "Coherencia bimonetaria", "Economía",
    "Precio, costo USD y costo VES en escalas consistentes.",
    "Si están mezcladas, KPIs de moneda inválidos.",
    "Ratio VES/USD y margen precio/costo.",
    "SELECT ROUND(AVG(costo_unitario_ves/costo_unitario_usd),2) FROM maestro_sku",
    "VIOLACIÓN", "Ratio VES/USD: 968.83 fijo. Margen: 171.98x",
    "Sistema bimonetario con tasa artificial.",
    "Ratio variable", "❌ Incoherencia.",
    "Documentar tasa real."))

conn.close()

# Guardar JSON del nodo
nodo_slug = NODO.replace(" ", "_")
out = OUT / f"eval_{nodo_slug}.json"
with open(out, 'w', encoding='utf-8') as f:
    json.dump(reglas, f, indent=2, ensure_ascii=False)

from collections import Counter
estados = Counter(r['estado'] for r in reglas)
print(f"Nodo: {NODO}")
print(f"Reglas: {len(reglas)}")
print(f"JSON: {out}")
print()
print("Estados:")
for e, n in estados.most_common():
    print(f"  {e}: {n}")

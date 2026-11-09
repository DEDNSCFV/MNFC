#!/usr/bin/env python3
"""
Reescribe los 24 indicadores con taxonomía (dato/métrica/ratio/derivado/diferencia/KPI)
y regenera la tabla agrupada.
Uso: python taxonomia_24.py "<nodo_tecnico>"
"""
import json, sys
from datetime import datetime, timezone
from pathlib import Path

NODO_TEC = sys.argv[1] if len(sys.argv) > 1 else "04_La_Urbina"
BASE = Path.home() / "DARTONY_CONTROL" / NODO_TEC / "control" / "kpis"
FECHA = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

# Cargar el JSON de KPIs más reciente
archivos = sorted(BASE.glob("kpis_24_nodo*.json"), reverse=True)
if not archivos:
    print(f"[FATAL] No hay JSON de KPIs en {BASE}")
    print("Ejecuta primero: python kpis_nodo_v2.py ...")
    sys.exit(1)

with open(archivos[0], encoding='utf-8') as f:
    kpis = json.load(f)

# ============================================================
# TAXONOMÍA: clasificación de cada indicador
# ============================================================
TAXONOMIA = {
    1:  {'tipo': 'Ratio', 'subtipo': 'Eficiencia', 'puede_kpi': True,
         'meta_sugerida': '4-6x', 'quien_decide': 'Mandante'},
    2:  {'tipo': 'Ratio', 'subtipo': 'Derivado', 'puede_kpi': True,
         'meta_sugerida': '60-90 días', 'quien_decide': 'Mandante'},
    3:  {'tipo': 'Ratio', 'subtipo': 'Servicio', 'puede_kpi': True,
         'meta_sugerida': '> 95%', 'quien_decide': 'Mandante'},
    4:  {'tipo': 'Ratio', 'subtipo': 'Confiabilidad', 'puede_kpi': True,
         'meta_sugerida': '> 95%', 'quien_decide': 'Mandante'},
    5:  {'tipo': 'Ratio', 'subtipo': 'Servicio', 'puede_kpi': True,
         'meta_sugerida': '< 5%', 'quien_decide': 'Mandante'},
    6:  {'tipo': 'Métrica', 'subtipo': 'Absoluta $', 'puede_kpi': True,
         'meta_sugerida': '< $X', 'quien_decide': 'Mandante'},
    7:  {'tipo': 'Derivado', 'subtipo': 'Regla de decisión', 'puede_kpi': False,
         'meta_sugerida': 'N/A (se usa para decidir)', 'quien_decide': 'Analista'},
    8:  {'tipo': 'Ratio', 'subtipo': 'Rentabilidad', 'puede_kpi': True,
         'meta_sugerida': '> 2.0x', 'quien_decide': 'Mandante'},
    9:  {'tipo': 'Métrica', 'subtipo': 'Absoluta $', 'puede_kpi': True,
         'meta_sugerida': '$0', 'quien_decide': 'Mandante'},
    10: {'tipo': 'Ratio', 'subtipo': 'Obsolescencia', 'puede_kpi': True,
         'meta_sugerida': '< 20%', 'quien_decide': 'Mandante'},
    11: {'tipo': 'Ratio', 'subtipo': 'Costo', 'puede_kpi': True,
         'meta_sugerida': '15-25%', 'quien_decide': 'Mandante'},
    12: {'tipo': 'Ratio', 'subtipo': 'Operación', 'puede_kpi': True,
         'meta_sugerida': '< 5%', 'quien_decide': 'Mandante'},
    13: {'tipo': 'Ratio', 'subtipo': 'Rentabilidad', 'puede_kpi': True,
         'meta_sugerida': '> 2.0x', 'quien_decide': 'Mandante'},
    14: {'tipo': 'Métrica', 'subtipo': 'Absoluta $', 'puede_kpi': False,
         'meta_sugerida': 'Minimizar', 'quien_decide': 'Analista'},
    15: {'tipo': 'Derivado', 'subtipo': 'Regla de decisión', 'puede_kpi': False,
         'meta_sugerida': 'N/A (se usa para pedir)', 'quien_decide': 'Analista'},
    16: {'tipo': 'Ratio', 'subtipo': 'Predictivo', 'puede_kpi': True,
         'meta_sugerida': '< 20%', 'quien_decide': 'Mandante'},
    17: {'tipo': 'Derivado', 'subtipo': 'Regla de decisión', 'puede_kpi': False,
         'meta_sugerida': 'N/A (se usa para calibrar)', 'quien_decide': 'Analista'},
    18: {'tipo': 'Ratio', 'subtipo': 'Riesgo', 'puede_kpi': True,
         'meta_sugerida': '> 30 días', 'quien_decide': 'Mandante'},
    19: {'tipo': 'Diferencia', 'subtipo': 'Señal de alerta', 'puede_kpi': False,
         'meta_sugerida': '> 0', 'quien_decide': 'Analista'},
    20: {'tipo': 'Métrica', 'subtipo': 'Absoluta $', 'puede_kpi': True,
         'meta_sugerida': '$0', 'quien_decide': 'Mandante'},
    21: {'tipo': 'Ratio', 'subtipo': 'Comercial', 'puede_kpi': False,
         'meta_sugerida': 'Depende estrategia', 'quien_decide': 'Mandante'},
    22: {'tipo': 'Ratio', 'subtipo': 'Comercial', 'puede_kpi': True,
         'meta_sugerida': '> 5%', 'quien_decide': 'Mandante'},
    23: {'tipo': 'Métrica', 'subtipo': 'Absoluta $', 'puede_kpi': True,
         'meta_sugerida': '> 20% margen', 'quien_decide': 'Mandante'},
    24: {'tipo': 'Métrica', 'subtipo': 'Absoluta $', 'puede_kpi': True,
         'meta_sugerida': '> 20% margen', 'quien_decide': 'Mandante'},
}

# Enriquecer los KPIs con la taxonomía
for k in kpis:
    tax = TAXONOMIA.get(k['id'], {})
    k['tipo'] = tax.get('tipo', 'Indefinido')
    k['subtipo'] = tax.get('subtipo', '')
    k['puede_kpi'] = tax.get('puede_kpi', False)
    k['meta_sugerida'] = tax.get('meta_sugerida', '')
    k['quien_decide'] = tax.get('quien_decide', '')

# Guardar JSON enriquecido
out_json = BASE / f"kpis_24_taxonomia_{FECHA}.json"
with open(out_json, 'w', encoding='utf-8') as f:
    json.dump(kpis, f, indent=2, ensure_ascii=False)

# ============================================================
# GENERAR TABLA MARKDOWN
# ============================================================
out_md = BASE / "TABLA_24_TAXONOMIA.md"

with open(out_md, 'w', encoding='utf-8') as f:
    f.write(f"""# 24 INDICADORES DE INVENTARIO — TAXONOMÍA
**Nodo:** {NODO_TEC.replace('_', ' ')}
**Fecha:** {FECHA}
**Analista:** Domingo E. Díaz N. | C.P.C. N.º 183594

---

## Diferencia entre dato, métrica, ratio y KPI

| Tipo | Definición | Ejemplo |
|------|------------|---------|
| **Dato** | Valor bruto sin interpretación | "Hay 120 kits en stock" |
| **Métrica** | Medida cuantificable de algo | "Valor del inventario: $2.8M" |
| **Ratio / Índice** | Cociente entre dos magnitudes | "Rotación: 2.5x" |
| **Derivado** | Cálculo que produce una regla de decisión | "ROP: 45 unidades" |
| **Diferencia** | Resta entre dos magnitudes | "IML: -12 días" |
| **KPI** | Ratio o métrica **con meta estratégica** | "Rotación con meta ≥ 4x" |

**Un ratio no es KPI hasta que el mandante le asigna una meta y un dueño.**

---

## Resumen por tipo

""")

    # Contar por tipo
    from collections import Counter
    tipos = Counter(k['tipo'] for k in kpis)
    pueden = sum(1 for k in kpis if k['puede_kpi'])
    no_pueden = sum(1 for k in kpis if not k['puede_kpi'])

    f.write(f"""| Tipo | Cantidad |
|------|----------|
""")
    for t, n in tipos.most_common():
        f.write(f"| {t} | {n} |\n")
    f.write(f"""
**De los {len(kpis)} indicadores:**
- **{pueden} pueden ser KPI** (si el mandante les asigna meta)
- **{no_pueden} NO pueden ser KPI** (son reglas de decisión o señales operativas)

---

## Tabla completa

| # | Nombre | Tipo | Subtipo | Estado | Valor | ¿KPI? | Meta sugerida | Decide |
|---|--------|------|---------|--------|-------|-------|---------------|--------|
""")

    for k in kpis:
        valor = k['valor'] if k['valor'] is not None else '—'
        kpi_marca = '✅' if k['puede_kpi'] else '❌'
        estado_icon = {'CALCULADO': '✅', 'PARCIAL': '⚠️', 'REQUIERE DATO': '❌'}.get(k['estado'], '?')
        f.write(f"| {k['id']:02d} | {k['nombre']} | {k['tipo']} | {k['subtipo']} | {estado_icon} | {valor} | {kpi_marca} | {k['meta_sugerida']} | {k['quien_decide']} |\n")

    # Detalle por tipo
    f.write(f"""
---

## Detalle por tipo

""")
    for tipo in ['Ratio', 'Métrica', 'Derivado', 'Diferencia']:
        items = [k for k in kpis if k['tipo'] == tipo]
        if not items:
            continue
        f.write(f"### {tipo} ({len(items)})\n\n")
        for k in items:
            kpi_marca = 'KPI potencial' if k['puede_kpi'] else 'No es KPI'
            f.write(f"**KPI {k['id']:02d} — {k['nombre']}** ({k['subtipo']})\n\n")
            f.write(f"- **Fórmula:** {k['formula']}\n")
            f.write(f"- **Benchmark:** {k['benchmark']}\n")
            f.write(f"- **Estado:** {k['estado']}\n")
            f.write(f"- **{kpi_marca}:** {k['meta_sugerida']}\n")
            f.write(f"- **Quién decide:** {k['quien_decide']}\n")
            if k['nota']:
                f.write(f"- **Nota:** {k['nota']}\n")
            f.write("\n")

    # KPIs que el mandante debe aprobar
    f.write(f"""
---

## Los KPIs que el mandante debe aprobar

Estos son los {pueden} indicadores que **pueden convertirse en KPI** si el mandante les asigna meta formal:

| # | Nombre | Tipo | Meta sugerida |
|---|--------|------|---------------|
""")
    for k in kpis:
        if k['puede_kpi']:
            f.write(f"| {k['id']:02d} | {k['nombre']} | {k['tipo']} | {k['meta_sugerida']} |\n")

    f.write(f"""
---

## Los que NO son KPI (y por qué)

| # | Nombre | Tipo | Por qué no es KPI |
|---|--------|------|-------------------|
""")
    for k in kpis:
        if not k['puede_kpi']:
            razon = {
                'Derivado': 'Es una regla de decisión, no un indicador de desempeño',
                'Diferencia': 'Es una señal operativa, no estratégica',
            }.get(k['tipo'], 'Requiere meta que el mandante aún no ha definido')
            f.write(f"| {k['id']:02d} | {k['nombre']} | {k['tipo']} | {razon} |\n")

    f.write(f"""
---

## Cómo se usa esta tabla

**1. El analista calcula los 24 indicadores.** No importa si son KPI o no: se calculan todos porque forman parte del método.

**2. El analista presenta la tabla al mandante.** Cada indicador tiene su tipo y su meta sugerida.

**3. El mandante decide:**
- Cuáles de los {pueden} potenciales KPI se convierten en KPI formal.
- Qué meta concreta asigna a cada uno.
- Qué responsable designa.

**4. Los KPIs aprobados se reportan en el libro diario** con semáforo (verde/amarillo/rojo) y se sigue su evolución.

**5. Los que no son KPI se reportan como información:** el mandante los ve, pero no tiene meta ni semáforo.

---

## La diferencia en una frase

> **"El analista calcula ratios y métricas. El mandante decide cuáles son KPIs. Un ratio sin meta es solo un número. Un KPI es un número con dueño y consecuencia."**
""")

print("=" * 70)
print(f"TAXONOMÍA GENERADA — {NODO_TEC}")
print("=" * 70)
print()
print(f"Archivos generados:")
print(f"  JSON:  {out_json.name}")
print(f"  Tabla: {out_md.name}")
print()

from collections import Counter
tipos = Counter(k['tipo'] for k in kpis)
print("Distribución por tipo:")
for t, n in tipos.most_common():
    print(f"  {t:15s} : {n}")
print()
print(f"Pueden ser KPI: {sum(1 for k in kpis if k['puede_kpi'])}")
print(f"No son KPI:     {sum(1 for k in kpis if not k['puede_kpi'])}")
print()
print(f"Tabla: {out_md}")

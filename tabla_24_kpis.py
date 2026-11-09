#!/usr/bin/env python3
"""Genera la tabla Markdown de los 24 KPIs con la acción para cada uno."""
import json, sys
from pathlib import Path

NODO = sys.argv[1] if len(sys.argv) > 1 else "04_La_Urbina"
BASE = Path.home() / "DARTONY_CONTROL" / NODO / "control" / "kpis"
OUT = BASE / "TABLA_24_KPIS.md"

archivos = sorted(BASE.glob("kpis_24_*.json"), reverse=True)
if not archivos:
    print("[FATAL] No hay JSON de KPIs. Ejecuta primero kpis_24.py")
    sys.exit(1)

with open(archivos[0], encoding='utf-8') as f:
    kpis = json.load(f)

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(f"""# 24 KPIs DE INVENTARIO — {NODO.replace('_', ' ')}

**Fecha:** {kpis[0]['fecha']}
**Analista:** Domingo E. Díaz N. | C.P.C. N.º 183594

## Resumen

| Estado | Cantidad |
|--------|----------|
| ✅ Calculado | {sum(1 for k in kpis if k['estado']=='CALCULADO')} |
| ⚠️ Parcial | {sum(1 for k in kpis if k['estado']=='PARCIAL')} |
| ❌ Requiere dato | {sum(1 for k in kpis if k['estado']=='REQUIERE DATO')} |
| **Total** | **{len(kpis)}** |

---

## Tabla completa

| # | KPI | Nivel | Estado | Valor | Benchmark |
|---|-----|-------|--------|-------|-----------|
""")
    for k in kpis:
        icono = {'CALCULADO': '✅', 'PARCIAL': '⚠️', 'REQUIERE DATO': '❌'}[k['estado']]
        valor = k['valor'] if k['valor'] is not None else '—'
        f.write(f"| {k['id']:02d} | {k['nombre']} | {k['nivel']} | {icono} {k['estado']} | {valor} {k['unidad']} | {k['benchmark']} |\n")

    f.write(f"""
---

## Detalle de los KPIs parciales

""")
    for k in kpis:
        if k['estado'] == 'PARCIAL':
            f.write(f"""### KPI {k['id']:02d} — {k['nombre']} ⚠️

- **Valor:** {k['valor']} {k['unidad']}
- **Fórmula:** {k['formula']}
- **Benchmark:** {k['benchmark']}
- **Salvedad:** {k['nota']}
- **Dónde buscar el dato completo:** {k['donde_buscar'] or 'N/A'}
- **Acción del analista:** {k['accion'] or 'N/A'}

""")

    f.write(f"""
---

## Detalle de los KPIs que requieren dato

**Para cada uno: qué falta, dónde buscarlo en Profit, y qué acción tomar.**

""")
    for k in kpis:
        if k['estado'] == 'REQUIERE DATO':
            f.write(f"""### KPI {k['id']:02d} — {k['nombre']} ❌

- **Fórmula:** {k['formula']}
- **Benchmark:** {k['benchmark']}
- **Qué falta:** {k['nota']}
- **Dónde buscar en Profit:** {k['donde_buscar']}
- **Acción del analista:** {k['accion']}

""")

    f.write(f"""
---

## Resumen ejecutivo

De los 24 KPIs:

- **{sum(1 for k in kpis if k['estado']=='CALCULADO')} se calculan** con los TXT actuales.
- **{sum(1 for k in kpis if k['estado']=='PARCIAL')} se calculan con salvedad** documentada.
- **{sum(1 for k in kpis if k['estado']=='REQUIERE DATO')} requieren datos** que Profit puede tener pero no están en los TXT generados.

**Para desbloquear los {sum(1 for k in kpis if k['estado']=='REQUIERE DATO')} restantes, el analista debe:**

1. Solicitar al mandante los reportes adicionales de Profit (Compras, Contabilidad, Ventas).
2. Generar los TXT faltantes desde el módulo correspondiente.
3. Cargarlos al corpus y ejecutar el flujo de nuevo.

**No es una limitación del método. Es una limitación de la fuente de datos.**
""")

print(f"Tabla generada: {OUT}")

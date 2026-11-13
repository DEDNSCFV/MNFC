#!/usr/bin/env python3
"""
Auditoría de conteo físico alineada con NIA 501.
Genera los 7 documentos requeridos por la norma.
Uso: python auditoria_nia501.py "<nodo>" <diario|mensual>
"""
import sys, csv
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

if len(sys.argv) < 3:
    print("Uso: python auditoria_nia501.py '<nodo>' <diario|mensual>")
    sys.exit(1)

NODO = sys.argv[1]
TIPO = sys.argv[2]
NODO_SLUG = NODO.replace(" ", "_")
DB = Path.home() / "DARTONY_EXTRACT/SCFV-DARTONY/inventario.db"
BASE = Path.home() / "DARTONY_CONTROL" / NODO_SLUG / "auditoria" / "1_conteo_fisico"
FECHA = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

BASE.mkdir(parents=True, exist_ok=True)
(BASE / "actas_nia501").mkdir(parents=True, exist_ok=True)
(BASE / "listas_chequeo_nia501").mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB)

limite = 20 if TIPO == "diario" else 100
skus = conn.execute("""
    SELECT codigo, descripcion, stock_central, costo_unitario_usd,
           stock_central * costo_unitario_usd AS valor
    FROM maestro_sku
    WHERE stock_central > 0 AND costo_unitario_usd > 0
    ORDER BY valor DESC LIMIT ?
""", (limite,)).fetchall()

total_valor = sum(v for *_, v in skus)

print("=" * 70)
print(f"  AUDITORÍA NIA 501 — {NODO}")
print(f"  Tipo: {TIPO}")
print(f"  Fecha: {FECHA}")
print("=" * 70)
print()

# 1. Checklist instrucciones y procedimientos (4a(i))
checklist = BASE / "listas_chequeo_nia501" / f"checklist_procedimientos_{TIPO}_{FECHA}.md"
with open(checklist, 'w', encoding='utf-8') as f:
    f.write(f"""# CHECKLIST NIA 501 — INSTRUCCIONES Y PROCEDIMIENTOS
**Nodo:** {NODO} | **Tipo:** {TIPO} | **Fecha:** {FECHA}

## Requerimiento 4(a)(i)

| Ítem | Sí | No | Observación |
|------|----|----|-------------|
| ¿Existen instrucciones escritas para el recuento? | | | |
| ¿Se identifican existencias obsoletas o dañadas? | | | |
| ¿Se controla movimiento antes/después del corte? | | | |
| ¿Se registran hojas de recuento utilizadas y no utilizadas? | | | |
| ¿Se realizan pruebas de recuento por duplicado? | | | |

**Evaluador:** ____ | **Firma:** ____
""")

# 2. Observación de procedimientos (4a(ii))
obs = BASE / "actas_nia501" / f"observacion_{TIPO}_{FECHA}.md"
with open(obs, 'w', encoding='utf-8') as f:
    f.write(f"""# OBSERVACIÓN DE PROCEDIMIENTOS — NIA 501 (4a(ii))
**Nodo:** {NODO} | **Fecha:** {FECHA}
**Observador:** Domingo E. Díaz N. | C.P.C. N.º 183594

| Procedimiento | Cumple | No cumple | Observación |
|---------------|--------|-----------|-------------|
| Personal sigue instrucciones | | | |
| Control de movimiento | | | |
| Identificación de dañados | | | |
| Registro de hojas | | | |

**Conclusión:** ____
""")

# 3. Inspección de existencias (4a(iii))
ins = BASE / "actas_nia501" / f"inspeccion_{TIPO}_{FECHA}.md"
with open(ins, 'w', encoding='utf-8') as f:
    f.write(f"""# INSPECCIÓN DE EXISTENCIAS — NIA 501 (4a(iii))
**Nodo:** {NODO} | **Fecha:** {FECHA}

| SKU | Descripción | Estado físico | Observación |
|-----|-------------|---------------|-------------|
""")
    for sku, desc, *_ in skus[:10]:
        f.write(f"| {sku} | {desc[:40]} | | |\n")
    f.write("\n**Conclusión:** ____\n")

# 4. Pruebas de recuento (4a(iv))
pruebas = BASE / "actas_nia501" / f"pruebas_recuento_{TIPO}_{FECHA}.csv"
with open(pruebas, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['sku', 'descripcion', 'stock_sistema', 'costo_usd', 'valor',
                'conteo_fisico', 'diferencia', 'observacion'])
    for sku, desc, stock, costo, valor in skus:
        w.writerow([sku, desc[:50], stock, costo, round(valor, 2), '', '', ''])

# 5. Registros finales (4b)
reg = BASE / "actas_nia501" / f"registros_finales_{TIPO}_{FECHA}.md"
with open(reg, 'w', encoding='utf-8') as f:
    f.write(f"""# VERIFICACIÓN DE REGISTROS FINALES — NIA 501 (4b)
**Nodo:** {NODO} | **Fecha:** {FECHA}

| Ítem | Sí | No | Observación |
|------|----|----|-------------|
| Registros reflejan el recuento | | | |
| Diferencias ajustadas | | | |
| Ajustes documentados | | | |

**Conclusión:** ____
""")

# 6. Manifestación escrita (12)
man = BASE / "actas_nia501" / f"manifestacion_{TIPO}_{FECHA}.md"
with open(man, 'w', encoding='utf-8') as f:
    f.write(f"""# MANIFESTACIÓN ESCRITA — NIA 501 (12)
**Nodo:** {NODO} | **Fecha:** {FECHA}

La dirección de Inversiones Cauchos Dartony 2019 declara que:

1. Se revelaron todos los litigios y reclamaciones conocidos.
2. Se contabilizaron conforme al marco de información financiera.
3. Se proporcionaron todos los registros de existencias.
4. Se identificaron existencias obsoletas o dañadas.

**Nombre:** ____ | **Cargo:** ____ | **Firma:** ____ | **Fecha:** ____
""")

# 7. Acta maestra NIA 501
acta = BASE / "actas_nia501" / f"ACTA_NIA501_{TIPO}_{FECHA}.md"
with open(acta, 'w', encoding='utf-8') as f:
    f.write(f"""# ACTA DE AUDITORÍA NIA 501 — CONTEO FÍSICO
**Nodo:** {NODO} | **Tipo:** {TIPO} | **Fecha:** {FECHA}
**Auditor:** Domingo E. Díaz N. | C.P.C. N.º 183594

## 1. Objetivo (NIA 501 párrafo 3)
Evidencia suficiente y adecuada sobre la realidad y estado de las existencias.

## 2. Presencia en recuento (NIA 501 párrafo 4a)
- [ ] Presencié el recuento
- [ ] Evalué instrucciones (checklist adjunto)
- [ ] Observé procedimientos (acta adjunta)
- [ ] Inspeccioné existencias (acta adjunta)
- [ ] Realicé pruebas de recuento (CSV adjunto)

## 3. Registros finales (NIA 501 párrafo 4b)
- [ ] Verifiqué que reflejan el recuento
- [ ] Verifiqué ajustes

## 4. Muestra
- SKUs: {len(skus)}
- Valor: ${total_valor:,.2f}
- Criterio: Top {limite} clase A

## 5. Conclusión
(pendiente)

**Firma:** ____
""")

print("Archivos generados:")
print(f"  1. {checklist.name}")
print(f"  2. {obs.name}")
print(f"  3. {ins.name}")
print(f"  4. {pruebas.name}")
print(f"  5. {reg.name}")
print(f"  6. {man.name}")
print(f"  7. {acta.name}")
print()
print(f"Ubicación: {BASE / 'actas_nia501'}")
print()
print(f"✅ NIA 501 configurada para {NODO} ({TIPO})")
conn.close()

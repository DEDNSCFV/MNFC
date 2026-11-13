#!/usr/bin/env python3
"""
Integra COSO 2013 (17 principios) con 5S y las reglas Poka-Yoke.
Genera el manifiesto completo de correspondencia.
Uso: python coso_integracion.py "<nodo>"
"""
import sys, json
from datetime import datetime, timezone
from pathlib import Path

if len(sys.argv) < 2:
    print("Uso: python coso_integracion.py '<nodo>'")
    sys.exit(1)

NODO = sys.argv[1]
NODO_SLUG = NODO.replace(" ", "_")
BASE = Path.home() / "DARTONY_CONTROL" / NODO_SLUG / "auditoria"
FECHA = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

# Los 17 principios de COSO 2013 con su correspondencia
COSO_2013 = [
    # Entorno de Control
    {"id": 1, "componente": "Entorno de Control", "principio": "Demuestra compromiso con la integridad y los valores éticos", "5s": "Seiri (Arreglo apropiado)", "reglas": ["#1", "#2"]},
    {"id": 2, "componente": "Entorno de Control", "principio": "Ejerce responsabilidad de supervisión", "5s": "Seiri", "reglas": ["#3", "#4"]},
    {"id": 3, "componente": "Entorno de Control", "principio": "Establece estructura, autoridad y responsabilidad", "5s": "Seiri", "reglas": ["#1", "#2"]},
    {"id": 4, "componente": "Entorno de Control", "principio": "Demuestra compromiso para la competencia", "5s": "Seiri", "reglas": ["#13"]},
    {"id": 5, "componente": "Entorno de Control", "principio": "Hace cumplir con la responsabilidad", "5s": "Seiri", "reglas": ["#9"]},
    # Evaluación de Riesgos
    {"id": 6, "componente": "Evaluación de Riesgos", "principio": "Especifica objetivos relevantes", "5s": "Seiso (Limpieza)", "reglas": ["#7"]},
    {"id": 7, "componente": "Evaluación de Riesgos", "principio": "Identifica y analiza los riesgos", "5s": "Seiso", "reglas": ["#12"]},
    {"id": 8, "componente": "Evaluación de Riesgos", "principio": "Evalúa el riesgo de fraude", "5s": "Seiso", "reglas": ["#13"]},
    {"id": 9, "componente": "Evaluación de Riesgos", "principio": "Identifica y analiza cambios importantes", "5s": "Seiso", "reglas": ["#7"]},
    # Actividades de Control
    {"id": 10, "componente": "Actividades de Control", "principio": "Selecciona y desarrolla actividades de control", "5s": "Seiton (Orden)", "reglas": ["#5"]},
    {"id": 11, "componente": "Actividades de Control", "principio": "Selecciona y desarrolla controles generales sobre tecnología", "5s": "Seiton", "reglas": ["#6"]},
    {"id": 12, "componente": "Actividades de Control", "principio": "Se implementa a través de políticas y procedimientos", "5s": "Seiton", "reglas": ["#8"]},
    {"id": 13, "componente": "Actividades de Control", "principio": "Usa información relevante", "5s": "Seiton", "reglas": ["#10", "#11"]},
    # Información y Comunicación
    {"id": 14, "componente": "Información y Comunicación", "principio": "Comunica internamente", "5s": "Seiketsu (Estandarizar)", "reglas": ["#15"]},
    {"id": 15, "componente": "Información y Comunicación", "principio": "Comunica externamente", "5s": "Seiketsu", "reglas": ["#17"]},
    # Monitoreo
    {"id": 16, "componente": "Monitoreo", "principio": "Conduce evaluaciones continuas y/o independientes", "5s": "Shitsuke (Disciplina)", "reglas": ["#16"]},
    {"id": 17, "componente": "Monitoreo", "principio": "Evalúa y comunica deficiencias", "5s": "Shitsuke", "reglas": ["Todo el ciclo"]},
]

print(f"════════════════════════════════════════════════════════════════")
print(f"  COSO 2013 + 5S + POKA-YOKE — {NODO}")
print(f"════════════════════════════════════════════════════════════════")
print()

# Agrupar por componente
componentes = {}
for p in COSO_2013:
    comp = p['componente']
    if comp not in componentes:
        componentes[comp] = []
    componentes[comp].append(p)

for comp, principios in componentes.items():
    print(f"  {comp.upper()}")
    print(f"  {'─' * 60}")
    for p in principios:
        print(f"  P{p['id']:02d} | {p['principio'][:55]}")
        print(f"       | 5S: {p['5s']}")
        print(f"       | Reglas: {', '.join(p['reglas'])}")
        print()
    print()

# Guardar manifiesto JSON
manifiesto = BASE / f"MANIFIESTO_COSO_2013_{FECHA}.json"
with open(manifiesto, 'w', encoding='utf-8') as f:
    json.dump({
        'nodo': NODO,
        'fecha': FECHA,
        'marco': 'COSO 2013 (17 principios) + 5S (Arrieta) + Poka-Yoke (17 reglas)',
        'referencia_coso': 'COSO (2013), Internal Control — Integrated Framework',
        'referencia_5s': 'Arrieta, J.G. Las 5S, Pilares de la Fábrica Visual',
        'principios': COSO_2013,
        'principio': 'Cada principio de COSO 2013 se materializa en una regla del Poka-Yoke y en un principio 5S. El control diario aplica las reglas. La auditoría continua verifica que los principios se cumplan.'
    }, f, indent=2, ensure_ascii=False)

print(f"Manifiesto: {manifiesto.name}")
print()

# Generar tabla Markdown
tabla = BASE / "TABLA_COSO_2013_COMPLETA.md"
with open(tabla, 'w', encoding='utf-8') as f:
    f.write(f"""# COSO 2013 + 5S + POKA-YOKE

**Nodo:** {NODO}
**Fecha:** {FECHA}
**Analista:** Domingo E. Díaz N. | C.P.C. N.º 183594

## Los 17 principios de COSO 2013

| # | Componente | Principio | 5S | Reglas Poka-Yoke |
|---|------------|-----------|----|------------------|
""")
    for p in COSO_2013:
        f.write(f"| P{p['id']:02d} | {p['componente']} | {p['principio']} | {p['5s']} | {', '.join(p['reglas'])} |\n")

    f.write(f"""
## Cobertura por componente

| Componente COSO | Principios | 5S | Estado |
|-----------------|------------|----|--------|
| Entorno de Control | P01–P05 | Seiri | ✅ Cubierto |
| Evaluación de Riesgos | P06–P09 | Seiso | ✅ Cubierto |
| Actividades de Control | P10–P13 | Seiton | ✅ Cubierto |
| Información y Comunicación | P14–P15 | Seiketsu | ✅ Cubierto |
| Monitoreo | P16–P17 | Shitsuke | ✅ Cubierto |

## Cómo se materializa cada principio

**Entorno de Control (P01–P05):** Se materializa en las reglas de inmutabilidad (#1, #2), integridad de fuentes (#3, #4), autorización de ajustes (#13), y documentación de motivos (#9). El 5S correspondiente es **Seiri**: clasificar lo que se necesita de lo que no, incluyendo los registros.

**Evaluación de Riesgos (P06–P09):** Se materializa en la detección de facturación sin stock (#7), transferencias sin recepción (#12), y ajustes de alto valor (#13). El 5S correspondiente es **Seiso**: limpiar los datos para que los riesgos sean visibles.

**Actividades de Control (P10–P13):** Se materializa en el kardex cuadrado (#5), integridad de hashes (#6), catálogo sin duplicados (#8), y valorización correcta (#10, #11). El 5S correspondiente es **Seiton**: ordenar el registro para que sea confiable.

**Información y Comunicación (P14–P15):** Se materializa en la detección de procesos automáticos (#15) y en la coherencia bimonetaria (#17). El 5S correspondiente es **Seiketsu**: estandarizar los reportes y los lenguajes.

**Monitoreo (P16–P17):** Se materializa en la compensación de facturas sin stock (#16) y en la auditoría continua con sus 6 tipos. El 5S correspondiente es **Shitsuke**: sostener la disciplina del control en el tiempo.
""")

print(f"Tabla completa: {tabla.name}")
print()
print(f"✅ Integración COSO 2013 + 5S + Poka-Yoke completada para {NODO}")

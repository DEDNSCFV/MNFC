# Arquitectura MNFC

## Capas

```

┌─────────────────────────────────────────────────────────┐
│  Entrada        ingest_txt.py · cargar_txt_seguro.py    │
│                 (TXT/Excel del ERP Profit)              │
├─────────────────────────────────────────────────────────┤
│  Normalización  paso1..paso4 · schema_limpio.sql        │
│                 (columnas, dedup, trazabilidad)         │
├─────────────────────────────────────────────────────────┤
│  Dinero         money.py (FUENTE ÚNICA) ✅              │
│                 baldor_centimos.py (puente) ✅          │
│                 → int centavos · Decimal · ROUND_HALF_EVEN │
├─────────────────────────────────────────────────────────┤
│  Kernel DSL     mnfc.py · dsl/ · modelos.py             │
│                 assembler · evaluator · persistencia    │
│                 ⚠️  float por diseño (fase 2)            │
├─────────────────────────────────────────────────────────┤
│  Dominio        kpis_nodo_v7.py · kpis_reticulo_v4.py   │
│                 libro_mensual_v2.py · libro_semanal.py  │
│                 (24 KPIs · nodo · retículo)             │
├─────────────────────────────────────────────────────────┤
│  Auditoría      auditoria_nia501.py · coso_integracion.py│
│                 auditoria_integridad.py                 │
├─────────────────────────────────────────────────────────┤
│  Salida         entregables.py · generar_informe.py     │
│                 (CSV · XLSX · SHA256)                   │
└─────────────────────────────────────────────────────────┘

```

## Estado por capa

| Capa | Madurez |
|---|---|
| Dinero | ✅ fase 1 cerrada, certificada |
| Kernel DSL | 🔵 fase 2 abierta |
| Dominio (KPIs/libros) | 🟡 consolidación pendiente |
| Auditoría | 🟢 operativa |
| Ingesta | 🟡 contrato de centavos verificado |

## Decisiones clave (ADRs)

- **ADR-001** — Dinero en centavos + Decimal (`docs/adr/001-dinero-centavos.md`)
- **ADR-002** — Kernel en float por diseño (fase 2) (`docs/adr/002-kernel-float-fase2.md`)

## Deuda técnica conocida

Ver `CHANGELOG.md` sección "Deuda separada" y `auditar_fase2.py`.

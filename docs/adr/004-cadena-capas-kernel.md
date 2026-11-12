# ADR-004 — Cadena secuencial capa 4 → capa 7 (no duplicación)

**Estado:** Aceptado (2026-11-12)

## Contexto
El diagnóstico para fase 2 reveló **dos tipos `Asiento`**:
- `mnfc.mnfc.Asiento` (capa 4): líneas como `list[dict]`, sin contexto
- `mnfc.extensiones.modelos.Asiento` (capa 7): líneas tipadas, con contexto contable

**No son duplicados.** Son **niveles semánticos distintos** de una cadena
secuencial:
procesar_asiento(dicts) → mnfc.Asiento → assembler → modelos.Asiento
capa 4                  intermedio                finalizado

```

Prueba: `modelos.py:7` dice "dicts que devuelve mnfc.procesar_asiento".
`__init__.py` solo exporta `mnfc.Asiento`. `modelos.Asiento` es interno del DSL.

## Decisión
- **No fusionar.** Los dos tipos coexisten con semántica distinta.
- Migración fase 2 los trata en orden: capa 4 (2.2) → capa 7 (2.3-2.5).
- La API pública (`mnfc.procesar_asiento`) se mantiene como punto de entrada.
- `modelos.Asiento` sigue siendo interno del DSL.

## Consecuencias
- ✅ Radio de explosión de `mnfc.py` es mínimo (1 test lo importa).
- ✅ Migración de capa 7 es donde está el trabajo real (26 tests).
- ⚠️ Mantener dos tipos `Asiento` requiere no confundirlos en código nuevo.
- 📋 Docs actualizan `ARCHITECTURE.md` con el diagrama secuencial.

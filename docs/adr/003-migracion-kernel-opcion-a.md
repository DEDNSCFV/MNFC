# ADR-003 — Migración completa del kernel a centavos (opción A)

**Estado:** Aceptado (2026-11-12)

## Contexto
El kernel del DSL (`assembler`, `evaluator`, `mnfc`, `modelos`, `persistencia`,
`reportes`) opera en `float`, según ADR-002. Es deuda real, no contrato de
negocio: MNFC no tiene consumidores externos publicados. Los 26 tests de
`test_dsl_assembler.py` son internos y se pueden reescribir.

## Decisión
Migración completa (opción A):
- Fuente de verdad: `monto_cent: int` (centavos enteros).
- `monto: float` → **propiedad derivada de solo lectura** durante transición,
  luego se elimina.
- **Breaking change** en la API pública de `mnfc` al final de la migración.
- Sin wrapper oculto, sin deprecation gradual. Deuda cerrada, no escondida.

## Plan de sub-fases (orden estricto)
| # | Módulo | Rompe |
|---|---|---|
| 2.1 | `modelos.py` — campo `monto_cent` + propiedad `monto` | No (agrega) |
| 2.2 | `mnfc.py` — kernel usa centavos | Tests (5) |
| 2.3 | `evaluator.py` — DSL evalúa en centavos | Tests (5) |
| 2.4 | `assembler.py` — puerta valida int centavos | Tests (26) |
| 2.5 | `persistencia.py` + `reportes.py` | Tests (5) |
| 2.6 | Reescritura de tests + eliminar `monto: float` | — |

## Consecuencias
- ✅ Kernel limpio, sin float.
- ✅ Fase 2 cerrada → nivel 4.5 alcanzado.
- ⚠️ Rompe API. Requiere reescribir los tests que asumían `float`.
- ⚠️ Duración: 1-2 días reales, 6 sesiones dedicadas.

## Rollback
`git reset --hard main` si la sub-fase no estabiliza en la sesión.

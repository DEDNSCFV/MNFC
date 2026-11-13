# ADR-005 — Decisiones de contrato para fase 2

**Estado:** Aceptado (2026-11-12)
**Bloquea:** 2.3, 2.4, 2.5, 2.6

## Contexto
El intento de 2.3 el 2026-11-11 reveló 3 cambios de contrato no explícitos
en ADR-003/004. Se revirtió 2.3 para decidir con claridad.

## Decisión 1 — Tolerancia float 0.001
**Decisión:** Eliminar. Solo montos exactos a 2 decimales.
**Razón:** Fase 2 migra a centavos. Admitir 99.999 reintroduce float.
**Afecta:** tests `test_justo_en_limite`, `test_fuera` (reescribir en 2.4).

## Decisión 2 — String como monto
**Decisión:** Rechazar strings.
**Razón:** `PartidaAutorizada` es tipo interno. Fase 2 no amplía contrato.
**Afecta:** test `test_monto_invalido["100"]` (mantener verde en 2.3).

## Decisión 3 — Detección de overflow (1e308)
**Decisión:** Detectar en suma, no en validación individual.
**Razón:** `1e308` es finito individualmente; el problema es al sumar.
**Afecta:** `test_overflow_en_total_error_con_regla` (revisar en 2.4).

## Plan revisado
1. **2.4a** — `Asiento.total_*_cent` como fuente (solo `Asiento`, no `LineaAsiento`)
2. **2.4b** — `LineaAsiento.monto_cent` como fuente
3. **2.3** — `PartidaAutorizada.monto_cent` como fuente
4. **2.5** — `assembler._validar_monto` int centavos
5. **2.6** — Eliminar `monto: float` + tag v0.5.0

**Presupuesto realista:** ~2-4 tests a reescribir, no 26. Los tests acceden
vía `@property` (float) y siguen funcionando.

## Predicción corregida
- 2.4a: 0-1 tests rotos (`test_overflow_...`)
- 2.4b: 0-1 tests rotos (nan/inf en `LineaAsiento`)
- 2.3: 0-1 tests rotos (string como monto)
- 2.5, 2.6: 0 tests rotos

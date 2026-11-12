# ADR-005 — Decisiones de contrato para fase 2

**Estado:** Propuesto (2026-11-12)
**Bloquea:** 2.3, 2.4, 2.5, 2.6

## Contexto
El intento de 2.3 el 2026-11-11 reveló 3 cambios de contrato que no estaban
explícitos en ADR-003/004. Se revirtió 2.3 para decidir con claridad.

## Decisión 1 — Tolerancia float 0.001

**Situación:** `test_justo_en_limite` verifica que `100.0 - 99.999` (dif 0.001)
sea descuadre. En centavos, `99.999` redondea a `100.00` → cuadra.

**Opciones:**
- 🅰️ Eliminar tolerancia. Solo montos exactos a 2 decimales válidos.
- 🅱️ Mantener tolerancia 0.001 comparando en Decimal antes de centavos.

**Decisión:** 🅰️ Eliminar tolerancia.
**Razón:** Fase 2 migra a centavos. Admitir 99.999 reintroduce float implícito.
Los montos con >2 decimales son error de ingesta, no válidos. Test reescribir.

## Decisión 2 — String como monto

**Situación:** `test_monto_invalido["100"]` espera "no numérico". Mi parche
de 2.3 convirtió strings a Decimal.

**Opciones:**
- 🅰️ Strings siguen siendo "no numérico" (kernel solo acepta numérico).
- 🅱️ Aceptar strings convertibles ("100" → 10000 cent).

**Decisión:** 🅰️ Strings rechazados.
**Razón:** `PartidaAutorizada` es tipo interno. Si un consumidor tiene strings,
debe convertirlos antes. Fase 2 no amplía contrato, solo cambia representación.

## Decisión 3 — Detección de overflow (1e308)

**Situación:** `test_overflow_en_total_error_con_regla` espera "total no finito"
al sumar dos `1e308`. Mi parche 2.3 lo detecta antes en `_validar_monto`.

**Opciones:**
- 🅰️ Detectar en `_validar_monto` (individual) → error "monto no finito".
- 🅱️ Detectar en suma (ensamblar) → error "total no finito".

**Decisión:** 🅱️ Detectar en suma.
**Razón:** `1e308` es finito como monto individual. El problema es la suma.
Detección individual sería falsa alarma. `_validar_monto` acepta finitos;
`ensamblar` detecta overflow al acumular. Con 2.4 (acumulación en centavos
via `int`, sin overflow) el problema se elimina naturalmente.

## Plan de ejecución revisado

Orden cambiado respecto a sesión anterior:
1. **2.4 primero** — `LineaAsiento`/`Asiento` a centavos (rompe 26 tests)
2. **2.3** — `PartidaAutorizada` a centavos (cae con 2.4 hecho)
3. **2.5** — `assembler._validar_monto` int (5 líneas con 2.4 hecho)
4. **2.6** — Eliminar `monto: float` + tag v0.5.0

**Presupuesto de tests:** ~26 en 2.4, ~4 en 2.3, 0 en 2.5, ~0 en 2.6.
Total ~30 tests a reescribir, todos en 2.4 y 2.3.

# ADR-001 — Dinero en centavos enteros + Decimal

**Estado:** Aceptado (2026-11-11)

## Contexto
El sistema calculaba dinero en `float`, causando derivas al céntimo
(0.1 + 0.2 ≠ 0.3) y fallos de redondeo en bordes (1.005 → 1.00 en vez de 1.01).

## Decisión
- Almacenamiento: `int` (centavos).
- Cálculo: `Decimal` + `ROUND_HALF_EVEN` (redondeo bancario).
- `float` prohibido en la frontera monetaria (`money.py`).
- Kernel del DSL mantiene `float` como deuda explícita (fase 2, ADR-002).

## Consecuencias
- ✅ Cálculos exactos al céntimo.
- ✅ Test de aceptación reproducible (`auditar_cierre_decimal.py`, `exit=0`).
- ⚠️ Migración del kernel pendiente (fase 2).

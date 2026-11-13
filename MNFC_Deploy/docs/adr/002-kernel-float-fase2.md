# ADR-002 — Kernel DSL en float (fase 2 pendiente)

**Estado:** Aceptado con deuda explícita (2026-11-11)

## Contexto
El kernel (`assembler`, `evaluator`, `mnfc`, `modelos`) opera en `float`
por decisión arquitectónica previa, documentada en
`tests/test_dsl_assembler.py::test_monto_decimal_rechazado_por_contrato_de_fase`.

## Decisión
- No migrar el kernel en fase 1.
- Frontera blindada con `money.py`.
- Fase 2 requiere decisión de negocio: compatibilidad de API, formato Excel.

## Consecuencias
- ✅ Fase 1 entregada sin romper consumidores.
- 🔵 31 tests + 5 módulos pendientes de migración.
- 📋 Inventario reproducible: `python auditar_fase2.py`.

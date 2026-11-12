# ADR-007 — Deprecación de @property monto para v0.6.0

Estado: Aceptado (2026-11-12)
Cierra: 2.6 de ADR-003/006

## Contexto
Tras 2.1-2.5, el kernel de MNFC opera internamente en centavos (int) en
las 4 capas:

- mnfc.Asiento.total_debe_cent (int, field)
- modelos.Asiento.total_debe_cent (int, field)
- modelos.LineaAsiento.monto_cent (int, field)
- modelos.PartidaAutorizada.monto_cent (int, field)
- assembler._validar_monto (retorna int)

La @property monto/total_debe/total_haber sigue existiendo como capa de
compat de lectura (devuelve float derivado de centavos). No es fuente de
verdad, es azúcar sintáctico.

## Decisión
- @property monto se mantiene como deprecated en v0.5.0.
- Se eliminará en v0.6.0 (fase 3).
- Los tests que acceden a .monto (float) siguen pasando.
- Código nuevo debe usar .monto_cent / .total_*_cent.

## Por qué no eliminar en v0.5.0
- Rompe ~25 tests (todos acceden a .monto para comparar floats).
- No aporta valor de negocio: el kernel ya opera en centavos.
- Es capa de compat, no fuente de verdad.
- Eliminarla requiere reescritura masiva de tests en un solo commit, alto riesgo.

## Deprecation plan
- v0.5.0 (hoy): @property monto marcada como deprecated en docstring.
- v0.5.x: warnings de deprecación opcionales.
- v0.6.0 (fase 3): eliminar @property monto. Tests usan .monto_cent.

## Migración de datos existentes
BDs con `monto: float` deben migrarse a `monto_cent: int`.
Script: migrar_monto_a_cent.py (idempotente, dry-run por defecto).

## Consecuencias
- ✅ Fase 2 cerrada: kernel 100% centavos internamente.
- ✅ Persistencia serializa monto_cent (int), no float.
- ⚠️ @property monto sigue devolviendo float (derivado, seguro).
- 📋 Fase 3: eliminar @property monto + warnings de deprecación.

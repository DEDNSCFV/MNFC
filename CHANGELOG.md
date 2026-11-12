# Changelog

Todos los cambios notables de MNFC se documentan en este archivo.
El formato sigue [Keep a Changelog](https://keepachangelog.com/es/1.1.0/).
El versionado sigue [Semantic Versioning](https://semver.org/lang/es/).

---

## [0.2.0] - 2026-10-07

Kernel + extensiones. Persistencia, maquina de estados y reportes.

### Anadido

**Capa 7 - Extensiones del kernel:**

- `extensiones/estados.py` - Enums y VersionContexto (migrado de SCFV_DSR).
- `extensiones/reticulo.py` - Reticulo booleano de cuentas. Misma algebra
  que xnor, a otra escala (autosimilitud verificable).
- `extensiones/serializador.py` - Serializacion canonica determinista.
  Garantiza hashes estables entre sesiones.
- `extensiones/modelos.py` - Modelos tipados (Asiento, LineaAsiento,
  PartidaAutorizada, ContextoContable).
- `extensiones/maquina.py` - Maquina de estados del asiento con historial
  hasheado.
- `extensiones/examinador.py` - Validador de evidencia (linea + conjunto).
- `extensiones/persistencia/base.py` - Interfaz abstracta `StoreBase`.
- `extensiones/persistencia/sqlite_store.py` - Implementacion SQLite
  con cadena hash Merkle.
- `extensiones/persistencia/json_store.py` - Implementacion JSON con
  misma semantica y **compatibilidad cross-backend** (mismo evento,
  mismo hash).
- `extensiones/reportes.py` - CSV diario, mayor y balance. PDF opcional.
- `extensiones/__init__.py` - Fachada publica con 22 simbolos.

**Tests:**

- `tests/test_extensiones.py` - 37 tests (incluye integracion
  end-to-end kernel + extensiones).
- Suite completa: **108 tests** en 1.77 segundos.

### Corregido

- `maquina.py`: `Transicion.hash()` usaba `.value` (int) en concatenacion
  con strings. Cambiado a `.name`. Bug heredado de SCFV_DSR.
- `reportes.py`: `generar_csv_balance()` sumaba cuentas 5xxx (gastos) a
  CAPITAL. Corregido a rubro GASTOS y agregado RESULTADO (INGRESOS -
  GASTOS). Bug heredado de SCFV_DSR.
- `sqlite_store.py`: `guardar()` ahora captura `sqlite3.IntegrityError`
  y relanza como `ValueError` para cumplir el contrato de `StoreBase`.

### Arquitectura

- Kernel (capas 0-6) sin cambios: xnor, baldor, estadistica, fractal,
  mnfc, ledger.
- Extensiones (capa 7) nueva, importable desde `mnfc.extensiones`.
- La API publica de `mnfc` (`from mnfc import procesar_asiento`) no
  cambia. Es una version menor: agrega sin romper.
- Persistencia intercambiable: `SQLiteStore` y `JSONStore` cumplen
  `StoreBase` (Liskov). Misma semantica, mismo hash.

---

## [0.1.0] - 2026-10-05

Primera materializacion del nucleo MNFC.

### Anadido

**Capas fractales (6):**

- Capa 0 · `xnor.py` — invariante de partida doble.
  Tres representaciones equivalentes (booleana, GF(2), signos).
  Verificado exhaustivamente en las 4 combinaciones posibles.
  Locus: Anexo I (invariante 2.5) + Boole 1847.

- Capa 1 · `baldor.py` — aritmetica contable trazable.
  Ley de signos, leyes formales, reduccion de terminos,
  interes compuesto, regla de tres, logaritmos.
  Locus: Baldor L1676-1699, L1885-1888, L874-997.

- Capa 2 · `estadistica.py` — medida estadistica aplicada.
  28 funciones: descriptivas, distribuciones, muestreo, estimacion,
  anomalias, proyeccion.
  Locus: Mendenhall 13ed caps 2, 6, 7, 8.

- Capa 3 · `fractal.py` — autosimilitud escalante en cascada.
  Analisis de exponente escalante sobre series contables.
  Locus: Mandelbrot 1975, 1982.

- Capa 4 · `mnfc.py` — composicion de asientos.
  Procesa N lineas, clasifica, cuadra, devuelve Asiento.

- Capa 5 · `__init__.py` — fachada publica.
  Reexporta 58 simbolos de las 6 capas.

- Capa 6 · `ledger.py` — cadena de hashes inmutable.
  Encadenamiento Merkle. Verify() detecta cualquier alteracion.
  Locus: Merkle 1979 + ProGit 2014.

**Tests (78):**

- `test_integracion.py` — 5 tests end-to-end de las 6 capas.
- `test_bordes.py` — 24 tests de inputs extremos.
- `test_contratos.py` — 31 tests de determinismo y mensajes de error.
- `test_fuzzing.py` — 11 tests con ~4,900 iteraciones y semilla fija.
- `test_estres.py` — 7 tests de rendimiento marcados `slow`.

**Documentacion:**

- `README.md` — nomenclatura, uso, bibliografia, rendimiento, licencia dual.
- `LICENSE` — AGPL-3.0-or-later (texto oficial completo, 661 lineas).
- `COMMERCIAL.md` — terminos de licencia comercial.
- `CONTRIBUTING.md` — guia de contribucion con CLA obligatorio.
- `NOTICE` — atribucion de las 6 tradiciones + procedencia criptografica.
- `CHANGELOG.md` — este archivo.

**Configuracion:**

- `pyproject.toml` — metadatos, licencia dual, marker `slow` de pytest.
- `conftest.py` — path setup para pytest.

### Correcciones durante desarrollo

- `fractal.py`: cascada ignora niveles con varianza cero (evita
  `math domain error` en series periodicas).
- `ledger.py`: `append` valida que el contenido sea `dict` y lanza
  `TypeError` con mensaje especifico si no lo es.

### Rendimiento (Termux / Android / aarch64 / Python 3.13)

- `calcular_ubicacion` — 0.72 us/op · 1,381,916 ops/s
- `procesar_asiento` (4 lineas) — 15.93 us · 62,759 asientos/s
- `procesar_asiento` (100 lineas) — 308.60 us · 3,240 asientos/s
- `Ledger.append` — 20.46 us · 48,882 bloques/s
- `Ledger.verify` (10k bloques) — 188.1 ms
- Memoria por bloque — 361 B
- Fractal sobre serie 100k — 164.5 ms

### Estado epistemico por capa

| Capa | N1 locus | N3 | N4 |
|------|----------|----|----|
| 0 xnor        | Anexo I + Boole 1847      | verificacion matematica exhaustiva | aplicada |
| 1 baldor      | Baldor L1885+             | pendiente auditoria formal         | dominio contable |
| 2 estadistica | Mendenhall caps 2,6,7,8   | pendiente PDF                      | pendiente |
| 3 fractal     | Mandelbrot 1975/1982      | pendiente PDF                      | pendiente |
| 4 mnfc        | N/A composicion           | N/A                                | aplicada |
| 6 ledger      | Merkle 1979 + ProGit 2014 | pendiente PDF                      | pendiente |

### Seguridad

- Commits firmados con SSH ED25519 desde el primer commit.
- Todos los commits de esta version tienen firma verificable.
- Tag `v0.1.0` firmado criptograficamente.
- Archivo `SHA256SUMS` con hashes de los artefactos distribuibles.

### Licencia

- Dual: AGPL-3.0-or-later OR Commercial.
- CLA obligatorio para contribuciones.

### Dependencias

Ninguna. Solo stdlib de Python 3.10+.

---

## [No publicado]

Cambios que aun no forman parte de un release. Se documentaran en la
proxima version.

### Deuda separada (NO fase 2) — detectada al cerrar fase 1
Los 4 fallos siguientes son **preexistentes** (no regresión del cierre decimal):
- tests/test_extensiones.py::test_reportes_csv_diario
- tests/test_extensiones.py::test_reportes_csv_mayor
- tests/test_extensiones.py::test_reportes_csv_balance
- tests/test_extensiones.py::test_integracion_kernel_y_extensiones

Son `AssertionError` en `src/mnfc/extensiones/reportes.py` (formato de salida CSV).
Diagnóstico pendiente. No bloquean fase 1.

### Fix: reportes CSV (deuda heredada)

Causa: `_leer_asientos` filtraba por `e["timestamp"]` (fecha de persistencia
del evento, "hoy") en lugar de `payload["fecha"]` (fecha contable del asiento).
Resultado: los 3 reportes CSV (diario, mayor, balance) generaban solo headers.

Fix: filtro por `payload["fecha"].startswith(periodo_id)` y orden por
`payload["fecha"]`. `_timestamp_rango` queda huérfano (no se borra).

Resuelve:
- tests/test_extensiones.py::test_reportes_csv_diario
- tests/test_extensiones.py::test_reportes_csv_mayor
- tests/test_extensiones.py::test_reportes_csv_balance
- tests/test_extensiones.py::test_integracion_kernel_y_extensiones

### Deuda: lint residual (~59 errores ruff)

Tras dos pases de `ruff --fix`, quedan ~59 errores no auto-fixables:
- Complejidad ciclomática (C901) en kpis_* y libro_*
- Shadowing de nombres (A001/A002)
- ~26 fixables con `--unsafe-fixes` (requieren revisión manual)
- ~33 requieren refactor (no automático)

Acción: sprint dedicado por archivo. No bloquea baseline.

### Fase 2.3 — Intento pausado (2026-11-12)

Sub-fase 2.3 (PartidaAutorizada.monto_cent como fuente) intentada y
revertida. El diagnóstico reveló 3 cambios de contrato mayores:

1. Tolerancia float 0.001 desaparece al redondear a centavos
   (99.999 → 100.00). Dos tests de TestTolerancia asumen el contrato
   viejo. Requieren reescritura, no son bugs.
2. String "100" debe seguir siendo "no numérico" (contrato viejo).
   Ajuste necesario en constructor.
3. Detección de overflow (1e308) se mueve de suma (ensamblar) a
   validación individual (_validar_monto). Cambio de semántica
   que solo se cierra con 2.4 (acumulación en centavos).

Decisión: parar en 2.2 (mnfc.py migrado, suite 624 verde).
2.3-2.6 requieren sesión dedicada con plan de reescritura de tests
(estimado: 4-6 tests afectados, ~2 h de trabajo enfocado).

### Fase 2.4b — Pausada por regresión de persistencia (2026-11-12)

Intento de migrar `LineaAsiento.monto` a @property reveló una regresión
silenciosa: **la persistencia deja de guardar los montos**.

## Causa
`serializar()` (en `extensiones/serializador.py`) usa `dataclasses.fields()`
para obtener los campos a serializar. Al convertir `monto` de field a
@property, el campo desaparece del payload JSON:

  ANTES (fase 1):
    fields(LineaAsiento) = ['cuenta', 'ubicacion', 'monto', 'naturaleza', 'movimiento']
    serializar incluye monto ✓

  DESPUÉS (2.4b intento):
    fields(LineaAsiento) = ['cuenta', 'ubicacion', 'naturaleza', 'movimiento']
    serializar NO incluye monto ✗

## Por qué los tests no lo detectan
Los tests de persistencia verifican estructura y errores de serialización,
pero **no verifican que el payload guardado contenga los montos**.

## El test viejo de Decimal
`test_decimal_en_partida_falla_sin_escritura` estaba verde en fase 1 porque
`Decimal` era un field. Al migrar a @property, el test pierde su razón de
ser: ya no hay Decimal en el payload, así que no puede fallar.

## Decisión: ADR-006 antes de reintentar

Antes de reintentar 2.4b, escribir ADR-006 con decisión:
- ¿`monto_cent` es field del dataclass (int) y se serializa?
- ¿O se amplía `serializar()` para incluir @properties?
- ¿Cómo se verifica que el payload incluye todos los montos?

Estado: 2.4a verde, 2.4b revertida. 3/7 sub-fases cerradas.

## [v0.5.0] — Fase 2 decimal CERRADA (2026-11-12)

Kernel de MNFC opera 100% en centavos (int). Fase 2 completa.

### Sub-fases cerradas (7/7)
- 2.1: @property monto_cent derivadas en ambas capas
- 2.2: mnfc.Asiento usa centavos como fuente (total_debe_cent int)
- 2.3: PartidaAutorizada.monto_cent como field serializable
- 2.4a: Asiento (modelos) con total_*_cent como field
- 2.4b: LineaAsiento con monto_cent como field serializable
- 2.5: assembler._validar_monto retorna int centavos
- 2.6: Migración de datos + tag (esta versión)

### Cambios en API
- @property monto/total_debe/total_haber: deprecated, eliminar en v0.6.0
- Código nuevo debe usar .monto_cent / .total_*_cent
- Persistencia serializa monto_cent (int) en payload
- Constructor sigue aceptando monto= (pesos) para compat

### Migración de datos
- Script: migrar_monto_a_cent.py (idempotente, dry-run por defecto)
- Uso: python migrar_monto_a_cent.py <db> --aplicar
- Backup automático antes de aplicar

### ADRs
- ADR-003: migración completa del kernel a centavos
- ADR-004: cadena capa 4 → capa 7 (no duplicación)
- ADR-005: decisiones de contrato (tolerancia, strings, overflow)
- ADR-006: persistencia de centavos en dataclasses
- ADR-007: deprecación de @property monto para v0.6.0

### Deuda explícita (fase 3, v0.6.0)
- Eliminar @property monto/total_debe/total_haber
- Reescribir ~25 tests para usar .monto_cent
- Warnings de deprecación opcionales

### Tests
- Suite: 625 passed, 0 failed, 1 xfailed
- Reescritos: test_redondeo_bancario_cuadra, test_diferencia_de_un_centimo_descuadra,
  test_diferencia_centimo_y_medio_descuadra, test_monto_decimal_ahora_es_valido_en_fase2,
  test_monto_fuera_de_rango_rechazado, test_tipo_no_serializable_en_partida_...,
  test_segundo_asiento_no_serializable_...

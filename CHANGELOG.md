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

# TRASPASO MNFC — cierre de sesión 2026-10-10 (extensión)

> Este archivo tiene dos partes.
> Parte 1: estado actual (2026-10-10).
> Parte 2: cierre original del 2026-10-08 (preservado sin alterar).
>
> El estado del 8-oct queda como foto histórica. La parte 1 lo
> actualiza sin borrarlo.

## Estado actual (2026-10-10)

- Repo:        https://github.com/DEDNSCFV/MNFC
- Versión repo:     v0.2.0 (pyproject.toml)
- Versión __init__: "0.1.0"  ← desincronizada, deuda viva
- Versión wheel instalado: 0.2.0, construido 2026-10-07 12:38
- HEAD:        96688af
- Última sesión funcional: 8-oct (26 commits, 290 tests + 1 xfailed)
- Última sesión documental: 10-oct (auditoría complementaria firmada)

## Actualización 2026-10-10 — hallazgos verificados

La ventana del 10-oct produjo un acta complementaria:

    ~/Programa-de-Investigacion-SCFV/ACTAS/
        AUDITORIA_COMPLEMENTARIA_INTEGRIDAD_DISTRIBUCION_2026-10-10.md
        AUDITORIA_COMPLEMENTARIA_INTEGRIDAD_DISTRIBUCION_2026-10-10.sha256
        AUDITORIA_COMPLEMENTARIA_INTEGRIDAD_DISTRIBUCION_2026-10-10.sha256.sig

Hash del acta: 32a3699cfb692d0f869059182f0a50577a28b1579e5d4dde73b9ba7697dce29d
Firma SSH:     ED25519, huella SHA256:C6OnkI1RAx7ffyKsMR0kQrfnIw6vnAFsFB1p1nYRTO4

### Hallazgos que cambian el estado del proyecto

R8  · Wheel desactualizado. El wheel instalado en site-packages es
      del 7-oct 12:38, anterior a las validaciones del 8-oct
      (_validar_finito). 16 horas de diferencia.

R10 · Distribución local desconectada del fuente. Quien instale el
      wheel local examinado recibe sumar_montos sin validación de
      finitud. Los tests de MNFC pasan porque pytest usa conftest.py
      con sys.path insert. En uso real vía `import mnfc`, no.

R11 · Tres identificadores de versión incoherentes:
      __init__.py → "0.1.0"
      pyproject.toml → "0.2.0"
      contenido del wheel → pre-_validar_finito

R3  · El campo funcion_baldor del JSON no lo lee ningún .py del
      proyecto. Marca operaciones reservadas (5 de 6 no se invocan
      nunca). La sexta (suma_montos) sí se invoca y su fb se ignora.

Cadena de custodia del wheel: íntegra criptográficamente (hash y
firma válidos), pero desactualizada respecto al fuente.

### Mapa del corpus DSL (resumen)

17 operaciones en operaciones.json.
11 operaciones se invocan desde fractales.
13 operaciones distintas tienen rama if op_id == en evaluador.py.
14 bloques if físicos (suma_montos duplicado).
6 entradas tienen funcion_baldor.
5 con fb no se invocan.
Detalle completo en el acta complementaria §4.

### Deudas nuevas (a sumar a las del 8-oct)

- R10/R11 · Reconstruir wheel desde HEAD, alinear versiones.
- R5      · JSON apunta a DSR (funcion_baldor → kernel/baldor.py),
            no a MNFC. Decisión arquitectónica pendiente.
- §7.3    · Decisión arquitectónica por grupos A/B/C/D. El mapa
            del acta complementaria desbloquea la clasificación,
            pero no se adoptó.
- §8.4    · Clasificar operaciones: ley matemática vs interpretación
            normativa, por componente (fórmula / aplicación /
            precondición).
- Actividad efectiva de las tres copias de evaluador.py
  (~/SCFV_DSR/scfv_dsr, ~/scfv-dsr/scfv_dsr, backup fase2a).

---

## Cierre original — 2026-10-08 (preservado sin alterar)

## Estado
- Repo: https://github.com/DEDNSCFV/MNFC
- Versión publicada: v0.2.0
- Última sesión: 25 commits firmados, 290 tests + 1 xfailed.
- Firma SSH: SHA256:C6OnkI1RAx7ffyKsMR0kQrfnIw6vnAFsFB1p1nYRTO4

## Protocolo N3-textual (consolidado)
Ver N3.md en el repo. Contiene:
- Definición operativa de N3-textual (no N3-estricto).
- Cinco reglas, tolerancias, protocolo de 5 pasos.
- Fuentes canónicas con SHA-256.
- Tabla de estado por función.
- Nota 6bis: tests por reconstrucción de parámetros.
- Nota 6ter: coef_variacion reclasificada N0.
- Advertencia sobre capa 3 (fuente pirata).

## Fuentes canónicas
Capa 2:
- PDF: ~/storage/downloads/sem8_introduccionalaprobabilidadyestadistica (1).pdf
  SHA-256: 0035b8511cb870eed019c260c38daa1c8a8094789cfd43a9e9da04af6ccf68c5
- Raw: ~/tmp/estadistica.txt
  SHA-256: 0ef0e73603575096363f40cde63c52381e16349e6c81a5bd7ef6f3dc90baa488

Capa 3 (provisional, fuente derivada):
- ~/.mandelbrot_1975_raw.txt  (4eff505a...)
- ~/.mandelbrot_1982_raw.txt  (0cb4e29a...)
Advertencia: EPUBs no autorizados (Lectulandia). Capa 3 bloqueada en N2.

## N3-textual capa 2: 23/30 (77%)

En N3:
media, mediana, moda*, modas, varianza_muestral, desviacion_muestral,
cuartiles, iqr, z_score, normal_cdf, z_critico_95, z_critico_90,
error_estandar_media, error_estandar_proporcion, tamano_muestra_media,
tamano_muestra_proporcion, margen_error, ic_media*, ic_proporcion,
es_atipico_z, limite_control_media*, ic_una_cola_sup*.
(* = por reconstrucción de parámetros, ver N3.md §6bis)

En N2 con motivo:
coef_variacion (N0 - cita previa incorrecta),
normal_pdf, z_critico_99, ic_una_cola_inf, es_atipico_iqr,
z_score_serie, proyeccion_error, stock_seguridad,
pronostico_media_movil.

## Bugs corregidos en esta sesión (4 + 1 cita falsa)
1. cuartiles() truncaba en vez de interpolar.
   Expuesto por Ejemplo 2.13.
2. modas() no exportada en la fachada pública.
   Expuesto por test de determinismo.
3. NaN/Inf propagados silenciosamente en 10 funciones.
   Expuesto por tests adversariales.
4. tamano_muestra_* redondeaba con round en vez de ceil.
   Expuesto por Ejercicios 8.69 y 8.77.
5. coef_variacion citaba "Mendenhall §2.3" incorrectamente.
   Expuesto por búsqueda de locus. Reclasificada N0.

## Tests nuevos
- tests/test_n3_estadistica.py    (74 tests)
- tests/test_determinismo.py      (45 tests)
- tests/test_golpes.py            (56 tests)
- tests/test_limites_numericos.py (8 tests)

## Deudas abiertas (del 8-oct, ver también la sección 2026-10-10 arriba)
1. __version__ en __init__.py dice "0.1.0" (desincronizado con v0.2.0).
   Decisión pendiente: parche rápido o esquema robusto en v0.3.0.
2. Migración a Decimal (capas 1, 4, 6). Plan documentado en README §
   "Limitación numérica conocida". Fecha estimada v0.3.0.
3. Capa 3 bloqueada en N2 por fuente pirata.
4. PyPI pospuesto.
5. SPDX license (PEP 639, deadline 2027-02).
6. v0.3.0: CLI, DSL, mnfc-arrays, motor neutral.

## Estado de determinismo (medido)
- Capas 0-6: 45 tests confirman idempotencia, orden-independencia
  (donde aplica), ledger estable, constantes inmutables.
- Capa 3: sensible al orden por diseño (cascada agrupa bloques
  consecutivos). Documentado en docstring + tests de sensibilidad.
- Capa 7: no determinista por diseño (uuid4, time.time).
  Deuda documental: no está en README.

## Cómo retomar
Pegar este archivo. Decir tarea. Tareas naturales:
- Cerrar los 6 N2 restantes si aparece fuente o ejemplo.
- Decidir __version__.
- Iniciar migración a Decimal (v0.3.0).
- Documentar no-determinismo de capa 7 en README.

## Convenciones
- Commits firmados (git commit -S, ED25519).
- Heredocs para escribir archivos.
- Un test N3 por función, commit por lote.
- No forzar N3 sobre fuentes dudosas.
- "Nunca romper API pública del kernel."
- Tolerancias: == para exactos, approx() para decimales,
  abs=10^-dec para redondeos del libro.

---

## Cómo retomar (actualizado 2026-10-10)

Leer primero:
1. Este archivo (TRASPASO.md), parte 1 arriba.
2. El acta complementaria en ~/Programa-de-Investigacion-SCFV/ACTAS/
   AUDITORIA_COMPLEMENTARIA_INTEGRIDAD_DISTRIBUCION_2026-10-10.md
3. El acta original del 8-oct, mismo directorio.

Tareas naturales (en orden sugerido):
- Decidir §7.3 por grupos con el mapa del acta complementaria §4.
- Resolver R5 (JSON apunta a DSR, no a MNFC).
- Cerrar R10/R11: reconstruir wheel desde HEAD, alinear versiones.
- Abrir §8.4: clasificar operaciones ley vs norma por componente.
- Iniciar construcción del DSL sobre decisiones arquitectónicas ya
  tomadas.

Estado de firmas:
- Este TRASPASO no está firmado. Es documento vivo.
- El acta complementaria del 10-oct está firmada y congelada.
- El acta original del 8-oct tiene hash pero no firma SSH.

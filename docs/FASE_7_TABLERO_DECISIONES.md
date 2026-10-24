# FASE_7_TABLERO_DECISIONES.md — Tablero de decisiones de gobernanza

**Estado:** `BORRADOR · NO ADOPTADO · NO AUTORIZA IMPLEMENTACIÓN`
**Versión:** v2 — incorpora correcciones F-01 a F-07
**Base:** `MATRIZ_MIGRACION_DECIMAL.txt` (56a4ba0) + conversación 2026-10-24
**Contrato asociado:** `docs/FASE_7_CONTRATO.md` — **PENDIENTE de materialización** (ver M-03)
**Propósito:** consolidar el estado de cada decisión de gobernanza en
categorías auditables. Este documento **no decide**; registra.

---

## §1 Categorías de estado

| Categoría | Significado |
|---|---|
| **ADOPTADA** | Decisión tomada explícitamente por el operador. Vinculante |
| **BLOQUEADA POR DECISIÓN** | Requiere decisión de gobernanza del operador |
| **CONDICIONAL** | Se activa solo si otra decisión toma un valor específico. No computa como activa mientras la condición no se cumpla |
| **PENDIENTE DE EVIDENCIA** | Requiere medición, inspección o ejecución antes de poder decidirse |
| **RESERVA** | Espacio reservado, sin asignar. No computa como decisión |
| **TAREA** | Acción materializable. No es decisión |

**Regla central:** una decisión `ADOPTADA` no cierra automáticamente
sus dependientes. Cada dependiente se verifica contra su propio
criterio de cierre.

**Convención de conteo:** solo filas cuyo ID empieza con `D<número>`
computan como decisión. Las reservas usan formato `— (D7)` y no
computan. Las condicionales se registran marcadas como tales pero se
excluyen del total activo hasta que su condición se cumpla.

---

## §2 Decisiones de dominio monetario

| ID | Pregunta | Opciones | Recomendación técnica | Estado |
|---|---|---|---|---|
| D10-01 | Alcance monetario v0.3.0 | (a) VES mono / (b) VES-first + nota multi / (c) multi desde contrato | (b) | **BLOQUEADA POR DECISIÓN** |
| D10a | Equivalencia numérica | (a1) sin escala / (a2) con escala / (a3) por moneda | depende de D10-01 | **BLOQUEADA POR DECISIÓN** (dep: D10-01) |
| D10b | Evidencia en hash | (b1) bytes fieles / (b2) canónica | depende de D10-01 | **BLOQUEADA POR DECISIÓN** (dep: D10-01) |
| D9 | Representación `Decimal` en `serializar` | (a) `str` canónico / (b) `str` normalizado / (c) numérico / (d) objeto custom / (e) rechazar | depende de D10a, D10b | **BLOQUEADA POR DECISIÓN** (dep: D10a, D10b) |
| D3a | Relación I-hash / I-decimal | (b) coordinadas / (c) secuenciales | depende de D10-01 | **BLOQUEADA POR DECISIÓN** (dep: D10-01) |
| D3b | Orden si D3a=(c) | I-hash→I-decimal / I-decimal→I-hash | depende de D10-01 | **CONDICIONAL** (se activa solo si D3a=(c)) |

---

## §3 Decisiones de integridad y versionado

| ID | Pregunta | Estado |
|---|---|---|
| D1 | Alcance de integridad: (a) 5 campos / (b) todos / (c) todos + delimitación | **BLOQUEADA POR DECISIÓN** |
| D1b | Autenticación de `hash_version`: (1a) centinela + referencia externa / (1b) manifiesto firmado / (1c) aceptar downgrade | **BLOQUEADA POR DECISIÓN** |
| D1c | Política ante truncamiento de centinela | **BLOQUEADA POR DECISIÓN** (dep: D1b) |
| D1d | Atribución histórica `v1`: criptográfica / asertiva | **BLOQUEADA POR DECISIÓN** |
| D2 | Convivencia `v1`/`v2`: cadena única / paralelas / corte | **BLOQUEADA POR DECISIÓN** |
| D5 | ¿`v2` compromete `evento_id` lógico? | **BLOQUEADA POR DECISIÓN** (dep: D6) |
| D6 | Forma de `evento_id`: = `idempotency_key` / campo nuevo | **BLOQUEADA POR DECISIÓN** |
| — (D7) | Reserva sin asignar. No computa como decisión. Espacio reservado para decisiones emergentes durante implementación de v2 | **RESERVA** |
| D8 | Mensajes de error: (a) detalle interno / (b) interfaz estable | **BLOQUEADA POR DECISIÓN** |
| D4 | Procedimiento de acreditación | **BLOQUEADA POR DECISIÓN** |

---

## §4 Pendiente de evidencia

| ID | Qué mide | Estado |
|---|---|---|
| H1' | ¿Phase 7a rompe igualdad semántica entre `float` y `Decimal`? | **PENDIENTE** — simulación por ejecutar |
| H2 | ¿Existe consumidor de `obtener_por_tipo()` cuyo output cambie con `timestamp`? | **PENDIENTE** — grep + inspección |
| N03 | ¿Existen stores productivos con datos históricos? | **PENDIENTE** — búsqueda en filesystem |

---

## §5 Tareas materializables

| ID | Descripción | Bloqueada por | Estado |
|---|---|---|---|
| M-01 | Materializar contrato de dominio monetario (sucesor conceptual de `DECIMAL.md`) | D10-01, D10a, D10b, D9 | **BLOQUEADA** |
| M-02 | Materializar este tablero | — | **EN CURSO** (este documento) |
| M-03 | Materializar contrato v2 de gobernanza | — | **PENDIENTE** (cuerpo no emitido íntegramente) |

---

## §6 Reglas de gobernanza

1. Una decisión `ADOPTADA` no cierra dependientes. Cada dependiente tiene su propio criterio de cierre.
2. Una recomendación técnica no es una decisión. Solo el operador convierte recomendaciones en decisiones.
3. Un hecho medido no es una decisión. La evidencia informa; no autoriza.
4. Materializar este tablero **no autoriza** migración, intervención técnica, ni modificación de `Ledger` / `SQLiteStore` / `JSONStore`.
5. Toda decisión adoptada debe registrar: fecha, opción elegida, justificación, y referencia al criterio de cierre del contrato.
6. Un defecto textual corregido no equivale a una garantía técnica demostrada.
7. Una prueba verde no equivale a una decisión de gobernanza.

---

## §7 Protocolo de actualización

Cuando el operador adopte una decisión:

1. Mover la fila de `BLOQUEADA POR DECISIÓN` a `ADOPTADA`.
2. Registrar opción, fecha y justificación en §6 como entrada nueva.
3. Re-evaluar cada dependiente: ¿sigue bloqueado o ahora puede decidirse?
4. Commits atómicos: uno por cambio de estado.

Si una decisión requiere evidencia antes de adoptarse, moverla a
`PENDIENTE DE EVIDENCIA` con la medición concreta requerida.

Si una condicional activa su condición, moverla de `CONDICIONAL` a
`BLOQUEADA POR DECISIÓN` y actualizar el conteo de §8.

---

## §8 Estado agregado (informativo, no normativo)

**Decisiones activas: 14**

- §2 (dominio monetario): 5
  - D10-01, D10a, D10b, D9, D3a
- §3 (integridad/versionado): 9
  - D1, D1b, D1c, D1d, D2, D5, D6, D8, D4

**Distribución por estado:**

- `ADOPTADA`: 0
- `BLOQUEADA POR DECISIÓN`: 14

**Elementos no computados como decisión activa:**

- Decisiones condicionales: 1 (D3b — se activa solo si D3a=(c))
- Reservas sin asignar: 1 (D7)

**Pendientes de evidencia:** 3 (H1', H2, N03)

**Tareas materializables:** 3
- M-01: bloqueada por decisiones de dominio monetario
- M-02: tablero en materialización (este documento)
- M-03: contrato v2 pendiente de materialización completa

**Nota sobre el total futuro:** si D3a=(c) se adopta, D3b pasa de
`CONDICIONAL` a activa y el total de decisiones activas será 15. Este
conteo refleja el estado **actual**; no anticipa el resultado de
decisiones pendientes.

**Conclusión:** ninguna decisión está adoptada. El tablero gobierna
el proceso de adopción; no representa una autorización de intervención.

---

## §9 Verificación de integridad del pegado

Ejecutar tras pegar y **antes** de commitear.

**Script consolidado:**

```bash
F=docs/FASE_7_TABLERO_DECISIONES.md
echo "lineas:               $(wc -l < $F)"
echo "secciones:            $(grep -c '^## §' $F)"
echo "filas_D_total:        $(grep -cE '^\| D[0-9]' $F)"
echo "filas_condicionales:  $(grep -cE '^\| D[0-9].*CONDICIONAL' $F)"
echo "filas_D3a:            $(grep -cE '^\| D3a ' $F)"
echo "filas_D3b:            $(grep -cE '^\| D3b ' $F)"
echo "activas_by_state:     $(( $(grep -cE '^\| D[0-9]' $F) - $(grep -cE '^\| D[0-9].*CONDICIONAL' $F) ))"
echo "activas_by_name:      $(( $(grep -cE '^\| D[0-9]' $F) - $(grep -cE '^\| D3b ' $F) ))"
echo "D7_reserva_fila:      $(grep -cE '^\| .*\(D7\)' $F)"
echo "D7_decision_activa:   $(grep -cE '^\| D7 ' $F)"
echo "evidencia:            $(grep -cE -e '^\| H1.' -e '^\| H2 ' -e '^\| N03 ' $F)"
echo "tareas:               $(grep -cE '^\| M-0[123]' $F)"
echo "decl_activas:         $(grep -cE '^\*\*Decisiones activas: 14\*\*' $F)"
echo "decl_condicionales:   $(grep -cE '^- Decisiones condicionales: 1' $F)"
echo "decl_reservas:        $(grep -cE '^- Reservas sin asignar: 1' $F)"


Valores esperados:

Variable Esperado
lineas 150–200
secciones 9
filas_D_total 15
filas_condicionales 1
filas_D3a 1
filas_D3b 1
activas_by_state 14
activas_by_name 14
D7_reserva_fila 1
D7_decision_activa 0
evidencia 3
tareas 3
decl_activas 1
decl_condicionales 1
decl_reservas 1

Criterios de coherencia:

1. filas_D_total − filas_condicionales = activas_by_state (15 − 1 = 14).
2. filas_D_total − filas_D3b = activas_by_name (15 − 1 = 14).
3. filas_condicionales = filas_D3b = 1 (D3b es la única condicional).
4. activas_by_state = activas_by_name = 14.
5. activas_by_state = decl_activas.
6. filas_condicionales = decl_condicionales.
7. filas_D3b ≥ 1 (presencia explícita).

Nota sobre H1': el patrón ^\| H1. usa . para absorber el apóstrofo.

Si algún conteo falla, no commitear.

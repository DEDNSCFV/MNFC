# Contrato técnico reconstruido: migración monetaria float → Decimal

- **Identificador:** MNFC-DECIMAL
- **Versión del documento:** 0.1.0
- **Estado:** PROPUESTA_NO_ACREDITADA
- **Base de evidencia:** `MATRIZ_MIGRACION_DECIMAL.txt`
- **Base de código de la matriz:** commit `56a4ba0`
- **Fecha de la matriz:** 2026-10-18
- **Autoridad de decisión:** Operador del SCFV
- **Alcance:** contrato técnico; no constituye autorización de ejecución

> Este documento es una reconstrucción contractual nueva. No debe presentarse
> como recuperación literal de un contrato anterior. Sus propuestas requieren
> revisión, falsación y aprobación expresa del Operador.

## 1. Objeto

Establecer las condiciones técnicas que deberá satisfacer una eventual
migración de importes monetarios y magnitudes contables desde `float` hacia
`Decimal` en MNFC.

La migración no consiste en sustituir indiscriminadamente todas las
apariciones de `float`. Debe preservar los contratos no monetarios, la
trazabilidad de los hechos, la persistencia, la determinación de resultados y
la verificabilidad de la cadena de eventos.

Este contrato separa cuatro estados:

1. Evidencia recopilada.
2. Contrato técnico propuesto.
3. Autorización de ejecución.
4. Acreditación posterior mediante pruebas y revisión independiente.

Ninguno de estos estados implica automáticamente el siguiente.

## 2. Línea base y límites de la evidencia

La matriz congelada informa de usos de `float`, conversiones, comprobaciones
de tipos, modelos contables, serialización, persistencia, Ledger y pruebas.

La suite ejecutada después de instalar el paquete en modo editable produjo:

`595 passed, 7 deselected, 1 xfailed`

Este resultado acredita únicamente que la suite ejecutada terminó con código
de salida cero en ese entorno. No acredita la migración a `Decimal`, la
integridad histórica de los hashes ni la suficiencia de las pruebas para
todos los requisitos de este contrato.

Antes de certificar la línea base de fuente, se deberá comprobar explícitamente
que los módulos importados durante las pruebas proceden de `src/`.

La matriz `MATRIZ_MIGRACION_DECIMAL.txt` es evidencia congelada y no debe
modificarse para acomodarla a decisiones posteriores.

## 3. Clasificación de magnitudes

Cada uso numérico deberá clasificarse por su significado y contrato, no
solamente por su tipo actual.

### 3.1. Magnitudes monetarias y contables

Candidatos a `Decimal`, sujetos a revisión de sus contratos:

- Importes de partidas y líneas de asientos.
- Totales Debe y Haber.
- Montos que pasan por el ensamblador DSL.
- Importes procesados por el serializador, los reportes y la persistencia.
- Funciones monetarias de `baldor`, incluidas las operaciones de suma,
  cuadre y cálculo de base e IVA.

La clasificación definitiva debe revisarse archivo por archivo y función por
función.

### 3.2. Magnitudes no monetarias

Las funciones estadísticas y matemáticas generales podrán conservar `float`
cuando ese sea su contrato apropiado.

No se autoriza una conversión global de todos los números del proyecto.

### 3.3. Ambigüedades

Toda magnitud cuyo dominio no esté determinado quedará pendiente de decisión.
No se resolverá por inferencia automática ni por conveniencia de implementación.

## 4. Contrato de representación monetaria

### 4.1. Tipo

La propuesta es utilizar `decimal.Decimal` en las fronteras internas que
representan importes monetarios, una vez aprobada la clasificación de cada
frontera.

### 4.2. Construcción

La implementación deberá evitar construir importes mediante conversiones
silenciosas desde valores binarios `float`.

Las entradas monetarias deberán proceder de representaciones explícitas y
controladas, por ejemplo cadenas decimales o enteros, de acuerdo con el
contrato de cada interfaz.

No se considerará equivalente:

- Interpretar el texto decimal original.
- Convertir un `float` ya aproximado a `Decimal`.

La política de aceptación de entradas `int`, `float`, `str` y `Decimal` deberá
documentarse en cada frontera. Los booleanos no deberán aceptarse como
importes por el hecho de ser subtipo de `int` en Python.

### 4.3. Valores inválidos

Las fronteras monetarias deberán definir el tratamiento de:

- Valores no finitos.
- Importes negativos cuando el dominio los prohíba.
- Cadenas inválidas.
- Tipos no admitidos.
- Valores fuera de los límites documentados.

No se ocultarán errores mediante conversiones implícitas.

### 4.4. Escala, precisión y redondeo

Quedan pendientes de aprobación expresa:

- Escala admitida para los importes.
- Precisión de cálculo.
- Política de redondeo.
- Momento y frontera en los que, si corresponde, se redondea.
- Tratamiento de monedas o magnitudes con escalas diferentes.

El núcleo no deberá introducir redondeos silenciosos ni fijar una escala
monetaria universal sin un contrato aprobado.

## 5. Cuadre contable

La propuesta es que el cuadre contable opere con valores decimales y que su
criterio de igualdad se defina expresamente.

No se presume que la tolerancia actual de `0.001` sea adecuada para la
contabilidad decimal. Tampoco se cambia ese comportamiento antes de aprobar
la política.

Antes de la implementación se deberá decidir:

1. Si el cuadre exige igualdad decimal exacta o admite una regla de tolerancia
   explícita.
2. Cómo se representan y comparan Debe y Haber.
3. Qué tratamiento corresponde a la escala y al redondeo.
4. Qué errores se producen ante valores inválidos.

Las pruebas deberán cubrir igualdad, desigualdad, límites y casos que
actualmente dependan de aproximaciones binarias.

## 6. Serialización y persistencia

La matriz identifica el serializador, los stores JSON y SQLite y la
persistencia del DSL como consumidores relevantes.

La migración deberá establecer una representación canónica de `Decimal` que
sea:

- Determinista.
- Reversible sin pérdida para los valores admitidos.
- Explícita respecto del tipo.
- Compatible con la validación del esquema.
- Independiente de formatos locales de presentación.

La representación elegida deberá distinguir el valor decimal del texto
destinado únicamente a presentación.

No se supondrá que el soporte actual de `int`, `float`, `str` y `bool`
incluye automáticamente `Decimal`.

### 6.1. Atomicidad

Si una operación no puede serializar todos los datos requeridos, deberá
preservar el contrato de ausencia de escrituras parciales donde este sea
aplicable.

La implementación y las pruebas deberán documentar el alcance real de la
atomicidad de cada store, incluidos los límites y mecanismos de recuperación.

### 6.2. Compatibilidad

Se deberá definir cómo se leen los datos históricos y cómo se distinguen
los esquemas antiguos de los nuevos.

No se cambiará silenciosamente la interpretación de registros existentes.

## 7. Ledger e integridad histórica

La matriz describe un encadenamiento de hashes con SHA-256 y una entrada
conceptual de la forma:

`SHA256(prev_hash || canonical_json(contenido))`

También identifica la construcción de un payload que concatena el hash previo
y la representación canónica del contenido.

La implementación exacta deberá verificarse directamente en el código antes
de acreditar este contrato. La matriz es evidencia de análisis, no sustituto
de la inspección del código ejecutable.

### 7.1. Riesgo

Cambiar la representación de un contenido de `float` a `Decimal` puede
cambiar su serialización canónica. Si cambia el contenido de entrada al hash,
el hash recalculado puede diferir del valor histórico.

Por tanto, cambiar tipos, serialización o canonicalización puede afectar la
verificación de la cadena aunque el importe aparente ser equivalente.

### 7.2. Versionado propuesto

Se propone introducir una identificación explícita de la versión de esquema
de payload/hash para los nuevos datos. El nombre `payload_version` es
provisional y deberá contrastarse con el modelo real del Ledger.

La versión deberá permitir determinar qué reglas de canonicalización
corresponden a cada evento. No basta con asumir que todos los eventos pueden
interpretarse con la regla más reciente.

Antes de implementar el versionado deberán definirse:

- La representación histórica que debe seguir siendo verificable.
- La representación canónica de los nuevos payloads decimales.
- La forma en que se identifica la versión aplicable.
- El comportamiento ante versiones desconocidas o inválidas.
- La compatibilidad entre eventos y hashes encadenados.
- La política de migración de datos ya persistidos.

### 7.3. No reescritura de hashes históricos

La propuesta prohíbe recalcular y sustituir silenciosamente los hashes
históricos para hacerlos coincidir con la nueva representación.

La verificación histórica deberá conservar acceso a las reglas de
interpretación y canonicalización con las que se generaron los hashes
originales.

Si se requiere una nueva cadena o representación derivada, deberá tratarse
como una operación explícita, trazable y separada; no como una corrección
invisible de la historia.

### 7.4. Doble verificación

Antes de acreditar la migración se deberán probar, de forma separada:

1. Verificación de los registros históricos conforme a su representación
   original.
2. Verificación de nuevos registros conforme al esquema decimal aprobado.

También se deberá probar el encadenamiento entre registros, el rechazo de
alteraciones y el comportamiento ante cambios de versión.

La estrategia concreta de doble verificación queda pendiente de validación
contra la implementación real. Este documento no afirma que ya exista.

## 8. Dependencias y alcance de la migración

La matriz señala, entre otros, los siguientes puntos de revisión:

- `src/mnfc/mnfc.py`
- `src/mnfc/baldor.py`
- `src/mnfc/extensiones/modelos.py`
- `src/mnfc/extensiones/serializador.py`
- `src/mnfc/extensiones/persistencia/sqlite_store.py`
- `src/mnfc/extensiones/persistencia/json_store.py`
- `src/mnfc/extensiones/reportes.py`
- `src/mnfc/dsl/assembler.py`
- `src/mnfc/dsl/evaluator.py`
- `src/mnfc/dsl/registry.py`
- `src/mnfc/dsl/persistencia.py`
- Implementación del Ledger y sus pruebas.

Esta lista es un inventario inicial derivado de la matriz, no una declaración
de que todos los puntos deban cambiar ni de que no existan otros consumidores.

Cada frontera deberá revisarse por sus productores, consumidores, tipos
admitidos, validaciones, serialización y efectos persistentes.

Las funciones estadísticas no se incorporarán a la migración monetaria sin
una justificación contractual específica.

## 9. Pruebas de aceptación requeridas

La acreditación futura deberá incluir, como mínimo:

1. Confirmación de que las pruebas importan el código fuente esperado.
2. Regresión de la suite existente.
3. Pruebas de construcción explícita de valores `Decimal`.
4. Rechazo de tipos y valores inválidos según contrato.
5. Cuadre contable con los criterios aprobados.
6. Serialización y deserialización decimal sin pérdida.
7. Persistencia y recuperación en JSON y SQLite.
8. Ausencia de escrituras parciales ante errores de serialización, dentro del
   alcance de atomicidad definido.
9. Integridad y determinismo del Ledger.
10. Verificación de hashes históricos sin reescribirlos.
11. Verificación de nuevos eventos con el esquema aprobado.
12. Pruebas de encadenamiento, alteración, versión desconocida y regresión.
13. Confirmación de que las funciones no monetarias conservan sus contratos.
14. Pruebas de integración del DSL, ensamblador, modelos y reportes.

Los resultados deberán registrar comando, entorno, versión del código,
resultado, artefactos y limitaciones.

Una suite verde es evidencia necesaria cuando corresponda, pero no es por sí
sola acreditación técnica ni autorización de despliegue.

## 10. Condiciones de bloqueo

La migración no podrá declararse acreditada si se presenta cualquiera de
estas condiciones:

- No está clasificada una frontera monetaria afectada.
- La política de precisión, escala o redondeo sigue indeterminada donde sea
  necesaria para decidir el resultado.
- El serializador no preserva el valor admitido.
- La persistencia no puede recuperar el dato conforme al contrato.
- Se alteran hashes históricos sin una operación autorizada y trazable.
- No puede verificarse la cadena histórica.
- El nuevo esquema no identifica de manera inequívoca su canonicalización.
- Las pruebas no corresponden al código fuente que se pretende acreditar.
- Se confunde la aprobación de pruebas con la autorización de ejecución.

## 11. Gobernanza y estados

Estados de este artefacto:

- `PROPUESTA_NO_ACREDITADA`: estado inicial de este documento.
- `EN_REVISION`: sometido a revisión técnica y falsación.
- `APROBADO_TECNICAMENTE`: requisitos técnicos revisados y aceptados; no
  autoriza por sí solo la ejecución.
- `ACREDITADO`: evidencia de aceptación revisada según el procedimiento
  aplicable.
- `BLOQUEADO`: existe una condición de bloqueo no resuelta.

El cambio de estado debe quedar documentado y trazable.

La autorización de gobernanza de la fase de ejecución corresponde a un
artefacto separado: `docs/FASE_7_CONTRATO.md`. Este documento no lo sustituye.

## 12. Pendientes antes de acreditar

- [ ] Verificar la ruta real de importación durante la suite.
- [ ] Inspeccionar la implementación real de canonicalización y hashing.
- [ ] Identificar cómo se persisten y verifican los hashes históricos.
- [ ] Definir el esquema decimal canónico.
- [ ] Aprobar escala, precisión y redondeo.
- [ ] Aprobar el criterio de cuadre contable.
- [ ] Definir el versionado de payload/hash y la doble verificación.
- [ ] Revisar los consumidores y las fronteras de tipos.
- [ ] Ejecutar las pruebas de aceptación.
- [ ] Obtener revisión independiente.
- [ ] Obtener autorización expresa del Operador mediante el procedimiento
      de gobernanza correspondiente.

## 13. Declaración final

Este documento define una propuesta de contrato técnico para orientar la
revisión de la migración `float → Decimal`.

No declara que la migración esté implementada, verificada, acreditada ni
autorizada. No modifica los datos históricos, el Ledger, la matriz congelada
ni el código fuente.

La secuencia de trabajo continúa siendo:

**HECHO → CONTRATO → FALSACIÓN → INTERVENCIÓN → VERIFICACIÓN**

Sin evidencia suficiente no se acredita. Sin autorización expresa no se
ejecuta.

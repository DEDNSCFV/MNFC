# MNFC · Motor Nucleo Fractal Contable

**Materializacion del nucleo del Programa de Investigacion SCFV.**

Kernel formal de partida doble. Recibe lineas contables, clasifica
DEBE/HABER, verifica cuadre, persiste en ledger inmutable.

---

## Nomenclatura

- **M**otor - implementa el ciclo: recibe lineas, clasifica, acumula,
  verifica cuadre, devuelve asiento.
- **N**ucleo - pieza minima de la que todo lo demas depende.
- **F**ractal - la misma ley se aplica identicamente en toda escala:
  linea, asiento, periodo, libro. Principio de autosimilitud tomado de
  Mandelbrot (1975 L11: "cuando las partes, por pequenas que estas sean,
  se parecen al todo"), suavizado del dominio geometrico al operativo
  (Mandelbrot 1982 L769: "el adjetivo suaviza el significado").
- **C**ontable - opera en el dominio de la partida doble.

---

## Que es MNFC

Un **kernel** de partida doble. Seis capas fractales:

| Capa | Archivo | Escala | Rol |
|------|---------|--------|-----|
| 0 | xnor.py        | Una linea  | Decide DEBE/HABER |
| 1 | baldor.py      | Un asiento | Aritmetica contable |
| 2 | estadistica.py | Un periodo | Medida estadistica |
| 3 | fractal.py     | El libro   | Autosimilitud escalante |
| 4 | mnfc.py        | El proceso | Composicion |
| 5 | __init__.py    | El motor   | Fachada publica |
| 6 | ledger.py      | El tiempo  | Cadena de hashes inmutable |

## Que NO es MNFC

- No es un ERP.
- No persiste a disco (el usuario decide donde guardar la cadena).
- No hace transacciones distribuidas.
- No reporta (genera la salida; los reportes son del usuario).
- No decide contabilidad profesional (eso es H2, fuera del kernel).
- No incluye catalogo de cuentas (PCU): eso es logica de negocio.

---

## Instalacion

Desde GitHub:

    pip install git+https://github.com/DEDNSCFV/MNFC.git@v0.2.0

Desde PyPI (proximamente):

    pip install mnfc

Modo desarrollo (con tests):

    git clone https://github.com/DEDNSCFV/MNFC.git
    cd MNFC
    pip install -e ".[test]"
    pytest tests/

---

## Uso minimo

### Clasificar un asiento

    from mnfc import procesar_asiento

    asiento = procesar_asiento([
        {"naturaleza": "DEUDORA",   "movimiento": "AUMENTA", "monto": 1000},
        {"naturaleza": "ACREEDORA", "movimiento": "AUMENTA", "monto": 1000},
    ])
    print(asiento)
    # Asiento(n=2, debe=1000.0, haber=1000.0, cuadrado)

### Encadenar en un ledger inmutable

    from mnfc import Ledger

    ledger = Ledger()
    ledger.append({"cuenta": "Caja",   "ubicacion": "DEBE",  "monto": 1000})
    ledger.append({"cuenta": "Ventas", "ubicacion": "HABER", "monto": 1000})

    assert ledger.verify()
    print(ledger.raiz())

### Analisis estadistico y fractal

    from mnfc import media, exponente_escalante, clasificar_cascada

    serie = [100, 120, 90, 130, 110, 105]
    print(media(serie))
    print(exponente_escalante(serie))
    print(clasificar_cascada(serie))

---

## Extensiones (v0.2.0) - Capa 7

Ademas del kernel, MNFC incluye extensiones importables desde
mnfc.extensiones. Son opt-in: el kernel sigue siendo ligero para
quien no las necesita.

### Persistencia intercambiable

- **StoreBase** - interfaz abstracta de almacenamiento.
- **SQLiteStore** - persistencia en SQLite con cadena hash Merkle.
- **JSONStore** - persistencia en archivo JSON, misma semantica.

Los dos backends producen el **mismo hash** para el mismo evento
(compatibilidad cross-backend verificada). Un ledger guardado en JSON
es verificable por una implementacion SQLite y viceversa.

### Maquina de estados del asiento

- **MaquinaEstadosAsiento** - gobierna el ciclo de vida:
  PROPUESTO -> EVALUADO -> ADMITIDO/MODIFICADO/RECHAZADO -> ASENTADO -> ANULADO.
- **Transicion** - registro inmutable de cada cambio de estado.
- **obtener_historial()** - devuelve el historial completo serializable.

### Reportes

- **generar_csv_diario** - libro diario del periodo.
- **generar_csv_mayor** - mayor por cuenta.
- **generar_csv_balance** - balance por rubros.
- **generar_pdf_diario** - libro diario en PDF (requiere fpdf).

### Otros componentes

- **ReticuloCuentas** - algebra booleana sobre el conjunto potencia
  de cuentas. Misma ley que xnor.py, a otra escala.
- **ExaminadorEvidencia** - validador de evidencia contable.
- **serializar / deserializar** - serializacion canonica determinista.
- **Asiento / LineaAsiento** - versiones tipadas.

### Compatibilidad

La API publica de mnfc (from mnfc import procesar_asiento) **no
cambia** entre v0.1.0 y v0.2.0. Es una version menor: agrega sin romper.

---

## Fundamento bibliografico

Cada capa cita su fuente primaria con linea de raw verificada.

| Tradicion | Obra | Aporte |
|-----------|------|--------|
| Boole 1847 | The Mathematical Analysis of Logic | Ley xx = x (L2022). Simbolos electivos distributivos y conmutativos (L2089). Regla de casos mutuamente exclusivos (L6066). |
| Baldor | Algebra | Ley de signos (L1885-1888). Leyes formales (L1676-1699). Reduccion de terminos semejantes (L874-997). |
| Mendenhall 13ed | Introduccion a la probabilidad y estadistica | Descriptivas (L6777-6820). Distribuciones (L16827-16880). Muestreo (L17791-18667). Tabla 8.7 (L22541-22560). |
| Mandelbrot 1975/1982 | Les objets fractals / La geometria fractal de la naturaleza | Autosimilitud (1975 L11). Exponente = dimension fractal (1975 L461). Escalante suaviza (1982 L769). Cascada de escalas (1982 L738). |
| Merkle 1979 | A Certified Digital Signature | Arbol de autenticacion (L2463). Camino de autenticacion (L2475). Raiz del arbol (L2564). |
| ProGit 2014 | Pro Git | Direccionamiento por hash SHA-1 (L494). Inmutabilidad (L684). Firma GPG (L2127). |

---

## Estado epistemico por capa

Taxonomia:

- **N1** - identificada (locus en raw)
- **N2** - reconstruida (notacion traducida)
- **N3** - verificada (confrontada contra PDF original)
- **N4** - aplicada (dominio real)

| Capa | N1 locus | N2 | N3 | N4 |
|------|----------|----|----|----|
| 0 xnor        | Anexo I + Boole 1847      | -  | verificacion matematica exhaustiva | aplicada |
| 1 baldor      | Baldor L1885+             | -  | pendiente auditoria N3 formal      | dominio contable |
| 2 estadistica | Mendenhall caps 2,6,7,8   | si | pendiente PDF                      | pendiente |
| 3 fractal     | Mandelbrot 1975/1982      | si | pendiente PDF                      | pendiente |
| 4 mnfc        | N/A (composicion)         | -  | N/A                                | aplicada |
| 6 ledger      | Merkle 1979 + ProGit 2014 | -  | pendiente PDF                      | pendiente |

---

## Rendimiento

Medido en Termux / Android / aarch64 / Python 3.13:

| Operacion | Tiempo/op | Throughput |
|-----------|-----------|------------|
| calcular_ubicacion | 0.72 us | 1,381,916 ops/s |
| procesar_asiento (4 lineas) | 15.93 us | 62,759 asientos/s |
| procesar_asiento (100 lineas) | 308.60 us | 3,240 asientos/s |
| Ledger.append | 20.46 us | 48,882 bloques/s |
| Ledger.verify (10k bloques) | 188.1 ms | - |
| Memoria por bloque | 361 B | - |
| Fractal (serie 100k) | 164.5 ms | - |

Sin dependencias externas. Solo stdlib.

Correr los benchmarks localmente:

    pytest tests/test_estres.py -v -m slow -s

---

## Tests

Suite completa:

    pytest tests/                # rapida (108 tests)
    pytest tests/ -m slow -s     # estres (7 tests)
    pytest tests/ -m ""          # todo (115 tests)

Categorias:

- test_integracion.py - end-to-end de las 6 capas
- test_bordes.py      - inputs extremos
- test_contratos.py   - determinismo + mensajes de error
- test_fuzzing.py     - 4,900 iteraciones con semilla fija
- test_estres.py      - benchmarks marcados slow
- test_extensiones.py - integracion kernel + extensiones

---

## Licencia

Licencia dual: **AGPL-3.0-or-later OR Commercial**.

### AGPL-3.0-or-later

Gratis para software cuyo codigo sea tambien AGPL-compatible.
Obligacion: quien use MNFC en un servicio de red debe publicar
el codigo completo de ese servicio bajo AGPL.

### Licencia comercial

Para uso en software propietario o servicios cerrados. Requiere
contrato con el autor. Contacto: **lic.dedn@gmail.com**

### Deuda de atribucion

Todo uso de MNFC, comercial o AGPL, obliga a declarar explicitamente
que se usa MNFC en los creditos del producto. Ver NOTICE.

---

## Contribuir

Ver CONTRIBUTING.md. Toda contribucion requiere aceptacion del CLA
(Contributor License Agreement) para preservar la licencia dual.

---

## Autor

**Domingo Eduardo Diaz Navas**
Programa de Investigacion SCFV
lic.dedn@gmail.com

Repositorio: https://github.com/DEDNSCFV/MNFC
Programa:    https://github.com/DEDNSCFV/Programa-de-Investigacion-SCFV

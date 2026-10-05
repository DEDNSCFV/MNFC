"""
Test de integracion end-to-end - las 6 capas en un flujo realista.

Simula el uso real del motor: 3 asientos contables, cada uno
clasificado por capa 0, compuesto por capa 4, persistido en el
ledger inmutable de capa 6, y analizado estadistica y fractalmente
por capas 2 y 3.
"""
from mnfc import (
    # Capa 0
    calcular_ubicacion,
    # Capa 1
    verificar_cuadre,
    # Capa 2
    media, desviacion_muestral,
    # Capa 3
    exponente_escalante, clasificar_cascada,
    # Capa 4
    procesar_asiento,
    # Capa 6
    Ledger, GENESIS,
)


def test_ciclo_completo_6_capas():
    """Un flujo realista que atraviesa las 6 capas."""
    # --- 3 asientos de entrada ---
    asientos_input = [
        [
            {"cuenta": "1105", "naturaleza": "DEUDORA",   "movimiento": "AUMENTA", "monto": 1000.0},
            {"cuenta": "4135", "naturaleza": "ACREEDORA", "movimiento": "AUMENTA", "monto": 1000.0},
        ],
        [
            {"cuenta": "1105", "naturaleza": "DEUDORA",   "movimiento": "AUMENTA", "monto": 2000.0},
            {"cuenta": "4135", "naturaleza": "ACREEDORA", "movimiento": "AUMENTA", "monto": 2000.0},
        ],
        [
            {"cuenta": "1105", "naturaleza": "DEUDORA",   "movimiento": "AUMENTA", "monto": 3000.0},
            {"cuenta": "4135", "naturaleza": "ACREEDORA", "movimiento": "AUMENTA", "monto": 3000.0},
        ],
    ]

    # --- CAPA 0 verificada en cada linea por procesar_asiento ---
    ubi = calcular_ubicacion("DEUDORA", "AUMENTA")
    assert ubi == "DEBE"

    # --- CAPA 4: composicion ---
    asientos = [procesar_asiento(lineas) for lineas in asientos_input]
    assert all(a.cuadrado for a in asientos)
    assert len(asientos) == 3

    # --- CAPA 1: cuadre verificado en cada asiento ---
    for a in asientos:
        assert verificar_cuadre(a.total_debe, a.total_haber)

    # --- CAPA 6: ledger inmutable ---
    ledger = Ledger()
    for a in asientos:
        ledger.append({"debe": a.total_debe, "haber": a.total_haber})

    assert len(ledger) == 3
    assert ledger.verify(), "cadena Merkle rota"
    raiz = ledger.raiz()
    assert raiz != GENESIS
    assert len(raiz) == 64

    # --- CAPA 2: estadistica sobre los montos ---
    montos = [a.total_debe for a in asientos]
    m = media(montos)
    s = desviacion_muestral(montos)
    assert m == 2000.0
    assert s > 0

    # --- CAPA 3: analisis fractal del flujo ---
    serie = montos * 4   # replicada para tener N suficiente
    beta = exponente_escalante(serie)
    clasif = clasificar_cascada(serie)
    assert clasif in ("plana", "lineal", "acumulada", "escalante")

    # --- Alteraacion del ledger debe romper la cadena ---
    ledger._contenidos[1] = {"debe": 9999.0, "haber": 9999.0}
    assert not ledger.verify(), "alteracion no detectada"


def test_ledger_determinista():
    """Dos ledgers con la misma secuencia producen la misma raiz."""
    l1 = Ledger()
    l2 = Ledger()
    for i in range(10):
        payload = {"n": i, "monto": i * 100}
        l1.append(payload)
        l2.append(payload)
    assert l1.raiz() == l2.raiz()
    assert l1.verify()
    assert l2.verify()


def test_ledger_alteracion_media():
    """Alterar un bloque en medio de la cadena la rompe."""
    l = Ledger()
    for i in range(5):
        l.append({"n": i})
    assert l.verify()
    l._contenidos[2] = {"n": 999}
    assert not l.verify()


def test_asiento_mixto_debe_haber():
    """Un asiento con lineas DEBE y HABER mezcladas debe cuadrar."""
    a = procesar_asiento([
        {"naturaleza": "DEUDORA",   "movimiento": "AUMENTA", "monto": 500.0},
        {"naturaleza": "DEUDORA",   "movimiento": "AUMENTA", "monto": 300.0},
        {"naturaleza": "ACREEDORA", "movimiento": "AUMENTA", "monto": 800.0},
    ])
    assert a.cuadrado
    assert a.total_debe == 800.0
    assert a.total_haber == 800.0
    assert len(a.lineas) == 3


def test_invariante_2_5_tres_caras():
    """Las 3 caras de xnor coinciden en los 4 casos (invariante 2.5)."""
    from mnfc import ubicacion_booleana, ubicacion_gf2, ubicacion_signos
    casos = [
        ("DEUDORA",   "AUMENTA"),
        ("DEUDORA",   "DISMINUYE"),
        ("ACREEDORA", "AUMENTA"),
        ("ACREEDORA", "DISMINUYE"),
    ]
    for n, m in casos:
        b = ubicacion_booleana(n, m)
        g = ubicacion_gf2(n, m)
        s = ubicacion_signos(n, m)
        assert b == g == s, f"divergencia en ({n},{m}): {b}/{g}/{s}"

"""
Categoria B - Fuzzing controlado.

Genera 1000+ combinaciones aleatorias con semilla fija (42).
Cada iteracion verifica un invariante que SIEMPRE debe cumplirse.

Semilla fija: random.seed(42) -> reproducible bit a bit.
"""
import random
import pytest
from mnfc import (
    calcular_ubicacion, ubicacion_booleana, ubicacion_gf2, ubicacion_signos,
    NATURALEZAS_VALIDAS, MOVIMIENTOS_VALIDOS,
    procesar_asiento, verificar_cuadre,
    media, mediana, desviacion_muestral,
    exponente_escalante, clasificar_cascada,
    Ledger, GENESIS,
)


# ─────────────────────────────────────────────────────────────────────
# F.1 Fuzzing de xnor - invariante 2.5 con 1000 combinaciones
# ─────────────────────────────────────────────────────────────────────

def test_fuzz_xnor_3_caras_1000_iteraciones():
    """Las 3 caras de xnor coinciden en TODAS las combinaciones."""
    random.seed(42)
    for i in range(1000):
        n = random.choice(NATURALEZAS_VALIDAS)
        m = random.choice(MOVIMIENTOS_VALIDOS)
        b = ubicacion_booleana(n, m)
        g = ubicacion_gf2(n, m)
        s = ubicacion_signos(n, m)
        assert b == g == s, f"iter {i}: ({n},{m}) -> {b}/{g}/{s}"


def test_fuzz_xnor_dominio_cerrado():
    """Todo par valido devuelve DEBE o HABER, nunca otra cosa."""
    random.seed(42)
    for i in range(500):
        n = random.choice(NATURALEZAS_VALIDAS)
        m = random.choice(MOVIMIENTOS_VALIDOS)
        r = calcular_ubicacion(n, m)
        assert r in ("DEBE", "HABER"), f"iter {i}: resultado invalido {r}"


# ─────────────────────────────────────────────────────────────────────
# F.2 Fuzzing de asientos - 1000 asientos random que deben cuadrar
# ─────────────────────────────────────────────────────────────────────

def _generar_asiento_cuadrado(rng):
    """Genera un asiento aleatorio que por construccion debe cuadrar."""
    n_lineas = rng.randint(1, 10)
    monto_base = rng.uniform(0.01, 1e6)

    # Mitad DEBE, mitad HABER (garantiza cuadre)
    lineas = []
    # Repartimos el monto en 2 partes: una mitad para DEBE, otra para HABER
    # Pero con N lineas random a cada lado

    n_debe = rng.randint(1, n_lineas)
    n_haber = rng.randint(1, n_lineas)

    # Monto DEBE: dividimos monto_base en n_debe partes
    montos_debe = []
    restante = monto_base
    for i in range(n_debe - 1):
        parte = round(rng.uniform(0.01, restante / 2), 2)
        montos_debe.append(parte)
        restante -= parte
    montos_debe.append(round(restante, 2))

    # Monto HABER: dividimos monto_base en n_haber partes
    montos_haber = []
    restante = monto_base
    for i in range(n_haber - 1):
        parte = round(rng.uniform(0.01, restante / 2), 2)
        montos_haber.append(parte)
        restante -= parte
    montos_haber.append(round(restante, 2))

    for m in montos_debe:
        lineas.append({"naturaleza": "DEUDORA",   "movimiento": "AUMENTA", "monto": m})
    for m in montos_haber:
        lineas.append({"naturaleza": "ACREEDORA", "movimiento": "AUMENTA", "monto": m})

    return lineas


def test_fuzz_1000_asientos_cuadran():
    """1000 asientos generados aleatoriamente deben cuadrar."""
    rng = random.Random(42)
    fallidos = 0
    for i in range(1000):
        lineas = _generar_asiento_cuadrado(rng)
        a = procesar_asiento(lineas)
        if not a.cuadrado:
            fallidos += 1
        assert a.cuadrado, f"iter {i} descuadrado"
    assert fallidos == 0


# ─────────────────────────────────────────────────────────────────────
# F.3 Fuzzing de series para fractal
# ─────────────────────────────────────────────────────────────────────

def test_fuzz_500_series_clasificacion_valida():
    """Toda serie aleatoria debe clasificarse en uno de los 4 valores."""
    rng = random.Random(42)
    clasificaciones = set()
    validos = {"plana", "lineal", "acumulada", "escalante"}

    for i in range(500):
        n = rng.randint(50, 500)
        xs = [rng.gauss(100, 20) for _ in range(n)]
        c = clasificar_cascada(xs)
        assert c in validos, f"iter {i}: clasificacion invalida {c}"
        clasificaciones.add(c)

    # Al menos 2 clasificaciones distintas (con 500 series random)
    assert len(clasificaciones) >= 2, f"solo {clasificaciones}"


def test_fuzz_exponente_escalante_es_float():
    """exponente_escalante devuelve float en todos los casos."""
    rng = random.Random(42)
    for i in range(200):
        n = rng.randint(50, 300)
        xs = [rng.random() * 1000 for _ in range(n)]
        beta = exponente_escalante(xs)
        assert isinstance(beta, float)
        # Beta tiene que ser un numero finito
        import math
        assert math.isfinite(beta), f"iter {i}: beta no finito: {beta}"


# ─────────────────────────────────────────────────────────────────────
# F.4 Fuzzing de ledger
# ─────────────────────────────────────────────────────────────────────

def test_fuzz_500_ledgers_random_verify():
    """500 ledgers con contenidos random: verify() siempre True."""
    rng = random.Random(42)
    for i in range(500):
        l = Ledger()
        n_bloques = rng.randint(1, 20)
        for _ in range(n_bloques):
            # Contenido random variado
            contenido = {
                "cuenta": rng.choice(["Caja", "Banco", "Proveedores"]),
                "monto": round(rng.uniform(0.01, 1e6), 2),
                "n": rng.randint(0, 1000),
            }
            l.append(contenido)
        assert l.verify(), f"iter {i} verify() fallo"
        assert len(l.raiz()) == 64


def test_fuzz_alteracion_detectada():
    """Alterar cualquier bloque en un ledger random rompe verify()."""
    rng = random.Random(42)
    detecciones = 0
    for i in range(200):
        l = Ledger()
        n = rng.randint(3, 10)
        for j in range(n):
            l.append({"n": j, "v": rng.random()})
        assert l.verify()

        # Alterar un bloque aleatorio
        idx = rng.randint(0, n - 1)
        l._contenidos[idx] = {"ALTERADO": True}
        assert not l.verify(), f"iter {i}: alteracion no detectada"
        detecciones += 1

    assert detecciones == 200


# ─────────────────────────────────────────────────────────────────────
# F.5 Fuzzing de estadistica
# ─────────────────────────────────────────────────────────────────────

def test_fuzz_media_entre_min_y_max():
    """media siempre esta entre min y max de la serie."""
    rng = random.Random(42)
    for i in range(300):
        n = rng.randint(1, 100)
        xs = [rng.uniform(-1000, 1000) for _ in range(n)]
        m = media(xs)
        assert min(xs) <= m <= max(xs), f"iter {i}: {min(xs)} <= {m} <= {max(xs)}"


def test_fuzz_desviacion_no_negativa():
    """s >= 0 siempre."""
    rng = random.Random(42)
    for i in range(300):
        n = rng.randint(2, 100)
        xs = [rng.gauss(0, 1) for _ in range(n)]
        s = desviacion_muestral(xs)
        assert s >= 0, f"iter {i}: s={s}"


def test_fuzz_mediana_entre_min_y_max():
    """mediana siempre entre min y max."""
    rng = random.Random(42)
    for i in range(300):
        n = rng.randint(1, 100)
        xs = [rng.uniform(-100, 100) for _ in range(n)]
        md = mediana(xs)
        assert min(xs) <= md <= max(xs), f"iter {i}"


# ─────────────────────────────────────────────────────────────────────
# F.6 Fuzzing de determinismo
# ─────────────────────────────────────────────────────────────────────

def test_fuzz_hash_determinista_bajo_repeticion():
    """El mismo contenido produce el mismo hash en 100 repeticiones."""
    rng = random.Random(42)
    for i in range(100):
        contenido = {
            "n": rng.randint(0, 1000),
            "v": round(rng.random(), 6),
            "s": rng.choice(["a", "b", "c"]),
        }
        hashes = set()
        for _ in range(10):
            l = Ledger()
            hashes.add(l.append(contenido))
        assert len(hashes) == 1, f"iter {i}: hashes divergentes {hashes}"

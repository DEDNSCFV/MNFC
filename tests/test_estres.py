"""
Categoria C - Pruebas de estres.

Marcadas con @pytest.mark.slow. Por defecto NO se corren.
Para correrlas:

    python3 -m pytest tests/test_estres.py -v -m slow -s

Miden rendimiento bajo carga. No buscan bugs funcionales -
buscan degradacion, fugas de memoria, tiempos excesivos.
"""
import time
import tracemalloc
import gc
import random
import pytest
from mnfc import (
    calcular_ubicacion, procesar_asiento, Ledger,
    exponente_escalante, clasificar_cascada,
)


def _fmt_tiempo(t):
    if t < 0.001:
        return f"{t*1e6:.1f} us"
    if t < 1:
        return f"{t*1000:.1f} ms"
    return f"{t:.2f} s"


def _fmt_memoria(bytes_):
    if bytes_ < 1024:
        return f"{bytes_} B"
    if bytes_ < 1024 * 1024:
        return f"{bytes_/1024:.1f} KB"
    return f"{bytes_/1024/1024:.2f} MB"


@pytest.mark.slow
def test_estres_100k_calcular_ubicacion():
    """100.000 llamadas a calcular_ubicacion."""
    N = 100_000
    print(f"\n[ESTRES] calcular_ubicacion x {N}")

    gc.collect()
    t0 = time.perf_counter()
    for _ in range(N):
        calcular_ubicacion("DEUDORA", "AUMENTA")
    dt = time.perf_counter() - t0

    print(f"  tiempo total : {_fmt_tiempo(dt)}")
    print(f"  por operacion: {dt/N*1e6:.2f} us")
    print(f"  throughput   : {N/dt:,.0f} ops/s")

    assert dt < 10.0, f"demasiado lento: {dt}s"


@pytest.mark.slow
@pytest.mark.parametrize("n_lineas,N", [(4, 10_000), (100, 1_000)])
def test_estres_asientos(n_lineas, N):
    """N asientos de n_lineas cada uno."""
    print(f"\n[ESTRES] procesar_asiento x {N} (n_lineas={n_lineas})")

    lineas = []
    for i in range(n_lineas // 2):
        lineas.append({"naturaleza": "DEUDORA",   "movimiento": "AUMENTA", "monto": 1.0})
    for i in range(n_lineas - n_lineas // 2):
        lineas.append({"naturaleza": "ACREEDORA", "movimiento": "AUMENTA", "monto": 1.0})

    gc.collect()
    t0 = time.perf_counter()
    for _ in range(N):
        procesar_asiento(lineas)
    dt = time.perf_counter() - t0

    print(f"  tiempo total : {_fmt_tiempo(dt)}")
    print(f"  por asiento  : {dt/N*1e6:.2f} us")
    print(f"  throughput   : {N/dt:,.0f} asientos/s")

    assert dt < 30.0, f"demasiado lento: {dt}s"


@pytest.mark.slow
def test_estres_ledger_10k():
    """Ledger con 10.000 bloques."""
    N = 10_000
    print(f"\n[ESTRES] Ledger.append x {N}")

    l = Ledger()
    gc.collect()
    t0 = time.perf_counter()
    for i in range(N):
        l.append({"n": i, "monto": i * 0.01})
    t_append = time.perf_counter() - t0

    print(f"  append total : {_fmt_tiempo(t_append)}")
    print(f"  por bloque   : {t_append/N*1e6:.2f} us")
    print(f"  throughput   : {N/t_append:,.0f} bloques/s")

    t0 = time.perf_counter()
    ok = l.verify()
    t_verify = time.perf_counter() - t0

    print(f"  verify       : {_fmt_tiempo(t_verify)}")
    print(f"  raiz         : {l.raiz()[:16]}...")

    assert ok
    assert len(l) == N
    assert t_append < 30.0


@pytest.mark.slow
def test_estres_memoria_ledger_10k():
    """Memoria de un ledger de 10.000 bloques."""
    N = 10_000
    print(f"\n[ESTRES] Memoria de Ledger con {N} bloques")

    gc.collect()
    tracemalloc.start()
    try:
        l = Ledger()
        for i in range(N):
            l.append({"n": i, "monto": i * 0.01})
        current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    print(f"  memoria actual: {_fmt_memoria(current)}")
    print(f"  memoria pico  : {_fmt_memoria(peak)}")
    print(f"  por bloque    : {peak/N:.0f} B")

    assert peak < 100 * 1024 * 1024


@pytest.mark.slow
def test_estres_asiento_1000_lineas():
    """Un unico asiento de 1000 lineas."""
    N_por_lado = 500
    print(f"\n[ESTRES] Asiento con {N_por_lado*2} lineas")

    lineas = []
    for i in range(N_por_lado):
        lineas.append({"naturaleza": "DEUDORA",   "movimiento": "AUMENTA", "monto": 0.01})
    for i in range(N_por_lado):
        lineas.append({"naturaleza": "ACREEDORA", "movimiento": "AUMENTA", "monto": 0.01})

    gc.collect()
    t0 = time.perf_counter()
    a = procesar_asiento(lineas)
    dt = time.perf_counter() - t0

    print(f"  tiempo       : {_fmt_tiempo(dt)}")
    print(f"  lineas       : {len(a.lineas)}")
    print(f"  debe         : {a.total_debe}")
    print(f"  haber        : {a.total_haber}")

    assert a.cuadrado
    assert len(a.lineas) == 1000
    assert dt < 5.0


@pytest.mark.slow
def test_estres_fractal_serie_100k():
    """Fractal sobre serie de 100.000 elementos."""
    print(f"\n[ESTRES] Fractal sobre serie de 100.000 elementos")
    rng = random.Random(42)
    xs = [rng.gauss(100, 20) for _ in range(100_000)]

    gc.collect()
    t0 = time.perf_counter()
    beta = exponente_escalante(xs)
    dt = time.perf_counter() - t0

    c = clasificar_cascada(xs)

    print(f"  tiempo       : {_fmt_tiempo(dt)}")
    print(f"  beta         : {beta:.4f}")
    print(f"  clasificacion: {c}")

    assert dt < 15.0

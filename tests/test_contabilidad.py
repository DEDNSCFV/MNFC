"""
Tests de runtime para el motor MNFC en Termux.
Verifican invariantes que NUNCA deben romperse.

Correr con:
  cd ~/MNFC
  export PYTHONPATH="$PWD/src"
  pytest tests/ -v
"""
import json
import sqlite3
import hashlib
import os
import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE, "nodo_principal_cliente_20261113_1736.db")

# ============================================================
# FIXTURES
# ============================================================
@pytest.fixture(scope="module")
def db():
    """Conexión a la BD. Se abre una vez y se reusa."""
    if not os.path.exists(DB_PATH):
        pytest.skip(f"No existe la BD: {DB_PATH}")
    con = sqlite3.connect(DB_PATH)
    yield con
    con.close()


@pytest.fixture(scope="module")
def config():
    with open(os.path.join(BASE, "config.json")) as f:
        return json.load(f)


# ============================================================
# TEST 1: PARTIDA DOBLE (DEBE = HABER)
# ============================================================
def test_partida_doble_global(db):
    """El total de DEBE debe ser igual al total de HABER en libro_diario."""
    debe = db.execute("SELECT SUM(debe_cent) FROM libro_diario").fetchone()[0] or 0
    haber = db.execute("SELECT SUM(haber_cent) FROM libro_diario").fetchone()[0] or 0
    assert debe == haber, f"Partida doble ROTA: DEBE={debe/100:,.2f} != HABER={haber/100:,.2f}"


def test_partida_doble_por_detal(db):
    """Cada detal debe tener partida doble."""
    rows = db.execute("""
        SELECT detal, SUM(debe_cent), SUM(haber_cent)
        FROM libro_diario
        GROUP BY detal
    """).fetchall()
    for detal, debe, haber in rows:
        debe = debe or 0
        haber = haber or 0
        assert debe == haber, f"Partida doble ROTA en {detal}: DEBE={debe} != HABER={haber}"


# ============================================================
# TEST 2: SOURCE_HASH ÚNICO
# ============================================================
def test_source_hash_no_duplicado(db):
    """No debe haber dos asientos con el mismo source_hash."""
    n_dups = db.execute("""
        SELECT COUNT(*) FROM (
            SELECT source_hash FROM libro_diario
            WHERE source_hash IS NOT NULL
            GROUP BY source_hash HAVING COUNT(*) > 1
        )
    """).fetchone()[0]
    assert n_dups == 0, f"Hay {n_dups} source_hash duplicados"


def test_source_hash_no_nulo(db):
    """Todos los asientos deben tener source_hash (idempotencia)."""
    n_nulos = db.execute("SELECT COUNT(*) FROM libro_diario WHERE source_hash IS NULL").fetchone()[0]
    assert n_nulos == 0, f"Hay {n_nulos} asientos sin source_hash"


def test_source_hash_formato(db):
    """source_hash debe ser SHA-256 (64 chars hex)."""
    rows = db.execute("SELECT source_hash FROM libro_diario LIMIT 100").fetchall()
    for (h,) in rows:
        assert h is not None, "source_hash nulo"
        assert len(h) == 64, f"source_hash con longitud incorrecta: {h}"
        assert all(c in "0123456789abcdef" for c in h), f"source_hash no es hex: {h}"


# ============================================================
# TEST 3: ÍNTEGRIDAD REFERENCIAL
# ============================================================
def test_cuentas_existen_en_plan(db):
    """Cada cuenta_codigo en libro_diario debe existir en plan_cuentas."""
    huerfanas = db.execute("""
        SELECT DISTINCT ld.cuenta_codigo
        FROM libro_diario ld
        LEFT JOIN plan_cuentas pc ON pc.codigo = ld.cuenta_codigo
        WHERE pc.codigo IS NULL
    """).fetchall()
    assert len(huerfanas) == 0, f"Cuentas huerfanas: {[r[0] for r in huerfanas]}"


# ============================================================
# TEST 4: INVENTARIO Y PLAN DE CUENTAS
# ============================================================
def test_inventario_no_vacio(db):
    """Debe haber al menos un SKU en inventario_nodo."""
    n = db.execute("SELECT COUNT(*) FROM inventario_nodo").fetchone()[0]
    assert n > 0, "inventario_nodo esta vacio"


def test_plan_cuentas_completo(db):
    """El catalogo debe tener al menos 46 cuentas (PCU basico)."""
    n = db.execute("SELECT COUNT(*) FROM plan_cuentas").fetchone()[0]
    assert n >= 46, f"Solo {n} cuentas en plan_cuentas (esperadas >= 46)"


def test_plan_cuentas_9_base(db):
    """Las 9 cuentas base originales deben existir."""
    base = ["1101", "1102", "1103", "1104", "2101", "2102", "3101", "4101", "5101"]
    for cod in base:
        row = db.execute("SELECT nombre FROM plan_cuentas WHERE codigo = ?", (cod,)).fetchone()
        assert row is not None, f"Falta cuenta base: {cod}"


# ============================================================
# TEST 5: MOVIMIENTOS
# ============================================================
def test_movimientos_tienen_detal(db):
    """Todos los movimientos deben tener detal (excepto los sin costo)."""
    n_sin_detal = db.execute("SELECT COUNT(*) FROM movimientos_dartony WHERE detal IS NULL").fetchone()[0]
    total = db.execute("SELECT COUNT(*) FROM movimientos_dartony").fetchone()[0]
    # Tolerar algunos sin detal (movimientos sin sucursal identificable)
    assert n_sin_detal < total * 0.1, f"{n_sin_detal}/{total} movimientos sin detal (>10%)"


def test_movimientos_tienen_fecha(db):
    """Todos los movimientos deben tener fecha."""
    n = db.execute("SELECT COUNT(*) FROM movimientos_dartony WHERE fecha IS NULL").fetchone()[0]
    assert n == 0, f"{n} movimientos sin fecha"


# ============================================================
# TEST 6: CONFIGURACIÓN
# ============================================================
def test_config_tiene_db_path(config):
    """config.json debe tener db_path."""
    assert "db_path" in config, "config.json sin db_path"
    db_file = os.path.join(BASE, config["db_path"])
    assert os.path.exists(db_file), f"No existe la BD configurada: {db_file}"


def test_config_tiene_detalles_disponibles(config):
    """config.json debe tener detalles_disponibles."""
    assert "detalles_disponibles" in config, "config.json sin detalles_disponibles"
    assert len(config["detalles_disponibles"]) > 0, "detalles_disponibles vacio"


# ============================================================
# TEST 7: TAMAÑO DE LA BD
# ============================================================
def test_bd_tamano_razonable():
    """La BD debe pesar entre 100 MB y 1 GB."""
    size = os.path.getsize(DB_PATH) / 1024 / 1024
    assert 100 < size < 1024, f"BD con tamano raro: {size:.1f} MB"

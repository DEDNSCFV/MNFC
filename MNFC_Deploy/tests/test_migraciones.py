"""Tests del sistema de migraciones."""
import sqlite3
import tempfile
import os
import pytest
from mnfc.migraciones import aplicar_migraciones, estado


def test_migracion_inicial_aplica(db_temporal):
    aplicadas = aplicar_migraciones(db_temporal)
    assert "001_initial" in aplicadas

    con = sqlite3.connect(db_temporal)
    tabla = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
    ).fetchone()
    con.close()
    assert tabla is not None


def test_migracion_idempotente(db_temporal):
    aplicar_migraciones(db_temporal)
    segunda = aplicar_migraciones(db_temporal)
    assert segunda == []  # nada nuevo


def test_estado_reporta_correctamente(db_temporal):
    st = estado(db_temporal)
    assert "001_initial" in st["total"]
    assert "001_initial" in st["pendientes"]
    aplicar_migraciones(db_temporal)
    st2 = estado(db_temporal)
    assert "001_initial" in st2["aplicadas"]


@pytest.fixture
def db_temporal():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)

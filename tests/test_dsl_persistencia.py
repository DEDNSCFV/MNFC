"""Tests de persistencia del DSL (Fase 6).

Verifican:
- Persistencia básica (1 asiento, varios, vacío).
- Cuadre obligatorio.
- Pre-serialización: payload no serializable falla sin escrituras.
- Payload correcto (campos, partidas, contexto).
- Idempotencia (duplicado).
- Fallo mid-batch (parcial, no recuperable).
- Hash retornado == obtener_hash_final.
- Cross-backend SQLite/JSON.
- Integración: .mnfc -> ensamblar -> persistir -> verificar_cadena.

Sin marcos reales. Sin fiscal. Todo sintético.
"""
import os
import shutil
import tempfile

import pytest

from mnfc.dsl.persistencia import persistir, DSLPersistenceError
from mnfc.extensiones.modelos import (
    Asiento,
    LineaAsiento,
    ContextoContable,
)
from mnfc.extensiones.persistencia.sqlite_store import SQLiteStore
from mnfc.extensiones.persistencia.json_store import JSONStore


# ═════════════════════════════════════════════════════════════════════
# Fixtures
# ═════════════════════════════════════════════════════════════════════

@pytest.fixture
def tmp_store_sqlite():
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, "test.db")
    store = SQLiteStore(path)
    try:
        yield store, path
    finally:
        try:
            store.cerrar()
        except Exception:
            pass
        shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def tmp_store_json():
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, "test.json")
    store = JSONStore(path)
    try:
        yield store, path
    finally:
        try:
            store.cerrar()
        except Exception:
            pass
        shutil.rmtree(tmp, ignore_errors=True)


def _asiento_cuadrado(cuenta_debe, cuenta_haber, monto,
                      contexto=None):
    return Asiento(
        lineas=[
            LineaAsiento(cuenta=cuenta_debe, ubicacion="DEBE",
                         monto=monto),
            LineaAsiento(cuenta=cuenta_haber, ubicacion="HABER",
                         monto=monto),
        ],
        total_debe=monto,
        total_haber=monto,
        cuadrado=True,
        contexto=contexto,
    )


def _contexto():
    return ContextoContable(
        marco_contable="PYMES",
        PCU_version="v1",
        reglas_version="v1",
        politica_monetaria_version="v1",
    )


# ═════════════════════════════════════════════════════════════════════
# A · Básico
# ═════════════════════════════════════════════════════════════════════

class TestBasico:

    def test_lista_vacia_retorna_vacio(self, tmp_store_sqlite):
        """F6-R1: lista vacía retorna [] sin tocar el store."""
        store, _ = tmp_store_sqlite
        assert persistir([], store, "c", "2026-10", "2026-10-17") == []
        assert len(store) == 0

    def test_lista_vacia_metadata_vacia(self, tmp_store_sqlite):
        """F6-R1: persistir([]) no valida metadata."""
        store, _ = tmp_store_sqlite
        assert persistir([], store, "", "", "") == []
        assert len(store) == 0

    def test_un_asiento(self, tmp_store_sqlite):
        store, _ = tmp_store_sqlite
        a = _asiento_cuadrado("110101", "410101", 100.0)
        hashes = persistir([a], store, "corr-1", "2026-10", "2026-10-17")
        assert len(hashes) == 1
        assert len(store) == 1
        assert hashes[0] == store.obtener_hash_final()

    def test_varios_asientos(self, tmp_store_sqlite):
        store, _ = tmp_store_sqlite
        a1 = _asiento_cuadrado("A", "B", 100.0)
        a2 = _asiento_cuadrado("C", "D", 50.0)
        hashes = persistir([a1, a2], store, "corr-1",
                           "2026-10", "2026-10-17")
        assert len(hashes) == 2
        assert len(store) == 2
        assert hashes[0] != hashes[1]


# ═════════════════════════════════════════════════════════════════════
# C · Cuadre obligatorio
# ═════════════════════════════════════════════════════════════════════

class TestCuadre:

    def test_no_cuadrado_falla_antes_de_escribir(self, tmp_store_sqlite):
        store, _ = tmp_store_sqlite
        a = Asiento(
            lineas=[LineaAsiento("A", "DEBE", 100.0)],
            total_debe=100.0, total_haber=50.0, cuadrado=False,
        )
        with pytest.raises(DSLPersistenceError,
                           match="asiento no cuadrado"):
            persistir([a], store, "corr", "2026-10", "2026-10-17")
        assert len(store) == 0

    def test_cuadrado_ok(self, tmp_store_sqlite):
        store, _ = tmp_store_sqlite
        a = _asiento_cuadrado("A", "B", 100.0)
        persistir([a], store, "corr", "2026-10", "2026-10-17")
        assert len(store) == 1


# ═════════════════════════════════════════════════════════════════════
# D · Pre-serialización (F6-R2)
# ═════════════════════════════════════════════════════════════════════

class TestPreSerializacion:

    def test_decimal_en_partida_falla_sin_escritura(self, tmp_store_sqlite):
        """F6-R2: Decimal no serializable. Falla ANTES de guardar nada."""
        from decimal import Decimal
        store, _ = tmp_store_sqlite
        a = Asiento(
            lineas=[
                LineaAsiento("A", "DEBE", Decimal("100")),
                LineaAsiento("B", "HABER", Decimal("100")),
            ],
            total_debe=100.0, total_haber=100.0, cuadrado=True,
        )
        with pytest.raises(DSLPersistenceError,
                           match="no serializable"):
            persistir([a], store, "corr", "2026-10", "2026-10-17")
        assert len(store) == 0
        ok, _ = store.verificar_cadena()
        assert ok is True

    def test_segundo_asiento_no_serializable_no_escribe_el_primero(
            self, tmp_store_sqlite):
        """Pre-serialización: si #2 falla, #1 NO se escribe."""
        from decimal import Decimal
        store, _ = tmp_store_sqlite
        a1 = _asiento_cuadrado("A", "B", 100.0)
        a2 = Asiento(
            lineas=[
                LineaAsiento("C", "DEBE", Decimal("50")),
                LineaAsiento("D", "HABER", Decimal("50")),
            ],
            total_debe=50.0, total_haber=50.0, cuadrado=True,
        )
        with pytest.raises(DSLPersistenceError,
                           match="no serializable"):
            persistir([a1, a2], store, "corr", "2026-10", "2026-10-17")
        assert len(store) == 0


# ═════════════════════════════════════════════════════════════════════
# E · Payload correcto (F6-R6)
# ═════════════════════════════════════════════════════════════════════

class TestPayload:

    def test_payload_campos(self, tmp_store_sqlite):
        store, _ = tmp_store_sqlite
        a = _asiento_cuadrado("110101", "410101", 100.0)
        persistir([a], store, "corr-1", "2026-10", "2026-10-17")
        ev = store.obtener_por_correlation("corr-1")
        p = ev["payload"]
        assert p["id"] == "corr-1-1"
        assert p["fecha"] == "2026-10-17"
        assert p["periodo_id"] == "2026-10"
        assert p["total_debe"] == 100.0
        assert p["total_haber"] == 100.0
        assert p["correlation_id"] == "corr-1"
        assert len(p["partidas"]) == 2
        assert p["partidas"][0]["cuenta_codigo"] == "110101"
        assert p["partidas"][0]["ubicacion"] == "DEBE"
        assert p["partidas"][1]["ubicacion"] == "HABER"

    def test_payload_contexto_none(self, tmp_store_sqlite):
        store, _ = tmp_store_sqlite
        a = _asiento_cuadrado("A", "B", 100.0, contexto=None)
        persistir([a], store, "corr", "2026-10", "2026-10-17")
        ev = store.obtener_por_correlation("corr")
        assert ev["payload"]["contexto"] is None

    def test_payload_contexto_dict(self, tmp_store_sqlite):
        store, _ = tmp_store_sqlite
        a = _asiento_cuadrado("A", "B", 100.0, contexto=_contexto())
        persistir([a], store, "corr", "2026-10", "2026-10-17")
        ev = store.obtener_por_correlation("corr")
        ctx = ev["payload"]["contexto"]
        assert ctx["marco_contable"] == "PYMES"
        assert ctx["PCU_version"] == "v1"
        assert ctx["reglas_version"] == "v1"
        assert ctx["politica_monetaria_version"] == "v1"


# ═════════════════════════════════════════════════════════════════════
# F · Idempotencia (F6-R3)
# ═════════════════════════════════════════════════════════════════════

class TestIdempotencia:

    def test_duplicado_corr_indice_falla(self, tmp_store_sqlite):
        store, _ = tmp_store_sqlite
        a = _asiento_cuadrado("A", "B", 100.0)
        persistir([a], store, "corr", "2026-10", "2026-10-17")
        with pytest.raises(DSLPersistenceError,
                           match="duplicado o payload rechazado"):
            persistir([a], store, "corr", "2026-10", "2026-10-17")
        assert len(store) == 1

    def test_distinto_corr_ok(self, tmp_store_sqlite):
        store, _ = tmp_store_sqlite
        a = _asiento_cuadrado("A", "B", 100.0)
        persistir([a], store, "corr-1", "2026-10", "2026-10-17")
        persistir([a], store, "corr-2", "2026-10", "2026-10-17")
        assert len(store) == 2

    def test_distinto_indice_mismo_corr_ok(self, tmp_store_sqlite):
        store, _ = tmp_store_sqlite
        a1 = _asiento_cuadrado("A", "B", 100.0)
        a2 = _asiento_cuadrado("C", "D", 50.0)
        persistir([a1, a2], store, "corr", "2026-10", "2026-10-17")
        assert len(store) == 2


# ═════════════════════════════════════════════════════════════════════
# G · Fallo mid-batch (F6-R4, F6-R9)
# ═════════════════════════════════════════════════════════════════════

class TestMidBatch:

    def test_falla_en_segundo_tras_guardar_primero(self, tmp_store_sqlite):
        """F6-R4: fallo en #2 deja #1 persistido. Sin rollback."""
        store, _ = tmp_store_sqlite
        a1 = _asiento_cuadrado("A", "B", 100.0)
        a2 = _asiento_cuadrado("C", "D", 50.0)

        original = store.guardar
        calls = {"n": 0}
        def guardar_con_fallo(*args, **kwargs):
            calls["n"] += 1
            if calls["n"] == 2:
                raise RuntimeError("fallo simulado #2")
            return original(*args, **kwargs)

        store.guardar = guardar_con_fallo
        with pytest.raises(DSLPersistenceError) as exc:
            persistir([a1, a2], store, "corr", "2026-10", "2026-10-17")
        assert "ASIENTO #2" in str(exc.value)
        assert "tras 1 asiento(s) guardado(s)" in str(exc.value)

        store.guardar = original
        assert len(store) == 1
        ev = store.obtener_por_correlation("corr")
        assert ev["payload"]["partidas"][0]["cuenta_codigo"] == "A"
        ok, _ = store.verificar_cadena()
        assert ok is True

    def test_reintento_lote_completo_falla_por_duplicado(
            self, tmp_store_sqlite):
        """F6-R9: reintento con el lote completo no funciona."""
        store, _ = tmp_store_sqlite
        a = _asiento_cuadrado("A", "B", 100.0)
        persistir([a], store, "corr", "2026-10", "2026-10-17")
        with pytest.raises(DSLPersistenceError,
                           match="duplicado"):
            persistir([a], store, "corr", "2026-10", "2026-10-17")


# ═════════════════════════════════════════════════════════════════════
# H · Hash retornado (F6-R5)
# ═════════════════════════════════════════════════════════════════════

class TestHash:

    def test_hash_es_el_final_del_store(self, tmp_store_sqlite):
        store, _ = tmp_store_sqlite
        a1 = _asiento_cuadrado("A", "B", 100.0)
        a2 = _asiento_cuadrado("C", "D", 50.0)
        hashes = persistir([a1, a2], store, "corr",
                           "2026-10", "2026-10-17")
        assert hashes[-1] == store.obtener_hash_final()
        assert hashes[0] != hashes[1]

    def test_hash_cambia_por_asiento(self, tmp_store_sqlite):
        store, _ = tmp_store_sqlite
        a1 = _asiento_cuadrado("A", "B", 100.0)
        hashes = persistir([a1], store, "corr",
                           "2026-10", "2026-10-17")
        assert hashes[0] != store.GENESIS_HASH


# ═════════════════════════════════════════════════════════════════════
# I · Cross-backend
# ═════════════════════════════════════════════════════════════════════

class TestCrossBackend:

    def test_sqlite_y_json_mismo_hash(self, tmp_store_sqlite,
                                      tmp_store_json):
        store_sql, _ = tmp_store_sqlite
        store_json, _ = tmp_store_json
        a = _asiento_cuadrado("A", "B", 100.0)
        h_sql = persistir([a], store_sql, "corr",
                          "2026-10", "2026-10-17")[0]
        h_json = persistir([a], store_json, "corr",
                           "2026-10", "2026-10-17")[0]
        assert h_sql == h_json

    def test_json_cadena_integra(self, tmp_store_json):
        store, _ = tmp_store_json
        a1 = _asiento_cuadrado("A", "B", 100.0)
        a2 = _asiento_cuadrado("C", "D", 50.0)
        persistir([a1, a2], store, "corr", "2026-10", "2026-10-17")
        ok, msg = store.verificar_cadena()
        assert ok is True


# ═════════════════════════════════════════════════════════════════════
# J · Integración: pipeline completo
# ═════════════════════════════════════════════════════════════════════

class TestIntegracion:

    def test_pipeline_mnfc_persistir_verificar(self, tmp_store_sqlite):
        """parse -> validar -> evaluar -> ensamblar -> persistir."""
        from mnfc.dsl import parse, validar, evaluar, ensamblar
        from mnfc.dsl.registry import Registry, OperacionRegistrada

        store, _ = tmp_store_sqlite

        pcu = {
            "110101": {"naturaleza": "DEUDORA",
                       "marcos": ["caja", "PYMES"]},
            "410101": {"naturaleza": "ACREEDORA",
                       "marcos": ["ingreso", "PYMES"]},
        }
        reg = Registry()
        reg.registrar(OperacionRegistrada(
            nombre="suma", fn=lambda ctx: sum(ctx["montos"]),
            tipo="norma", fuente="PYMES:S23",
        ))

        src = '''
        DSL_VERSION "1.6";
        ELEMENTOS { activo; ingreso; }
        MARCOS { PYMES; }
        CATEGORIA caja = elemento: activo; universal: VERDADERO;
        CATEGORIA ingreso = elemento: ingreso; universal: FALSO;
        HECHO activo;
        FRACTAL ventas:
            REGLA registro:
                SI activo
                ENTONCES
                    GENERAR CONSECUENCIA(categoria=categoria(caja), operacion=suma, movimiento=AUMENTA, fuente=PYMES:S23)
                    GENERAR CONSECUENCIA(categoria=categoria(ingreso), operacion=suma, movimiento=AUMENTA, fuente=PYMES:S23);
        '''
        prog = parse(src)
        validar(prog)
        resultados = evaluar(
            prog, {"activo": True, "montos": [100.0, 50.0]},
            pcu, reg.to_dict(), "PYMES",
        )
        asientos = ensamblar(resultados, contexto=_contexto())
        assert len(asientos) == 1
        assert asientos[0].cuadrado

        hashes = persistir(asientos, store, "corr-int",
                           "2026-10", "2026-10-17")
        assert len(hashes) == 1
        ok, _ = store.verificar_cadena()
        assert ok is True
        ev = store.obtener_por_correlation("corr-int")
        assert ev["payload"]["total_debe"] == 150.0
        assert ev["payload"]["total_haber"] == 150.0

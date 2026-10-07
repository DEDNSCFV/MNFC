"""
Tests de integracion de las extensiones de MNFC.

Cubre:
    - Estados y maquina de estados del asiento
    - Serializador canonico
    - Reticulo booleano de cuentas
    - Examinador de evidencia
    - Persistencia (SQLite y JSON)
    - Reportes
    - Integracion end-to-end entre capas
"""
import json
import os
import tempfile
import shutil
import pytest

from mnfc.extensiones import (
    # Estados
    VersionContexto, EstadoAsiento, TipoEvento,
    # Maquina
    MaquinaEstadosAsiento, Transicion,
    # Modelos
    ContextoContable, PartidaAutorizada, LineaAsiento, Asiento,
    # Serializador
    serializar, deserializar, PersistenciaViolacion,
    # Reticulo
    ReticuloCuentas,
    # Examinador
    ExaminadorEvidencia, Reporte,
    # Persistencia
    StoreBase, SQLiteStore, JSONStore,
)


VC = {"version_id": "v1", "PCU_version": "1.0"}


# ======================================================================
# Estados
# ======================================================================

def test_version_contexto_dataclass():
    vc = VersionContexto(
        version_id="v1", fecha_inicio="2026-01-01", fecha_fin="2026-12-31",
        PCU_version="1.0", reglas_version="1.0",
        politica_inventario_version="1.0", marco_contable_version="NIIF",
        politica_monetaria_version="VES",
    )
    assert vc.version_id == "v1"
    assert vc.marco_contable_version == "NIIF"


def test_estado_asiento_miembros():
    assert len(EstadoAsiento) == 7
    assert EstadoAsiento.PROPUESTO.name == "PROPUESTO"
    assert EstadoAsiento["ASENTADO"] is EstadoAsiento.ASENTADO


# ======================================================================
# Maquina de estados
# ======================================================================

def test_maquina_ciclo_feliz():
    m = MaquinaEstadosAsiento()
    assert m.estado_actual == EstadoAsiento.PROPUESTO
    m.transicionar(EstadoAsiento.EVALUADO, "u", "c", VC)
    m.transicionar(EstadoAsiento.ADMITIDO, "u", "c", VC, justificacion="ok")
    m.transicionar(EstadoAsiento.ASENTADO, "u", "c", VC)
    assert m.estado_actual == EstadoAsiento.ASENTADO
    assert m.puede_anular()
    assert len(m.historial) == 3


def test_maquina_rechazo_desde_terminal():
    m = MaquinaEstadosAsiento()
    m.transicionar(EstadoAsiento.EVALUADO, "u", "c", VC)
    m.transicionar(EstadoAsiento.RECHAZADO, "u", "c", VC, justificacion="no")
    assert m.es_terminal()
    with pytest.raises(ValueError):
        m.transicionar(EstadoAsiento.PROPUESTO, "u", "c", VC)


def test_maquina_precondicion_justificacion():
    m = MaquinaEstadosAsiento()
    m.transicionar(EstadoAsiento.EVALUADO, "u", "c", VC)
    with pytest.raises(ValueError):
        m.transicionar(EstadoAsiento.ADMITIDO, "u", "c", VC)


def test_maquina_historial_serializable():
    m = MaquinaEstadosAsiento()
    m.transicionar(EstadoAsiento.EVALUADO, "u", "c", VC)
    m.transicionar(EstadoAsiento.ADMITIDO, "u", "c", VC, justificacion="ok")
    h = m.obtener_historial()
    assert len(h) == 2
    assert all(len(item["hash"]) == 64 for item in h)
    assert h[0]["desde"] == "PROPUESTO"
    assert h[-1]["hasta"] == "ADMITIDO"


# ======================================================================
# Serializador canonico
# ======================================================================

def test_serializar_primitivos():
    assert serializar(None) is None
    assert serializar(True) is True
    assert serializar(42) == 42
    assert serializar(3.14) == 3.14
    assert serializar("x") == "x"


def test_serializar_enum_usa_name():
    assert serializar(EstadoAsiento.ASENTADO) == "ASENTADO"


def test_serializar_dataclass_recursivo():
    vc = VersionContexto(
        version_id="v1", fecha_inicio="2026-01-01", fecha_fin="2026-12-31",
        PCU_version="1.0", reglas_version="1.0",
        politica_inventario_version="1.0", marco_contable_version="NIIF",
        politica_monetaria_version="VES",
    )
    s = serializar(vc)
    assert s["version_id"] == "v1"
    assert s["marco_contable_version"] == "NIIF"


def test_serializar_rechaza_tipo_no_soportado():
    class Foo:
        pass
    with pytest.raises(PersistenciaViolacion):
        serializar(Foo())


def test_serializar_round_trip():
    vc = VersionContexto(
        version_id="v1", fecha_inicio="2026-01-01", fecha_fin="2026-12-31",
        PCU_version="1.0", reglas_version="1.0",
        politica_inventario_version="1.0", marco_contable_version="NIIF",
        politica_monetaria_version="VES",
    )
    recuperado = deserializar(serializar(vc), VersionContexto)
    assert recuperado == vc


# ======================================================================
# Reticulo booleano de cuentas
# ======================================================================

def test_reticulo_operaciones_basicas():
    universo = ["1101", "1102", "2101", "2102"]
    subconjuntos = {
        "activo": ["1101", "1102"],
        "pasivo": ["2101", "2102"],
    }
    r = ReticuloCuentas(universo, subconjuntos)
    assert len(r.universo_set()) == 4
    assert r.union("activo", "pasivo") == frozenset(universo)
    assert r.interseccion("activo", "pasivo") == frozenset()
    assert r.complemento("activo") == frozenset(["2101", "2102"])


def test_reticulo_particion():
    universo = ["1101", "2101"]
    subconjuntos = {"activo": ["1101"], "pasivo": ["2101"]}
    r = ReticuloCuentas(universo, subconjuntos)
    assert r.es_particion("activo", "pasivo")


def test_reticulo_cuentas_huerfanas():
    universo = ["1101", "1102", "2101"]
    r = ReticuloCuentas(universo, {"solo_activo": ["1101"]})
    huerfanas = r.cuentas_huerfanas()
    assert huerfanas == frozenset(["1102", "2101"])


# ======================================================================
# Examinador de evidencia
# ======================================================================

@pytest.fixture
def pcu_test():
    return {
        "1101": {"naturaleza": "DEUDORA",   "marcos": ["NIIF", "VEN_NIF"]},
        "1102": {"naturaleza": "DEUDORA",   "marcos": ["NIIF", "VEN_NIF"]},
        "2101": {"naturaleza": "ACREEDORA", "marcos": ["NIIF", "VEN_NIF"]},
        "4101": {"naturaleza": "ACREEDORA", "marcos": ["NIIF"]},
    }


def test_examinador_evidencia_limpia(pcu_test):
    e = ExaminadorEvidencia(pcu_test)
    r = e.examinar({
        "marco_contable": "NIIF",
        "partidas": [
            {"cuenta_codigo": "1101", "movimiento": "AUMENTA"},
            {"cuenta_codigo": "4101", "movimiento": "AUMENTA"},
        ],
    })
    assert r.linea["ok"] is True
    assert r.conjunto["ok"] is True


def test_examinador_detecta_cuenta_ausente(pcu_test):
    e = ExaminadorEvidencia(pcu_test)
    r = e.examinar({
        "marco_contable": "NIIF",
        "partidas": [{"cuenta_codigo": "9999", "movimiento": "AUMENTA"}],
    })
    assert r.linea["ok"] is False
    assert any("cuenta_ausente" in h for h in r.linea["hallazgos"])


def test_examinador_detecta_movimiento_invalido(pcu_test):
    e = ExaminadorEvidencia(pcu_test)
    r = e.examinar({
        "marco_contable": "NIIF",
        "partidas": [{"cuenta_codigo": "1101", "movimiento": "SUMA"}],
    })
    assert r.linea["ok"] is False


def test_examinador_rechaza_no_mapping(pcu_test):
    e = ExaminadorEvidencia(pcu_test)
    with pytest.raises(TypeError):
        e.examinar([1, 2, 3])


# ======================================================================
# Persistencia - fixtures y tests
# ======================================================================

@pytest.fixture
def tmp_store(request):
    """Crea un store temporal (SQLite o JSON segun parametro)."""
    tmpdir = tempfile.mkdtemp()
    try:
        if request.param == "sqlite":
            path = os.path.join(tmpdir, "test.db")
            store = SQLiteStore(path)
        elif request.param == "json":
            path = os.path.join(tmpdir, "test.json")
            store = JSONStore(path)
        else:
            raise ValueError("backend desconocido: %s" % request.param)
        yield store, path
    finally:
        try:
            store.cerrar()
        except Exception:
            pass
        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)


@pytest.mark.parametrize("tmp_store", ["sqlite", "json"], indirect=True)
def test_store_vacio(tmp_store):
    store, _ = tmp_store
    assert len(store) == 0
    assert store.obtener_hash_final() == StoreBase.GENESIS_HASH
    assert store.verificar_cadena() == (True, "CADENA_INTEGRA")


@pytest.mark.parametrize("tmp_store", ["sqlite", "json"], indirect=True)
def test_store_guarda_y_recupera(tmp_store):
    store, _ = tmp_store
    store.guardar(
        "ASIENTO_REGISTRADO",
        {"cuenta": "1101", "monto": 1000, "ubicacion": "DEBE"},
        "corr-1", "idem-1", {"version_id": "v1"},
    )
    assert len(store) == 1
    e = store.obtener_por_id(1)
    assert e is not None
    assert e["payload"]["cuenta"] == "1101"
    assert e["correlation_id"] == "corr-1"


@pytest.mark.parametrize("tmp_store", ["sqlite", "json"], indirect=True)
def test_store_cadena_integra(tmp_store):
    store, _ = tmp_store
    for i in range(5):
        store.guardar("EVENTO", {"n": i}, "corr-%d" % i, "idem-%d" % i)
    assert len(store) == 5
    ok, msg = store.verificar_cadena()
    assert ok is True
    assert msg == "CADENA_INTEGRA"


@pytest.mark.parametrize("tmp_store", ["sqlite", "json"], indirect=True)
def test_store_idempotency_duplicada(tmp_store):
    store, _ = tmp_store
    store.guardar("EVENTO", {"n": 1}, "corr-1", "idem-1")
    with pytest.raises(ValueError):
        store.guardar("EVENTO", {"n": 2}, "corr-2", "idem-1")


@pytest.mark.parametrize("tmp_store", ["sqlite", "json"], indirect=True)
def test_store_obtener_por_tipo(tmp_store):
    store, _ = tmp_store
    store.guardar("TIPO_A", {"n": 1}, "c1", "i1")
    store.guardar("TIPO_B", {"n": 2}, "c2", "i2")
    store.guardar("TIPO_A", {"n": 3}, "c3", "i3")
    a = store.obtener_por_tipo("TIPO_A")
    assert len(a) == 2
    assert len(store.obtener_por_tipo("TIPO_A", limite=1)) == 1
    assert store.obtener_por_tipo("NO_EXISTE") == []


@pytest.mark.parametrize("tmp_store", ["sqlite", "json"], indirect=True)
def test_store_obtener_por_correlation(tmp_store):
    store, _ = tmp_store
    store.guardar("EVENTO", {"n": 1}, "corr-X", "idem-1")
    assert store.obtener_por_correlation("corr-X") is not None
    assert store.obtener_por_correlation("no-existe") is None


def test_compatibilidad_cross_backend():
    """JSONStore y SQLiteStore producen el mismo hash para el mismo evento."""
    tmpdir = tempfile.mkdtemp()
    try:
        s_json = JSONStore(os.path.join(tmpdir, "a.json"))
        s_sql = SQLiteStore(os.path.join(tmpdir, "a.db"))
        payload = {"cuenta": "1101", "monto": 1000, "ubicacion": "DEBE"}
        vc = {"version_id": "v1"}
        s_json.guardar("ASIENTO_REGISTRADO", payload, "c1", "i1", vc)
        s_sql.guardar("ASIENTO_REGISTRADO", payload, "c1", "i1", vc)
        assert s_json.obtener_hash_final() == s_sql.obtener_hash_final()
        s_json.cerrar()
        s_sql.cerrar()
    finally:
        shutil.rmtree(tmpdir)


# ======================================================================
# Reportes
# ======================================================================

@pytest.fixture
def store_con_asientos():
    tmpdir = tempfile.mkdtemp()
    store = JSONStore(os.path.join(tmpdir, "t.json"))
    store.guardar("ASIENTO_REGISTRADO", {
        "id": "A-001", "fecha": "2026-10-15", "periodo_id": "2026-10",
        "total_debe": 1000.0, "total_haber": 1000.0, "correlation_id": "c1",
        "partidas": [
            {"cuenta_codigo": "1101", "ubicacion": "DEBE",  "monto": 1000.0},
            {"cuenta_codigo": "4101", "ubicacion": "HABER", "monto": 1000.0},
        ],
    }, "c1", "i1")
    store.guardar("ASIENTO_REGISTRADO", {
        "id": "A-002", "fecha": "2026-10-20", "periodo_id": "2026-10",
        "total_debe": 500.0, "total_haber": 500.0, "correlation_id": "c2",
        "partidas": [
            {"cuenta_codigo": "5101", "ubicacion": "DEBE",  "monto": 500.0},
            {"cuenta_codigo": "1101", "ubicacion": "HABER", "monto": 500.0},
        ],
    }, "c2", "i2")
    yield store, tmpdir
    store.cerrar()
    shutil.rmtree(tmpdir)


def test_reportes_csv_diario(store_con_asientos):
    from mnfc.extensiones import reportes
    store, tmpdir = store_con_asientos
    out = os.path.join(tmpdir, "libros")
    ruta = reportes.generar_csv_diario(store, "2026-10", out)
    assert os.path.exists(ruta)
    with open(ruta) as f:
        contenido = f.read()
    assert "A-001" in contenido
    assert "A-002" in contenido


def test_reportes_csv_mayor(store_con_asientos):
    from mnfc.extensiones import reportes
    store, tmpdir = store_con_asientos
    out = os.path.join(tmpdir, "libros")
    ruta = reportes.generar_csv_mayor(store, "2026-10", out)
    with open(ruta) as f:
        contenido = f.read()
    assert "1101,500.0" in contenido
    assert "4101,-1000.0" in contenido
    assert "5101,500.0" in contenido


def test_reportes_csv_balance(store_con_asientos):
    from mnfc.extensiones import reportes
    store, tmpdir = store_con_asientos
    out = os.path.join(tmpdir, "libros")
    ruta = reportes.generar_csv_balance(store, "2026-10", out)
    with open(ruta) as f:
        contenido = f.read()
    assert "ACTIVO,500.0" in contenido
    assert "INGRESOS,-1000.0" in contenido
    assert "GASTOS,500.0" in contenido
    assert "RESULTADO,-1500.0" in contenido


def test_reportes_periodo_vacio(store_con_asientos):
    from mnfc.extensiones import reportes
    store, tmpdir = store_con_asientos
    out = os.path.join(tmpdir, "libros")
    ruta = reportes.generar_csv_diario(store, "2025-01", out)
    with open(ruta) as f:
        lineas = f.read().strip().split("\n")
    assert len(lineas) == 1  # solo encabezado


# ======================================================================
# Integracion end-to-end: kernel + extensiones
# ======================================================================

def test_integracion_kernel_y_extensiones():
    """
    Flujo completo:
        mnfc (kernel) clasifica y cuadra un asiento
        extensiones (persistencia) lo guarda
        extensiones (reportes) lo reporta
        extensiones (examinador) lo valida
    """
    from mnfc import procesar_asiento
    from mnfc.extensiones import reportes

    # 1. Procesar asiento con el kernel
    asiento = procesar_asiento([
        {"cuenta": "1101", "naturaleza": "DEUDORA",
         "movimiento": "AUMENTA", "monto": 1000},
        {"cuenta": "4101", "naturaleza": "ACREEDORA",
         "movimiento": "AUMENTA", "monto": 1000},
    ])
    assert asiento.cuadrado

    # 2. Guardar en persistencia
    tmpdir = tempfile.mkdtemp()
    try:
        store = SQLiteStore(os.path.join(tmpdir, "e2e.db"))
        payload = {
            "id": "E2E-001",
            "fecha": "2026-10-15",
            "periodo_id": "2026-10",
            "total_debe": asiento.total_debe,
            "total_haber": asiento.total_haber,
            "correlation_id": "corr-e2e",
            "partidas": [
                {"cuenta_codigo": "1101", "ubicacion": "DEBE",
                 "monto": asiento.total_debe},
                {"cuenta_codigo": "4101", "ubicacion": "HABER",
                 "monto": asiento.total_haber},
            ],
        }
        store.guardar("ASIENTO_REGISTRADO", payload, "corr-e2e", "e2e-1")

        # 3. Verificar cadena
        ok, _ = store.verificar_cadena()
        assert ok

        # 4. Generar reporte
        out = os.path.join(tmpdir, "libros")
        ruta = reportes.generar_csv_diario(store, "2026-10", out)
        with open(ruta) as f:
            contenido = f.read()
        assert "E2E-001" in contenido

        store.cerrar()
    finally:
        shutil.rmtree(tmpdir)


def test_integracion_examinador_con_asiento_kernel():
    """
    El examinador valida que un asiento procesado por el kernel
    cumpla las reglas del PCU.
    """
    from mnfc import procesar_asiento

    pcu = {
        "1101": {"naturaleza": "DEUDORA",   "marcos": ["NIIF"]},
        "4101": {"naturaleza": "ACREEDORA", "marcos": ["NIIF"]},
    }
    e = ExaminadorEvidencia(pcu)

    asiento = procesar_asiento([
        {"cuenta": "1101", "naturaleza": "DEUDORA",
         "movimiento": "AUMENTA", "monto": 1000},
        {"cuenta": "4101", "naturaleza": "ACREEDORA",
         "movimiento": "AUMENTA", "monto": 1000},
    ])

    evidencia = {
        "marco_contable": "NIIF",
        "partidas": [
            {"cuenta_codigo": "1101", "movimiento": "AUMENTA",
             "ubicacion": "DEBE"},
            {"cuenta_codigo": "4101", "movimiento": "AUMENTA",
             "ubicacion": "HABER"},
        ],
    }
    r = e.examinar(evidencia)
    assert r.linea["ok"] is True
    assert r.conjunto["ok"] is True

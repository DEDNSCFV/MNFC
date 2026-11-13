"""Tests de observabilidad."""
import json
import io
import logging
from mnfc.observability import get_logger, con_correlacion, correlation_id_actual, JSONFormatter


def _capturar(logger, fn):
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    try:
        fn()
    finally:
        logger.removeHandler(handler)
    return stream.getvalue()


def test_log_json_minimo():
    log = get_logger("test.min")
    salida = _capturar(log, lambda: log.info("hola"))
    payload = json.loads(salida.strip())
    assert payload["msg"] == "hola"
    assert payload["level"] == "INFO"
    assert "ts" in payload


def test_log_incluye_extra():
    log = get_logger("test.extra")
    salida = _capturar(log, lambda: log.info("op", extra={"asiento_id": "A-001"}))
    payload = json.loads(salida.strip())
    assert payload["asiento_id"] == "A-001"


def test_correlation_id_propaga():
    log = get_logger("test.corr")

    def _emitir():
        with con_correlacion("c-test"):
            assert correlation_id_actual() == "c-test"
            log.info("dentro")

    salida = _capturar(log, _emitir)
    payload = json.loads(salida.strip())
    assert payload["correlation_id"] == "c-test"


def test_sin_correlacion_no_agrega_campo():
    log = get_logger("test.scorr")
    salida = _capturar(log, lambda: log.info("fuera"))
    payload = json.loads(salida.strip())
    assert "correlation_id" not in payload

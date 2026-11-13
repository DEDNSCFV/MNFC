"""Observabilidad: logs JSON estructurados + correlation IDs.

Uso:
    from mnfc.observability import get_logger, con_correlacion

    log = get_logger(__name__)
    log.info("asiento registrado", extra={"asiento_id": "A-001", "monto_cent": 10000})

    with con_correlacion("c-abc-123"):
        log.info("operacion en contexto")

Los logs salen a stderr como JSON de una línea. Compatible con
Datadog/Loki/CloudWatch sin parser adicional.
"""
import json
import logging
import sys
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Optional

_correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)

# Campos que logging reserva (no van al JSON extra)
_RESERVADOS = {
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "taskName", "message", "asctime",
}


class JSONFormatter(logging.Formatter):
    """Formatea logs como JSON de una línea."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        corr = _correlation_id.get()
        if corr:
            payload["correlation_id"] = corr

        # Campos extra pasados vía extra={}
        for k, v in record.__dict__.items():
            if k not in _RESERVADOS and not k.startswith("_"):
                try:
                    json.dumps(v)  # serializable
                    payload[k] = v
                except (TypeError, ValueError):
                    payload[k] = repr(v)

        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Devuelve logger con JSONFormatter. Idempotente."""
    log = logging.getLogger(name)
    if not log.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(JSONFormatter())
        log.addHandler(handler)
        log.setLevel(level)
        log.propagate = False
    return log


@contextmanager
def con_correlacion(correlation_id: Optional[str] = None):
    """Context manager que propaga un correlation_id en el contexto actual."""
    cid = correlation_id or str(uuid.uuid4())
    token = _correlation_id.set(cid)
    try:
        yield cid
    finally:
        _correlation_id.reset(token)


def correlation_id_actual() -> Optional[str]:
    return _correlation_id.get()

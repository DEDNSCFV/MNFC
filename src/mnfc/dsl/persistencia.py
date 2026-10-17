"""MNFC DSL — Fase 6 · Persistencia.

Persiste una lista de Asiento (salida de ensamblar) en un store
de capa 7 (StoreBase). Cada Asiento se guarda como evento
ASIENTO_REGISTRADO con payload tipado, encadenado al hash previo.

Frontera:
- No importa SQLiteStore ni JSONStore. Recibe un StoreBase inyectado.
- No carga marcos reales.
- No toca fiscal.
- El caller provee correlation_id, periodo_id, fecha.

Contrato:

LISTA VACÍA (F6-R1):
    persistir([]) retorna [] sin validar correlation_id,
    periodo_id ni fecha. Cero asientos no requiere metadata.

PRE-SERIALIZACIÓN (F6-R2):
    Todos los payloads se construyen y serializan ANTES del
    primer guardar. Si un payload no es serializable, se lanza
    DSLPersistenceError sin haber tocado el store.

NO TRANSACCIONAL (F6-R4, F6-R9):
    La función NO es transaccional. Si el store falla a mitad
    del lote, los asientos ya guardados permanecen. StoreBase
    no ofrece rollback ni delete.

    La idempotencia es por evento (idempotency_key =
    f"{correlation_id}-{i}"). Esto evita duplicados pero NO
    permite reanudación automática: si guard 1 y 2 OK y falla
    el 3, un reintento con el lote completo fallará en el 1
    por duplicado.

    Recuperación de lote parcial: deuda explícita (F6-R9).
    Requiere consulta por idempotency_key, que StoreBase no
    expone. obtener_por_correlation() devuelve solo el primer
    evento, no todos.

    verificar_cadena() verifica integridad criptográfica de
    la cadena. No es mecanismo de recuperación.

HASH RETORNADO (F6-R5):
    Cada hash es el actual tras el guardar correspondiente,
    confirmado por evidencia de que obtener_hash_final()
    devuelve el hash_actual del último evento.

ValueError (F6-R3):
    StoreBase.guardar lanza ValueError si idempotency_key
    duplicada. Capturado como DSLPersistenceError. El mensaje
    dice "duplicado o payload rechazado" porque no podemos
    distinguir por tipo de excepción.
"""

from typing import Dict, List, Optional, Tuple

from .evaluator import DSLEvaluationError
from ..extensiones.modelos import Asiento, ContextoContable
from ..extensiones.persistencia.base import StoreBase
from ..extensiones.serializador import serializar


class DSLPersistenceError(DSLEvaluationError):
    """Error de persistencia del DSL.

    Hereda de DSLEvaluationError (como DSLAssemblyError) para que
    el pipeline completo pueda capturarse con un except único.
    Contexto: 'ASIENTO #<indice>'.
    """


def persistir(
    asientos: List[Asiento],
    store: StoreBase,
    correlation_id: str,
    periodo_id: str,
    fecha: str,
) -> List[str]:
    """Persiste cada Asiento como evento ASIENTO_REGISTRADO.

    Ver contrato completo en el docstring del módulo.

    Args:
        asientos: salida de ensamblar().
        store: implementación de StoreBase (inyectada por el caller).
        correlation_id: agrupa los asientos de una misma corrida.
        periodo_id: período contable (ej. "2026-10").
        fecha: fecha de los asientos (ISO 8601).

    Returns:
        Lista de hashes actuales tras cada guardar (uno por asiento).

    Raises:
        DSLPersistenceError: asiento no cuadrado, payload no
            serializable, metadata vacía, o error del store.
    """
    if not asientos:
        return []

    if not correlation_id or not correlation_id.strip():
        raise DSLPersistenceError("correlation_id vacío")
    if not periodo_id or not periodo_id.strip():
        raise DSLPersistenceError("periodo_id vacío")
    if not fecha or not fecha.strip():
        raise DSLPersistenceError("fecha vacía")

    # Pre-serializar todo antes de tocar el store (F6-R2, F6-R4)
    preparados: List[Tuple[int, Dict]] = []
    for i, asiento in enumerate(asientos, start=1):
        ctx = f"ASIENTO #{i}"
        if not asiento.cuadrado:
            raise DSLPersistenceError(
                f"asiento no cuadrado (DEBE={asiento.total_debe}, "
                f"HABER={asiento.total_haber})", ctx
            )
        payload = _construir_payload(asiento, correlation_id,
                                     periodo_id, fecha, i)
        try:
            serializar(payload)
        except Exception as e:
            raise DSLPersistenceError(
                f"payload no serializable: {e}", ctx
            ) from e
        preparados.append((i, payload))

    # Guardar (ventana mid-batch reducida a errores del store)
    hashes: List[str] = []
    for i, payload in preparados:
        ctx = f"ASIENTO #{i}"
        idem_key = f"{correlation_id}-{i}"
        try:
            store.guardar(
                tipo_evento="ASIENTO_REGISTRADO",
                payload=payload,
                correlation_id=correlation_id,
                idempotency_key=idem_key,
                version_contexto=None,
            )
        except ValueError as e:
            raise DSLPersistenceError(
                f"duplicado o payload rechazado por el store: {e}", ctx
            ) from e
        except Exception as e:
            raise DSLPersistenceError(
                f"store.guardar falló tras {len(hashes)} asiento(s) "
                f"guardado(s): {e}", ctx
            ) from e
        hashes.append(store.obtener_hash_final())

    return hashes


def _construir_payload(
    asiento: Asiento,
    correlation_id: str,
    periodo_id: str,
    fecha: str,
    indice: int,
) -> Dict:
    """Construye el payload serializable del asiento."""
    return {
        "id": f"{correlation_id}-{indice}",
        "fecha": fecha,
        "periodo_id": periodo_id,
        "total_debe": asiento.total_debe,
        "total_haber": asiento.total_haber,
        "correlation_id": correlation_id,
        "partidas": [
            {
                "cuenta_codigo": linea.cuenta,
                "ubicacion": linea.ubicacion,
                "monto": linea.monto,
            }
            for linea in asiento.lineas
        ],
        "contexto": _contexto_a_dict(asiento.contexto),
    }


def _contexto_a_dict(ctx: Optional[ContextoContable]) -> Optional[Dict]:
    """Serializa ContextoContable o None."""
    if ctx is None:
        return None
    return {
        "marco_contable": ctx.marco_contable,
        "PCU_version": ctx.PCU_version,
        "reglas_version": ctx.reglas_version,
        "politica_monetaria_version": ctx.politica_monetaria_version,
    }

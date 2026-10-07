"""
MNFC v0.2.0 - Capa 7 - Maquina de estados del asiento.

Gobierna el ciclo de vida del asiento:
    PROPUESTO -> EVALUADO -> ADMITIDO/MODIFICADO/RECHAZADO -> ASENTADO -> ANULADO

No contiene logica contable, fiscal ni normativa.
Migrado de SCFV_DSR/scfv_dsr/contable/maquina_estados_asiento.py.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import uuid
import time
import hashlib

from .estados import EstadoAsiento


@dataclass
class Transicion:
    """Registro inmutable de una transicion de estado."""
    id: str
    desde: EstadoAsiento
    hasta: EstadoAsiento
    autor: str
    timestamp: int
    justificacion: str
    correlation_id: str
    version_contexto: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def hash(self) -> str:
        contenido = (
            self.id + "|" + self.desde.name + "|" + self.hasta.name
            + "|" + self.autor + "|" + str(self.timestamp)
            + "|" + self.correlation_id
        )
        return hashlib.sha256(contenido.encode("utf-8")).hexdigest()


class MaquinaEstadosAsiento:
    """Maquina de estados del asiento."""

    _TRANSICIONES = {
        EstadoAsiento.PROPUESTO: {
            EstadoAsiento.EVALUADO: lambda self, **k: True,
        },
        EstadoAsiento.EVALUADO: {
            EstadoAsiento.ADMITIDO: lambda self, **k: k.get("justificacion") is not None,
            EstadoAsiento.MODIFICADO: lambda self, **k: (
                k.get("justificacion") is not None
                and k.get("propuesta_modificada") is not None
            ),
            EstadoAsiento.RECHAZADO: lambda self, **k: k.get("justificacion") is not None,
        },
        EstadoAsiento.MODIFICADO: {
            EstadoAsiento.EVALUADO: lambda self, **k: True,
        },
        EstadoAsiento.ADMITIDO: {
            EstadoAsiento.ASENTADO: lambda self, **k: True,
        },
        EstadoAsiento.ASENTADO: {
            EstadoAsiento.ANULADO: lambda self, **k: k.get("justificacion") is not None,
        },
        EstadoAsiento.RECHAZADO: {},
        EstadoAsiento.ANULADO: {},
    }

    def __init__(self, estado_inicial: EstadoAsiento = EstadoAsiento.PROPUESTO):
        self.estado_actual = estado_inicial
        self.historial: List[Transicion] = []
        self.propuesta_original_id: Optional[str] = None
        self.propuesta_modificada_id: Optional[str] = None

    def transicionar(
        self,
        nuevo_estado: EstadoAsiento,
        autor: str,
        correlation_id: str,
        version_contexto: Dict[str, Any],
        justificacion: Optional[str] = None,
        propuesta_modificada: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> Transicion:
        if metadata is None:
            metadata = {}

        if self.estado_actual not in self._TRANSICIONES:
            raise ValueError(
                "Estado terminal %s no permite transiciones salientes"
                % self.estado_actual
            )

        if nuevo_estado not in self._TRANSICIONES[self.estado_actual]:
            raise ValueError(
                "Transicion invalida: %s -> %s. Permitidas desde %s: %s"
                % (
                    self.estado_actual,
                    nuevo_estado,
                    self.estado_actual,
                    list(self._TRANSICIONES[self.estado_actual].keys()),
                )
            )

        precondicion = self._TRANSICIONES[self.estado_actual][nuevo_estado]
        if not precondicion(
            self,
            justificacion=justificacion,
            propuesta_modificada=propuesta_modificada,
        ):
            raise ValueError(
                "Precondicion fallida para %s -> %s. Requisitos: %s"
                % (
                    self.estado_actual,
                    nuevo_estado,
                    self._describir_precondicion(self.estado_actual, nuevo_estado),
                )
            )

        transicion = Transicion(
            id=str(uuid.uuid4()),
            desde=self.estado_actual,
            hasta=nuevo_estado,
            autor=autor,
            timestamp=int(time.time()),
            justificacion=justificacion or "",
            correlation_id=correlation_id,
            version_contexto=version_contexto,
            metadata={
                "propuesta_original_id": self.propuesta_original_id,
                "propuesta_modificada_id": self.propuesta_modificada_id,
                **metadata,
            },
        )

        if nuevo_estado == EstadoAsiento.MODIFICADO:
            self.propuesta_modificada_id = (
                propuesta_modificada.get("id") if propuesta_modificada else None
            )

        self.historial.append(transicion)
        self.estado_actual = nuevo_estado

        if (
            nuevo_estado == EstadoAsiento.ADMITIDO
            and self.propuesta_original_id is None
        ):
            self.propuesta_original_id = correlation_id

        return transicion

    def es_terminal(self) -> bool:
        return self.estado_actual in {
            EstadoAsiento.RECHAZADO,
            EstadoAsiento.ASENTADO,
            EstadoAsiento.ANULADO,
        }

    def obtener_historial(self) -> List[Dict]:
        return [
            {
                "id": t.id,
                "desde": t.desde.name,
                "hasta": t.hasta.name,
                "autor": t.autor,
                "timestamp": t.timestamp,
                "justificacion": t.justificacion,
                "correlation_id": t.correlation_id,
                "version_contexto": t.version_contexto,
                "metadata": t.metadata,
                "hash": t.hash(),
            }
            for t in self.historial
        ]

    @staticmethod
    def _describir_precondicion(desde: EstadoAsiento, hasta: EstadoAsiento) -> str:
        descripciones = {
            (EstadoAsiento.EVALUADO, EstadoAsiento.ADMITIDO): "Se requiere justificacion",
            (EstadoAsiento.EVALUADO, EstadoAsiento.MODIFICADO): (
                "Se requiere justificacion y propuesta_modificada"
            ),
            (EstadoAsiento.EVALUADO, EstadoAsiento.RECHAZADO): "Se requiere justificacion",
            (EstadoAsiento.ASENTADO, EstadoAsiento.ANULADO): "Se requiere justificacion",
        }
        return descripciones.get((desde, hasta), "Sin requisitos adicionales")

    def puede_asentar(self) -> bool:
        return self.estado_actual == EstadoAsiento.ADMITIDO

    def puede_anular(self) -> bool:
        return self.estado_actual == EstadoAsiento.ASENTADO

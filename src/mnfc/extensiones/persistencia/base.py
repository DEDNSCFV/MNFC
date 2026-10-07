"""
MNFC v0.2.0 - Capa 7 - Persistencia. Interfaz abstracta.

Contrato comun que toda implementacion de persistencia debe cumplir.

Contrato derivado de SCFV_DSR/scfv_dsr/contable/event_store.py:
las implementaciones concretas (SQLite, JSON) deben exponer los
mismos metodos y garantizar la misma semantica.

Sin dependencias externas. Solo stdlib.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple


class StoreBase(ABC):
    """Interfaz abstracta de un almacen de eventos con cadena hash."""

    GENESIS_HASH = "0" * 64

    @abstractmethod
    def guardar(
        self,
        tipo_evento: str,
        payload: Dict,
        correlation_id: str,
        idempotency_key: str,
        version_contexto: Optional[Dict] = None,
    ) -> None:
        """
        Persiste un evento.

        Contrato:
            - Serializa payload y version_contexto con el serializador canonico.
            - Calcula hash_actual encadenado al hash_previo.
            - Almacena el evento de forma inmutable.
            - Lanza ValueError si idempotency_key ya existe.
        """
        pass

    @abstractmethod
    def obtener_hash_final(self) -> str:
        """Devuelve el hash del ultimo evento, o GENESIS_HASH si esta vacio."""
        pass

    @abstractmethod
    def verificar_cadena(self) -> Tuple[bool, str]:
        """
        Verifica la integridad de toda la cadena hash.

        Retorna:
            (True, "CADENA_INTEGRA") si todo esta bien
            (False, "mensaje descriptivo") si hay corrupcion
        """
        pass

    @abstractmethod
    def obtener_por_id(self, evento_id: int) -> Optional[Dict]:
        """Devuelve el evento con ese id, o None si no existe."""
        pass

    @abstractmethod
    def obtener_por_tipo(
        self,
        tipo_evento: str,
        limite: Optional[int] = None,
    ) -> List[Dict]:
        """Devuelve eventos de un tipo, ordenados por timestamp descendente."""
        pass

    @abstractmethod
    def obtener_por_correlation(
        self,
        correlation_id: str,
    ) -> Optional[Dict]:
        """Devuelve el primer evento con ese correlation_id, o None."""
        pass

    @abstractmethod
    def cerrar(self) -> None:
        """Cierra recursos abiertos (conexiones, archivos, etc.)."""
        pass

    @abstractmethod
    def __len__(self) -> int:
        """Devuelve la cantidad de eventos almacenados."""
        pass

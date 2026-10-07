"""
MNFC v0.2.0 - Capa 7 - Persistencia JSON.

Implementacion concreta de StoreBase usando un archivo JSON.

Misma semantica que SQLiteStore:
    - Mismo formato de payload canonico.
    - Misma formula de hash.
    - Misma cadena Merkle.

Un mismo evento guardado en SQLiteStore o JSONStore produce el mismo
hash. La cadena es verificable indistintamente entre implementaciones.

Escritura atomica: archivo temporal + os.replace.
"""

import os
import json
import hashlib
import time

from typing import Dict, Any, Optional, List, Tuple

from ..serializador import serializar
from .base import StoreBase


class JSONStore(StoreBase):
    """Almacen de eventos con cadena hash inmutable, en archivo JSON."""

    def __init__(self, file_path: str = "mnfc.json"):
        self.file_path = file_path
        self._eventos: List[Dict] = []
        self._next_id: int = 1
        if os.path.exists(file_path):
            self._cargar()

    # ------------------------------------------------------------------
    # Persistencia interna
    # ------------------------------------------------------------------

    def _cargar(self) -> None:
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._eventos = data.get("eventos", [])
        if self._eventos:
            self._next_id = max(e["id"] for e in self._eventos) + 1

    def _persistir(self) -> None:
        """Escritura atomica: escribir en .tmp y renombrar."""
        data = {"version": 1, "eventos": self._eventos}
        tmp = self.file_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.file_path)

    def _idempotency_existe(self, key: str) -> bool:
        return any(e["idempotency_key"] == key for e in self._eventos)

    def _hash_evento(
        self,
        payload_json: str,
        version_json: str,
        correlation_id: str,
        idempotency_key: str,
        hash_previo: str,
    ) -> str:
        datos = (
            payload_json
            + version_json
            + correlation_id
            + idempotency_key
            + hash_previo
        )
        return hashlib.sha256(datos.encode("utf-8")).hexdigest()

    # ------------------------------------------------------------------
    # Contrato StoreBase
    # ------------------------------------------------------------------

    def guardar(
        self,
        tipo_evento: str,
        payload: Dict,
        correlation_id: str,
        idempotency_key: str,
        version_contexto: Optional[Dict] = None,
    ) -> None:
        if self._idempotency_existe(idempotency_key):
            raise ValueError(
                "idempotency_key duplicada: " + repr(idempotency_key)
            )

        hash_previo = (
            self._eventos[-1]["hash_actual"]
            if self._eventos else self.GENESIS_HASH
        )

        tipo_evento_canonico = serializar(tipo_evento)
        if not isinstance(tipo_evento_canonico, (str, int, float, bool)):
            raise TypeError(
                "tipo_evento debe producir representacion escalar"
            )

        payload_canonico = serializar(payload)
        payload_json = json.dumps(
            payload_canonico,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        version_canonica = (
            serializar(version_contexto)
            if version_contexto is not None else {}
        )
        version_json = json.dumps(
            version_canonica,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        hash_actual = self._hash_evento(
            payload_json, version_json,
            correlation_id, idempotency_key, hash_previo,
        )
        timestamp = int(time.time())

        self._eventos.append({
            "id": self._next_id,
            "tipo_evento": tipo_evento_canonico,
            "payload": payload_json,
            "correlation_id": correlation_id,
            "idempotency_key": idempotency_key,
            "hash_previo": hash_previo,
            "hash_actual": hash_actual,
            "timestamp": timestamp,
            "version_contexto": version_json,
        })
        self._next_id += 1
        self._persistir()

    def obtener_hash_final(self) -> str:
        return (
            self._eventos[-1]["hash_actual"]
            if self._eventos else self.GENESIS_HASH
        )

    def verificar_cadena(self) -> Tuple[bool, str]:
        hash_esperado = self.GENESIS_HASH
        for e in self._eventos:
            if e["hash_previo"] != hash_esperado:
                return (False, "Cadena rota en evento %s" % e["id"])
            recomputado = self._hash_evento(
                e["payload"],
                e["version_contexto"] or "{}",
                e["correlation_id"],
                e["idempotency_key"],
                e["hash_previo"],
            )
            if recomputado != e["hash_actual"]:
                return (False, "Hash invalido en evento %s" % e["id"])
            hash_esperado = e["hash_actual"]
        return (True, "CADENA_INTEGRA")

    def _evento_a_dict(self, e: Dict) -> Dict:
        return {
            "id": e["id"],
            "tipo_evento": e["tipo_evento"],
            "payload": json.loads(e["payload"]),
            "correlation_id": e["correlation_id"],
            "idempotency_key": e["idempotency_key"],
            "hash_previo": e["hash_previo"],
            "hash_actual": e["hash_actual"],
            "timestamp": e["timestamp"],
            "version_contexto": (
                json.loads(e["version_contexto"])
                if e["version_contexto"] else None
            ),
        }

    def obtener_por_id(self, evento_id: int) -> Optional[Dict]:
        for e in self._eventos:
            if e["id"] == evento_id:
                return self._evento_a_dict(e)
        return None

    def obtener_por_tipo(
        self,
        tipo_evento: str,
        limite: Optional[int] = None,
    ) -> List[Dict]:
        tipo_canonico = serializar(tipo_evento)
        filtrados = [e for e in self._eventos if e["tipo_evento"] == tipo_canonico]
        filtrados.sort(key=lambda e: (-e["timestamp"], -e["id"]))
        if limite is not None:
            filtrados = filtrados[:limite]
        return [self._evento_a_dict(e) for e in filtrados]

    def obtener_por_correlation(self, correlation_id: str) -> Optional[Dict]:
        for e in self._eventos:
            if e["correlation_id"] == correlation_id:
                return self._evento_a_dict(e)
        return None

    def cerrar(self) -> None:
        pass

    def __len__(self) -> int:
        return len(self._eventos)

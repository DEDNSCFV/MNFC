"""
MNFC v0.2.0 - Capa 7 - Persistencia SQLite.

Implementacion concreta de StoreBase usando SQLite.

Persiste eventos con representacion canonica y cadena hash Merkle.
Migrado de SCFV_DSR/scfv_dsr/contable/event_store.py.
Adaptado para heredar de StoreBase y usar el serializador de MNFC.
"""

import sqlite3
import json
import hashlib
import time

from typing import Dict, Any, Optional, List, Tuple

from ..serializador import serializar
from .base import StoreBase


class SQLiteStore(StoreBase):
    """
    Almacen de eventos con cadena hash inmutable, en SQLite.

    StoreBase no interpreta el significado del evento.
    Solo persiste y recupera representaciones canonicas.
    """

    def __init__(self, db_path: str = "mnfc.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS event_store (
                id INTEGER PRIMARY KEY,
                tipo_evento TEXT NOT NULL,
                payload TEXT NOT NULL,
                correlation_id TEXT NOT NULL,
                idempotency_key TEXT UNIQUE NOT NULL,
                hash_previo TEXT NOT NULL,
                hash_actual TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                version_contexto TEXT
            )
        """)
        self.conn.commit()

    def guardar(
        self,
        tipo_evento: str,
        payload: Dict,
        correlation_id: str,
        idempotency_key: str,
        version_contexto: Optional[Dict] = None,
    ) -> None:
        cursor = self.conn.cursor()

        # 1. Hash anterior
        cursor.execute(
            "SELECT hash_actual FROM event_store ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        hash_previo = row[0] if row else self.GENESIS_HASH

        # 2. Tipo canonico
        tipo_evento_canonico = serializar(tipo_evento)
        if not isinstance(tipo_evento_canonico, (str, int, float, bool)):
            raise TypeError(
                "tipo_evento debe producir representacion escalar"
            )

        # 3. Payload canonico
        payload_canonico = serializar(payload)
        payload_json = json.dumps(
            payload_canonico,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        # 4. Version contexto canonica
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

        # 5. Hash
        datos = (
            payload_json
            + version_json
            + correlation_id
            + idempotency_key
            + hash_previo
        )
        hash_actual = hashlib.sha256(datos.encode("utf-8")).hexdigest()
        timestamp = int(time.time())

        # 6. Persistir
        try:
            cursor.execute(
                """
                INSERT INTO event_store (
                    tipo_evento, payload, correlation_id, idempotency_key,
                    hash_previo, hash_actual, timestamp, version_contexto
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tipo_evento_canonico, payload_json, correlation_id,
                    idempotency_key, hash_previo, hash_actual, timestamp,
                    version_json,
                ),
            )
            self.conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError(
                "idempotency_key duplicada: " + repr(idempotency_key)
            ) from exc

    def obtener_hash_final(self) -> str:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT hash_actual FROM event_store ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        return row[0] if row else self.GENESIS_HASH

    def verificar_cadena(self) -> Tuple[bool, str]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, hash_previo, hash_actual, payload, version_contexto,
                   correlation_id, idempotency_key
            FROM event_store ORDER BY id
        """)
        rows = cursor.fetchall()
        hash_esperado = self.GENESIS_HASH

        for row in rows:
            if row["hash_previo"] != hash_esperado:
                return (False, "Cadena rota en evento %s" % row["id"])

            version_json = row["version_contexto"] or "{}"
            payload_json = row["payload"]

            datos = (
                payload_json + version_json + row["correlation_id"]
                + row["idempotency_key"] + row["hash_previo"]
            )
            recomputado = hashlib.sha256(datos.encode("utf-8")).hexdigest()

            if recomputado != row["hash_actual"]:
                return (False, "Hash invalido en evento %s" % row["id"])

            hash_esperado = row["hash_actual"]

        return (True, "CADENA_INTEGRA")

    def _fila_a_dict(self, row) -> Dict:
        return {
            "id": row[0],
            "tipo_evento": row[1],
            "payload": json.loads(row[2]),
            "correlation_id": row[3],
            "idempotency_key": row[4],
            "hash_previo": row[5],
            "hash_actual": row[6],
            "timestamp": row[7],
            "version_contexto": json.loads(row[8]) if row[8] else None,
        }

    def obtener_por_id(self, evento_id: int) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, tipo_evento, payload, correlation_id, idempotency_key,
                   hash_previo, hash_actual, timestamp, version_contexto
            FROM event_store WHERE id = ?
        """, (evento_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return self._fila_a_dict(row)

    def obtener_por_tipo(
        self,
        tipo_evento: str,
        limite: Optional[int] = None,
    ) -> List[Dict]:
        cursor = self.conn.cursor()
        tipo_evento_canonico = serializar(tipo_evento)

        if limite is not None:
            cursor.execute("""
                SELECT id, tipo_evento, payload, correlation_id, idempotency_key,
                       hash_previo, hash_actual, timestamp, version_contexto
                FROM event_store WHERE tipo_evento = ?
                ORDER BY timestamp DESC, id DESC LIMIT ?
            """, (tipo_evento_canonico, limite))
        else:
            cursor.execute("""
                SELECT id, tipo_evento, payload, correlation_id, idempotency_key,
                       hash_previo, hash_actual, timestamp, version_contexto
                FROM event_store WHERE tipo_evento = ?
                ORDER BY timestamp DESC, id DESC
            """, (tipo_evento_canonico,))

        return [self._fila_a_dict(row) for row in cursor.fetchall()]

    def obtener_por_correlation(self, correlation_id: str) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, tipo_evento, payload, correlation_id, idempotency_key,
                   hash_previo, hash_actual, timestamp, version_contexto
            FROM event_store WHERE correlation_id = ?
        """, (correlation_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return self._fila_a_dict(row)

    def cerrar(self) -> None:
        self.conn.close()

    def __len__(self) -> int:
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM event_store")
        return cursor.fetchone()[0]

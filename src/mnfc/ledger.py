"""
Capa 6 - Ledger inmutable - el TIEMPO.

Encadenamiento por hash de bloques. Cada bloque incluye el hash del
bloque anterior. Alterar un bloque rompe todos los siguientes.

Locus:
    Merkle 1979 - A Certified Digital Signature
        ~/.merkle_1979_raw.txt
        L213   - "the new signature method is called a 'tree signature'"
        L243   - "The Winternitz one time signature"
        L2463  - "the root of the authentication tree, or R"
        L2475  - "the authentication path for Yi"
        L2564  - "B knows R, the root of the au[thentication tree]"
        L3374  - "authentication path must be precomputed"

    ProGit 2014 - ~/.progit_2014_raw.txt
        L494   - Git usa hash SHA-1 como suma de comprobacion
        L500   - "Git guarda todo no por nombre de archivo, sino por hash"
        L684   - "introducida de manera inmutable en los commits"
        L2127  - firma y verificacion con GPG

Estado epistemico:
    N1 - Merkle 1979 + ProGit 2014 (locus verificado)
    N3 - pendiente verificacion contra PDF
    N4 - pendiente aplicacion industrial

Implementacion: cadena de hashes (Merkle DAG degenerado - un arbol
uninodal). v0.2.0 puede agregar arbol completo con pruebas de inclusion.

Frontera: el modulo no persiste. El usuario decide donde guardar la
cadena. No decide contabilidad (capa 0). No calcula aritmetica (capa 1).
"""

import hashlib
import json
from typing import List


GENESIS = "0" * 64


def _hash_bloque(prev_hash: str, contenido: dict) -> str:
    """
    H = SHA256(prev_hash || canonical_json(contenido)).

    Locus: Merkle 1979 L2463 ("the root of the authentication tree").
    ProGit 2014 L494 ("hash SHA-1 como suma de comprobacion").
    """
    canonical = json.dumps(contenido, sort_keys=True, separators=(",", ":"))
    payload = f"{prev_hash}|{canonical}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class Ledger:
    """
    Cadena de hashes de bloques contables.

    Uso:
        ledger = Ledger()
        h1 = ledger.append(asiento_1)   # -> hash 64 hex
        h2 = ledger.append(asiento_2)   # -> hash encadenado a h1
        assert ledger.verify()          # True si la cadena es integra
    """

    def __init__(self) -> None:
        self._hashes: List[str] = []
        self._contenidos: List[dict] = []

    def append(self, contenido: dict) -> str:
        """Anade un bloque. Devuelve su hash."""
        prev = self._hashes[-1] if self._hashes else GENESIS
        h = _hash_bloque(prev, contenido)
        self._hashes.append(h)
        self._contenidos.append(contenido)
        return h

    def raiz(self) -> str:
        """Raiz de la cadena. Merkle 1979 L2463."""
        return self._hashes[-1] if self._hashes else GENESIS

    def verify(self) -> bool:
        """Verifica la integridad de toda la cadena. Merkle 1979 L2564."""
        prev = GENESIS
        for h, contenido in zip(self._hashes, self._contenidos):
            if _hash_bloque(prev, contenido) != h:
                return False
            prev = h
        return True

    def __len__(self) -> int:
        return len(self._hashes)

    def __repr__(self) -> str:
        return f"Ledger(n={len(self)}, raiz={self.raiz()[:12]}...)"

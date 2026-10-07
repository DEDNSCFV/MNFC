"""
MNFC v0.2.0 - Extensiones del kernel. Capas 7-9.

Reexporta la API publica de las extensiones del kernel MNFC:

    - Estados y enumeraciones (ciclo de vida del asiento)
    - Maquina de estados del asiento (transiciones validas)
    - Modelos tipados (Asiento, LineaAsiento, PartidaAutorizada)
    - Serializador canonico (representacion determinista)
    - Reticulo booleano de cuentas (algebra de conjuntos)
    - Examinador de evidencia (validaciones)
    - Persistencia (SQLite + JSON con cadena Merkle)
    - Reportes (libro diario, mayor, balance)

Uso:
    from mnfc.extensiones import SQLiteStore, JSONStore
    from mnfc.extensiones import MaquinaEstadosAsiento, EstadoAsiento
    from mnfc.extensiones import reportes
"""

# Estados y enumeraciones
from .estados import (
    VersionContexto,
    EstadoEpistemico,
    EstadoPropuesta,
    EstadoConsecuencia,
    EstadoAsiento,
    TipoDecisionH2,
    TipoEvento,
)

# Maquina de estados
from .maquina import (
    MaquinaEstadosAsiento,
    Transicion,
)

# Modelos tipados
from .modelos import (
    ContextoContable,
    PartidaAutorizada,
    LineaAsiento,
    Asiento,
)

# Serializador canonico
from .serializador import (
    serializar,
    deserializar,
    PersistenciaViolacion,
)

# Reticulo booleano
from .reticulo import ReticuloCuentas

# Examinador
from .examinador import (
    ExaminadorEvidencia,
    Reporte,
)

# Persistencia
from .persistencia.base import StoreBase
from .persistencia.sqlite_store import SQLiteStore
from .persistencia.json_store import JSONStore


__all__ = [
    # Estados
    "VersionContexto",
    "EstadoEpistemico",
    "EstadoPropuesta",
    "EstadoConsecuencia",
    "EstadoAsiento",
    "TipoDecisionH2",
    "TipoEvento",
    # Maquina
    "MaquinaEstadosAsiento",
    "Transicion",
    # Modelos
    "ContextoContable",
    "PartidaAutorizada",
    "LineaAsiento",
    "Asiento",
    # Serializador
    "serializar",
    "deserializar",
    "PersistenciaViolacion",
    # Reticulo
    "ReticuloCuentas",
    # Examinador
    "ExaminadorEvidencia",
    "Reporte",
    # Persistencia
    "StoreBase",
    "SQLiteStore",
    "JSONStore",
]

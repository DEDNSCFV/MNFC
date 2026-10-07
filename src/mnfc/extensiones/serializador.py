"""
MNFC v0.2.0 - Capa 7 - Serializador canonico.

Convierte objetos Python soportados en estructuras JSON canonicas,
deterministas y libres de representaciones Python no portables.

Reglas:
    None       -> None
    bool       -> bool
    int        -> int
    float      -> float
    str        -> str
    Enum       -> Enum.name
    datetime   -> datetime.isoformat()
    list       -> lista recursiva
    tuple      -> lista recursiva
    dict       -> diccionario recursivo
    dataclass  -> diccionario de campos recursivos

Todo tipo no soportado produce PersistenciaViolacion.

Sin dependencias externas. Solo stdlib.
Migrado desde SCFV_DSR/scfv_dsr/infraestructura/serializador_canonico.py.
"""

from dataclasses import fields, is_dataclass, MISSING
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Type, Union, get_args, get_origin


class PersistenciaViolacion(Exception):
    """Error de integridad de persistencia."""
    pass


def _es_enum(tipo: Any) -> bool:
    return isinstance(tipo, type) and issubclass(tipo, Enum)


def _tipo_optional(tipo: Any) -> tuple:
    """Extrae el tipo interno de Optional[T]."""
    origen = get_origin(tipo)
    if origen is Union:
        argumentos = get_args(tipo)
        if type(None) in argumentos and len(argumentos) == 2:
            tipo_interno = next(
                a for a in argumentos if a is not type(None)
            )
            return tipo_interno, True
    return tipo, False


def serializar(obj: Any) -> Any:
    """Convierte recursivamente un objeto a una estructura JSON canonica."""
    if obj is None:
        return None

    # bool antes que int por herencia de Python
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, int):
        return obj
    if isinstance(obj, float):
        return obj
    if isinstance(obj, str):
        return obj

    if isinstance(obj, Enum):
        return obj.name

    if isinstance(obj, datetime):
        return obj.isoformat()

    if isinstance(obj, list):
        return [serializar(item) for item in obj]

    if isinstance(obj, tuple):
        return [serializar(item) for item in obj]

    if isinstance(obj, dict):
        resultado = {}
        for clave, valor in obj.items():
            clave_serializada = serializar(clave)
            if not isinstance(
                clave_serializada,
                (str, int, float, bool)
            ) and clave_serializada is not None:
                raise PersistenciaViolacion(
                    "Clave de diccionario no compatible con JSON: "
                    + type(clave).__name__
                )
            resultado[clave_serializada] = serializar(valor)
        return resultado

    if is_dataclass(obj) and not isinstance(obj, type):
        resultado = {}
        for campo in fields(obj):
            valor = getattr(obj, campo.name)
            resultado[campo.name] = serializar(valor)
        return resultado

    raise PersistenciaViolacion(
        "Tipo no soportado para serializacion canonica: "
        + type(obj).__name__
        + " (valor: " + repr(obj) + ")"
    )


def _deserializar_tipado(data: Any, tipo: Any) -> Any:
    """Reconstruye un valor utilizando su tipo declarado."""
    tipo_real, es_optional = _tipo_optional(tipo)

    if data is None:
        return None

    if _es_enum(tipo_real):
        if not isinstance(data, str):
            raise PersistenciaViolacion(
                "Valor invalido para Enum " + tipo_real.__name__
            )
        try:
            return tipo_real[data]
        except KeyError as exc:
            raise PersistenciaViolacion(
                "Miembro Enum invalido para " + tipo_real.__name__
                + ": " + repr(data)
            ) from exc

    if tipo_real is datetime:
        if not isinstance(data, str):
            raise PersistenciaViolacion(
                "datetime canonico debe ser cadena ISO 8601"
            )
        try:
            return datetime.fromisoformat(data)
        except ValueError as exc:
            raise PersistenciaViolacion(
                "datetime ISO invalido: " + repr(data)
            ) from exc

    if isinstance(tipo_real, type) and is_dataclass(tipo_real):
        return deserializar(data, tipo_real)

    origen = get_origin(tipo_real)

    if origen is list:
        argumentos = get_args(tipo_real)
        if not isinstance(data, list):
            raise PersistenciaViolacion(
                "Se esperaba lista para " + str(tipo_real)
            )
        if argumentos:
            tipo_elemento = argumentos[0]
            return [
                _deserializar_tipado(item, tipo_elemento)
                for item in data
            ]
        return list(data)

    if origen is tuple:
        argumentos = get_args(tipo_real)
        if not isinstance(data, list):
            raise PersistenciaViolacion(
                "Se esperaba lista para " + str(tipo_real)
            )
        if len(argumentos) == 2 and argumentos[1] is Ellipsis:
            return tuple(
                _deserializar_tipado(item, argumentos[0])
                for item in data
            )
        if argumentos:
            if len(data) != len(argumentos):
                raise PersistenciaViolacion(
                    "Longitud incorrecta para " + str(tipo_real)
                )
            return tuple(
                _deserializar_tipado(item, ti)
                for item, ti in zip(data, argumentos)
            )
        return tuple(data)

    if origen is dict:
        argumentos = get_args(tipo_real)
        if not isinstance(data, dict):
            raise PersistenciaViolacion(
                "Se esperaba dict para " + str(tipo_real)
            )
        if len(argumentos) == 2:
            tipo_clave, tipo_valor = argumentos
            return {
                _deserializar_tipado(k, tipo_clave):
                _deserializar_tipado(v, tipo_valor)
                for k, v in data.items()
            }
        return dict(data)

    if tipo_real in (str, int, float, bool):
        if not isinstance(data, tipo_real):
            raise PersistenciaViolacion(
                "Tipo incorrecto: se esperaba " + tipo_real.__name__
                + ", se recibio " + type(data).__name__
            )
        return data

    return deserializar(data)


def deserializar(data: Any, target_class: Optional[Type] = None) -> Any:
    """Reconstruye una estructura JSON canonica."""
    if target_class is not None:
        if not isinstance(target_class, type):
            raise PersistenciaViolacion(
                "target_class debe ser un tipo/clase"
            )
        if not is_dataclass(target_class):
            raise PersistenciaViolacion(
                "target_class debe ser un dataclass"
            )
        if not isinstance(data, dict):
            raise PersistenciaViolacion(
                "Se esperaba dict para " + target_class.__name__
            )

        kwargs = {}
        for campo in fields(target_class):
            if campo.name not in data:
                tiene_default = (
                    campo.default is not MISSING
                    or campo.default_factory is not MISSING
                )
                if tiene_default:
                    continue
                raise PersistenciaViolacion(
                    "Campo requerido ausente: "
                    + target_class.__name__ + "." + campo.name
                )
            try:
                kwargs[campo.name] = _deserializar_tipado(
                    data[campo.name], campo.type
                )
            except PersistenciaViolacion:
                raise
            except Exception as exc:
                raise PersistenciaViolacion(
                    "Error reconstruyendo campo "
                    + target_class.__name__ + "." + campo.name
                    + ": " + str(exc)
                ) from exc

        try:
            return target_class(**kwargs)
        except Exception as exc:
            raise PersistenciaViolacion(
                "Error reconstruyendo dataclass "
                + target_class.__name__ + ": " + str(exc)
            ) from exc

    if data is None:
        return None
    if isinstance(data, (bool, int, float, str)):
        return data
    if isinstance(data, list):
        return [deserializar(item) for item in data]
    if isinstance(data, dict):
        return {
            deserializar(k): deserializar(v)
            for k, v in data.items()
        }

    raise PersistenciaViolacion(
        "Tipo no soportado para deserializacion: " + type(data).__name__
    )

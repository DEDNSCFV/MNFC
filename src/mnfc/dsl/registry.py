"""MNFC DSL — Fase 5 · Registry (operaciones con metadatos).

Contenedor tipado de operaciones con metadatos (tipo, fuente,
descripción). Provee to_dict() para retro-compatibilidad con el
evaluator de Fase 3b, que espera Dict[str, Callable].

Frontera:
- No carga marcos reales.
- No carga operaciones.json.
- No valida contra kernel (baldor/estadistica).
- No persiste.
- Sin fiscal.

Los datos del registry son inyectados por el caller. En tests,
datos sintéticos. En producción (Fase 7), carga desde fuentes
aprobadas por separado.

Contrato de registrar()
-----------------------
Orden de validación (pasos 1-6 solo lectura; paso 7 única escritura):

  1. isinstance(op, OperacionRegistrada)
  2. nombre: str, no vacío, no solo espacios
  3. tipo: str y pertenece a TIPOS_VALIDOS
  4. fn: invocable
  5. fuente, descripcion: str o None
  6. nombre no duplicado
  7. self._ops[op.nombre] = op

No hay normalización silenciosa de nombres (mayúsculas, espacios,
tildes, etc.). Lo que el caller pasa es lo que queda.

Contrato de mutación
--------------------
registrar() efectúa una única mutación de estado, mediante la
inserción en _ops, después de completar todas las validaciones.
Se elimina _orden y, por tanto, no existe una segunda estructura
cuyo orden deba mantenerse sincronizado. El contrato garantiza
que los errores de validación y los duplicados no alteran el
estado. No promete rollback frente a cualquier fallo excepcional
ni seguridad concurrente.

Orden de iteración
------------------
El dict de Python preserva orden de inserción desde 3.7. listar()
y to_dict() devuelven los elementos en orden de registro.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Literal, Optional


TIPOS_VALIDOS = frozenset({"ley", "norma", "compuesta"})


class DSLRegistryError(Exception):
    """Error del registry: duplicado, tipo inválido, ausente."""

    def __init__(self, mensaje: str, contexto: str = ""):
        self.mensaje = mensaje
        self.contexto = contexto
        if contexto:
            super().__init__(f"{contexto}: {mensaje}")
        else:
            super().__init__(mensaje)


@dataclass(frozen=True)
class OperacionRegistrada:
    """Una operación con metadatos.

    Inmutabilidad: frozen=True impide reasignar campos (nombre, fn,
    tipo, fuente, descripcion). NO garantiza que el objeto callable
    en 'fn' sea puro, ni que su comportamiento no cambie por estado
    interno, ni que sea thread-safe. La garantía es de campos del
    dataclass, no del callable referenciado.
    """
    nombre: str
    fn: Callable[[dict], float]
    tipo: Literal["ley", "norma", "compuesta"] = "ley"
    fuente: Optional[str] = None
    descripcion: Optional[str] = None


class Registry:
    """Registro de operaciones con metadatos.

    Uso:
        r = Registry()
        r.registrar(OperacionRegistrada("suma", fn, tipo="ley"))
        r.contiene("suma")           # True
        r.obtener("suma").tipo       # "ley"
        ops_dict = r.to_dict()       # {"suma": fn}
    """

    def __init__(self) -> None:
        self._ops: Dict[str, OperacionRegistrada] = {}

    def registrar(self, op: OperacionRegistrada) -> None:
        """Registra una operación. Orden de validación documentado
        en el docstring del módulo. Lanza DSLRegistryError si algo
        no cumple, sin dejar estado parcial.
        """
        # 1. Tipo del argumento
        if not isinstance(op, OperacionRegistrada):
            raise DSLRegistryError(
                f"se esperaba OperacionRegistrada, no {type(op).__name__}"
            )

        # 2. Nombre: str, no vacío, no solo espacios
        if not isinstance(op.nombre, str):
            raise DSLRegistryError(
                f"nombre debe ser str, no {type(op.nombre).__name__}"
            )
        if not op.nombre.strip():
            raise DSLRegistryError(
                f"nombre no puede estar vacío ni ser solo espacios: "
                f"{op.nombre!r}"
            )

        # 3. Tipo: str y en TIPOS_VALIDOS
        if not isinstance(op.tipo, str):
            raise DSLRegistryError(
                f"tipo debe ser str, no {type(op.tipo).__name__}"
            )
        if op.tipo not in TIPOS_VALIDOS:
            raise DSLRegistryError(
                f"tipo inválido '{op.tipo}' para operación "
                f"'{op.nombre}'. Válidos: {sorted(TIPOS_VALIDOS)}"
            )

        # 4. fn invocable
        if not callable(op.fn):
            raise DSLRegistryError(
                f"fn no es callable en operación '{op.nombre}'"
            )

        # 5. fuente y descripcion: str o None
        if op.fuente is not None and not isinstance(op.fuente, str):
            raise DSLRegistryError(
                f"fuente debe ser str o None, no "
                f"{type(op.fuente).__name__}"
            )
        if op.descripcion is not None and not isinstance(op.descripcion, str):
            raise DSLRegistryError(
                f"descripcion debe ser str o None, no "
                f"{type(op.descripcion).__name__}"
            )

        # 6. No duplicado
        if op.nombre in self._ops:
            raise DSLRegistryError(
                f"operación '{op.nombre}' ya registrada"
            )

        # 7. Única escritura (después de todas las validaciones)
        self._ops[op.nombre] = op

    def obtener(self, nombre: str) -> OperacionRegistrada:
        """Devuelve la operación. Contrato: 'nombre' debe ser str.
        Con no-str lanza DSLRegistryError('no está en el registry')."""
        if nombre not in self._ops:
            raise DSLRegistryError(
                f"operación '{nombre}' no está en el registry"
            )
        return self._ops[nombre]

    def contiene(self, nombre: str) -> bool:
        """True si 'nombre' está registrado. Acepta str; con tipos
        no-str retorna False sin error (búsqueda en dict)."""
        return nombre in self._ops

    def __contains__(self, nombre: str) -> bool:
        return self.contiene(nombre)

    def listar(self) -> List[OperacionRegistrada]:
        """Devuelve operaciones en orden de registro."""
        return list(self._ops.values())

    def to_dict(self) -> Dict[str, Callable]:
        """Compat con evaluator de Fase 3b: {nombre: fn} sin metadatos.

        Devuelve un dict nuevo en cada llamada. Mutarlo no afecta
        el estado del registry.
        """
        return {n: op.fn for n, op in self._ops.items()}

    def __len__(self) -> int:
        return len(self._ops)

    def __repr__(self) -> str:
        return f"Registry(n={len(self)})"

"""
MNFC DSL — Fase 2
Parser recursivo descendente para la gramática v1.6.

Reconoce:
    - DSL_VERSION
    - ELEMENTOS / MARCOS / CATEGORIA / HECHO
    - FRACTAL con reglas SI/ENTONCES y acciones GENERAR CONSECUENCIA

El parser NO hereda de DSR. NO acepta `cuenta=`. El DSL sólo cita
categorías universales.

Sin dependencias externas. Solo stdlib.
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple


# ═════════════════════════════════════════════════════════════════════
# Excepción
# ═════════════════════════════════════════════════════════════════════

class DSLSyntaxError(Exception):
    """Error de sintaxis del DSL. Incluye archivo, línea, columna."""

    def __init__(self, mensaje: str, linea: int = 0, col: int = 0,
                 archivo: str = "<input>"):
        self.mensaje = mensaje
        self.linea = linea
        self.col = col
        self.archivo = archivo
        super().__init__(f"{archivo}:{linea}:{col}: {mensaje}")


# ═════════════════════════════════════════════════════════════════════
# Tokens reservados
# ═════════════════════════════════════════════════════════════════════

KEYWORDS = frozenset({
    "DSL_VERSION", "ELEMENTOS", "MARCOS", "CATEGORIA", "HECHO", "FRACTAL",
    "REGLA", "SI", "ENTONCES", "GENERAR", "CONSECUENCIA",
    "Y", "O", "NO", "VERDADERO", "FALSO",
    "categoria", "elemento", "universal", "operacion", "movimiento",
    "fuente", "evidencia", "AUMENTA", "DISMINUYE",
})


# ═════════════════════════════════════════════════════════════════════
# Token
# ═════════════════════════════════════════════════════════════════════

@dataclass
class Token:
    tipo: str
    valor: str
    linea: int
    col: int

    def __repr__(self):
        return f"Token({self.tipo!r}, {self.valor!r}, L{self.linea}:{self.col})"


# ═════════════════════════════════════════════════════════════════════
# Lexer
# ═════════════════════════════════════════════════════════════════════

_SINGLE = {
    "=": "ASSIGN", ";": "SEMI", ":": "COLON", ",": "COMMA", ".": "DOT",
    "[": "LBRACK", "]": "RBRACK", "{": "LBRACE", "}": "RBRACE",
    "(": "LPAREN", ")": "RPAREN", ">": "GT", "<": "LT",
    "\u222a": "UNION",    # ∪
    "\u2229": "INTER",    # ∩
    "\u2216": "DIFF",     # ∖
    "\u00ac": "NOT",      # ¬
    "\u2208": "IN",       # ∈
    "\u2286": "SUBSET",   # ⊆
}


class Lexer:

    def __init__(self, texto: str, archivo: str = "<input>"):
        self.texto = texto
        self.archivo = archivo
        self.i = 0
        self.linea = 1
        self.col = 1

    def _peek(self, k: int = 0) -> str:
        j = self.i + k
        return self.texto[j] if j < len(self.texto) else ""

    def _advance(self, n: int = 1) -> None:
        for _ in range(n):
            if self.i < len(self.texto):
                if self.texto[self.i] == "\n":
                    self.linea += 1
                    self.col = 1
                else:
                    self.col += 1
                self.i += 1

    def tokenizar(self) -> List[Token]:
        tokens: List[Token] = []
        while self.i < len(self.texto):
            c = self.texto[self.i]

            if c in " \t\r\n":
                self._advance()
                continue

            if c == "#":
                while self.i < len(self.texto) and self.texto[self.i] != "\n":
                    self._advance()
                continue

            if c == '"':
                tokens.append(self._lex_string())
                continue

            if c.isdigit() or (c == "-" and self._peek(1).isdigit()):
                tokens.append(self._lex_number())
                continue

            if c.isalpha() or c == "_":
                tokens.append(self._lex_identifier())
                continue

            if c == "=" and self._peek(1) == "=":
                tokens.append(self._emit("EQ", "==", 2)); continue
            if c == "!" and self._peek(1) == "=":
                tokens.append(self._emit("NEQ", "!=", 2)); continue
            if c == ">" and self._peek(1) == "=":
                tokens.append(self._emit("GE", ">=", 2)); continue
            if c == "<" and self._peek(1) == "=":
                tokens.append(self._emit("LE", "<=", 2)); continue

            if c in _SINGLE:
                tokens.append(self._emit(_SINGLE[c], c, 1)); continue

            raise DSLSyntaxError(
                f"carácter inesperado {c!r}", self.linea, self.col, self.archivo
            )

        tokens.append(Token("EOF", "", self.linea, self.col))
        return tokens

    def _emit(self, tipo: str, valor: str, n: int) -> Token:
        t = Token(tipo, valor, self.linea, self.col)
        self._advance(n)
        return t

    def _lex_string(self) -> Token:
        linea, col = self.linea, self.col
        self._advance()
        chars: List[str] = []
        while self.i < len(self.texto) and self.texto[self.i] != '"':
            if self.texto[self.i] == "\n":
                raise DSLSyntaxError(
                    "string sin cerrar", linea, col, self.archivo)
            chars.append(self.texto[self.i])
            self._advance()
        if self.i >= len(self.texto):
            raise DSLSyntaxError(
                "string sin cerrar", linea, col, self.archivo)
        self._advance()
        return Token("STRING", "".join(chars), linea, col)

    def _lex_number(self) -> Token:
        linea, col = self.linea, self.col
        chars: List[str] = []
        if self.texto[self.i] == "-":
            chars.append("-"); self._advance()
        while self.i < len(self.texto) and self.texto[self.i].isdigit():
            chars.append(self.texto[self.i]); self._advance()
        if self.i < len(self.texto) and self.texto[self.i] == "." \
                and self._peek(1).isdigit():
            chars.append("."); self._advance()
            while self.i < len(self.texto) and self.texto[self.i].isdigit():
                chars.append(self.texto[self.i]); self._advance()
        return Token("NUMBER", "".join(chars), linea, col)

    def _lex_identifier(self) -> Token:
        linea, col = self.linea, self.col
        chars: List[str] = []
        while self.i < len(self.texto) and \
                (self.texto[self.i].isalnum() or self.texto[self.i] == "_"):
            chars.append(self.texto[self.i]); self._advance()
        nombre = "".join(chars)
        tipo = nombre if nombre in KEYWORDS else "IDENT"
        return Token(tipo, nombre, linea, col)


# ═════════════════════════════════════════════════════════════════════
# AST
# ═════════════════════════════════════════════════════════════════════

# Condiciones
@dataclass
class CmpEscalar:
    izq: str
    op: str
    der: Any        # str (ident) o str (string) o str (number)

@dataclass
class HechoRef:
    nombre: str

@dataclass
class NegBool:
    interno: "NodoCond"

@dataclass
class Conjuncion:
    partes: List["NodoCond"]

@dataclass
class Disyuncion:
    partes: List["NodoCond"]

# Conjuntos
@dataclass
class CategoriaRef:
    nombre: str

@dataclass
class SetLiteral:
    items: List[str]

@dataclass
class Union:
    izq: "NodoSet"
    der: "NodoSet"

@dataclass
class Inter:
    izq: "NodoSet"
    der: "NodoSet"

@dataclass
class Diff:
    izq: "NodoSet"
    der: "NodoSet"

@dataclass
class Complemento:
    interno: "NodoSet"

@dataclass
class Relacion:
    """set_expr (∈ | ⊆) set_expr"""
    izq: "NodoSet"
    op: str         # '∈' o '⊆'
    der: "NodoSet"

NodoCond = Any
NodoSet = Any

# Acciones
@dataclass
class Cita:
    marco: str
    seccion: str

@dataclass
class Accion:
    categoria: Optional[NodoSet] = None
    operacion: Optional[str] = None
    movimiento: Optional[str] = None
    fuente: Optional[Cita] = None
    evidencia: Optional[str] = None

# Estructuras de nivel superior
@dataclass
class Elemento:
    nombre: str
    descripcion: Optional[str] = None

@dataclass
class Categoria:
    nombre: str
    elemento: str
    universal: bool

@dataclass
class Regla:
    nombre: str
    condicion: NodoCond
    acciones: List[Accion]

@dataclass
class Fractal:
    nombre: str
    reglas: List[Regla]

@dataclass
class Programa:
    version: str
    elementos: List[Elemento] = field(default_factory=list)
    marcos: List[str] = field(default_factory=list)
    categorias: List[Categoria] = field(default_factory=list)
    hechos: List[str] = field(default_factory=list)
    fractales: List[Fractal] = field(default_factory=list)


# ═════════════════════════════════════════════════════════════════════
# Parser
# ═════════════════════════════════════════════════════════════════════

class Parser:

    def __init__(self, tokens: List[Token], archivo: str = "<input>"):
        self.tokens = tokens
        self.pos = 0
        self.archivo = archivo

    # --- utilidades ---

    def _actual(self) -> Token:
        return self.tokens[self.pos]

    def _tipo(self) -> str:
        return self.tokens[self.pos].tipo

    def _avanzar(self) -> Token:
        t = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return t

    def _esperar(self, tipo: str, contexto: str = "") -> Token:
        if self._tipo() != tipo:
            t = self._actual()
            ctx = f" en {contexto}" if contexto else ""
            raise DSLSyntaxError(
                f"esperaba {tipo}{ctx}, encontró {t.tipo} ({t.valor!r})",
                t.linea, t.col, self.archivo)
        return self._avanzar()

    def _es(self, *tipos: str) -> bool:
        return self._tipo() in tipos

    # --- entrada ---

    def parsear(self) -> Programa:
        prog = Programa(version="")
        # DSL_VERSION "..." ;
        self._esperar("DSL_VERSION", "inicio de programa")
        v = self._esperar("STRING", "DSL_VERSION")
        prog.version = v.valor
        self._esperar("SEMI", "DSL_VERSION")

        # declaraciones
        while not self._es("EOF"):
            t = self._tipo()
            if t == "ELEMENTOS":
                self._parsear_elementos(prog)
            elif t == "MARCOS":
                self._parsear_marcos(prog)
            elif t == "CATEGORIA":
                self._parsear_categoria(prog)
            elif t == "HECHO":
                self._parsear_hecho(prog)
            elif t == "FRACTAL":
                self._parsear_fractal(prog)
            else:
                tt = self._actual()
                raise DSLSyntaxError(
                    f"declaración inesperada {tt.tipo} ({tt.valor!r})",
                    tt.linea, tt.col, self.archivo)
        return prog

    # --- vocabulario ---

    def _parsear_elementos(self, prog: Programa) -> None:
        self._esperar("ELEMENTOS")
        self._esperar("LBRACE")
        while not self._es("RBRACE"):
            nombre = self._esperar("IDENT", "elemento").valor
            desc = None
            if self._es("COLON"):
                self._avanzar()
                desc = self._esperar("STRING", "descripción").valor
            self._esperar("SEMI", "elemento")
            prog.elementos.append(Elemento(nombre, desc))
        self._esperar("RBRACE")

    def _parsear_marcos(self, prog: Programa) -> None:
        self._esperar("MARCOS")
        self._esperar("LBRACE")
        while not self._es("RBRACE"):
            nombre = self._esperar("IDENT", "marco").valor
            self._esperar("SEMI", "marco")
            prog.marcos.append(nombre)
        self._esperar("RBRACE")

    def _parsear_categoria(self, prog: Programa) -> None:
        self._esperar("CATEGORIA")
        nombre = self._esperar("IDENT", "nombre de categoría").valor
        self._esperar("ASSIGN", "categoria_decl")
        self._esperar("elemento", "categoria_decl")
        self._esperar("COLON", "categoria_decl")
        elem = self._esperar("IDENT", "elemento").valor
        self._esperar("SEMI", "categoria_decl")
        self._esperar("universal", "categoria_decl")
        self._esperar("COLON", "categoria_decl")
        if self._es("VERDADERO"):
            self._avanzar(); uni = True
        elif self._es("FALSO"):
            self._avanzar(); uni = False
        else:
            t = self._actual()
            raise DSLSyntaxError(
                f"esperaba VERDADERO o FALSO, encontró {t.tipo}",
                t.linea, t.col, self.archivo)
        self._esperar("SEMI", "categoria_decl")
        prog.categorias.append(Categoria(nombre, elem, uni))

    def _parsear_hecho(self, prog: Programa) -> None:
        self._esperar("HECHO")
        nombre = self._esperar("IDENT", "hecho").valor
        self._esperar("SEMI", "hecho")
        prog.hechos.append(nombre)

    # --- fractal / reglas ---

    def _parsear_fractal(self, prog: Programa) -> None:
        self._esperar("FRACTAL")
        nombre = self._esperar("IDENT", "nombre de fractal").valor
        self._esperar("COLON", "fractal")
        reglas: List[Regla] = []
        # al menos una regla
        reglas.append(self._parsear_regla())
        while self._es("REGLA"):
            reglas.append(self._parsear_regla())
        prog.fractales.append(Fractal(nombre, reglas))

    def _parsear_regla(self) -> Regla:
        self._esperar("REGLA")
        nombre = self._esperar("IDENT", "nombre de regla").valor
        self._esperar("COLON", "regla")
        self._esperar("SI", "regla")
        cond = self._parsear_condicion()
        self._esperar("ENTONCES", "regla")
        acciones: List[Accion] = []
        acciones.append(self._parsear_accion())
        while self._es("GENERAR"):
            acciones.append(self._parsear_accion())
        self._esperar("SEMI", "fin de regla")
        return Regla(nombre, cond, acciones)

    # --- condiciones ---

    def _parsear_condicion(self) -> NodoCond:
        return self._parsear_disyuncion()

    def _parsear_disyuncion(self) -> NodoCond:
        partes = [self._parsear_conjuncion()]
        while self._es("O"):
            self._avanzar()
            partes.append(self._parsear_conjuncion())
        return partes[0] if len(partes) == 1 else Disyuncion(partes)

    def _parsear_conjuncion(self) -> NodoCond:
        partes = [self._parsear_neg_bool()]
        while self._es("Y"):
            self._avanzar()
            partes.append(self._parsear_neg_bool())
        return partes[0] if len(partes) == 1 else Conjuncion(partes)

    def _parsear_neg_bool(self) -> NodoCond:
        if self._es("NO"):
            self._avanzar()
            return NegBool(self._parsear_neg_bool())
        return self._parsear_atomo()

    def _parsear_atomo(self) -> NodoCond:
        t = self._tipo()
        if t == "LBRACK":
            self._avanzar()
            c = self._parsear_condicion()
            self._esperar("RBRACK", "condición agrupada")
            return c
        if t == "IDENT":
            return self._parsear_operand_chain()
        if t in ("NOT", "categoria", "LBRACE", "LPAREN"):
            return self._parsear_set_chain()
        raise DSLSyntaxError(
            f"átomo inesperado {self._actual().tipo}",
            self._actual().linea, self._actual().col, self.archivo)

    def _parsear_operand_chain(self) -> NodoCond:
        ident = self._esperar("IDENT", "operando").valor
        if self._es("EQ", "NEQ", "GE", "LE", "GT", "LT"):
            op = self._avanzar().valor
            der = self._parsear_operand()
            return CmpEscalar(ident, op, der)
        return HechoRef(ident)

    def _parsear_operand(self) -> Any:
        t = self._actual()
        if t.tipo == "IDENT":
            self._avanzar(); return t.valor
        if t.tipo == "STRING":
            self._avanzar(); return t.valor
        if t.tipo == "NUMBER":
            self._avanzar(); return t.valor
        raise DSLSyntaxError(
            f"operando inesperado {t.tipo}", t.linea, t.col, self.archivo)

    def _parsear_set_chain(self) -> NodoCond:
        izq = self._parsear_set_expr()
        if self._es("IN", "SUBSET"):
            op = self._avanzar().valor
            der = self._parsear_set_expr()
            return Relacion(izq, op, der)
        # Error: set_chain exige ∈ o ⊆
        t = self._actual()
        raise DSLSyntaxError(
            f"se esperaba ∈ o ⊆ después de expresión de conjunto, encontró {t.tipo}",
            t.linea, t.col, self.archivo)

    def _parsear_set_expr(self) -> NodoSet:
        return self._parsear_set_union()

    def _parsear_set_union(self) -> NodoSet:
        izq = self._parsear_set_inter()
        while self._es("UNION"):
            self._avanzar()
            der = self._parsear_set_inter()
            izq = Union(izq, der)
        return izq

    def _parsear_set_inter(self) -> NodoSet:
        izq = self._parsear_set_diff()
        while self._es("INTER"):
            self._avanzar()
            der = self._parsear_set_diff()
            izq = Inter(izq, der)
        return izq

    def _parsear_set_diff(self) -> NodoSet:
        izq = self._parsear_set_unary()
        while self._es("DIFF"):
            self._avanzar()
            der = self._parsear_set_unary()
            izq = Diff(izq, der)
        return izq

    def _parsear_set_unary(self) -> NodoSet:
        if self._es("NOT"):
            self._avanzar()
            return Complemento(self._parsear_set_unary())
        return self._parsear_set_primary()

    def _parsear_set_primary(self) -> NodoSet:
        t = self._tipo()
        if t == "categoria":
            self._avanzar()
            self._esperar("LPAREN", "categoria(...)")
            nombre = self._esperar("IDENT", "argumento de categoria").valor
            self._esperar("RPAREN", "categoria(...)")
            return CategoriaRef(nombre)
        if t == "LBRACE":
            self._avanzar()
            items: List[str] = []
            if not self._es("RBRACE"):
                items.append(self._esperar("IDENT", "item").valor)
                while self._es("COMMA"):
                    self._avanzar()
                    items.append(self._esperar("IDENT", "item").valor)
            self._esperar("RBRACE", "set literal")
            return SetLiteral(items)
        if t == "LPAREN":
            self._avanzar()
            s = self._parsear_set_expr()
            self._esperar("RPAREN", "conjunto agrupado")
            return s
        raise DSLSyntaxError(
            f"conjunto inesperado {self._actual().tipo}", self._actual().linea, self._actual().col, self.archivo)

    # --- acciones ---

    def _parsear_accion(self) -> Accion:
        self._esperar("GENERAR", "acción")
        self._esperar("CONSECUENCIA", "acción")
        self._esperar("LPAREN", "acción")
        acc = Accion()
        self._parsear_argumento(acc)
        while self._es("COMMA"):
            self._avanzar()
            self._parsear_argumento(acc)
        self._esperar("RPAREN", "acción")
        return acc

    def _parsear_argumento(self, acc: Accion) -> None:
        t = self._tipo()
        if t == "categoria":
            self._avanzar()
            self._esperar("ASSIGN", "categoria=")
            acc.categoria = self._parsear_set_expr()
            return
        if t == "operacion":
            self._avanzar()
            self._esperar("ASSIGN", "operacion=")
            acc.operacion = self._esperar("IDENT", "operacion").valor
            return
        if t == "movimiento":
            self._avanzar()
            self._esperar("ASSIGN", "movimiento=")
            if self._es("AUMENTA"):
                self._avanzar(); acc.movimiento = "AUMENTA"
            elif self._es("DISMINUYE"):
                self._avanzar(); acc.movimiento = "DISMINUYE"
            else:
                tt = self._actual()
                raise DSLSyntaxError(
                    f"esperaba AUMENTA o DISMINUYE, encontró {tt.tipo}",
                    tt.linea, tt.col, self.archivo)
            return
        if t == "fuente":
            self._avanzar()
            self._esperar("ASSIGN", "fuente=")
            acc.fuente = self._parsear_cita()
            return
        if t == "evidencia":
            self._avanzar()
            self._esperar("ASSIGN", "evidencia=")
            acc.evidencia = self._esperar("IDENT", "evidencia").valor
            return
        tt = self._actual()
        raise DSLSyntaxError(
            f"argumento desconocido {tt.tipo} ({tt.valor!r})",
            tt.linea, tt.col, self.archivo)

    def _parsear_cita(self) -> Cita:
        marco = self._esperar("IDENT", "marco de cita").valor
        self._esperar("COLON", "cita (marco:seccion)")
        seccion = self._parsear_section()
        return Cita(marco, seccion)

    def _parsear_section(self) -> str:
        partes = [self._parsear_section_atom()]
        while self._es("DOT"):
            self._avanzar()
            partes.append(self._parsear_section_atom())
        return ".".join(partes)

    def _parsear_section_atom(self) -> str:
        t = self._actual()
        if t.tipo == "IDENT":
            self._avanzar(); return t.valor
        if t.tipo == "NUMBER":
            # Acepta NUMBER con o sin punto (lexer por maximal munch).
            # El '-' no es válido: gramática digits = digit { digit }.
            if t.valor.startswith("-"):
                raise DSLSyntaxError(
                    f"section_atom: dígitos sin signo, recibió {t.valor!r}",
                    t.linea, t.col, self.archivo)
            self._avanzar(); return t.valor
        raise DSLSyntaxError(
            f"section_atom inesperado {t.tipo}", t.linea, t.col, self.archivo)


# ═════════════════════════════════════════════════════════════════════
# Punto de entrada
# ═════════════════════════════════════════════════════════════════════

def parse(texto: str, archivo: str = "<input>") -> Programa:
    """Tokeniza y parsea un texto en el DSL de MNFC. Devuelve Programa."""
    lexer = Lexer(texto, archivo)
    tokens = lexer.tokenizar()
    parser = Parser(tokens, archivo)
    return parser.parsear()

"""
Baldor contable — operador algebraico elemental.

Fuente · ~/.baldor_algebra_raw.txt (Álgebra de A. Baldor, 287 pp.)
Origen · ~/storage/downloads/ALGEBRA_de_BALDOR.pdf
SHA256 raw · 63fe32a1ece2e183c43a5d040003c1efc6f6745e0afa976c7aed052c77f5fbaf
Fecha · 2026-09-25

Cada función implementa una ley o regla del raw con locus declarado.
No inventa operaciones. No confunde aritmética con álgebra.

Autoridad:
    - NO decide DEBE/HABER (eso es XNOR).
    - NO decide profesionalmente (eso es H2).
    - NO escribe en el motor.

Frontera declarada (D-BALDOR-2):
    Cubre leyes algebraicas elementales extraídas del Álgebra de Baldor
    (referencia bibliográfica: 287 pp., edición única).
    La correspondencia exhaustiva página→función NO ha sido auditada;
    el alcance efectivo es el conjunto de funciones definidas abajo.
    NO cubre: redondeo administrativo, conversión con spread cambiario,
    cálculo de mora legal, operaciones específicas de industria.
"""

from math import isnan, isinf
from typing import List, Tuple


# ═════════════════════════════════════════════════════════════════════
# BLOQUE 1 · REGISTRO · leyes formales del álgebra
# ═════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────
# LEY DE LOS SIGNOS
# Raw L1885-1888:
#   "El producto hallado llevará signo positivo (+) si los signos de
#    ambos factores son iguales; llevará signo negativo (−) si los
#    factores tienen signos distintos. Si uno de los factores es 0
#    el producto será 0."
# ─────────────────────────────────────────────────────────────────────

def ley_de_signos(signo_a: int, signo_b: int) -> int:
    """Producto algebraico de dos signos (+1 o −1). Raw L1885-1888."""
    if signo_a == 0 or signo_b == 0:
        return 0
    return signo_a * signo_b


# ─────────────────────────────────────────────────────────────────────
# LEYES FORMALES DE LA SUMA
# Raw L1676 (conmutativa) · L1678 (asociativa) · L1680 (identidad)
# ─────────────────────────────────────────────────────────────────────

def suma_conmutativa(a, b):
    """Raw L1676: a + b = b + a."""
    return a + b == b + a


def suma_asociativa(a, b, c):
    """Raw L1678: (a + b) + c = a + (b + c)."""
    return (a + b) + c == a + (b + c)


def suma_identidad(a):
    """Raw L1680: a + 0 = a."""
    return a + 0 == a


# ─────────────────────────────────────────────────────────────────────
# LEYES FORMALES DE LA MULTIPLICACIÓN
# Raw L1689 · L1691 · L1693 · L1696 · L1699
# ─────────────────────────────────────────────────────────────────────

def multiplicacion_conmutativa(a, b):
    """Raw L1689: ab = ba."""
    return a * b == b * a


def multiplicacion_asociativa(a, b, c):
    """Raw L1691: (ab)c = a(bc)."""
    return (a * b) * c == a * (b * c)


def multiplicacion_distributiva(a, b, c):
    """Raw L1693: a(b + c) = ab + ac."""
    return a * (b + c) == (a * b) + (a * c)


def multiplicacion_identidad(a):
    """Raw L1696: a · 1 = a."""
    return a * 1 == a


def multiplicacion_inverso(a):
    """Raw L1699: para todo a ≠ 0 existe x tal que a · x = 1."""
    if a == 0:
        raise ValueError("inverso no definido para 0 (Baldor L1699)")
    return 1 / a


# ─────────────────────────────────────────────────────────────────────
# REDUCCIÓN DE TÉRMINOS SEMEJANTES
# Raw L874-997 · tres casos
# ─────────────────────────────────────────────────────────────────────

Termino = Tuple[float, int, str]   # (coeficiente, signo, parte_literal)


def reducir_mismo_signo(terminos: List[Termino]) -> Termino:
    """
    Raw L877-894 · caso 1.
    "Se suman los coeficientes, poniendo delante de esta suma el mismo
     signo que tienen todos, y a continuación se escribe la parte literal."
    """
    if not terminos:
        raise ValueError("lista vacía")
    signo = terminos[0][1]
    parte = terminos[0][2]
    for _, s, p in terminos:
        if s != signo:
            raise ValueError("caso 1 requiere signos iguales")
        if p != parte:
            raise ValueError("caso 1 requiere términos semejantes")
    coef = sum(c for c, _, _ in terminos)
    return (coef, signo, parte)


def reducir_signo_distinto(terminos: List[Termino]) -> Termino:
    """
    Raw L935-960 · caso 2.
    "Se restan los coeficientes, poniendo delante de esta diferencia
     el signo del mayor."
    """
    if len(terminos) != 2:
        raise ValueError("caso 2 requiere exactamente dos términos")
    (c1, s1, p1), (c2, s2, p2) = terminos
    if p1 != p2:
        raise ValueError("caso 2 requiere términos semejantes")
    if s1 == s2:
        raise ValueError("caso 2 requiere signos distintos")
    if c1 == c2:
        return (0, 0, p1)
    if c1 > c2:
        return (c1 - c2, s1, p1)
    return (c2 - c1, s2, p2)


def reducir_terminos_semejantes(terminos: List[Termino]) -> Termino:
    """
    Raw L874-997 · los tres casos.
    Caso 3: reducir positivos, reducir negativos, aplicar caso 2.
    """
    if not terminos:
        raise ValueError("lista vacía")
    parte = terminos[0][2]
    positivos = [t for t in terminos if t[1] > 0]
    negativos = [t for t in terminos if t[1] < 0]
    if not positivos:
        return reducir_mismo_signo(negativos)
    if not negativos:
        return reducir_mismo_signo(positivos)
    coef_pos = sum(c for c, _, _ in positivos)
    coef_neg = sum(c for c, _, _ in negativos)
    return reducir_signo_distinto([(coef_pos, +1, parte), (coef_neg, -1, parte)])


def _validar_finito(x, nombre: str = "valor") -> None:
    """Rechaza NaN e Inf. Los montos contables son finitos."""
    if isinstance(x, float) and (isnan(x) or isinf(x)):
        raise ValueError(nombre + " no finito: " + repr(x))


def sumar_montos(montos: List[float]) -> float:
    """Suma algebraica de montos. Raw L874-997 (reduccion de terminos)."""
    for m in montos:
        _validar_finito(m, "monto")
    return sum(montos)


def verificar_cuadre(total_debe: float, total_haber: float) -> bool:
    """ΣDEBE == ΣHABER. Raw L1676 (conmutatividad) + L874 (reduccion)."""
    _validar_finito(total_debe, "total_debe")
    _validar_finito(total_haber, "total_haber")
    return abs(total_debe - total_haber) < 0.001


def calcular_base_e_iva(monto_con_iva: float, tasa: float) -> tuple:
    """
    Desglosa monto con IVA incluido en (base, iva).
    Raw L1693 (distributiva) + L1699 (inverso).
    """
    base = monto_con_iva / (1.0 + tasa)
    iva = monto_con_iva - base
    return base, iva


# ═════════════════════════════════════════════════════════════════════
# BLOQUE 2 · PROGRESIONES
# ═════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────
# PROGRESIÓN ARITMÉTICA
# Raw L29085: "toda serie en la cual cada término después del primero
#             se obtiene sumándole al término anterior una cantidad
#             constante llamada razón o diferencia."
# Raw L29113: u = a + (n-1)r
# Raw L29260+: S = n(a + u) / 2
# ─────────────────────────────────────────────────────────────────────

def termino_nesimo_ap(a: float, r: float, n: int) -> float:
    """Término n-ésimo de progresión aritmética. Raw L29113: u = a + (n-1)r."""
    return a + (n - 1) * r


def razon_ap(a: float, u: float, n: int) -> float:
    """Razón de progresión aritmética dado a, u, n. Despeje de L29113."""
    if n <= 1:
        raise ValueError("n debe ser > 1")
    return (u - a) / (n - 1)


def suma_ap(a: float, r: float, n: int) -> float:
    """
    Suma de los n primeros términos de progresión aritmética.
    Raw L29260+: S = n(a + u) / 2 donde u es el término n-ésimo.
    """
    u = termino_nesimo_ap(a, r, n)
    return n * (a + u) / 2


def numero_terminos_ap(a: float, u: float, r: float) -> int:
    """Número de términos de PA conociendo a, u, r. Despeje de L29113."""
    if r == 0:
        raise ValueError("razón no puede ser 0")
    return int(round((u - a) / r)) + 1


# ─────────────────────────────────────────────────────────────────────
# PROGRESIÓN GEOMÉTRICA
# Raw L29659: "toda serie en la cual cada término se obtiene multiplicando
#             el anterior por una cantidad constante que es la razón."
# Raw L29700: u = a · r^(n-1)
# Raw L29657 (deducción): S = a(r^n - 1) / (r - 1) cuando r ≠ 1
# Raw L253 (pág.): S_inf = a / (1 - r) cuando |r| < 1
# ─────────────────────────────────────────────────────────────────────

def termino_nesimo_pg(a: float, r: float, n: int) -> float:
    """Término n-ésimo de progresión geométrica. Raw L29700: u = a·r^(n-1)."""
    return a * (r ** (n - 1))


def razon_pg(a: float, u: float, n: int) -> float:
    """Razón de PG dado a, u, n. Despeje de L29700: r = (u/a)^(1/(n-1))."""
    if a == 0:
        raise ValueError("a no puede ser 0")
    if n <= 1:
        raise ValueError("n debe ser > 1")
    return (u / a) ** (1 / (n - 1))


def suma_pg(a: float, r: float, n: int) -> float:
    """
    Suma de los n primeros términos de PG. Raw L29657 (deducción):
    'S(r − 1) = a(r^n − 1). Y de aquí S = a(r^n − 1)/(r − 1).'
    """
    if r == 1:
        return a * n
    return a * (r ** n - 1) / (r - 1)


def suma_pg_infinita(a: float, r: float) -> float:
    """
    Suma de PG infinita. Raw pág. 253: S = a / (1 − r) cuando |r| < 1.
    Ejemplo verificado: a=5, r=2/5 → S=25/3.
    """
    if abs(r) >= 1:
        raise ValueError("suma infinita requiere |r| < 1")
    return a / (1 - r)


def numero_terminos_pg(a: float, u: float, r: float) -> int:
    """
    Número de términos de PG. Raw L258 (pág.):
    'n = (log u − log a) / log r + 1'
    """
    from math import log
    if a <= 0 or u <= 0 or r <= 0 or r == 1:
        raise ValueError("a, u, r deben ser > 0 y r ≠ 1")
    return int(round((log(u) - log(a)) / log(r))) + 1


# ═════════════════════════════════════════════════════════════════════
# BLOQUE 3 · LOGARITMOS
# ═════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────
# DEFINICIÓN
# Raw L30176: "Logaritmo de un número es el exponente a que hay que
#             elevar otro número llamado base para obtener el número dado."
# ─────────────────────────────────────────────────────────────────────

def logaritmo(x: float, base: float = 10) -> float:
    """Logaritmo. Raw L30176."""
    from math import log
    if base <= 0 or base == 1:
        raise ValueError("base debe ser > 0 y ≠ 1")
    if x <= 0:
        raise ValueError("x debe ser > 0")
    return log(x) / log(base)


def antilog(y: float, base: float = 10) -> float:
    """Antilogaritmo: número cuyo log es y. Raw pág. 258."""
    return base ** y


# ─────────────────────────────────────────────────────────────────────
# PROPIEDADES
# Raw L30253: log(A×B) = log A + log B
# Raw L30286 (deducción): log(A/B) = log A − log B
# Raw L30286+ (deducción): log(A^n) = n·log A
# Raw L30286+ (deducción): log(ⁿ√A) = (log A) / n
# ─────────────────────────────────────────────────────────────────────

def log_producto(A: float, B: float, base: float = 10) -> float:
    """Raw L30253: log(A×B) = log A + log B."""
    return logaritmo(A, base) + logaritmo(B, base)


def log_cociente(A: float, B: float, base: float = 10) -> float:
    """Raw L30286 (deducción textual): log(A/B) = log A − log B."""
    return logaritmo(A, base) - logaritmo(B, base)


def log_potencia(A: float, n: float, base: float = 10) -> float:
    """Raw L30286+ (deducción): log(A^n) = n · log A."""
    return n * logaritmo(A, base)


def log_raiz(A: float, n: float, base: float = 10) -> float:
    """Raw L30286+ (deducción): log(ⁿ√A) = (log A) / n."""
    return logaritmo(A, base) / n


# ─────────────────────────────────────────────────────────────────────
# COLOGARITMO
# Raw pág. 257: "Se llama cologaritmo de un número al logaritmo de su
#                inverso. colog x = −log x."
# ─────────────────────────────────────────────────────────────────────

def colog(x: float, base: float = 10) -> float:
    """Raw pág. 257: colog x = −log x."""
    return -logaritmo(x, base)


# ─────────────────────────────────────────────────────────────────────
# CARACTERÍSTICA Y MANTISA
# Raw pág. 257: "La parte entera se llama característica, y la parte
#                decimal, mantisa."
# ─────────────────────────────────────────────────────────────────────

def caracteristica(x: float) -> int:
    """Parte entera del logaritmo. Raw pág. 257."""
    from math import floor
    if x <= 0:
        raise ValueError("x debe ser > 0")
    return int(floor(logaritmo(x)))


def mantisa(x: float) -> float:
    """Parte decimal del logaritmo. Raw pág. 257."""
    from math import floor
    l = logaritmo(x)
    return l - floor(l)


def log_por_factores(factores: List[Tuple[int, int]], base: float = 10) -> float:
    """
    log de un número por descomposición en factores primos.
    Raw pág. 259: ejemplo 108 = 2² × 3³
                  log 108 = 2·log 2 + 3·log 3
    Recibe: [(primo, exponente), ...]
    """
    resultado = 0
    for primo, exp in factores:
        resultado += exp * logaritmo(primo, base)
    return resultado


# ═════════════════════════════════════════════════════════════════════
# BLOQUE 4 · INTERÉS COMPUESTO
# ═════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────
# FÓRMULAS
# Raw L30886: C = c(1+r)^t
# Raw L30896: c = C / (1+r)^t
# Raw L30909: t = (log C − log c) / log(1+r)
# Raw L30920: r = (C/c)^(1/t) − 1
# ─────────────────────────────────────────────────────────────────────

def capital_final(c: float, r: float, t: float) -> float:
    """Capital final a interés compuesto. Raw L30886: C = c(1+r)^t."""
    return c * ((1 + r) ** t)


def capital_inicial(C: float, r: float, t: float) -> float:
    """Capital inicial (valor presente). Raw L30896: c = C / (1+r)^t."""
    return C / ((1 + r) ** t)


def tiempo_ic(C: float, c: float, r: float) -> float:
    """
    Tiempo de capitalización. Raw L30909:
    t = (log C − log c) / log(1+r)
    """
    from math import log
    if c <= 0 or C <= 0 or (1 + r) <= 0 or r <= -1:
        raise ValueError("valores fuera de dominio")
    return (log(C) - log(c)) / log(1 + r)


def tasa_ic(C: float, c: float, t: float) -> float:
    """Tasa implícita. Raw L30920: r = (C/c)^(1/t) − 1."""
    if c <= 0 or t <= 0:
        raise ValueError("c y t deben ser > 0")
    return (C / c) ** (1 / t) - 1


# ═════════════════════════════════════════════════════════════════════
# BLOQUE 5 · PROPORCIONALIDAD
# ═════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────
# Raw L17283: "Si A es proporcional a B, A = kB."
# Raw L17300: "Si A es inversamente proporcional a B, A = k/B."
# Raw L17326: "Si A es proporcional a B y C, A = kBC."
# ─────────────────────────────────────────────────────────────────────

def constante_directa(A: float, B: float) -> float:
    """Constante de proporcionalidad directa. Raw L17283: k = A/B."""
    if B == 0:
        raise ValueError("B no puede ser 0")
    return A / B


def constante_inversa(A: float, B: float) -> float:
    """Constante de proporcionalidad inversa. Raw L17300: k = A·B."""
    return A * B


def proporcional_directa(k: float, B: float) -> float:
    """A = kB. Raw L17283."""
    return k * B


def proporcional_inversa(k: float, B: float) -> float:
    """A = k/B. Raw L17300."""
    if B == 0:
        raise ValueError("B no puede ser 0")
    return k / B


def proporcional_conjunta(k: float, B: float, C: float) -> float:
    """A = kBC. Raw L17326."""
    return k * B * C


def regla_de_tres_directa(a: float, b: float, c: float) -> float:
    """
    Regla de tres simple directa: a/b = c/x → x = b·c/a.
    Raw L17283 (proporcionalidad directa aplicada).
    """
    if a == 0:
        raise ValueError("a no puede ser 0")
    return (b * c) / a


def regla_de_tres_inversa(a: float, b: float, c: float) -> float:
    """
    Regla de tres simple inversa: a·b = c·x → x = a·b/c.
    Raw L17300 (proporcionalidad inversa aplicada).
    """
    if c == 0:
        raise ValueError("c no puede ser 0")
    return (a * b) / c


# ═════════════════════════════════════════════════════════════════════
# BLOQUE 6 · SISTEMAS Y ECUACIONES CUADRÁTICAS
# ═════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────
# SISTEMA 2×2 · raw L19298-19550
# "SISTEMA DE ECUACIONES es la reunión de dos o más ecuaciones con
#  dos o más incógnitas."
# Tres métodos: igualación, sustitución, reducción.
# ─────────────────────────────────────────────────────────────────────

def resolver_2x2(a1: float, b1: float, c1: float,
                a2: float, b2: float, c2: float) -> Tuple[float, float]:
    """
    Resuelve el sistema:
        a1·x + b1·y = c1
        a2·x + b2·y = c2
    Por determinantes. Raw L19298-19550 (métodos de eliminación).
    """
    det = a1 * b2 - a2 * b1
    if det == 0:
        raise ValueError("sistema sin solución única (determinante 0)")
    x = (c1 * b2 - c2 * b1) / det
    y = (a1 * c2 - a2 * c1) / det
    return x, y


# ─────────────────────────────────────────────────────────────────────
# ECUACIÓN CUADRÁTICA
# Raw L27078-27200 (deducción):
#   "La ecuación es ax² + bx + c = 0.
#    ... (x + b/2a)² = b²/4a² − c/a
#    ... x = (−b ± √(b² − 4ac)) / 2a"
# ─────────────────────────────────────────────────────────────────────

def discriminante(a: float, b: float, c: float) -> float:
    """Discriminante: D = b² − 4ac. Raw L27078+."""
    return b * b - 4 * a * c


def resolver_cuadratica(a: float, b: float, c: float) -> Tuple:
    """
    Raíces de ax² + bx + c = 0.
    Raw L27078+ (deducción textual):
    "x = (−b ± √(b² − 4ac)) / 2a"
    Retorna (raíz1, raíz2).
    """
    from math import sqrt
    if a == 0:
        raise ValueError("a no puede ser 0 (no es cuadrática)")
    D = discriminante(a, b, c)
    if D < 0:
        raise ValueError("raíces imaginarias (D < 0)")
    raiz_D = sqrt(D)
    return ((-b + raiz_D) / (2 * a), (-b - raiz_D) / (2 * a))


# ─────────────────────────────────────────────────────────────────────
# RADICALES
# Raw L23560: "EXPRESIÓN RADICAL es toda raíz indicada."
# Raw L23632: "Para extraer una raíz a una potencia se divide el
#             exponente de la potencia por el índice de la raíz."
# ─────────────────────────────────────────────────────────────────────

def raiz_potencia(a: float, m: float, n: float) -> float:
    """
    ⁿ√(a^m) = a^(m/n).
    Raw L23632: "se divide el exponente de la potencia por el índice
    de la raíz."
    """
    if n == 0:
        raise ValueError("índice no puede ser 0")
    return a ** (m / n)


def raiz_enesima(a: float, n: float) -> float:
    """ⁿ√a. Raw L23560 (definición) + L23632 (regla)."""
    if n == 0:
        raise ValueError("índice no puede ser 0")
    return a ** (1 / n)


# ═════════════════════════════════════════════════════════════════════
# BLOQUE 7 · EXPONENCIALES Y UTILIDADES
# ═════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────
# ECUACIONES EXPONENCIALES
# Raw pág. 258: "Ecuaciones exponenciales son ecuaciones en que la
#                incógnita es exponente de una cantidad. Para resolver
#                ecuaciones exponenciales, se aplican logaritmos a los
#                dos miembros."
# ─────────────────────────────────────────────────────────────────────

def resolver_exponencial(b: float, k: float) -> float:
    """
    Resuelve b^x = k. Raw pág. 258: x = log(k) / log(b).
    """
    from math import log
    if b <= 0 or b == 1 or k <= 0:
        raise ValueError("b > 0, b ≠ 1, k > 0")
    return log(k) / log(b)


# ─────────────────────────────────────────────────────────────────────
# COMBINACIÓN DE OPERACIONES POR LOGARITMOS
# Raw pág. 258: "El logaritmo se usa para convertir en suma una resta
#                de logaritmos."
# ─────────────────────────────────────────────────────────────────────

def calcular_por_logaritmos(operaciones: List[Tuple[str, float]],
                            base: float = 10) -> float:
    """
    Calcula expresiones con productos y cocientes por medio de logaritmos.
    Raw pág. 258.
    operaciones: [("mul", 3284), ("mul", 0.09132), ("div", 715.84)]

    Alcance actual: solo operaciones "mul" y "div".
    Potencias y raíces NO están implementadas (deuda declarada).
    """
    suma = 0.0
    for op, valor in operaciones:
        if op == "mul":
            suma += logaritmo(valor, base)
        elif op == "div":
            suma += colog(valor, base)
        else:
            raise ValueError(f"operación no soportada: {op}")
    return antilog(suma, base)


# ─────────────────────────────────────────────────────────────────────
# FRONTERA DECLARADA
# ─────────────────────────────────────────────────────────────────────
#
# Este módulo implementa funciones derivadas del Álgebra de Baldor.
# La cobertura de las 287 pp. NO ha sido auditada (deuda declarada).
# Bloques efectivamente implementados:
#   - leyes formales (bloques 1)
#   - progresiones aritméticas y geométricas (bloque 2)
#   - logaritmos (bloque 3)
#   - interés compuesto (bloque 4)
#   - proporcionalidad (bloque 5)
#   - sistemas y cuadráticas (bloque 6)
#   - exponenciales (bloque 7)
#
# NO cubre:
#   - redondeo administrativo (no está en Baldor)
#   - conversión con spread cambiario (dato externo)
#   - cálculo de mora legal (legislación)
#   - operaciones específicas de industria
#
# Estas operaciones requieren componentes distintos y se declaran
# fuera del alcance de este módulo.

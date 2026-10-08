"""
Capa 2 - Estadistica aplicada.

Fuente: Mendenhall/Beaver/Beaver, Introduccion a la probabilidad y
estadistica, 13a ed. Raw: ~/tmp/estadistica.txt (50729 lineas).

Locus verificado:
    L6777-6820   - Cap. 2 Conceptos clave (descriptivas)
    L16827-16880 - Cap. 6 Conceptos clave (distribuciones)
    L17791-18667 - Cap. 7 (muestreo, error estandar, TLC)
    L22541-22560 - Tabla 8.7 (tamanos muestrales)
    L22731+      - Cap. 8 Conceptos clave (estimacion)

Estado epistemico:
    N1 - Mendenhall caps 2, 6, 7, 8 (locus verificado)
    N2 - reconstruccion por contexto (notacion degradada en OCR)
    N3 - pendiente verificacion contra PDF
    N4 - pendiente aplicacion industrial

Frontera: el modulo no decide contabilidad. Mide series contables.
"""

from math import sqrt, log, exp, erf
from typing import List, Tuple
from collections import Counter


def media(xs: List[float]) -> float:
    """Media aritmetica. Mendenhall L6781-6782 (§2.2)."""
    if not xs:
        raise ValueError("serie vacia")
    return sum(xs) / len(xs)


def mediana(xs: List[float]) -> float:
    """Posicion .5(n+1). Mendenhall L6783 (§2.2)."""
    if not xs:
        raise ValueError("serie vacia")
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def moda(xs: List[float]) -> float:
    """Una de las modas (la primera hallada). Mendenhall L6784 (§2.2).

    Nota: en distribuciones multimodales devuelve la primera segun
    orden de insercion en Counter. Para obtener todas las modas, usar
    modas(). Mendenhall Ejercicio 2.3: "c. 5 y 6".
    """
    if not xs:
        raise ValueError("serie vacia")
    return Counter(xs).most_common(1)[0][0]


def modas(xs: List[float]) -> List[float]:
    """Todas las modas. Mendenhall L4789 (definicion).

    Devuelve la lista de valores con frecuencia maxima. Si la
    distribucion es unimodal, lista de un solo elemento. Si bimodal
    o multimodal, todos los valores empatados en el maximo.

    Verificacion N3-textual: Mendenhall Ejercicio 2.3 (L4865,
    respuesta en L48515): datos [3,5,4,6,10,5,6,9,2,8] -> [5, 6].
    """
    if not xs:
        raise ValueError("serie vacia")
    c = Counter(xs)
    max_f = max(c.values())
    return [v for v, f in c.items() if f == max_f]


def varianza_muestral(xs: List[float]) -> float:
    """s2 = sum((xi-x_bar)^2)/(n-1). Mendenhall L6801-6809 (§2.3).

    N3-textual: Ejemplo 2.5 (L5239) - datos [5,7,1,2,4] -> s^2 = 5.70.
    """
    if len(xs) < 2:
        raise ValueError("n >= 2")
    m = media(xs)
    return sum((x - m) ** 2 for x in xs) / (len(xs) - 1)


def desviacion_muestral(xs: List[float]) -> float:
    """s = sqrt(s2). Mendenhall L6813-6814 (§2.3).

    N3-textual: Ejemplo 2.5 (L5239) - datos [5,7,1,2,4] -> s ~= 2.39.
    """
    return sqrt(varianza_muestral(xs))


def cuartiles(xs: List[float]) -> Tuple[float, float, float]:
    """Q1 .25(n+1), Q2 .5(n+1), Q3 .75(n+1). Mendenhall L6827-6829 (§2.7).

    Interpolacion lineal cuando la posicion no es entera, segun
    Mendenhall L~6210: "Cuando .25(n+1) y .75(n+1) no son enteros,
    los cuartiles se encuentran por interpolacion, usando los valores
    de las dos posiciones adyacentes."

    N3-textual: Ejemplo 2.13 (L~6222) - datos [16,25,4,18,11,13,20,
    8,11,9] -> Q1=8.75, Q3=18.5. Tambien Repertorio A (L~6303):
    [2,5,7,1,1,2,8] -> Q1=1, Q3=7 (posiciones enteras, sin interpolacion).
    """
    if not xs:
        raise ValueError("serie vacia")
    s = sorted(xs)
    n = len(s)

    def pos(p):
        idx = p * (n + 1)
        k = int(idx)
        f = idx - k
        if f == 0:
            return float(s[k - 1])
        if k >= n:
            return float(s[n - 1])
        return s[k - 1] + f * (s[k] - s[k - 1])

    return pos(.25), pos(.50), pos(.75)


def iqr(xs: List[float]) -> float:
    """IQR = Q3 - Q1. Mendenhall L6831 (§2.7)."""
    q1, _, q3 = cuartiles(xs)
    return q3 - q1


def z_score(x: float, xs: List[float]) -> float:
    """z = (x - x_bar)/s. Mendenhall L6824 (§2.6)."""
    return (x - media(xs)) / desviacion_muestral(xs)


def coef_variacion(xs: List[float]) -> float:
    """CV = s/x_bar. Mendenhall §2.3."""
    m = media(xs)
    if m == 0:
        raise ValueError("media cero")
    return desviacion_muestral(xs) / m


def normal_pdf(x: float, mu: float = 0, sigma: float = 1) -> float:
    """f(x) = (1/sigma*sqrt(2pi))*e^(-z^2/2). Mendenhall L16843 (§6.2)."""
    if sigma <= 0:
        raise ValueError("sigma > 0")
    z = (x - mu) / sigma
    return (1 / (sigma * sqrt(2 * 3.141592653589793))) * exp(-z * z / 2)


def normal_cdf(x: float, mu: float = 0, sigma: float = 1) -> float:
    """F(x) = integral_-inf^x f(t)dt. Mendenhall L16851 (§6.3)."""
    if sigma <= 0:
        raise ValueError("sigma > 0")
    z = (x - mu) / sigma
    return 0.5 * (1 + erf(z / sqrt(2)))


def z_critico_95() -> float:
    """z = 1.96. Mendenhall L16872."""
    return 1.96


def z_critico_99() -> float:
    """z = 2.58. Mendenhall L16872."""
    return 2.58


def z_critico_90() -> float:
    """z = 1.645. Mendenhall L16872."""
    return 1.645


def error_estandar_media(sigma: float, n: int) -> float:
    """SE = sigma/sqrt(n). Mendenhall L18107 (§7.5)."""
    if n <= 0:
        raise ValueError("n > 0")
    return sigma / sqrt(n)


def error_estandar_proporcion(p: float, n: int) -> float:
    """SE = sqrt(pq/n). Mendenhall L18667 (§7.6)."""
    if not 0 <= p <= 1 or n <= 0:
        raise ValueError("p in [0,1], n > 0")
    return sqrt(p * (1 - p) / n)


def tamano_muestra_media(z: float, sigma: float, B: float) -> int:
    """n = z^2*sigma^2/B^2. Mendenhall L22545-22548 (Tabla 8.7)."""
    if B <= 0:
        raise ValueError("B > 0")
    return int(round((z * sigma / B) ** 2))


def tamano_muestra_proporcion(z: float, p: float, B: float) -> int:
    """n = z^2*p*q/B^2. Mendenhall L22561-22564 (Tabla 8.7)."""
    if B <= 0:
        raise ValueError("B > 0")
    return int(round(z * z * p * (1 - p) / (B * B)))


def limite_control_media(xs: List[float], k: float = 3.0) -> Tuple[float, float]:
    """LCS/LCI = x_bar +/- k*sigma/sqrt(n). Mendenhall L18107 (§7.7)."""
    m = media(xs)
    s = desviacion_muestral(xs)
    n = len(xs)
    return m + k * s / sqrt(n), m - k * s / sqrt(n)


def margen_error(z: float, sigma: float, n: int) -> float:
    """Z*sigma/sqrt(n). Mendenhall §8.5."""
    return z * error_estandar_media(sigma, n)


def ic_media(xs: List[float], z: float = 1.96) -> Tuple[float, float]:
    """x_bar +/- Z*sigma/sqrt(n). Mendenhall §8.5."""
    m = media(xs)
    s = desviacion_muestral(xs)
    n = len(xs)
    me = z * s / sqrt(n)
    return m - me, m + me


def ic_proporcion(p: float, n: int, z: float = 1.96) -> Tuple[float, float]:
    """p_hat +/- Z*sqrt(pq/n). Mendenhall §8.5."""
    se = error_estandar_proporcion(p, n)
    return p - z * se, p + z * se


def proyeccion_error(error_muestra: float, N: int, n: int) -> float:
    """error_muestra * (N/n). Mendenhall §8.9."""
    if n <= 0:
        raise ValueError("n > 0")
    return error_muestra * (N / n)


def ic_una_cola_sup(xs: List[float], z_alpha: float) -> float:
    """x_bar + Z_alpha*sigma/sqrt(n). Mendenhall §8.8."""
    m = media(xs)
    s = desviacion_muestral(xs)
    return m + z_alpha * s / sqrt(len(xs))


def ic_una_cola_inf(xs: List[float], z_alpha: float) -> float:
    """x_bar - Z_alpha*sigma/sqrt(n). Mendenhall §8.8."""
    m = media(xs)
    s = desviacion_muestral(xs)
    return m - z_alpha * s / sqrt(len(xs))


def es_atipico_z(x: float, xs: List[float], umbral: float = 3.0) -> bool:
    """|z| > 3. Mendenhall L6824 (§2.6)."""
    return abs(z_score(x, xs)) > umbral


def es_atipico_iqr(x: float, xs: List[float], k: float = 1.5) -> bool:
    """Fuera de [Q1-k*IQR, Q3+k*IQR]. Mendenhall L6831 (§2.7)."""
    q1, _, q3 = cuartiles(xs)
    r = q3 - q1
    return x < q1 - k * r or x > q3 + k * r


def z_score_serie(xs: List[float]) -> List[float]:
    """z para toda la serie. Mendenhall L6824 (§2.6)."""
    m = media(xs)
    s = desviacion_muestral(xs)
    return [(x - m) / s for x in xs]


def stock_seguridad(z: float, sigma_d: float, L: float) -> float:
    """SS = Z*sigma_d*sqrt(L). Derivado §6.5+§7.5."""
    return z * sigma_d * sqrt(L)


def pronostico_media_movil(xs: List[float], n: int) -> float:
    """(y_t + ... + y_t-n)/n. Mendenhall cap 12 (derivado)."""
    if n <= 0 or n > len(xs):
        raise ValueError("n fuera de rango")
    return sum(xs[-n:]) / n

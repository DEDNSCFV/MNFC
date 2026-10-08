"""
Capa 3 - Fractalidad escalante en cascada.

Fuentes:
    Mandelbrot 1975 - Les objets fractals
        ~/.mandelbrot_1975_raw.txt
    Mandelbrot 1982 - La geometria fractal de la naturaleza
        ~/.mandelbrot_1982_raw.txt

Locus verificado:
    1975 L11-13   - definicion de autosimilitud
    1975 L461-462 - "el exponente es una dimension fractal"
    1975 L736     - "irregularidad... iguales entre escalas"
    1975 L859     - "exponente de homotecia"
    1982 L121-122 - "escalantes... identico a todas las escalas"
    1982 L738-744 - cascada de escalas
    1982 L747     - "invariancia por cambio de escala y autosemejanza"
    1982 L766-767 - "Diremos que son escalantes"
    1982 L769     - "el adjetivo suaviza el significado"

Nota conceptual:
    Mandelbrot define fractalidad en geometria. El termino compuesto
    "fractal escalante" (1982 L769) suaviza el significado: mantiene
    invariancia por cambio de escala, relaja el requisito de forma
    geometrica. MNFC toma ese principio suavizado y lo desplaza del
    dominio de la geometria al de las operaciones contables.

Estado epistemico:
    N1 - Mandelbrot 1975, 1982 (locus verificado)
    N2 - reconstruccion del exponente escalante por contexto
    N3 - pendiente verificacion contra PDF
    N4 - pendiente aplicacion industrial

Frontera: el modulo no decide contabilidad. Mide estructura cascante
de series contables (saldos, movimientos, consumos).
"""

from math import log
from typing import List, Tuple


def cascada(xs: List[float], niveles: List[int]) -> List[Tuple[int, float]]:
    """
    Aplica la misma operacion (suma y varianza) a la serie agregada
    en cada nivel de escala.

    Locus: Mandelbrot 1982 L738-744 (cascada de escalas de un mapa);
    1982 L121-122 ("identico a todas las escalas").

    Sensibilidad al orden: la agregacion se hace sobre bloques
    CONSECUTIVOS (xs[i:i+k]). El orden de la serie ES la informacion;
    permutarla cambia el resultado. No usar sobre series que no tengan
    orden temporal. Ver tests/test_determinismo.py::TestSensibilidadAlOrden.

    Devuelve: [(nivel, varianza_agregada), ...]
    """
    resultado = []
    for k in niveles:
        if k <= 1 or k > len(xs):
            continue
        agregada = [sum(xs[i:i+k]) for i in range(0, len(xs) - k + 1, k)]
        if len(agregada) < 2:
            continue
        m = sum(agregada) / len(agregada)
        v = sum((x - m) ** 2 for x in agregada) / len(agregada)
        if v > 0:
            resultado.append((k, v))
    return resultado


def exponente_escalante(xs: List[float],
                         niveles: List[int] = None) -> float:
    """
    Pendiente de log(varianza) vs log(escala) sobre la cascada.

    Locus: Mandelbrot 1975 L461-462 ("el exponente es una dimension
    fractal"). Aplicado aqui a la varianza de series contables
    agregadas, no a la longitud de una costa.

    Interpretacion:
        beta ~= 0      - serie sin estructura (ruido blanco)
        beta ~= 1      - ruido con varianza proporcional
        beta ~= 2      - paseo aleatorio acumulado
        1 < beta < 2   - escalante (fractal suavizado)
    """
    if niveles is None:
        niveles = [2, 3, 5, 8, 13, 21]
    puntos = cascada(xs, niveles)
    if len(puntos) < 2:
        raise ValueError("serie demasiado corta para estimar beta")
    n = len(puntos)
    sx = sum(log(k) for k, _ in puntos)
    sy = sum(log(v) for _, v in puntos)
    sxx = sum(log(k) ** 2 for k, _ in puntos)
    sxy = sum(log(k) * log(v) for k, v in puntos)
    denom = n * sxx - sx * sx
    if denom == 0:
        raise ValueError("escala constante: beta indefinido")
    return (n * sxy - sx * sy) / denom


def clasificar_cascada(xs: List[float]) -> str:
    """
    Clasifica una serie contable segun su exponente escalante.

    Locus: Mandelbrot 1982 L766-767 ("Diremos que son escalantes")
    + 1975 L736 ("irregularidad... iguales entre escalas").

    Clasificacion:
        beta ~= 0       - "plana"
        beta ~= 1       - "lineal"
        beta ~= 2       - "acumulada"
        intermedio      - "escalante"
    """
    beta = exponente_escalante(xs)
    if abs(beta) < 0.3:
        return "plana"
    if abs(beta - 1) < 0.3:
        return "lineal"
    if abs(beta - 2) < 0.3:
        return "acumulada"
    return "escalante"


def reporte_cascada(xs: List[float]) -> dict:
    """
    Reporte del comportamiento cascante de una serie contable.
    Devuelve exponente, clasificacion, y niveles usados.
    """
    return {
        "exponente_escalante": exponente_escalante(xs),
        "clasificacion": clasificar_cascada(xs),
        "niveles": [k for k, _ in cascada(xs, [2, 3, 5, 8, 13, 21])],
    }

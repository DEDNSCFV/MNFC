"""
Capa 0 - XNOR contable - el BIT.

Fuente unica del axioma cargo/abono. Tres representaciones equivalentes:
    1. Booleana : tabla cerrada de 4 combinaciones
    2. GF(2)    : 1 xor n xor m  (1 -> DEBE, 0 -> HABER)
    3. Signos   : chi(n)*chi(m)  (+1 -> DEBE, -1 -> HABER)

Locus:
    Anexo I, invariante 2.5 (documento interno SCFV).
    Boole 1847 - The Mathematical Analysis of Logic
        ~/.boole_laws_raw.txt
        L2022   - xx = x        (ley de idempotencia)
        L2089   - simbolos electivos son distributivos y conmutativos
        L6066   - regla de casos mutuamente exclusivos (XOR ancestral)

Estado epistemico:
    N1 - Anexo I + Boole 1847
    N3 - verificacion matematica exhaustiva (4/4 combinaciones)
    N4 - aplicada (dominio contable)
"""

NATURALEZAS_VALIDAS = ("DEUDORA", "ACREEDORA")
MOVIMIENTOS_VALIDOS = ("AUMENTA", "DISMINUYE")

_TABLA = {
    ("DEUDORA",   "AUMENTA"):   "DEBE",
    ("DEUDORA",   "DISMINUYE"): "HABER",
    ("ACREEDORA", "AUMENTA"):   "HABER",
    ("ACREEDORA", "DISMINUYE"): "DEBE",
}

_N_A_GF2 = {"DEUDORA": 1, "ACREEDORA": 0}
_M_A_GF2 = {"AUMENTA": 1, "DISMINUYE": 0}

_N_A_SIGNO = {"DEUDORA": +1, "ACREEDORA": -1}
_M_A_SIGNO = {"AUMENTA": +1, "DISMINUYE": -1}


def _validar(naturaleza: str, movimiento: str) -> None:
    if naturaleza not in NATURALEZAS_VALIDAS:
        raise ValueError(
            f"XNOR invalido para naturaleza='{naturaleza}', "
            f"movimiento='{movimiento}'"
        )
    if movimiento not in MOVIMIENTOS_VALIDOS:
        raise ValueError(
            f"XNOR invalido para naturaleza='{naturaleza}', "
            f"movimiento='{movimiento}'"
        )


def ubicacion_booleana(naturaleza: str, movimiento: str) -> str:
    """Cara 1 - tabla cerrada de 4 combinaciones. Boole 1847 L2022."""
    _validar(naturaleza, movimiento)
    return _TABLA[(naturaleza, movimiento)]


def ubicacion_gf2(naturaleza: str, movimiento: str) -> str:
    """Cara 2 - suma modulo 2. DEBE = 1 xor n xor m."""
    _validar(naturaleza, movimiento)
    bit = 1 ^ _N_A_GF2[naturaleza] ^ _M_A_GF2[movimiento]
    return "DEBE" if bit == 1 else "HABER"


def ubicacion_signos(naturaleza: str, movimiento: str) -> str:
    """Cara 3 - producto de caracteres. Boole 1847 L2089."""
    _validar(naturaleza, movimiento)
    producto = _N_A_SIGNO[naturaleza] * _M_A_SIGNO[movimiento]
    return "DEBE" if producto == +1 else "HABER"


calcular_ubicacion = ubicacion_booleana

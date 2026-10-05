"""
MNFC - Motor Nucleo Fractal Contable.

Materializacion del nucleo del Programa de Investigacion SCFV.

Seis capas fractales:
    Capa 0 - xnor.py        -> el BIT          (una linea)
    Capa 1 - baldor.py      -> la OPERACION    (un asiento)
    Capa 2 - estadistica.py -> la DISTRIBUCION (un periodo)
    Capa 3 - fractal.py     -> la AUTOSIMILITUD (el libro completo)
    Capa 4 - mnfc.py        -> la COMPOSICION  (el proceso)
    Capa 5 - __init__.py    -> la UNIDAD       (la fachada)
    Capa 6 - ledger.py      -> la INMUTABILIDAD (el tiempo)

Uso:
    from mnfc import procesar_asiento, Ledger

Licencia: AGPL-3.0-or-later OR Commercial. Ver LICENSE y COMMERCIAL.md.
"""

# Capa 0 - invariante
from .xnor import (
    calcular_ubicacion, ubicacion_booleana, ubicacion_gf2,
    ubicacion_signos, NATURALEZAS_VALIDAS, MOVIMIENTOS_VALIDOS,
)

# Capa 1 - aritmetica contable
from .baldor import (
    ley_de_signos, reducir_terminos_semejantes, sumar_montos,
    verificar_cuadre, calcular_base_e_iva, capital_final,
    capital_inicial, tiempo_ic, tasa_ic, regla_de_tres_directa,
    regla_de_tres_inversa, logaritmo, resolver_exponencial,
)

# Capa 2 - estadistica aplicada
from .estadistica import (
    media, mediana, moda, varianza_muestral, desviacion_muestral,
    cuartiles, iqr, z_score, coef_variacion,
    normal_pdf, normal_cdf, z_critico_90, z_critico_95, z_critico_99,
    error_estandar_media, error_estandar_proporcion,
    tamano_muestra_media, tamano_muestra_proporcion,
    limite_control_media, margen_error, ic_media, ic_proporcion,
    proyeccion_error, ic_una_cola_sup, ic_una_cola_inf,
    es_atipico_z, es_atipico_iqr, z_score_serie,
    stock_seguridad, pronostico_media_movil,
)

# Capa 3 - fractalidad escalante
from .fractal import (
    cascada, exponente_escalante, clasificar_cascada, reporte_cascada,
)

# Capa 4 - composicion
from .mnfc import Asiento, procesar_asiento

# Capa 6 - ledger inmutable
from .ledger import Ledger, GENESIS

__version__ = "0.1.0"

__all__ = [
    # Capa 0
    "calcular_ubicacion", "ubicacion_booleana", "ubicacion_gf2",
    "ubicacion_signos", "NATURALEZAS_VALIDAS", "MOVIMIENTOS_VALIDOS",
    # Capa 1
    "ley_de_signos", "reducir_terminos_semejantes", "sumar_montos",
    "verificar_cuadre", "calcular_base_e_iva", "capital_final",
    "capital_inicial", "tiempo_ic", "tasa_ic",
    "regla_de_tres_directa", "regla_de_tres_inversa",
    "logaritmo", "resolver_exponencial",
    # Capa 2
    "media", "mediana", "moda", "varianza_muestral", "desviacion_muestral",
    "cuartiles", "iqr", "z_score", "coef_variacion",
    "normal_pdf", "normal_cdf", "z_critico_90", "z_critico_95", "z_critico_99",
    "error_estandar_media", "error_estandar_proporcion",
    "tamano_muestra_media", "tamano_muestra_proporcion",
    "limite_control_media", "margen_error", "ic_media", "ic_proporcion",
    "proyeccion_error", "ic_una_cola_sup", "ic_una_cola_inf",
    "es_atipico_z", "es_atipico_iqr", "z_score_serie",
    "stock_seguridad", "pronostico_media_movil",
    # Capa 3
    "cascada", "exponente_escalante", "clasificar_cascada", "reporte_cascada",
    # Capa 4
    "Asiento", "procesar_asiento",
    # Capa 6
    "Ledger", "GENESIS",
    # Metadata
    "__version__",
]

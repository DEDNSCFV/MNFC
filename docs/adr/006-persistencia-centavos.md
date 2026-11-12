# ADR-006 — Persistencia de centavos en dataclasses

Estado: Aceptado (2026-11-12)
Bloquea: 2.4b, 2.3, 2.5, 2.6

## Contexto
El intento 2.4b convirtió LineaAsiento.monto de field a @property.
El serializador usa dataclasses.fields(), que solo ve fields declarados.
Al convertir monto en @property, desapareció del payload JSON.
Resultado: la persistencia dejó de guardar montos, sin que los tests
lo detectaran (verifican estructura, no contenido).

## Decisión: opción C

monto_cent: int como field real (serializable),
monto: @property derivada,
__init__ custom para aceptar monto= o monto_cent=.

Ejemplo:

    @dataclass(init=False)
    class LineaAsiento:
        cuenta: str
        ubicacion: str
        monto_cent: int
        naturaleza: str | None = None
        movimiento: str | None = None

        def __init__(self, cuenta, ubicacion, monto=None, monto_cent=None, ...):
            # acepta monto= (pesos) o monto_cent= (int)
            ...

        @property
        def monto(self) -> float:
            return self.monto_cent / 100.0

## Consecuencias

- serializar() incluye monto_cent en payload (int)
- Constructor sigue aceptando monto= para compat
- monto sigue disponible como @property
- Cambio de payload: {"monto": 100.5} -> {"monto_cent": 10050}
- Persistencia necesita migración de datos (ver 2.6)

## Tests afectados

test_decimal_en_partida_falla_sin_escritura
test_segundo_asiento_no_serializable_no_escribe_el_primero

Usaban Decimal("100") como monto no serializable. Con ADR-006, Decimal
se convierte a monto_cent. Los tests reescritos usan naturaleza=complex(1,2)
para preservar la intención (tipo no serializable en campo no monetario).

## Alternativas descartadas

A: monto_cent como field + romper constructor -> demasiado disruptive
B: ampliar serializar() para @property -> contrato del serializer muy amplio

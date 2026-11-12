"""Tests de sub-fase 2.1: propiedades derivadas monto_cent coinciden con float."""
import random
from decimal import Decimal
from mnfc import Asiento as AsientoCapa4, procesar_asiento
from mnfc.extensiones.modelos import (
    Asiento as AsientoCapa7, LineaAsiento, PartidaAutorizada,
)


class TestCapa4:
    def test_propiedades_derivadas_basicas(self):
        a = procesar_asiento([
            {"naturaleza": "DEUDORA", "movimiento": "AUMENTA", "monto": 100.50},
            {"naturaleza": "ACREEDORA", "movimiento": "AUMENTA", "monto": 100.50},
        ])
        assert a.total_debe_cent == 10050
        assert a.total_haber_cent == 10050
        assert a.cuadrado_cent is True

    def test_1000_casos_aleatorios_capa4(self):
        for _ in range(1000):
            m = round(random.uniform(0, 10000), 2)
            a = procesar_asiento([
                {"naturaleza": "DEUDORA", "movimiento": "AUMENTA", "monto": m},
                {"naturaleza": "ACREEDORA", "movimiento": "AUMENTA", "monto": m},
            ])
            esperado = int(Decimal(str(m)) * 100)
            assert a.total_debe_cent == esperado, f"deriva en {m}"


class TestCapa7:
    def test_partida_autorizada_derivada(self):
        p = PartidaAutorizada(
            cuenta_codigo="A", cuenta_version="v1", monto=100.50,
            ubicacion="DEBE", movimiento="AUMENTA",
        )
        assert p.monto_cent == 10050

    def test_linea_asiento_derivada(self):
        l = LineaAsiento(cuenta="A", ubicacion="DEBE", monto=99.99)
        assert l.monto_cent == 9999

    def test_asiento_derivado(self):
        a = AsientoCapa7(
            total_debe=1000.00, total_haber=1000.00,
            lineas=[LineaAsiento(cuenta="A", ubicacion="DEBE", monto=1000.00)],
        )
        assert a.total_debe_cent == 100000
        assert a.total_haber_cent == 100000
        assert a.cuadrado_cent is True

    def test_1000_casos_aleatorios_capa7(self):
        for _ in range(1000):
            m = round(random.uniform(0, 10000), 2)
            p = PartidaAutorizada(
                cuenta_codigo="A", cuenta_version="v1", monto=m,
                ubicacion="DEBE", movimiento="AUMENTA",
            )
            assert p.monto_cent == int(Decimal(str(m)) * 100), f"deriva en {m}"

from django.test import SimpleTestCase
from decimal import Decimal
from datetime import date

from liquidacion.lsd.registro05 import (
    DatosRegistro05,
    GeneradorRegistro05,
)


class TestGeneradorRegistro05(SimpleTestCase):
    def datos_registro(self, **kwargs):
        datos = {
            "cuil_trabajador": "33693450239",
            "categoria_profesional": "000001",
            "puesto_desempeniado": "0001",
            "fecha_ingreso": date(2020, 1, 15),
            "fecha_egreso": date(2020, 12, 31),
            "remuneracion": Decimal("100000.00"),
            "cuit_empleador": "33693450239",
        }

        datos.update(kwargs)
        return DatosRegistro05(**datos)

    def test_generar(self):
        casos = [
            (
                "original",
                {},
                "05336934502390000010001202001152020123100000001000000033693450239",
            ),
            (
                "otra_categoria",
                {
                    "categoria_profesional": "56",
                },
                "05336934502390000560001202001152020123100000001000000033693450239",
            ),
            (
                "otro_puesto",
                {
                    "puesto_desempeniado": "76",
                },
                "05336934502390000010076202001152020123100000001000000033693450239",
            ),
            (
                "fecha_ingreso_y_egreso",
                {
                    "fecha_ingreso": date(1994, 7, 1),
                    "fecha_egreso": date(2005, 11, 30),
                },
                "05336934502390000010001199407012005113000000001000000033693450239",
            ),
            (
                "ingreso_y_egreso_mismo_dia",
                {
                    "fecha_ingreso": date(2026, 9, 26),
                    "fecha_egreso": date(2026, 9, 26),
                },
                "05336934502390000010001202609262026092600000001000000033693450239",
            ),
            (
                "remuneracion_entera",
                {
                    "remuneracion": Decimal("1234567890123.00"),
                },
                "05336934502390000010001202001152020123112345678901230033693450239",
            ),
            (
                "remuneracion_con_decimales",
                {
                    "remuneracion": Decimal("123456789012.34"),
                },
                "05336934502390000010001202001152020123101234567890123433693450239",
            ),
            (
                "remuneracion_cero",
                {
                    "remuneracion": Decimal("0.00"),
                },
                "05336934502390000010001202001152020123100000000000000033693450239",
            ),
        ]

        for nombre, cambios, esperado in casos:
            with self.subTest(nombre):
                datos = self.datos_registro(**cambios)
                registro = GeneradorRegistro05(datos).generar()

                self.assertEqual(registro, esperado)

    def test_datos_invalidos(self):
        casos = [
            (
                "fechas_invalidas",
                {
                    "fecha_ingreso": date(2026, 9, 26),
                    "fecha_egreso": date(2025, 9, 26),
                },
                ValueError,
            ),
            (
                "categoria_invalida",
                {
                    "categoria_profesional": "5487354",
                },
                ValueError,
            ),
            (
                "puesto_invalido",
                {
                    "puesto_desempeniado": "76213",
                },
                ValueError,
            ),
            (
                "remuneracion_tope",
                {
                    "remuneracion": Decimal("12345678901234.00"),
                },
                ValueError,
            ),
            (
                "remuneracion_negativa",
                {
                    "remuneracion": Decimal("-10.00"),
                },
                ValueError,
            ),
            (
                "fecha_ingreso_no_es_fecha",
                {
                    "fecha_ingreso": "2026-09-26",
                },
                ValueError,
            ),
            (
                "remuneracion_no_finita",
                {
                    "remuneracion": Decimal("NaN"),
                },
                ValueError,
            ),
            (
                "categoria_no_es_texto",
                {
                    "categoria_profesional": 12,
                },
                ValueError,
            ),
        ]

        for nombre, cambios, esperado in casos:
            with self.subTest(nombre):
                datos = self.datos_registro(**cambios)

                with self.assertRaises(esperado):
                    GeneradorRegistro05(datos).generar()

    def test_fecha_identificador_y_redondeo_fuera_de_rango_se_validan(self):
        casos = (
            {"fecha_ingreso": "2026-09-26"},
            {"cuit_empleador": "20123456789"},
            {"remuneracion": Decimal("9999999999999.999")},
        )

        for cambios in casos:
            with self.subTest(cambios=cambios):
                with self.assertRaises(ValueError):
                    GeneradorRegistro05(self.datos_registro(**cambios)).generar()

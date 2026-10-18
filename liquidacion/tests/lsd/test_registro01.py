from django.test import SimpleTestCase
from datetime import date
from liquidacion.lsd.registro01 import DatosRegistro01, GeneradorRegistro01
from liquidacion.choices import TipoEnvio, TipoLiquidacion


class TestGeneradorRegistro01(SimpleTestCase):
    def datos_registro(self, **kwargs):
        datos = {
            "cuit_empleador": "33693450239",
            "tipo_envio": TipoEnvio.SJ,
            "periodo_liquidacion": date(2026, 9, 1),
            "tipo_liquidacion": TipoLiquidacion.M,
            "numero_liquidacion": 123,
            "cantidad_trabajadores": 37,
        }
        datos.update(kwargs)
        return DatosRegistro01(**datos)

    def test_generar(self):
        casos = [
            (
                "mensual",
                {},
                "0133693450239SJ202609M0012330000037",
            ),
            (
                "quincenal",
                {
                    "tipo_liquidacion": TipoLiquidacion.Q,
                },
                "0133693450239SJ202609Q0012330000037",
            ),
            (
                "solo informa",
                {
                    "tipo_envio": TipoEnvio.RE,
                    "tipo_liquidacion": None,
                    "numero_liquidacion": None,
                },
                "0133693450239RE202609 0000030000037",
            ),
            (
                "un trabajador",
                {
                    "cantidad_trabajadores": 1,
                },
                "0133693450239SJ202609M0012330000001",
            ),
            (
                "máxima cantidad de trabajadores",
                {
                    "cantidad_trabajadores": 999999,
                },
                "0133693450239SJ202609M0012330999999",
            ),
        ]

        for nombre, cambios, esperado in casos:
            with self.subTest(nombre=nombre):
                datos = self.datos_registro(**cambios)
                registro = GeneradorRegistro01(datos).generar()

                self.assertEqual(registro, esperado)

    def test_tipo_liquidacion_error(self):
        cambios = {
            "tipo_envio": TipoEnvio.RE,
            "tipo_liquidacion": TipoLiquidacion.M,
        }

        datos = self.datos_registro(**cambios)

        self.assertRaises(Exception, lambda: GeneradorRegistro01(datos).generar())

    def test_numero_liquidacion_error(self):
        cambios = {
            "tipo_envio": TipoEnvio.RE,
            "numero_liquidacion": 123,
        }

        datos = self.datos_registro(**cambios)

        self.assertRaises(Exception, lambda: GeneradorRegistro01(datos).generar())

    def test_datos_con_tipos_o_rangos_invalidos_producen_value_error(self):
        casos = (
            {"periodo_liquidacion": "2026-09-01"},
            {"cantidad_trabajadores": "37"},
            {"cantidad_trabajadores": True},
            {"numero_liquidacion": 100000},
            {"cuit_empleador": "20123456789"},
        )

        for cambios in casos:
            with self.subTest(cambios=cambios):
                with self.assertRaises(ValueError):
                    GeneradorRegistro01(self.datos_registro(**cambios)).generar()

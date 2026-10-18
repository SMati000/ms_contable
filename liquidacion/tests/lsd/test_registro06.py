from django.test import SimpleTestCase

from liquidacion.lsd.registro06 import (
    DatosRegistro06,
    GeneradorRegistro06,
)


class TestGeneradorRegistro06(SimpleTestCase):
    def datos_registro(self, **kwargs):
        datos = {
            "cuil_trabajador": "33693450239",
            "observaciones": "Observación de prueba",
        }

        datos.update(kwargs)
        return DatosRegistro06(**datos)

    def test_generar(self):
        casos = [
            (
                "observacion_vacia",
                {"observaciones": ""},
                "0633693450239" + "0" * 80,
            ),
            (
                "original",
                {},
                "063369345023900000000000000000000000000000000000000000000000000000000000Observación de prueba",
            ),
            (
                "observacion_exactamente_80_caracteres",
                {
                    "observaciones": "A" * 80,
                },
                "0633693450239AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            ),
            (
                "observacion_con_caracteres_especiales",
                {
                    "observaciones": "Licencia: art. 208 LCT - período 01/09/2026",
                },
                "06336934502390000000000000000000000000000000000000Licencia: art. 208 LCT - período 01/09/2026",
            ),
        ]

        for nombre, cambios, esperado in casos:
            with self.subTest(nombre):
                datos = self.datos_registro(**cambios)
                registro = GeneradorRegistro06(datos).generar()

                self.assertEqual(registro, esperado)

    def test_observaciones_mayores_a_80_caracteres_o_fuera_de_ansi_son_invalidas(self):
        casos = [
            (
                "observacion_tope",
                {
                    "observaciones": "A" * 82,
                }
            ),
            (
                "caracter_no_ansi",
                {"observaciones": "Observación 😀"},
            ),
        ]

        for nombre, cambios in casos:
            with self.subTest(nombre):
                datos = self.datos_registro(**cambios)

                with self.assertRaises(ValueError):
                    GeneradorRegistro06(datos).generar()

    def test_observaciones_y_cuil_invalidos_producen_value_error(self):
        casos = (
            {"observaciones": None},
            {"observaciones": 123},
            {"cuil_trabajador": "20123456789"},
        )

        for cambios in casos:
            with self.subTest(cambios=cambios):
                with self.assertRaises(ValueError):
                    GeneradorRegistro06(self.datos_registro(**cambios)).generar()


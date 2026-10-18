from decimal import Decimal

from django.test import SimpleTestCase

from liquidacion.lsd.registro04 import GeneradorRegistro04
from liquidacion.tests.lsd.fixtures_registro04 import datos_registro04


class ValidacionesRegistro04Tests(SimpleTestCase):
    def test_rechaza_importes_y_cantidades_con_tipos_invalidos(self):
        casos = (
            {"remuneracion_bruta": Decimal("NaN")},
            {"remuneracion_bruta": object()},
            {"dia_inicio_situacion_revista_1": 1.5},
            {"cantidad_hijos": "3"},
            {"codigo_situacion_revista_1": "1", "dia_inicio_situacion_revista_1": None},
            {"porcentaje_aporte_adicional_seg_social": Decimal("100.01")},
        )

        for cambios in casos:
            with self.subTest(cambios=cambios):
                with self.assertRaises(ValueError):
                    GeneradorRegistro04(datos_registro04(**cambios)).generar()

    def test_dia_inicio_debe_ser_mayor_a_cero(self):
        datos = datos_registro04(dia_inicio_situacion_revista_1=0)

        with self.assertRaises(ValueError):
            GeneradorRegistro04(datos).generar()

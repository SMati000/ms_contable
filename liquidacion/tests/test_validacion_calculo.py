from decimal import Decimal

from django.test import SimpleTestCase

from liquidacion.exceptions import ExpresionBaseInvalida
from liquidacion.models import DetalleLiquidacion
from liquidacion.services.validacion_calculo import validar_rango_decimal_calculado


class ValidacionCalculoTests(SimpleTestCase):
    def test_permite_precision_fraccionaria_superior_a_la_almacenada(self):
        validar_rango_decimal_calculado(
            DetalleLiquidacion,
            "importe",
            Decimal("12.123456789"),
        )

    def test_rechaza_resultados_no_finitos(self):
        with self.assertRaises(ExpresionBaseInvalida):
            validar_rango_decimal_calculado(
                DetalleLiquidacion,
                "importe",
                Decimal("NaN"),
            )

    def test_rechaza_resultados_fuera_del_rango_del_campo(self):
        with self.assertRaises(ExpresionBaseInvalida):
            validar_rango_decimal_calculado(
                DetalleLiquidacion,
                "importe",
                Decimal("1000000000000000"),
            )

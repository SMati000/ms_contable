from decimal import Decimal, ROUND_HALF_UP, localcontext

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from core.forms import DecimalInputField
from core.utils import format_decimal_2, format_decimal_trimmed


class FormatDecimalTrimmedTests(SimpleTestCase):
    def test_conserva_hasta_cinco_decimales_significativos(self):
        self.assertEqual(
            format_decimal_trimmed(Decimal("1.23456"), max_places=5),
            "1.23456",
        )

    def test_mantiene_dos_decimales_como_minimo(self):
        self.assertEqual(
            format_decimal_trimmed(Decimal("1.2"), max_places=5),
            "1.20",
        )

    def test_quita_ceros_finales_sin_perder_minimo(self):
        self.assertEqual(
            format_decimal_trimmed(Decimal("1.23000"), max_places=5),
            "1.23",
        )

    def test_formato_monetario_conserva_redondeo_half_even_explicito(self):
        with localcontext() as contexto:
            contexto.rounding = ROUND_HALF_UP
            self.assertEqual(format_decimal_2(Decimal("1.005")), "1.00")


class DecimalInputFieldTests(SimpleTestCase):
    def setUp(self):
        self.field = DecimalInputField(max_digits=12, decimal_places=5)

    def test_acepta_cinco_decimales(self):
        self.assertEqual(self.field.clean("1.23456"), Decimal("1.23456"))

    def test_rechaza_mas_de_cinco_decimales(self):
        with self.assertRaises(ValidationError):
            self.field.clean("1.234567")

    def test_widget_declara_escala_y_teclado_decimal(self):
        self.assertEqual(
            self.field.widget.attrs["data-decimal-places"],
            "5",
        )
        self.assertEqual(self.field.widget.attrs["inputmode"], "decimal")

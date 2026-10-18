from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from core.utils import format_cuil
from core.validators import (
    es_cuil_valido,
    es_dni_valido,
    validar_cbu,
    validar_cuil,
    validar_dni,
)


class ValidadoresIdentificadoresTests(SimpleTestCase):
    def test_dni_rechaza_digitos_unicode(self):
        self.assertFalse(es_dni_valido("1234567²"))
        with self.assertRaises(ValidationError):
            validar_dni("1234567²")

    def test_cuil_rechaza_digitos_unicode_sin_excepcion_de_conversion(self):
        cuil = "2012345678²"

        self.assertFalse(es_cuil_valido(cuil))
        with self.assertRaises(ValidationError):
            validar_cuil(cuil)

    def test_cbu_rechaza_digitos_unicode_sin_excepcion_de_conversion(self):
        cbu = "0000000²" + "0" * 14

        with self.assertRaises(ValidationError):
            validar_cbu(cbu)

    def test_formateador_cuil_rechaza_digitos_unicode(self):
        with self.assertRaises(ValueError):
            format_cuil("20-12345678-²")

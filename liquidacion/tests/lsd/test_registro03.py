from django.test import SimpleTestCase
from decimal import Decimal
from datetime import date
from liquidacion.lsd.registro03 import DatosRegistro03, GeneradorRegistro03
from liquidacion.choices import DebitoCredito, UnidadesLsd


class TestGeneradorRegistro03(SimpleTestCase):
    def datos_registro(self, **kwargs):
        datos = {
            "cuil_trabajador": "33693450239",
            "codigo_arca_concepto": "800810",
            "cantidad": Decimal("132.24"),
            "unidades": UnidadesLsd.MONEDA,
            "importe": Decimal("520.37"),
            "debito_credito": DebitoCredito.DEBITO,
            "periodo_ajuste_retractivo": date(2026, 9, 30)
        }
        datos.update(kwargs)
        return DatosRegistro03(**datos)

    def test_generar(self):
        casos = [
            (
                "original",
                {},
                "0333693450239800810    13224$000000000052037D202609",
            ),
            (
                "caso2",
                {
                    "cantidad": None,
                    "unidades": None,
                    "importe": Decimal("1.375"),
                },
                "0333693450239800810    00000 000000000000138D202609",
            ),
            (
                "caso2",
                {
                    "importe": Decimal("1234567891234.21"),
                    "debito_credito": DebitoCredito.CREDITO,
                    "periodo_ajuste_retractivo": None,
                },
                "0333693450239800810    13224$123456789123421C      ",
            ),
        ]

        for nombre, cambios, esperado in casos:
            with self.subTest(nombre):
                datos = self.datos_registro(**cambios)
                registro = GeneradorRegistro03(datos).generar()

                self.assertEqual(registro, esperado)

    def test_cantidades_invalidas(self):
        cambios = {
            "cantidad": Decimal("-1"),
        }

        datos = self.datos_registro(**cambios)

        self.assertRaises(Exception, lambda: GeneradorRegistro03(datos).generar())

        cambios = {
            "cantidad": Decimal("1000"),
        }

        datos = self.datos_registro(**cambios)

        self.assertRaises(Exception, lambda: GeneradorRegistro03(datos).generar())

    def test_cantidad_es_obligatoria_para_codigos_arca_especificos(self):
        codigos = ("123000", "130000", "130001", "130002", "130003", "150000")

        for codigo in codigos:
            with self.subTest(codigo=codigo):
                datos = self.datos_registro(
                    codigo_arca_concepto=codigo,
                    cantidad=None,
                )

                with self.assertRaisesRegex(ValueError, "cantidad es obligatoria"):
                    GeneradorRegistro03(datos).generar()

    def test_cantidad_cero_es_un_valor_presente(self):
        datos = self.datos_registro(
            codigo_arca_concepto="123000",
            cantidad=Decimal("0"),
        )

        self.assertEqual(len(GeneradorRegistro03(datos).generar()), 51)

    def test_importes_invalidas(self):
        cambios = {
            "importe": Decimal("-1.35"),
        }

        datos = self.datos_registro(**cambios)

        self.assertRaises(Exception, lambda: GeneradorRegistro03(datos).generar())

    def test_cuil_y_decimales_fuera_de_rango_se_validan_antes_de_formatear(self):
        casos = (
            {"cuil_trabajador": "20123456789"},
            {"codigo_arca_concepto": 800810},
            {"importe": Decimal("9999999999999.999")},
            {"importe": Decimal("NaN")},
        )

        for cambios in casos:
            with self.subTest(cambios=cambios):
                with self.assertRaises(ValueError):
                    GeneradorRegistro03(self.datos_registro(**cambios)).generar()

        cambios = {
            "importe": Decimal("12345678912345.12"),
        }

        datos = self.datos_registro(**cambios)

        self.assertRaises(Exception, lambda: GeneradorRegistro03(datos).generar())

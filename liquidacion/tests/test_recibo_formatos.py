from decimal import Decimal
from decimal import ROUND_HALF_UP, localcontext

from django.test import SimpleTestCase

from concepto.choices import Unidad
from liquidacion.forms.f_liquidacion_empleado import (
    LiquidacionEmpleadoForm,
    ResultadoBaseImponibleInlineForm,
)
from liquidacion.lsd.formatting import FormateadorRegistroLsd
from liquidacion.services.s_recibo import ReciboSueldoService
from liquidacion.services.s_recibo_pdf import convertir_svg_a_pdf
from liquidacion.services.s_recibo_svg import ReciboSueldoSvgRenderer


class FormatoUnidadReciboTests(SimpleTestCase):
    def test_muestra_precision_significativa_hasta_cinco_decimales(self):
        self.assertEqual(
            ReciboSueldoService._formatear_unidad(
                Unidad.CANTIDAD,
                Decimal("1.23456"),
            ),
            "1.23456",
        )

    def test_mantiene_dos_decimales_minimos_y_sufijo_porcentual(self):
        self.assertEqual(
            ReciboSueldoService._formatear_unidad(
                Unidad.PORCENTAJE,
                Decimal("1.2"),
            ),
            "1.20 %",
        )

    def test_redondeo_de_pantalla_no_depende_del_contexto_decimal_global(self):
        with localcontext() as contexto:
            contexto.rounding = ROUND_HALF_UP
            self.assertEqual(
                ReciboSueldoService._formatear_unidad(
                    Unidad.CANTIDAD,
                    Decimal("1.234565"),
                ),
                "1.23456",
            )


class FormatoImporteEditableTests(SimpleTestCase):
    def test_acepta_y_muestra_hasta_cinco_decimales(self):
        campo = ResultadoBaseImponibleInlineForm().fields["importe"]

        self.assertEqual(campo.decimal_places, 5)
        self.assertEqual(campo.clean("1.23456"), Decimal("1.23456"))
        self.assertEqual(
            campo.prepare_value(Decimal("1.23456")),
            "1.23456",
        )
        self.assertEqual(
            campo.prepare_value(Decimal("1.2")),
            "1.20",
        )

    def test_importes_auxiliares_admiten_y_formatean_cinco_decimales(self):
        campo = LiquidacionEmpleadoForm().fields[
            "aporte_adicional_obra_social"
        ]

        self.assertEqual(campo.decimal_places, 5)
        self.assertEqual(campo.clean("1500.25999"), Decimal("1500.25999"))
        self.assertEqual(
            campo.prepare_value(Decimal("1500.25999")),
            "1500.25999",
        )


class FormatoImporteSalidaTests(SimpleTestCase):
    def test_recibo_presenta_dos_decimales(self):
        self.assertEqual(
            ReciboSueldoSvgRenderer._dinero(Decimal("1.23999")),
            "1.24",
        )

    def test_lsd_redondea_a_dos_decimales(self):
        self.assertEqual(
            FormateadorRegistroLsd.numeros_con_decimales_formateados(
                Decimal("1.23999"),
                long_entero=13,
                long_decimal=2,
            ),
            "000000000000124",
        )

    def test_lsd_redondea_a_centavos_como_la_planilla_oficial(self):
        self.assertEqual(
            FormateadorRegistroLsd.numeros_con_decimales_formateados(
                Decimal("1.235"),
                long_entero=13,
                long_decimal=2,
            ),
            "000000000000124",
        )

    def test_neto_en_letras_usa_el_mismo_redondeo_que_el_importe_del_recibo(self):
        self.assertEqual(
            ReciboSueldoService.neto_en_letras(Decimal("1.005")),
            "uno",
        )


class ReciboSvgPdfTests(SimpleTestCase):
    def test_muestra_importes_a_dos_decimales_y_genera_pdf(self):
        composicion = {
            clave: {
                "total": "1.23999",
                "empleador": "0.61999",
                "trabajador": "0.62000",
            }
            for clave in (
                "sindical",
                "seguridad_social",
                "obra_social",
                "inssjp",
                "art",
                "scvo",
            )
        }
        datos = {
            "tipo": "original",
            "empresa": {
                "nombre": "Empresa de prueba",
                "domicilio": "Dirección",
                "cuit": "20123456786",
            },
            "mes": 1,
            "anio": 2025,
            "empleado": {
                "apellido_nombre": "Persona de prueba",
                "legajo": "1",
                "sueldo_bruto": "1.23999",
                "antiguedad": "1 AÑOS",
                "fecha_ingreso": "01/01/2024",
                "categoria": "Categoría",
                "cuil": "20123456786",
                "banco": "Banco",
                "periodo_pago": "31/01/2025",
            },
            "contribuciones": [],
            "remunerativos": [{
                "concepto": "Sueldo",
                "unidad": "1.23456",
                "base": "1.23999",
                "monto": "1.23999",
            }],
            "no_remunerativos": [],
            "descuentos": [],
            "costo_total_empleador": "1.23999",
            "subtotal_contribuciones": "1.23999",
            "sueldo_bruto": "1.23999",
            "total_remunerativo": "1.23999",
            "total_no_remunerativo": "0",
            "total_descuentos": "0",
            "sueldo_neto": "1.23999",
            "neto_en_letras": "uno con 24/100",
            "observaciones": "-",
            "detalle": composicion,
            "grafico_torta_svg": None,
        }

        svg = ReciboSueldoSvgRenderer(datos).render()
        pdf = convertir_svg_a_pdf(svg)

        self.assertIn("$ 1.24", svg)
        self.assertIn("1.23456", svg)
        self.assertTrue(pdf.startswith(b"%PDF-"))

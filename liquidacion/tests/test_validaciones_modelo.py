from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase

from concepto.choices import Categoria, Tipo, Unidad
from concepto.models import Concepto, VersionConcepto
from concepto.rules import validar_tipo_categoria
from concepto.validation import validar_unidades
from concepto.validators import validar_no_remuneracion
from core.validators import validar_cbu
from empleado.rules import validar_dni_cuil
from empresa.choices import TipoEmpleador
from empresa.models import Empresa
from liquidacion.models import (
    DetalleLiquidacion,
    Liquidacion,
    LiquidacionEmpleado,
    TramoSituacionRevista,
)
from liquidacion.choices import TipoEnvio, TipoLiquidacion
from liquidacion.forms.f_liquidacion import LiquidacionForm
from liquidacion.validators.v_detalles import validar_debito_credito
from liquidacion.exceptions import ExpresionBaseInvalida
from liquidacion.services.s_expresiones import LiquidacionEmpleadoService
from plantilla_liquidacion.models import (
    DetallePlantillaLiquidacion,
    PlantillaLiquidacion,
)
from plantilla_liquidacion.forms import DetallePlantillaLiquidacionForm


class ValidacionesModeloTests(SimpleTestCase):
    def test_validadores_de_campos_requeridos_ignoran_valores_ausentes(self):
        validar_no_remuneracion(None)
        validar_tipo_categoria(None, None)
        validar_dni_cuil(None, None)

    def test_dni_debe_coincidir_con_el_segmento_del_cuil(self):
        validar_dni_cuil("12345678", "20123456789")
        validar_dni_cuil("1234567", "20012345679")

        with self.assertRaises(ValidationError):
            validar_dni_cuil("345678", "20123456789")

    def test_cbu_corto_devuelve_error_de_validacion(self):
        with self.assertRaises(ValidationError):
            validar_cbu("123")

    def test_unidades_porcentuales_deben_estar_entre_cero_y_cien(self):
        validar_unidades(Unidad.PORCENTAJE, Decimal("100"))

        with self.assertRaises(ValidationError):
            validar_unidades(Unidad.PORCENTAJE, Decimal("100.01"))

    def test_conceptos_arca_requieren_debito_o_credito(self):
        validar_debito_credito("123456", "D")

        with self.assertRaises(ValidationError):
            validar_debito_credito("123456", "")

        validar_debito_credito("", "")

    def test_clean_de_modelos_incompletos_no_accede_a_relaciones_ausentes(self):
        DetalleLiquidacion().clean()
        DetallePlantillaLiquidacion().clean()
        LiquidacionEmpleado().clean()
        TramoSituacionRevista().clean()


class DetallePlantillaValidacionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.empresa = Empresa.objects.create(
            cuit="20123456786",
            nombre="Empresa de prueba",
            tipo_empleador=TipoEmpleador.ADMINISTRACION_PUBLICA,
            domicilio="",
        )
        cls.plantilla = PlantillaLiquidacion.objects.create(
            empresa=cls.empresa,
            denominacion="Plantilla de prueba",
        )

    def crear_concepto(self, *, codigo_arca=""):
        concepto = Concepto.objects.create(empresa=self.empresa)
        VersionConcepto.objects.create(
            concepto=concepto,
            denominacion="Porcentaje de prueba",
            codigo_arca=codigo_arca,
            categoria=Categoria.TRABAJADOR,
            tipo=Tipo.DESCUENTO,
            unidad=Unidad.PORCENTAJE,
        )
        return concepto

    def crear_detalle(self, *, concepto, unidades=Decimal("50"), debito_credito=None):
        return DetallePlantillaLiquidacion(
            plantilla=self.plantilla,
            concepto=concepto,
            unidades=unidades,
            formula_base="1",
            debito_credito=debito_credito,
        )

    def test_porcentaje_fuera_de_rango_es_rechazado_por_el_modelo(self):
        concepto = self.crear_concepto()
        detalle = self.crear_detalle(
            concepto=concepto,
            unidades=Decimal("100.01"),
        )

        with self.assertRaises(ValidationError) as error:
            detalle.full_clean()

        self.assertIn("unidades", error.exception.message_dict)

    def test_codigo_arca_requiere_debito_o_credito_en_el_modelo(self):
        concepto = self.crear_concepto(codigo_arca="ABC123")
        detalle = self.crear_detalle(concepto=concepto)

        with self.assertRaises(ValidationError) as error:
            detalle.full_clean()

        self.assertIn("debito_credito", error.exception.message_dict)

    def test_formula_rechaza_sintaxis_y_operaciones_no_soportadas(self):
        concepto = self.crear_concepto()
        casos = (
            "1 /",
            "__import__('os')",
            "1 // 2",
        )

        for formula in casos:
            with self.subTest(formula=formula):
                detalle = self.crear_detalle(concepto=concepto)
                detalle.formula_base = formula

                with self.assertRaises(ValidationError) as error:
                    detalle.full_clean()

                self.assertIn("formula_base", error.exception.message_dict)

    def test_plantilla_rechaza_formula_fuera_del_lenguaje_soportado(self):
        concepto = self.crear_concepto()
        detalle = self.crear_detalle(concepto=concepto)
        detalle.formula_base = "1 // 2"

        with self.assertRaises(ValidationError) as error:
            detalle.full_clean()

        self.assertIn("formula_base", error.exception.message_dict)

    def test_save_rechaza_unidades_invalidas_y_datos_arca_incompletos(self):
        concepto_porcentual = self.crear_concepto()
        detalle_porcentual = self.crear_detalle(
            concepto=concepto_porcentual,
            unidades=Decimal("100.01"),
        )
        concepto_arca = self.crear_concepto(codigo_arca="ABC123")
        detalle_arca = self.crear_detalle(concepto=concepto_arca)

        for detalle in (detalle_porcentual, detalle_arca):
            with self.subTest(detalle=detalle):
                with self.assertRaises(ValidationError):
                    detalle.save()

    def test_formulario_muestra_un_concepto_eliminado_sin_error(self):
        concepto = self.crear_concepto(codigo_arca="ABC123")
        Concepto.todos.filter(pk=concepto.pk).update(eliminado=True)
        detalle = self.crear_detalle(concepto=concepto)
        detalle.pk = 999

        formulario = DetallePlantillaLiquidacionForm(instance=detalle)

        self.assertTrue(formulario.fields["debito_credito"].required)
        self.assertIn("identificador:", str(detalle))

    def test_save_de_liquidacion_incompleta_devuelve_error_de_validacion(self):
        with self.assertRaises(ValidationError):
            Liquidacion().save()

    def test_liquidacion_sj_exige_tipo_tambien_en_guardado_directo(self):
        liquidacion = Liquidacion(
            empresa=self.empresa,
            periodo=date(2025, 3, 1),
            fecha_pago=date(2025, 3, 31),
            tipo_envio=TipoEnvio.SJ,
            tipo_liquidacion="",
        )

        with self.assertRaises(ValidationError) as error:
            liquidacion.save()

        self.assertIn("tipo_liquidacion", error.exception.message_dict)

    def test_transiciones_y_bloqueo_de_liquidacion_cerrada(self):
        liquidacion = Liquidacion.objects.create(
            empresa=self.empresa,
            periodo=date(2025, 3, 1),
            fecha_pago=date(2025, 3, 31),
            tipo_envio=TipoEnvio.SJ,
            tipo_liquidacion=TipoLiquidacion.M,
        )

        with self.assertRaises(ValidationError):
            liquidacion.rectificar()

        liquidacion.cerrar()
        liquidacion.refresh_from_db()
        self.assertEqual(liquidacion.estado, Liquidacion.Estado.CERRADA)

        liquidacion.fecha_pago = date(2025, 4, 10)
        with self.assertRaises(ValidationError):
            liquidacion.save()

        liquidacion.refresh_from_db()
        self.assertEqual(liquidacion.fecha_pago, date(2025, 3, 31))

        liquidacion.rectificar()
        liquidacion.refresh_from_db()
        self.assertEqual(liquidacion.estado, Liquidacion.Estado.EN_RECTIFICACION)
        self.assertTrue(liquidacion.editable())

    def test_liquidacion_no_permite_cambiar_empresa_tras_el_alta(self):
        liquidacion = Liquidacion.objects.create(
            empresa=self.empresa,
            periodo=date(2025, 3, 1),
            fecha_pago=date(2025, 3, 31),
            tipo_envio=TipoEnvio.SJ,
            tipo_liquidacion=TipoLiquidacion.M,
        )
        otra_empresa = Empresa.objects.create(
            cuit="33693450239",
            nombre="Otra empresa",
            tipo_empleador=TipoEmpleador.ADMINISTRACION_PUBLICA,
            domicilio="",
        )
        liquidacion.empresa = otra_empresa

        with self.assertRaises(ValueError):
            liquidacion.save()

        liquidacion.refresh_from_db()
        self.assertEqual(liquidacion.empresa_id, self.empresa.pk)

    def test_formulario_de_liquidacion_usa_la_restriccion_unica_del_modelo(self):
        Liquidacion.objects.create(
            empresa=self.empresa,
            periodo=date(2025, 3, 1),
            fecha_pago=date(2025, 3, 31),
            tipo_envio=TipoEnvio.SJ,
            tipo_liquidacion=TipoLiquidacion.M,
        )
        form = LiquidacionForm(data={
            "empresa": self.empresa.pk,
            "periodo": "2025-03-01",
            "numero": 1,
            "fecha_pago": "2025-03-31",
            "estado": Liquidacion.Estado.BORRADOR,
            "tipo_envio": TipoEnvio.SJ,
            "tipo_liquidacion": TipoLiquidacion.M,
        })

        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_formulario_y_modelo_rechazan_tipo_vacio_para_envio_sj(self):
        form = LiquidacionForm(data={
            "empresa": self.empresa.pk,
            "periodo": "2025-03-01",
            "numero": 1,
            "fecha_pago": "2025-03-31",
            "estado": Liquidacion.Estado.BORRADOR,
            "tipo_envio": TipoEnvio.SJ,
            "tipo_liquidacion": "",
        })

        self.assertFalse(form.is_valid())
        self.assertIn("tipo_liquidacion", form.errors)

    def test_modelo_admite_todos_los_tipos_de_liquidacion_sj_definidos(self):
        for tipo_liquidacion in TipoLiquidacion.values:
            with self.subTest(tipo_liquidacion=tipo_liquidacion):
                liquidacion = Liquidacion.objects.create(
                    empresa=self.empresa,
                    periodo=date(2025, 3, 1),
                    fecha_pago=date(2025, 3, 31),
                    tipo_envio=TipoEnvio.SJ,
                    tipo_liquidacion=tipo_liquidacion,
                )

                self.assertEqual(liquidacion.tipo_liquidacion, tipo_liquidacion)

    def test_error_aritmetico_de_formula_se_expone_como_error_de_dominio(self):
        servicio = LiquidacionEmpleadoService(None)

        with self.assertRaises(ExpresionBaseInvalida):
            servicio.evaluar_formula("1 / 0")

    def test_formula_conserva_la_precision_original_de_literales_decimales(self):
        servicio = LiquidacionEmpleadoService(None)

        self.assertEqual(
            servicio.evaluar_formula("0.123456789012345678901"),
            Decimal("0.123456789012345678901"),
        )

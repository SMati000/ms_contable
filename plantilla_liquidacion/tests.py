from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from concepto.choices import Categoria, Tipo, Unidad
from concepto.models import Concepto, VersionConcepto
from empresa.choices import TipoEmpleador
from empresa.models import Empresa
from liquidacion.choices import DebitoCredito, UnidadesLsd
from plantilla_liquidacion.models import (
    DetallePlantillaLiquidacion,
    PlantillaLiquidacion,
)


class DuplicarPlantillaAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_superuser(
            username="admin_plantillas",
            email="admin@example.com",
            password="test-password",
        )
        cls.empresa = Empresa.objects.create(
            cuit="20123456786",
            nombre="Empresa de prueba",
            tipo_empleador=TipoEmpleador.ADMINISTRACION_PUBLICA,
        )
        cls.plantilla = PlantillaLiquidacion.objects.create(
            empresa=cls.empresa,
            denominacion="Plantilla original",
        )

    def crear_concepto(self, unidad=Unidad.CANTIDAD):
        concepto = Concepto.objects.create(empresa=self.empresa)
        VersionConcepto.objects.create(
            concepto=concepto,
            denominacion="Concepto de prueba",
            categoria=Categoria.TRABAJADOR,
            tipo=Tipo.REMUNERATIVO,
            unidad=unidad,
        )
        return concepto

    def duplicar_url(self):
        return reverse(
            "admin:plantillaliquidacion_duplicar",
            args=[self.plantilla.pk],
        )

    def test_duplica_plantilla_y_conserva_datos_de_cada_detalle(self):
        concepto = self.crear_concepto()
        DetallePlantillaLiquidacion.objects.create(
            plantilla=self.plantilla,
            concepto=concepto,
            unidades=Decimal("1.23456"),
            formula_base="5 + 2",
            cantidad=Decimal("2.30"),
            unidades_lsd=UnidadesLsd.H,
            debito_credito=DebitoCredito.CREDITO,
            periodo_ajuste_retroactivo=date(2025, 2, 1),
        )
        self.client.force_login(self.usuario)

        respuesta = self.client.get(self.duplicar_url())

        self.assertEqual(respuesta.status_code, 302)
        copia = PlantillaLiquidacion.objects.get(
            empresa=self.empresa,
            denominacion="Plantilla original (copia)",
        )
        detalle = copia.detalles.get()
        self.assertEqual(detalle.concepto, concepto)
        self.assertEqual(detalle.unidades, Decimal("1.23456"))
        self.assertEqual(detalle.formula_base, "5 + 2")
        self.assertEqual(detalle.cantidad, Decimal("2.30"))
        self.assertEqual(detalle.unidades_lsd, UnidadesLsd.H)
        self.assertEqual(detalle.debito_credito, DebitoCredito.CREDITO)
        self.assertEqual(
            detalle.periodo_ajuste_retroactivo,
            date(2025, 2, 1),
        )

    def test_no_crea_copia_si_un_detalle_no_valida(self):
        concepto = self.crear_concepto(unidad=Unidad.PORCENTAJE)
        DetallePlantillaLiquidacion.objects.bulk_create([
            DetallePlantillaLiquidacion(
                plantilla=self.plantilla,
                concepto=concepto,
                unidades=Decimal("100.01"),
                formula_base="1",
            ),
        ])
        self.client.force_login(self.usuario)

        respuesta = self.client.get(self.duplicar_url())

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(PlantillaLiquidacion.objects.count(), 1)

    def test_alta_desde_admin_crea_plantilla(self):
        self.client.force_login(self.usuario)
        inline = admin.site._registry[PlantillaLiquidacion].inlines[0](
            PlantillaLiquidacion,
            admin.site,
        )
        request = RequestFactory().get("/admin/")
        request.user = self.usuario
        prefijo = inline.get_formset(
            request,
            obj=None,
        ).get_default_prefix()

        respuesta = self.client.post(
            reverse("admin:plantilla_liquidacion_plantillaliquidacion_add"),
            {
                "empresa": self.empresa.pk,
                "denominacion": "Plantilla desde admin",
                f"{prefijo}-TOTAL_FORMS": "0",
                f"{prefijo}-INITIAL_FORMS": "0",
            },
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(
            PlantillaLiquidacion.objects.filter(
                empresa=self.empresa,
                denominacion="Plantilla desde admin",
            ).exists()
        )

    def test_agregar_todos_incluye_validos_y_omite_conceptos_invalidos(self):
        concepto_valido = self.crear_concepto()
        concepto_sin_version = Concepto.objects.create(empresa=self.empresa)
        admin_plantillas = admin.site._registry[PlantillaLiquidacion]
        request = RequestFactory().post(
            "/admin/plantilla_liquidacion/plantillaliquidacion/1/change/",
            {"_agregar_todos": "1"},
        )
        request.user = self.usuario
        mensaje = Mock()

        with patch.object(admin_plantillas, "message_user", mensaje):
            respuesta = admin_plantillas.response_change(request, self.plantilla)

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(
            list(
                self.plantilla.detalles.values_list("concepto_id", flat=True)
            ),
            [concepto_valido.pk],
        )
        mensaje.assert_called_once()
        self.assertIn("Se agregaron 1 conceptos", mensaje.call_args.args[1])
        self.assertIn("Se omitieron 1", mensaje.call_args.args[1])

    def test_editar_plantilla_muestra_conceptos_sin_version(self):
        concepto = Concepto.objects.create(empresa=self.empresa)
        self.client.force_login(self.usuario)

        respuesta = self.client.get(
            reverse(
                "admin:plantilla_liquidacion_plantillaliquidacion_change",
                args=[self.plantilla.pk],
            )
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, f"Concepto {concepto.pk}")

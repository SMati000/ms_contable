from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from liquidacion.admin.a_liquidacion import LiquidacionAdmin
from liquidacion.admin.a_liquidacion_empleado import LiquidacionEmpleadoAdmin
from liquidacion.models import LiquidacionEmpleado
from liquidacion.models.m_liquidacion import Liquidacion
from plantilla_liquidacion.models import PlantillaLiquidacion


class LiquidacionAdminExportTests(SimpleTestCase):
    def test_descarga_txt_usa_codificacion_ansi_y_cierra_tras_generar(self):
        liquidacion = SimpleNamespace(
            id=7,
            pk=7,
            empresa=SimpleNamespace(nombre="Compañía Ñ"),
            periodo=date(2026, 9, 1),
            numero=2,
            cerrar=Mock(),
        )
        model_admin = LiquidacionAdmin(Liquidacion, admin.site)
        model_admin.get_object = Mock(return_value=liquidacion)
        request = RequestFactory().post("/admin/liquidacion/liquidacion/7/txt/")

        with patch(
            "liquidacion.admin.a_liquidacion.LsdTxtArcaService"
        ) as servicio:
            servicio.return_value.generar.return_value = "Línea ñ\r\n"
            response = model_admin.generar_txt_view(request, "7")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "Línea ñ\r\n".encode("cp1252"))
        self.assertEqual(
            response["Content-Type"],
            "text/plain; charset=windows-1252",
        )
        self.assertIn("liquidacion_compania_n_09_2026_2.txt", response["Content-Disposition"])
        liquidacion.cerrar.assert_called_once_with()


class LiquidacionEmpleadoAdminChangeFormTests(SimpleTestCase):
    def test_contexto_incluye_urls_de_recibos(self):
        empleado_liquidado = Mock()
        empleado_liquidado.pk = 17
        empleado_liquidado.liquidacion.editable.return_value = True
        model_admin = LiquidacionEmpleadoAdmin(LiquidacionEmpleado, admin.site)
        model_admin.get_object = Mock(return_value=empleado_liquidado)
        request = RequestFactory().get("/admin/liquidaciones-por-empleado/17/editar/")
        plantillas = Mock()
        plantillas.order_by.return_value = plantillas

        with (
            patch.object(
                PlantillaLiquidacion.objects,
                "filter",
                return_value=plantillas,
            ),
            patch(
                "django.contrib.admin.options.ModelAdmin.changeform_view",
                return_value=HttpResponse("ok"),
            ) as changeform_view,
        ):
            response = model_admin.changeform_view(request, "17")

        self.assertEqual(response.status_code, 200)
        contexto = changeform_view.call_args.args[3]
        self.assertEqual(
            contexto["recibo_original_url"],
            "/admin/liquidaciones-por-empleado/17/recibo/?tipo=original",
        )
        self.assertEqual(
            contexto["recibo_duplicado_url"],
            "/admin/liquidaciones-por-empleado/17/recibo/?tipo=duplicado",
        )


class LiquidacionEmpleadoAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_superuser(
            username="admin_liquidacion",
            email="admin-liquidacion@example.com",
            password="test-password",
        )

    def test_rutas_de_registro_inexistente_responden_404(self):
        self.client.force_login(self.usuario)

        edicion = self.client.get(
            reverse(
                "admin:liquidacion_liquidacionempleado_change",
                args=[999999],
            )
        )
        recibo = self.client.get(
            reverse("admin:liquidacionempleado_recibo", args=[999999])
        )

        self.assertEqual(edicion.status_code, 404)
        self.assertEqual(recibo.status_code, 404)

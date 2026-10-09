from django.contrib import admin, messages
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.urls import path
from django.template.loader import render_to_string
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from base_imponible.models import ResultadoBaseImponible
from plantilla_liquidacion.models import PlantillaLiquidacion
from plantilla_liquidacion.services import PlantillaLiquidacionService
from .a_detalles_liquidacion import DetalleLiquidacionInline
from ..models import TramoSituacionRevista, Liquidacion
from ..models.m_liquidacion_empleado import LiquidacionEmpleado
from ..models.m_detalles_liquidacion import DetalleLiquidacion
from ..forms.f_liquidacion_empleado import (
    LiquidacionEmpleadoForm,
    ResultadoBaseImponibleInlineForm,
    TramoSituacionRevistaInlineForm
)
from ..services.s_expresiones import LiquidacionEmpleadoService
from ..services.s_recibo import ReciboSueldoService
from ..services.s_recibo_pdf import convertir_svg_a_pdf
from ..services.s_recibo_svg import ReciboSueldoSvgRenderer


class TramoSituacionRevistaInline(admin.TabularInline):
    model = TramoSituacionRevista
    form = TramoSituacionRevistaInlineForm

    extra = 0
    max_num = 3
    can_delete = True
    show_change_link = True

    fields = (
        "situacion_revista",
        "codigo_situacion",
        "dia_inicio",
    )

    readonly_fields = ("situacion_revista",)

    ordering = ("dia_inicio",)

    def has_change_permission(self, request, obj=None):
        if obj and not obj.liquidacion.editable():
            return False

        return super().has_change_permission(request, obj)

    @admin.display(description="Situación de Revista")
    def situacion_revista(self, obj):
        return "Situación de Revista"


class ResultadoBaseImponibleInline(admin.TabularInline):
    model = ResultadoBaseImponible
    form = ResultadoBaseImponibleInlineForm

    extra = 0
    max_num = 0
    can_delete = False

    def get_fields(self, request, obj=None):
        if obj and obj.liquidacion.editable():
            return (
                "base_imponible_display",
                "descripcion_display",
                "importe",  # usa el form y solo permite editar las detracciones
            )

        return (
            "base_imponible_display",
            "descripcion_display",
            "importe_display",  # no usa el form xq has_change_permission=False
        )

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.liquidacion.editable():
            return (
                "base_imponible_display",
                "descripcion_display",
            )

        return (
            "base_imponible_display",
            "descripcion_display",
            "importe_display",
        )

    def has_change_permission(self, request, obj=None):
        if obj and not obj.liquidacion.editable():
            return False

        return super().has_change_permission(request, obj)

    @admin.display(description="Base imponible")
    def base_imponible_display(self, obj):
        return obj.base_imponible

    @admin.display(description="Descripción")
    def descripcion_display(self, obj):
        return obj.base_imponible.descripcion


@admin.register(LiquidacionEmpleado)
class LiquidacionEmpleadoAdmin(admin.ModelAdmin):
    inlines = [
        TramoSituacionRevistaInline,
        ResultadoBaseImponibleInline,
        DetalleLiquidacionInline,
    ]
    form = LiquidacionEmpleadoForm

    fieldsets = (
        (None, {
            "fields": (
                "liquidacion",
                "empleado_display",
                "liq_previa"
            ),
        }),
        ("Datos Adicionales", {
            "classes": ("columnas-custom-2",),
            "fields": (
                ("fecha_rubrica", "cantidad_dias_proporcionar_tope", "unidad_tiempo_trabajado", "tiempo_trabajado"),
                ("codigo_situacion", "codigo_condicion", "codigo_actividad", "codigo_modalidad_contratacion",),
                ("codigo_siniestrado", "codigo_localidad", "porcentaje_aporte_adicional_ss", "porcentaje_contrib_tarea_diferencial",),
                ("remuneracion_maternidad_anses", "cantidad_adherentes_obra_social", "aporte_adicional_obra_social", "contrib_adicional_obra_social"),
                ("base_calc_diferencial_aportes_obra_social_fsr", "base_calc_diferencial_contrib_obra_social_fsr",
                 "base_calc_diferencial_ley_riesgos_trabajo", "base_calc_diferencial_aportes_seg_social",),
                ("base_calc_diferencial_contrib_seg_social",)
            )
        }),
        ("Observaciones", {
            "classes": ("columnas-custom-2",),
            "fields": (
                ("observaciones_recibo", "observaciones_lsd",),
            ),
        }),
        ("Totales de liquidación", {
            "classes": ("columnas-custom-2",),
            "fields": (
                ("remunerativo_display", "bruto_display", "descuentos_display",),
                ("no_remunerativo_display", "neto_display", "contribuciones_display",),
                ("costo_laboral_display",),
            ),
        }),
    )

    readonly_fields = (
        "liquidacion",
        "empleado_display",
        "liq_previa",
        "remunerativo_display",
        "no_remunerativo_display",
        "bruto_display",
        "descuentos_display",
        "neto_display",
        "contribuciones_display",
        "costo_laboral_display",
    )

    def has_change_permission(self, request, obj=None):
        if obj and not obj.liquidacion.editable():
            return False

        return super().has_change_permission(request, obj)

    @admin.display(description="Empleado")
    def empleado_display(self, obj):
        if not obj.empleado_id:
            return "-"

        url = reverse(
            "admin:empleado_empleado_change",
            args=[obj.empleado_id],
        )

        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.version_empleado,
        )

    @admin.display(description="Liquidación previa")
    def liq_previa(self, obj):
        if not obj or not obj.pk:
            return "-"

        if not obj.liquidacion.editable():
            return "-"

        url = reverse(
            "admin:liquidacionempleado_previa",
            args=[obj.pk],
        )

        return format_html(
            '<button type="button" '
            'class="button" '
            'id="btn-liq-previa" '
            'data-url="{}">'
            'Completar con liquidación previa'
            '</button>',
            url,
        )

    change_form_template = "admin/liquidacion/change_form.html"

    # Ocultar LiquidacionEmpleado de las vistas globales
    def has_module_permission(self, request):
        return False

    class Media:
        js = ("liquidacion/admin/detalle_liquidacion_empleado.js",)

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None, ):
        extra_context = extra_context or {}

        if object_id:
            obj = self.get_object(request, object_id)

            extra_context["liq_editable"] = obj is None or obj.liquidacion.editable()

            recibo_url = reverse(
                "admin:liquidacionempleado_recibo",
                args=[obj.pk],
            )

            if obj:
                extra_context["liquidacion_empleado"] = True
                extra_context["plantillas"] = (
                    PlantillaLiquidacion.objects
                    .filter(empresa=obj.liquidacion.empresa)
                    .order_by("denominacion")
                )

                extra_context["recibo_original_url"] = (
                    f"{recibo_url}?tipo=original"
                )
                extra_context["recibo_duplicado_url"] = (
                    f"{recibo_url}?tipo=duplicado"
                )

        return super().changeform_view(request, object_id, form_url, extra_context, )

    def get_urls(self):
        urls = super().get_urls()

        custom = [
            path(
                "<int:liquidacion_empleado_id>/previa/",
                self.admin_site.admin_view(self.liq_previa_view),
                name="liquidacionempleado_previa",
            ),
            path(
                "<int:object_id>/recibo/",
                self.admin_site.admin_view(self.recibo_view),
                name="liquidacionempleado_recibo",
            ),
            path(
                "plantilla/<int:plantilla_id>/detalles/",
                self.admin_site.admin_view(self.plantilla_detalles_view),
                name="liquidacion_plantilla_detalles",
            ),
            path(
                "concepto-detalles/<int:concepto_id>/",
                self.admin_site.admin_view(self.concepto_detalles_view),
                name="liquidacion_concepto_detalles",
            ),
        ]

        return custom + urls

    def response_change(self, request, obj):
        if "_calcular" in request.POST:
            try:
                LiquidacionEmpleadoService(obj).liquidar()
                self.message_user(
                    request,
                    "Liquidación calculada correctamente.",
                    messages.SUCCESS,
                )
            except Exception as e:
                self.message_user(request, str(e), messages.ERROR, )

            return HttpResponseRedirect(request.path)

        return super().response_change(request, obj)

    def liq_previa_view(self, request, liquidacion_empleado_id):
        actual = LiquidacionEmpleado.objects.get(pk=liquidacion_empleado_id)

        liq_previa = (
            LiquidacionEmpleado.objects
            .filter(
                empleado=actual.empleado,
                liquidacion__empresa=actual.liquidacion.empresa,
            )
            .filter(
                Q(  # periodo es menor al período actual
                    liquidacion__periodo__lt=actual.liquidacion.periodo,
                )
                | Q(  # tiene el mismo periodo, pero un numero menor
                    liquidacion__periodo=actual.liquidacion.periodo,
                    liquidacion__numero__lt=actual.liquidacion.numero,
                )
            )
            .order_by(
                "-liquidacion__periodo",
                "-liquidacion__numero",
            )
            .first()
        )

        if liq_previa:
            datos = {
                "cantidad_dias_proporcionar_tope": liq_previa.cantidad_dias_proporcionar_tope,
                "unidad_tiempo_trabajado": liq_previa.unidad_tiempo_trabajado,
                "tiempo_trabajado": liq_previa.tiempo_trabajado,

                "codigo_situacion": liq_previa.codigo_situacion,
                "codigo_condicion": liq_previa.codigo_condicion,
                "codigo_actividad": liq_previa.codigo_actividad,
                "codigo_modalidad_contratacion": liq_previa.codigo_modalidad_contratacion,
                "codigo_siniestrado": liq_previa.codigo_siniestrado,
                "codigo_localidad": liq_previa.codigo_localidad,

                "porcentaje_aporte_adicional_ss": liq_previa.porcentaje_aporte_adicional_ss,
                "porcentaje_contrib_tarea_diferencial": liq_previa.porcentaje_contrib_tarea_diferencial,
                "remuneracion_maternidad_anses": liq_previa.remuneracion_maternidad_anses,

                "cantidad_adherentes_obra_social": liq_previa.cantidad_adherentes_obra_social,
                "aporte_adicional_obra_social": liq_previa.aporte_adicional_obra_social,
                "contrib_adicional_obra_social": liq_previa.contrib_adicional_obra_social,

                "base_calc_diferencial_aportes_obra_social_fsr": liq_previa.base_calc_diferencial_aportes_obra_social_fsr,
                "base_calc_diferencial_contrib_obra_social_fsr": liq_previa.base_calc_diferencial_contrib_obra_social_fsr,
                "base_calc_diferencial_ley_riesgos_trabajo": liq_previa.base_calc_diferencial_ley_riesgos_trabajo,
                "base_calc_diferencial_aportes_seg_social": liq_previa.base_calc_diferencial_aportes_seg_social,
                "base_calc_diferencial_contrib_seg_social": liq_previa.base_calc_diferencial_contrib_seg_social,

                "observaciones_recibo": liq_previa.observaciones_recibo,
                "observaciones_lsd": liq_previa.observaciones_lsd,
            }

            return JsonResponse({"liq_previa": datos})
        else:
            return JsonResponse({"liq_previa": None}, encoder=DjangoJSONEncoder)

    def recibo_view(self, request, object_id):
        tipo = "duplicado" if request.GET.get("tipo") == "duplicado" else "original"

        datos = ReciboSueldoService(
            LiquidacionEmpleado.objects.get(pk=object_id)
        ).obtener_datos(tipo=tipo)
        svg = ReciboSueldoSvgRenderer(datos).render()

        if request.GET.get("formato") == "pdf":
            pdf = convertir_svg_a_pdf(svg)
            response = HttpResponse(pdf, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename="recibo-{object_id}-{tipo}.pdf"'
            )
            return response

        html = render_to_string(
            "admin/liquidacion/recibo_sueldo.html",
            {
                "svg_markup": mark_safe(svg),
                "pdf_url": f"{request.path}?tipo={tipo}&formato=pdf",
            },
            request=request,
        )

        return HttpResponse(
            html,
            content_type="text/html",
        )

    def plantilla_detalles_view(self, request, plantilla_id):
        plantilla = get_object_or_404(
            PlantillaLiquidacion,
            pk=plantilla_id,
        )

        plantilla_service = PlantillaLiquidacionService(plantilla.empresa)

        detalles = [
            {
                "concepto": detalle.concepto.versiones.ultima().id,
                "unidades": str(detalle.unidades),
                "formula_base": plantilla_service.reemplazar_identificadores_formula(detalle.formula_base),
                "cantidad": detalle.cantidad,
                "unidades_lsd": detalle.unidades_lsd,
                "debito_credito": detalle.debito_credito,
                "periodo_ajuste_retroactivo": detalle.periodo_ajuste_retroactivo,
            }
            for detalle in plantilla.detalles.all()
        ]

        return JsonResponse({"detalles": detalles})

    def concepto_detalles_view(self, request, concepto_id):
        VersionConceptoModel = DetalleLiquidacion._meta.get_field("concepto").related_model

        try:
            concepto = VersionConceptoModel.objects.get(pk=concepto_id)
        except VersionConceptoModel.DoesNotExist:
            return JsonResponse({
                "identificador": "", "grupo": "", "tipo": "", "categoria": "",
                "unidad": "", "tiene_codigo_arca": False,
            })

        return JsonResponse({
            "identificador": concepto.identificador_version,
            "grupo": concepto.grupo.denominacion if concepto.grupo else "",
            "tipo": concepto.get_tipo_display(),
            "categoria": concepto.get_categoria_display(),
            "unidad": concepto.get_unidad_display(),
            "tiene_codigo_arca": True if concepto.codigo_arca else False,
        })

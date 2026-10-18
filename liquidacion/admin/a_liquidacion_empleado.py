from django.contrib import admin
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.urls import path
from django.template.loader import render_to_string
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.utils import timezone
from django.utils.http import content_disposition_header

from base_imponible.models import ResultadoBaseImponible
from plantilla_liquidacion.models import PlantillaLiquidacion
from plantilla_liquidacion.services import PlantillaLiquidacionService
from .a_detalles_liquidacion import DetalleLiquidacionInline
from .v_liquidacion_previa import liquidacion_previa_view
from ..models import TramoSituacionRevista, Liquidacion
from ..models.m_liquidacion_empleado import LiquidacionEmpleado
from ..models.m_detalles_liquidacion import DetalleLiquidacion
from ..forms.f_liquidacion_empleado import (
    LiquidacionEmpleadoForm,
    ResultadoBaseImponibleInlineForm,
    TramoSituacionRevistaInlineForm
)
from ..services.s_recibo import ReciboSueldoService
from ..services.s_recibo_pdf import convertir_svg_a_pdf
from ..services.s_recibo_svg import ReciboSueldoSvgRenderer
from .a_liquidacion_empleado_ajax import LiquidacionEmpleadoAjaxMixin


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
class LiquidacionEmpleadoAdmin(LiquidacionEmpleadoAjaxMixin, admin.ModelAdmin):
    inlines = [
        TramoSituacionRevistaInline,
        ResultadoBaseImponibleInline,
        DetalleLiquidacionInline,
    ]
    form = LiquidacionEmpleadoForm

    fieldsets = (
        (None, {
            "classes": ("liquidacion-wizard-empleado",),
            "fields": (
                "liquidacion",
                "empleado_display",
                "liq_previa"
            ),
        }),
        ("Datos Adicionales", {
            "classes": ("columnas-custom-2", "liquidacion-wizard-complementarios"),
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
            "classes": ("columnas-custom-2", "liquidacion-wizard-observaciones"),
            "fields": (
                ("observaciones_recibo", "observaciones_lsd",),
            ),
        }),
        ("Totales de liquidación", {
            "classes": ("columnas-custom-2", "liquidacion-wizard-totales"),
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
        js = (
            "liquidacion/admin/detalle_liquidacion_empleado.js",
            "liquidacion/admin/liquidacion_previa.js",
            "liquidacion/admin/liquidacion_empleado_wizard.js",
            "liquidacion/admin/liquidacion_empleado_resultados.js",
            "liquidacion/admin/liquidacion_empleado_plantilla.js",
        )

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None, ):
        extra_context = extra_context or {}

        if object_id:
            obj = self.get_object(request, object_id)

            if obj:
                extra_context["liq_editable"] = obj.liquidacion.editable()
                extra_context["liquidacion_empleado"] = True
                recibo_url = reverse(
                    "admin:liquidacionempleado_recibo",
                    args=[obj.pk],
                )
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
                self.admin_site.admin_view(liquidacion_previa_view),
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

    def recibo_view(self, request, object_id):
        tipo = "duplicado" if request.GET.get("tipo") == "duplicado" else "original"

        datos = ReciboSueldoService(
            get_object_or_404(LiquidacionEmpleado, pk=object_id)
        ).obtener_datos(tipo=tipo)
        svg = ReciboSueldoSvgRenderer(datos).render()

        if request.GET.get("formato") == "pdf":
            pdf = convertir_svg_a_pdf(svg)
            response = HttpResponse(pdf, content_type="application/pdf")
            entidad = slugify(datos["empresa"]["nombre"]) or "entidad"
            fecha_hora = timezone.localtime().strftime("%Y-%m-%d_%H-%M-%S")
            nombre_archivo = f"recibo-{entidad}-{fecha_hora}-{tipo}.pdf"
            response["Content-Disposition"] = content_disposition_header(
                True,
                nombre_archivo,
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

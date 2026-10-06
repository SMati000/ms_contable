from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.http import HttpResponse, Http404
from django.shortcuts import redirect
from django.urls import reverse, path
from django.utils.html import format_html

from core.utils import normalizar_identificador
from ..forms import LiquidacionEmpleadoInlineForm, LiquidacionEmpleadoInlineFormSet, LiquidacionForm
from ..models import LiquidacionEmpleado
from ..models.m_liquidacion import Liquidacion
from ..services.TxtLsdArca import LsdTxtArcaService


class LiquidacionEmpleadoInline(admin.TabularInline):
    model = LiquidacionEmpleado
    form = LiquidacionEmpleadoInlineForm
    formset = LiquidacionEmpleadoInlineFormSet

    extra = 0
    can_delete = True
    show_change_link = True

    fields = (
        "detalle_link",
        "empleado",
        "remunerativo_display",
        "no_remunerativo_display",
        "bruto_display",
        "descuentos_display",
        "neto_display",
        "contribuciones_display",
        "costo_laboral_display",
        "recibo_sueldo",
    )

    readonly_fields = (
        "detalle_link",
        "remunerativo_display",
        "no_remunerativo_display",
        "bruto_display",
        "descuentos_display",
        "neto_display",
        "contribuciones_display",
        "costo_laboral_display",
        "recibo_sueldo",
    )

    @admin.display(description="")
    def detalle_link(self, obj):
        if not obj.pk:
            return ""

        url = reverse(
            "admin:liquidacion_liquidacionempleado_change",
            args=[obj.pk],
        )

        return format_html(
            '<a href="{}">Ver detalle</a>',
            url,
        )

    @admin.display(description="Recibo")
    def recibo_sueldo(self, obj):
        if not obj or not obj.pk:
            return "-"

        return format_html(
            '{} {}',
            self._boton_recibo(obj, "original", "Original"),
            self._boton_recibo(obj, "duplicado", "Duplicado"),
        )

    def has_add_permission(self, request, obj):
        if obj and not obj.editable():
            return False

        return super().has_add_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and not obj.editable():
            return False

        return super().has_delete_permission(request, obj)

    def _boton_recibo(self, obj, tipo, etiqueta):
        url = reverse(
            "admin:liquidacionempleado_recibo",
            args=[obj.pk],
        )

        url = f"{url}?tipo={tipo}"
        filename = f"recibo-{obj.pk}-{tipo}.pdf"

        return format_html(
            '<a href="{}" target="_blank" '
            'class="button js-recibo-pdf" '
            'style="display: inline-block; margin-right: 4px;" '
            'data-url="{}" '
            'data-filename="{}">{}</a>',
            url,
            url,
            filename,
            etiqueta,
        )


@admin.register(Liquidacion)
class LiquidacionAdmin(admin.ModelAdmin):
    inlines = [LiquidacionEmpleadoInline]
    form = LiquidacionForm
    actions = None

    list_display = (
        "__str__",
        "periodo",
        "fecha_pago",
        "tipo_envio",
        "tipo_liquidacion",
        "numero",
        "estado",
    )

    fields = (
        "empresa",
        "estado",
        "periodo",
        "tipo_envio",
        "tipo_liquidacion",
        "numero",
        "fecha_pago",
    )

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.pk:
            return (
                "estado",
                "empresa",
            )

        return (
            "estado",
        )

    list_filter = ('empresa', 'estado',)
    list_select_related = ('empresa',)

    search_fields = ('periodo',)
    search_help_text = "Busqueda por periodo (fecha, año, mes, etc)"

    ordering = ('empresa', 'periodo',)

    change_form_template = "admin/liquidacion/change_form.html"

    def has_change_permission(self, request, obj=None):
        if obj and not obj.editable():
            return False

        return super().has_change_permission(request, obj)

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                "<path:object_id>/txt/",
                self.admin_site.admin_view(self.generar_txt_view),
                name="liquidacion_generar_txt",
            ),
            path(
                "<path:object_id>/rectificar/",
                self.admin_site.admin_view(self.rectificar_view),
                name="liquidacion_rectificar",
            ),
        ]

        return custom_urls + urls

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = extra_context or {}

        obj = self.get_object(request, object_id)

        extra_context["liq_editable"] = obj is None or obj.editable()

        return super().changeform_view(
            request,
            object_id,
            form_url,
            extra_context=extra_context,
        )

    def generar_txt_view(self, request, object_id):
        if request.method != "POST":
            raise PermissionDenied

        obj = self.get_object(request, object_id)

        if obj is None:
            raise Http404

        txt = LsdTxtArcaService(obj.id).generar()
        obj.cerrar()

        response = HttpResponse(
            txt,
            content_type="text/plain; charset=utf-8",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="liquidacion_'
            f'{normalizar_identificador(obj.empresa.nombre)}_'
            f'{obj.periodo.strftime("%m_%Y")}_{obj.numero}.txt"'
        )

        return response

    def rectificar_view(self, request, object_id):
        obj = self.get_object(request, object_id)

        if obj is None:
            raise Http404

        obj.rectificar()

        self.message_user(
            request,
            "La liquidación se encuentra en rectificación, puede ser modificada.",
            messages.SUCCESS,
        )

        return redirect(
            reverse(
                "admin:liquidacion_liquidacion_change",
                args=[obj.pk],
            )
        )

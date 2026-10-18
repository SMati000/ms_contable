from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.http import JsonResponse
from django.urls import path, reverse
from django.http import HttpResponseRedirect

from base_imponible.models import BaseImponible
from concepto.models import VersionConcepto, Concepto
from .models import PlantillaLiquidacion
from .admin_detalles import DetallePlantillaLiquidacionInline
from .services import agregar_conceptos_faltantes, duplicar_plantilla


@admin.register(PlantillaLiquidacion)
class PlantillaLiquidacionAdmin(admin.ModelAdmin):
    inlines = [DetallePlantillaLiquidacionInline]

    list_per_page = 10
    list_display = ('denominacion', 'empresa', 'duplicar',)
    list_filter = ('empresa',)
    search_fields = ('denominacion',)
    search_help_text = "Buscar por denominacion"
    preserve_filters = True
    list_select_related = ('empresa',)
    ordering = ('denominacion', 'empresa',)

    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return ("empresa",)

        return ()

    change_form_template = "admin/plantilla_liquidacion/change_form.html"

    class Media:
        js = ("plantilla_liquidacion/admin/detalle_plantilla_liquidacion.js",)

    def changeform_view(
        self,
        request,
        object_id=None,
        form_url="",
        extra_context=None,
    ):
        extra_context = extra_context or {}

        extra_context["bases_imponibles"] = (
            BaseImponible.objects
            .order_by("id")
        )

        return super().changeform_view(
            request,
            object_id,
            form_url,
            extra_context=extra_context,
        )

    @admin.display(description="Duplicar")
    def duplicar(self, obj):
        url = reverse(
            "admin:plantillaliquidacion_duplicar",
            args=[obj.pk],
        )

        return format_html(
            '<a href="{}">Duplicar</a>',
            url,
        )

    def response_change(self, request, obj):
        if "_agregar_todos" in request.POST:
            agregados, omitidos = agregar_conceptos_faltantes(obj)

            mensaje = f"Se agregaron {agregados} conceptos a la plantilla."
            if omitidos:
                mensaje += (
                    f" Se omitieron {omitidos} que requieren una versión vigente "
                    "o datos adicionales de ARCA."
                )

            self.message_user(
                request,
                mensaje,
                messages.SUCCESS,
            )

            return HttpResponseRedirect(request.path)

        return super().response_change(request, obj)

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "concepto-detalles/<int:concepto_id>/",
                self.admin_site.admin_view(self.concepto_detalles_view),
                name="liquidacion_concepto_detalles",
            ),
            path(
                "<int:object_id>/duplicar/",
                self.admin_site.admin_view(self.duplicar_view),
                name="plantillaliquidacion_duplicar",
            ),
        ]
        return custom + urls

    def concepto_detalles_view(self, request, concepto_id):
        concepto = Concepto.objects.filter(pk=concepto_id).first()
        version_concepto = concepto.versiones.ultima() if concepto else None

        if version_concepto is None:
            return JsonResponse({
                "identificador": "", "grupo": "", "tipo": "", "categoria": "",
                "unidad": "", "tiene_codigo_arca": False,
            })

        return JsonResponse({
            "identificador": version_concepto.identificador_concepto,
            "grupo": version_concepto.grupo.denominacion if version_concepto.grupo else "",
            "tipo": version_concepto.get_tipo_display(),
            "categoria": version_concepto.get_categoria_display(),
            "unidad": version_concepto.get_unidad_display(),
            "tiene_codigo_arca": True if version_concepto.codigo_arca else False,
        })

    def duplicar_view(self, request, object_id):
        plantilla = self.get_object(request, object_id)

        if plantilla is None:
            self.message_user(
                request,
                "La plantilla no existe.",
                level=messages.ERROR,
            )
            return HttpResponseRedirect(
                reverse("admin:plantilla_liquidacion_plantillaliquidacion_changelist")
            )

        try:
            nueva_plantilla = duplicar_plantilla(plantilla)
        except ValidationError as error:
            self.message_user(
                request,
                f"No se puede duplicar la plantilla: {error}",
                level=messages.ERROR,
            )
            return HttpResponseRedirect(
                reverse(
                    "admin:plantilla_liquidacion_plantillaliquidacion_change",
                    args=[plantilla.pk],
                )
            )

        self.message_user(
            request,
            f'Se duplicó la plantilla "{plantilla.denominacion}".',
            level=messages.SUCCESS,
        )

        return HttpResponseRedirect(
            reverse(
                "admin:plantilla_liquidacion_plantillaliquidacion_change",
                args=[nueva_plantilla.pk],
            )
        )

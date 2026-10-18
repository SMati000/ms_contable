from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import reverse
from django.db import transaction
from django.db.models import Prefetch
from .exceptions import ConceptoEnUsoEnLiquidacionAbierta
from .models import Concepto, VersionConcepto
from .forms import ConceptoAdminForm
from .services import actualizar_concepto, eliminar_concepto
from .admin_filters import (
    ConceptoCategoriaFilter,
    ConceptoEliminadosFilter,
    ConceptoGrupoFilter,
    ConceptoTipoFilter,
)


class VersionConceptoInline(admin.TabularInline):
    model = VersionConcepto

    can_delete = False
    max_num = 0
    extra = 0

    verbose_name = "Versión anterior"
    verbose_name_plural = "Historial de versiones"

    fields = (
        "version",
        "denominacion",
        "grupo",
        "codigo_arca",
        "categoria",
        "tipo",
        "bases_imponibles_version",
        "unidad",
    )

    readonly_fields = fields

    @admin.display(description="Bases Imponibles")
    def bases_imponibles_version(self, obj):
        resultado = ", ".join(
            base.denominacion
            for base in obj.bases_imponibles.all()
        ) or "-"

        return resultado.replace("Remuneración ", "R")

    def get_queryset(self, request):
        return super().get_queryset(request).order_by("-version")


@admin.register(Concepto)
class ConceptoAdmin(admin.ModelAdmin):
    form = ConceptoAdminForm
    inlines = [VersionConceptoInline]

    list_display = (
        "denominacion",
        "empresa",
        "grupo",
        "codigo_arca",
        "categoria",
        "tipo",
        "bases_imponibles",
        "unidad",
    )

    list_filter = (
        ConceptoCategoriaFilter,
        ConceptoGrupoFilter,
        ConceptoTipoFilter,
        ConceptoEliminadosFilter,
        "empresa",
    )
    preserve_filters = True
    ordering = ('empresa',)

    class Media:
        js = ("concepto/admin/concepto_admin.js",)

    @admin.display(description="Denominación")
    def denominacion(self, obj):
        version = self._version_vigente(obj)
        return version.denominacion if version else "-"

    @admin.display(description="Código ARCA")
    def codigo_arca(self, obj):
        version = self._version_vigente(obj)
        return version.codigo_arca if version else "-"

    @admin.display(description="Categoría")
    def categoria(self, obj):
        version = self._version_vigente(obj)
        return version.get_categoria_display() if version else "-"

    @admin.display(description="Tipo")
    def tipo(self, obj):
        version = self._version_vigente(obj)
        return version.get_tipo_display() if version else "-"

    @admin.display(description="Unidad")
    def unidad(self, obj):
        version = self._version_vigente(obj)
        return version.get_unidad_display() if version else "-"

    @admin.display(description="Grupo")
    def grupo(self, obj):
        version = self._version_vigente(obj)
        return version.grupo if version else "-"

    @admin.display(description="Bases Imponibles")
    def bases_imponibles(self, obj):
        version = self._version_vigente(obj)

        if not version:
            return "-"

        resultado = ", ".join(
            base.denominacion
            for base in version.bases_imponibles.all()
        ) or "-"

        return resultado.replace("Remuneración ", "R")

    # Por ahora el usuario no puede ver las versiones del concepto eliminado, para eso deberia restaurarlo primero
    def get_list_display_links(self, request, list_display):
        if request.GET.get("eliminados") == "eliminados":
            return None

        return super().get_list_display_links(request, list_display)

    actions = ("eliminar_conceptos", "restaurar_conceptos", "eliminar_definitivamente",)

    def get_actions(self, request):
        actions = super().get_actions(request)

        eliminados = request.GET.get("eliminados") == "eliminados"

        if eliminados:
            actions.pop("delete_selected", None)
            actions.pop("eliminar_conceptos", None)
        else:
            actions.pop("delete_selected", None)
            actions.pop("restaurar_conceptos", None)
            actions.pop("eliminar_definitivamente", None)

        return actions

    @admin.action(description="Eliminar conceptos seleccionados")
    def eliminar_conceptos(self, request, queryset):
        for concepto in queryset:
            try:
                eliminar_concepto(concepto)
            except ConceptoEnUsoEnLiquidacionAbierta as e:
                self.message_user(
                    request,
                    str(e),
                    level=messages.ERROR,
                )
                return redirect(
                    reverse(
                        f"admin:{self.opts.app_label}_{self.opts.model_name}_changelist"
                    )
                )

    @admin.action(description="Restaurar conceptos seleccionados")
    def restaurar_conceptos(self, request, queryset):
        queryset.update(eliminado=False)

    @admin.action(description="Eliminar definitivamente conceptos seleccionados")
    def eliminar_definitivamente(self, request, queryset):
        queryset.hard_delete()

    change_form_template = "admin/concepto/change_form.html"

    def _version_vigente(self, obj):
        return (
            obj.ultima_version[0]  # Prefetch(..., ) siempre devuelve una colección
            if obj.ultima_version
            else None
        )

    def get_queryset(self, request):
        queryset = self.model.todos.all()

        if request.GET.get("eliminados") == "eliminados":
            queryset = queryset.eliminados()
            versiones = VersionConcepto.todos.eliminados().ultima_version()
        else:
            queryset = queryset.activos()
            versiones = VersionConcepto.objects.ultima_version()

        return queryset.prefetch_related(
            Prefetch(
                "versiones",
                queryset=versiones,
                to_attr="ultima_version",
            )
        )

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        actualizar_concepto(
            concepto=obj,
            denominacion=form.cleaned_data["denominacion"],
            codigo_arca=form.cleaned_data["codigo_arca"],
            categoria=form.cleaned_data["categoria"],
            tipo=form.cleaned_data["tipo"],
            unidad=form.cleaned_data["unidad"],
            grupo=form.cleaned_data["grupo"],
            bases_imponibles=form.cleaned_data["bases_imponibles"],
        )

    def delete_view(self, request, object_id, extra_context=None):
        concepto = self.get_object(request, object_id)

        if concepto is not None:
            try:
                eliminar_concepto(concepto)
            except ConceptoEnUsoEnLiquidacionAbierta as e:
                self.message_user(
                    request,
                    str(e),
                    level=messages.ERROR,
                )
                return redirect(
                    reverse(
                        f"admin:{self.opts.app_label}_{self.opts.model_name}_changelist"
                    )
                )

        return redirect(
            reverse(
                f"admin:{self.opts.app_label}_{self.opts.model_name}_changelist"
            )
        )

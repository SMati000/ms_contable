from django.contrib import admin
from django.db.models import Prefetch
from django.utils.html import format_html

from concepto.choices import Unidad
from concepto.models import Concepto, VersionConcepto
from .forms import DetallePlantillaLiquidacionForm
from .models import DetallePlantillaLiquidacion


class DetallePlantillaLiquidacionInline(admin.StackedInline):
    model = DetallePlantillaLiquidacion
    form = DetallePlantillaLiquidacionForm

    extra = 0
    can_delete = True
    show_change_link = True

    fieldsets = (
        (
            "Concepto",
            {
                "classes": ("columnas-custom",),
                "fields": (
                    ("concepto", "grupo", "tipo", "categoria",),
                    ("unidad", "unidades", "formula_base"),
                ),
            },
        ),
        (
            "Detalles Registro 03 LSD Arca",
            {
                "classes": ("columnas-custom", "registro03-fieldset", ),
                "fields": (
                    ("cantidad", "unidades_lsd", "debito_credito", "periodo_ajuste_retroactivo"),
                ),
            },
        ),
    )

    readonly_fields = (
        "grupo",
        "tipo",
        "categoria",
        "unidad",
    )

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)

        if obj:
            empresa = obj.empresa
            formset.form.base_fields["concepto"].queryset = (
                Concepto.objects.filter(empresa=empresa)
            )
        else:
            formset.form.base_fields["concepto"].queryset = (
                Concepto.objects.none()
            )

        return formset

    @admin.display(description="Grupo")
    def grupo(self, obj):
        version = self.version_vigente(obj)

        texto = (
            version.grupo.denominacion
            if version and version.grupo
            else "-"
        )

        return format_html('<span class="grupo-display">{}</span>', texto)

    @admin.display(description="Tipo")
    def tipo(self, obj):
        version = self.version_vigente(obj)

        texto = version.get_tipo_display() if version else "-"

        return format_html('<span class="tipo-display">{}</span>', texto)

    @admin.display(description="Categoria")
    def categoria(self, obj):
        version = self.version_vigente(obj)

        texto = version.get_categoria_display() if version else "-"

        return format_html('<span class="categoria-display">{}</span>', texto)

    @admin.display(description="Unidad")
    def unidad(self, obj):
        nombre = "-"
        descripcion = ""

        version = self.version_vigente(obj)

        if version:
            unidad = Unidad(version.unidad)
            nombre = unidad.label
            descripcion = unidad.descripcion

        return format_html(
            '<span class="unidad-display" title="{}">{}</span>',
            descripcion,
            nombre,
        )

    def version_vigente(self, obj):
        if not obj or not obj.concepto_id:
            return None

        versiones = getattr(
            obj.concepto,
            "_versiones_vigentes",
            [],
        )

        return versiones[0] if versiones else None

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        versiones = (
            VersionConcepto.todos
            .select_related("grupo")
            .ultima_version()
        )

        return (
            queryset
            .select_related("concepto")
            .prefetch_related(
                Prefetch(
                    "concepto__versiones",
                    queryset=versiones,
                    to_attr="_versiones_vigentes",
                )
            )
        )

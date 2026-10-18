from django.contrib import admin

from grupo_concepto.models import GrupoConcepto
from .models import VersionConcepto


class ConceptoCategoriaFilter(admin.SimpleListFilter):
    title = "categoría"
    parameter_name = "categoria"

    def lookups(self, request, model_admin):
        field = VersionConcepto._meta.get_field("categoria")
        return list(dict(field.choices).items())

    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        versiones = (
            VersionConcepto.objects
            .ultima_version()
            .filter(categoria=self.value())
        )
        return queryset.filter(versiones__in=versiones)


class ConceptoGrupoFilter(admin.SimpleListFilter):
    title = "grupo"
    parameter_name = "grupo"

    def lookups(self, request, model_admin):
        return (
            GrupoConcepto.objects
            .order_by("denominacion")
            .values_list("pk", "denominacion")
        )

    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        version_vigente = (
            VersionConcepto.objects
            .ultima_version()
            .filter(grupo_id=self.value())
        )
        return queryset.filter(versiones__in=version_vigente)


class ConceptoTipoFilter(admin.SimpleListFilter):
    title = "tipo"
    parameter_name = "tipo"

    def lookups(self, request, model_admin):
        field = VersionConcepto._meta.get_field("tipo")
        return list(dict(field.choices).items())

    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        versiones = (
            VersionConcepto.objects
            .ultima_version()
            .filter(tipo=self.value())
        )
        return queryset.filter(versiones__in=versiones)


class ConceptoEliminadosFilter(admin.SimpleListFilter):
    title = "eliminados"
    parameter_name = "eliminados"

    def lookups(self, request, model_admin):
        return (("eliminados", "Sí"),)

    def choices(self, changelist):
        yield {
            "selected": self.value() is None,
            "query_string": changelist.get_query_string(
                remove=[self.parameter_name],
            ),
            "display": "No",
        }

        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == str(lookup),
                "query_string": changelist.get_query_string(
                    {self.parameter_name: lookup},
                ),
                "display": title,
            }

    def queryset(self, request, queryset):
        return queryset

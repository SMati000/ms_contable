from django.contrib import admin
from .models import Empresa
from django.contrib.auth.models import Group, User
from django.contrib.admin.models import (
    LogEntry,
    ADDITION,
    CHANGE,
    DELETION,
)
import json


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_per_page = 10
    list_display = ('nombre', 'cuit', 'tipo_empleador', 'domicilio')
    search_fields = ('nombre',)
    search_help_text = "Buscar por nombre"
    list_filter = ('tipo_empleador',)
    list_editable = ('domicilio',)
    list_display_links = None


admin.site.unregister(Group)
admin.site.unregister(User)


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_per_page = 25

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Modelo")
    def model_name(self, obj):
        return obj.content_type.model_class()._meta.verbose_name

    @admin.display(description="Objeto")
    def object_name(self, obj):
        return obj.object_repr

    @admin.display(description="Cambios")
    def changes(self, obj):
        if obj.action_flag != CHANGE:
            return ""

        if not obj.change_message:
            return ""

        try:
            messages = json.loads(obj.change_message)
        except (TypeError, ValueError):
            return obj.change_message

        fields = []

        for message in messages:
            if "changed" in message:
                fields.extend(message["changed"].get("fields", []))

        return ", ".join(fields)

    list_display = (
        "action_time",
        "action_flag",
        "model_name",
        "object_name",
        "changes"
    )

    list_filter = (
        "action_flag",
    )

    search_fields = (
        "object_repr",
        "change_message",
    )

    search_help_text = "Buscar por objeto o campos que se cambiaron"

    ordering = ("-action_time",)
    actions = None
    list_display_links = None

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


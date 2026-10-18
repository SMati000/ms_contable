from django.apps import AppConfig


class BaseImponibleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "base_imponible"
    verbose_name = "Parámetros salariales"

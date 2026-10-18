from django.db import models
from core.models import ValidatingModel
from core.validators import validar_cuit
from empresa.choices import TipoEmpleador


class Empresa(ValidatingModel):
    id = models.BigAutoField(primary_key=True)

    cuit = models.CharField(
        max_length=11,
        null=False,
        blank=False,
        validators=[validar_cuit],
    )

    nombre = models.CharField(
        max_length=255,
        null=False,
        blank=False,
    )

    tipo_empleador = models.CharField(
        max_length=50,
        choices=TipoEmpleador.choices,
        null=False,
        blank=False
    )

    domicilio = models.CharField(
        max_length=255,
        null=False,
        blank=True,
    )

    def save(self, *args, **kwargs):
        if self.pk is not None:
            original = type(self).objects.get(pk=self.pk)

            immutable_fields = [
                "cuit",
                "nombre",
                "tipo_empleador",
            ]

            for field in immutable_fields:
                if getattr(self, field) != getattr(original, field):
                    raise ValueError(
                        f"El campo '{field}' de una empresa es inmutable."
                    )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.cuit})"

from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from core.models import ValidatingModel

GRUPOS_PROTEGIDOS = {
    "sindical",
    "seguridad_social",
    "obra_social",
    "inssjp",
    "art",
    "scvo",
    "entidades_empresariales",
}


class GrupoConceptoQuerySet(models.QuerySet):

    def delete(self):
        protegidos = self.filter(
            codigo__in=GRUPOS_PROTEGIDOS,
        )

        if protegidos.exists():
            codigos = ", ".join(
                protegidos.values_list("codigo", flat=True)
            )
            raise ValidationError(
                f"No se pueden eliminar grupos obligatorios: {codigos}."
            )

        return super().delete()


class GrupoConcepto(ValidatingModel):
    objects = GrupoConceptoQuerySet.as_manager()

    id = models.BigAutoField(
        primary_key=True,
    )

    codigo = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        unique=True,
        validators=[RegexValidator(
            regex=r"^[a-z0-9_]+$",
            message="El código solo puede contener letras minúsculas, números y guiones bajos.",
        )],
        help_text="Ej: seguridad_social, inssjp, obra_social, etc",
    )

    denominacion = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        help_text="Ej: Seguridad Social, INSSJP, Obra Social, etc",
    )

    class Meta:
        verbose_name = "grupo para conceptos"
        verbose_name_plural = "grupos para los conceptos"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            original = type(self).objects.get(pk=self.pk)

            if self.denominacion != original.denominacion:
                raise ValueError(
                    "La denominación de un grupo de concepto es inmutable."
                )

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.codigo in self.GRUPOS_PROTEGIDOS:
            raise ValidationError(
                f"El grupo de concepto '{self.denominacion}' "
                "no puede eliminarse."
            )

        return super().delete(*args, **kwargs)

    def __str__(self):
        return self.denominacion

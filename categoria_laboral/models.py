from django.db import models
from core.models import ValidatingModel


class CategoriaLaboral(ValidatingModel):
    id = models.BigAutoField(
        primary_key=True,
    )

    empresa = models.ForeignKey(
        "empresa.Empresa",
        on_delete=models.PROTECT,
        related_name="categorias_laborales",
    )

    denominacion = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        help_text="Ej: Personal de Obra, Administrativo, etc",
    )

    class Meta:
        verbose_name = "categoría laboral"
        verbose_name_plural = "categorías laborales"

        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "denominacion"],
                name="unique_categoria_laboral_por_empresa",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.pk is not None:
            original = type(self).objects.get(pk=self.pk)

            if self.empresa_id != original.empresa_id:
                raise ValueError(
                    "La categoría no se puede cambiar de empresa."
                )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.denominacion

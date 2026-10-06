from django.db import models
from django.core.exceptions import ValidationError
from liquidacion.choices import UnidadesLsd, DebitoCredito


class PlantillaLiquidacion(models.Model):
    id = models.BigAutoField(
        primary_key=True,
    )

    empresa = models.ForeignKey(
        "empresa.Empresa",
        on_delete=models.CASCADE,
        related_name="plantillas_liquidacion",
    )

    denominacion = models.CharField(
        max_length=255,
        null=False,
        blank=False,
    )

    class Meta:
        verbose_name = "Plantilla para liquidacion"
        verbose_name_plural = "Plantillas para liquidacion"

        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "denominacion"],
                name="unique_plantilla_por_empresa",
            ),
        ]

    def __str__(self):
        return f"{self.denominacion}"


class DetallePlantillaLiquidacion(models.Model):
    id = models.BigAutoField(
        primary_key=True,
    )

    plantilla = models.ForeignKey(
        "plantilla_liquidacion.PlantillaLiquidacion",
        on_delete=models.CASCADE,
        related_name="detalles",
    )

    concepto = models.ForeignKey(
        "concepto.Concepto",
        on_delete=models.PROTECT,
        related_name="detalles_plantillas",
    )

    unidades = models.DecimalField(
        max_digits=12,
        decimal_places=5,
        null=False,
        blank=False,
    )

    formula_base = models.CharField(
        max_length=500,
        null=False,
        blank=False,
    )

    cantidad = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        default=None,
    )

    unidades_lsd = models.CharField(
        max_length=10,
        choices=UnidadesLsd.choices,
        null=True,
        blank=True,
    )

    debito_credito = models.CharField(
        max_length=10,
        choices=DebitoCredito.choices,
        null=True,
        blank=True,
    )

    periodo_ajuste_retroactivo = models.DateField(
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Detalle de plantilla para liquidacion"
        verbose_name_plural = "Detalles de plantilla para liquidacion"

        constraints = [
            models.UniqueConstraint(
                fields=["plantilla", "concepto"],
                name="unique_concepto_por_plantilla",
            ),
        ]

    def clean(self):
        super().clean()

        if (
            self.plantilla_id
            and self.concepto_id
            and self.plantilla.empresa_id != self.concepto.empresa_id
        ):
            raise ValidationError(
                "El concepto asociado no pertenece a la empresa de la plantilla."
            )

    def __str__(self):
        return f"identificador: {self.concepto.versiones.ultima().identificador_concepto}"

from datetime import date

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib import admin

from concepto.choices import Unidad
from concepto.models import VersionConcepto
from core.utils import format_decimal_2
from liquidacion.choices import UnidadesLsd, DebitoCredito


class DetalleLiquidacion(models.Model):
    id = models.BigAutoField(
        primary_key=True,
    )

    liquidacion_empleado = models.ForeignKey(
        "liquidacion.LiquidacionEmpleado",
        on_delete=models.CASCADE,
        related_name="detalles",
    )

    concepto = models.ForeignKey(
        "concepto.VersionConcepto",
        on_delete=models.PROTECT,
        related_name="detalles_liquidacion",
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

    base = models.DecimalField(
        max_digits=20,
        decimal_places=5,
        null=False,
        blank=False,
        default=0,
        editable=False,
    )

    importe = models.DecimalField(
        max_digits=20,
        decimal_places=5,
        null=False,
        blank=False,
        default=0,
        editable=False,
        help_text="Unidades * Base",
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

    @property
    @admin.display(description="Base")
    def base_display(self):
        return format_decimal_2(self.base)

    @property
    @admin.display(description="Importe")
    def importe_display(self):
        return format_decimal_2(self.importe)

    class Meta:
        verbose_name = "detalle liquidación"
        verbose_name_plural = "detalles de liquidación"

        constraints = [
            models.UniqueConstraint(
                fields=["liquidacion_empleado", "concepto"],
                name="unique_concepto_por_liquidacion_empleado",
            ),
        ]

    def clean(self):
        super().clean()

        if not self.liquidacion_empleado.liquidacion.editable():
            raise ValidationError(
                "Esta liquidación no se puede modificar."
            )

        if (
            self.liquidacion_empleado_id
            and self.concepto_id
            and self.liquidacion_empleado.liquidacion.empresa_id != self.concepto.concepto.empresa_id
        ):
            raise ValidationError(
                "El concepto asociado no pertenece a la empresa de la liquidación."
            )

        unidad = Unidad(self.concepto.unidad)
        if not unidad.constraint(self.unidades):
            raise ValidationError({
                "unidades": (
                    f"El valor no es válido para la unidad "
                    f"{self.concepto.get_unidad_display()}."
                )
            })

    def save(self, *args, **kwargs):
        if self.pk is not None:
            if not self.liquidacion_empleado.liquidacion.editable():
                raise ValidationError(
                    "Esta liquidación no se puede modificar."
                )

            original = type(self).objects.get(pk=self.pk)

            if self.liquidacion_empleado_id != original.liquidacion_empleado_id:
                raise ValueError(
                    "No se puede cambiar la liquidación asociada."
                )

            if self.concepto_id != original.concepto_id:
                raise ValueError(
                    "No se puede cambiar el concepto asociado."
                )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"identificador: {self.concepto.identificador_version}"

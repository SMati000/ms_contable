from django.db import models
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.contrib import admin

from concepto.validation import validar_unidades
from core.models import ValidatingModel
from core.utils import format_decimal_2
from liquidacion.choices import UnidadesLsd, DebitoCredito
from liquidacion.validators.v_detalles import validar_debito_credito
from liquidacion.validators.v_expresiones import validar_formula


class DetalleLiquidacion(ValidatingModel):
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
        help_text="Precisión de hasta 5 decimales",
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

        try:
            liquidacion_empleado = self.liquidacion_empleado
        except ObjectDoesNotExist:
            liquidacion_empleado = None

        try:
            concepto = self.concepto
        except ObjectDoesNotExist:
            concepto = None

        try:
            concepto_base = concepto.concepto if concepto else None
        except ObjectDoesNotExist:
            concepto_base = None

        try:
            liquidacion = (
                liquidacion_empleado.liquidacion
                if liquidacion_empleado and liquidacion_empleado.liquidacion_id
                else None
            )
        except ObjectDoesNotExist:
            liquidacion = None

        if liquidacion and not liquidacion.editable():
            raise ValidationError(
                "Esta liquidación no se puede modificar."
            )

        if (
            liquidacion
            and concepto_base
            and liquidacion.empresa_id != concepto_base.empresa_id
        ):
            raise ValidationError(
                "El concepto asociado no pertenece a la empresa de la liquidación."
            )

        if concepto:
            validar_unidades(concepto.unidad, self.unidades)
            validar_debito_credito(concepto.codigo_arca, self.debito_credito)

        if self.formula_base:
            validar_formula(self.formula_base)

    def save(self, *args, **kwargs):
        if self.pk is not None:
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

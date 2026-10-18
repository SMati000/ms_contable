from django.db import models
from django.contrib import admin
from django.core.validators import RegexValidator
from core.models import ValidatingModel
from core.utils import format_decimal_2


class BaseImponible(models.Model):
    id = models.BigAutoField(primary_key=True,)

    denominacion = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        unique=True,
        editable=False,
    )

    identificador = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        unique=True,
        validators=[RegexValidator(
            regex=r"^[a-z0-9_]+$",
            message="El código solo puede contener letras minúsculas, números y guiones bajos.",
        )],
        editable=False,
    )

    descripcion = models.CharField(
        max_length=500,
        null=False,
        blank=True,
        default="",
        editable=False,
    )

    configurable = models.BooleanField(
        default=False,
        editable=False,
    )

    class Meta:
        verbose_name = "base imponible"
        verbose_name_plural = "bases imponibles"

    def __str__(self):
        return f"{self.denominacion}"


class ResultadoBaseImponible(ValidatingModel):
    liquidacion_empleado = models.ForeignKey(
        "liquidacion.LiquidacionEmpleado",
        on_delete=models.CASCADE,
        related_name="resultados_bases_imponibles",
    )

    base_imponible = models.ForeignKey(
        BaseImponible,
        on_delete=models.PROTECT,
        related_name="resultados",
    )

    importe = models.DecimalField(
        max_digits=20,
        decimal_places=5,
        default=0,
        null=False,
        blank=False,
    )

    @property
    @admin.display(description="Importe")
    def importe_display(self):
        return format_decimal_2(self.importe)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "liquidacion_empleado",
                    "base_imponible",
                ),
                name="uq_resultado_base_liquidacion_empleado",
            ),
        ]
        ordering = ("base_imponible__id",)
        verbose_name = "Resultado de base imponible"
        verbose_name_plural = "Resultados de bases imponibles"

    def __str__(self):
        return f"identificador: {self.base_imponible.identificador}"

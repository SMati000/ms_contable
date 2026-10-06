from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.contrib import admin
from core.utils import format_decimal_2


IDENTIFICADORES_LE = {
    "remunerativo": "remunerativo",
    "no_remunerativo": "no_remunerativo",
    "bruto": "bruto",
    "neto": "neto",
    "contribuciones": "contribuciones",
    "descuentos": "descuentos",
    "costo_laboral": "costo_laboral",
}


class LiquidacionEmpleado(models.Model):
    class UnidadTiempoTrabajado(models.TextChoices):
        D = "d", "Días"
        H = "h", "Horas"

    id = models.BigAutoField(
        primary_key=True,
    )

    liquidacion = models.ForeignKey(
        "liquidacion.Liquidacion",
        on_delete=models.PROTECT,
        related_name="empleados",
    )

    empleado = models.ForeignKey(
        "empleado.Empleado",
        on_delete=models.PROTECT,
        related_name="liquidaciones",
    )

    version_empleado = models.ForeignKey(
        "empleado.VersionEmpleado",
        on_delete=models.PROTECT,
        related_name="liquidaciones",
    )

    remunerativo = models.DecimalField(
        max_digits=20,
        decimal_places=5,
        default=0,
        null=False,
        blank=False,
        editable=False,
    )

    no_remunerativo = models.DecimalField(
        max_digits=20,
        decimal_places=5,
        default=0,
        null=False,
        blank=False,
        editable=False,
    )

    bruto = models.DecimalField(
        max_digits=20,
        decimal_places=5,
        default=0,
        null=False,
        blank=False,
        editable=False,
    )

    descuentos = models.DecimalField(
        max_digits=20,
        decimal_places=5,
        default=0,
        null=False,
        blank=False,
        editable=False,
    )

    neto = models.DecimalField(
        max_digits=20,
        decimal_places=5,
        default=0,
        null=False,
        blank=False,
        editable=False,
    )

    contribuciones = models.DecimalField(
        max_digits=20,
        decimal_places=5,
        default=0,
        null=False,
        blank=False,
        editable=False,
    )

    costo_laboral = models.DecimalField(
        max_digits=20,
        decimal_places=5,
        default=0,
        null=False,
        blank=False,
        editable=False,
    )

    observaciones_recibo = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        editable=True,
        default="",
        help_text="Observaciones que se reflejaran en el recibo de sueldo"
    )

    observaciones_lsd = models.CharField(
        max_length=80,
        null=False,
        blank=True,
        help_text="Observaciones para Libro de Sueldos Digital de ARCA. Max 80 caracteres.",
    )

    fecha_rubrica = models.DateField(
        null=True,
        blank=True,
    )

    cantidad_dias_proporcionar_tope = models.PositiveIntegerField(
        null=False,
        blank=False,
        validators=[MinValueValidator(0), MaxValueValidator(999)],
        default=0
    )

    codigo_situacion = models.CharField(
        max_length=2,
        null=False,
        blank=True,
    )

    codigo_condicion = models.CharField(
        max_length=2,
        null=False,
        blank=True,
    )

    codigo_actividad = models.CharField(
        max_length=3,
        null=False,
        blank=True,
    )

    codigo_modalidad_contratacion = models.CharField(
        max_length=3,
        null=False,
        blank=True,
    )

    codigo_siniestrado = models.CharField(
        max_length=2,
        null=False,
        blank=True,
    )

    codigo_localidad = models.CharField(
        max_length=2,
        null=False,
        blank=True,
    )

    unidad_tiempo_trabajado = models.CharField(
        max_length=10,
        choices=UnidadTiempoTrabajado.choices,
        null=True,
        blank=True,
    )

    tiempo_trabajado = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(999)]
    )

    porcentaje_aporte_adicional_ss = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        null=False,
        blank=False,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    porcentaje_contrib_tarea_diferencial = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        null=False,
        blank=False,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    cantidad_adherentes_obra_social = models.PositiveIntegerField(
        null=False,
        blank=False,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(99)]
    )

    aporte_adicional_obra_social = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        null=False,
        blank=False,
    )

    contrib_adicional_obra_social = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        null=False,
        blank=False,
    )

    base_calc_diferencial_aportes_obra_social_fsr = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        null=False,
        blank=False,
    )

    base_calc_diferencial_contrib_obra_social_fsr = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        null=False,
        blank=False,
    )

    base_calc_diferencial_ley_riesgos_trabajo = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        null=False,
        blank=False,
    )

    remuneracion_maternidad_anses = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        null=False,
        blank=False,
    )

    base_calc_diferencial_aportes_seg_social = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        null=False,
        blank=False,
    )

    base_calc_diferencial_contrib_seg_social = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        null=False,
        blank=False,
    )

    @property
    @admin.display(description="Remunerativo")
    def remunerativo_display(self):
        return format_decimal_2(self.remunerativo)

    @property
    @admin.display(description="No Remunerativo")
    def no_remunerativo_display(self):
        return format_decimal_2(self.no_remunerativo)

    @property
    @admin.display(description="Bruto")
    def bruto_display(self):
        return format_decimal_2(self.bruto)

    @property
    @admin.display(description="Descuentos")
    def descuentos_display(self):
        return format_decimal_2(self.descuentos)

    @property
    @admin.display(description="Neto")
    def neto_display(self):
        return format_decimal_2(self.neto)

    @property
    @admin.display(description="Contribuciones")
    def contribuciones_display(self):
        return format_decimal_2(self.contribuciones)

    @property
    @admin.display(description="Costo Laboral")
    def costo_laboral_display(self):
        return format_decimal_2(self.costo_laboral)

    class Meta:
        verbose_name = "liquidación por empleado"
        verbose_name_plural = "liquidación por empleado"

        constraints = [
            models.UniqueConstraint(
                fields=["liquidacion", "empleado"],
                name="unique_empleado_por_liquidacion",
            ),
        ]

    def clean(self):
        super().clean()

        if not self.liquidacion.editable():
            raise ValidationError(
                "Esta liquidación no se puede modificar."
            )

        if (
            self.liquidacion_id
            and self.empleado_id
            and self.liquidacion.empresa_id != self.empleado.empresa_id
        ):
            raise ValidationError(
                "El empleado no pertenece a la empresa de la liquidación."
            )

        if (
            self.empleado_id and self.version_empleado_id
            and self.empleado_id != self.version_empleado.empleado_id
        ):
            raise ValidationError(
                "Empleado y version de empleado inconsistentes."
            )

    def save(self, *args, **kwargs):
        if self.pk:
            if not self.liquidacion.editable():
                raise ValidationError(
                    "Esta liquidación no se puede modificar."
                )

            original = type(self).objects.get(pk=self.pk)

            if self.liquidacion_id != original.liquidacion_id:
                raise ValueError(
                    "La liquidación asociada no se puede modificar."
                )

            if self.empleado_id != original.empleado_id:
                raise ValueError(
                    "El empleado de una liquidación no puede ser modificado."
                )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.liquidacion.periodo} - {self.empleado.apellidos}, {self.empleado.nombres}"

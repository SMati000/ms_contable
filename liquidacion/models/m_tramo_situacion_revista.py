from calendar import monthrange
from datetime import date

from django.db import models
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import ValidatingModel


class TramoSituacionRevista(ValidatingModel):
    id = models.BigAutoField(
        primary_key=True,
    )

    liquidacion_empleado = models.ForeignKey(
        "liquidacion.LiquidacionEmpleado",
        on_delete=models.CASCADE,
        related_name="situaciones_revista",
    )

    codigo_situacion = models.CharField(
        max_length=2,
        null=False,
        blank=True,
    )

    dia_inicio = models.PositiveIntegerField(
        null=False,
        blank=False,
        validators=[MinValueValidator(1), MaxValueValidator(31)]
    )

    class Meta:
        verbose_name = "tramo de situacion de revista"
        verbose_name_plural = "tramos de situacion de revista"

    def clean(self):
        super().clean()

        try:
            liquidacion_empleado = self.liquidacion_empleado
        except ObjectDoesNotExist:
            return

        try:
            liquidacion = liquidacion_empleado.liquidacion
        except ObjectDoesNotExist:
            return

        if not liquidacion.editable():
            raise ValidationError("Esta liquidación no se puede modificar.")

        try:
            dia_inicio = self._meta.get_field("dia_inicio").to_python(
                self.dia_inicio,
            )
        except ValidationError:
            return

        if not isinstance(dia_inicio, int) or not isinstance(liquidacion.periodo, date):
            return

        ultimo_dia = monthrange(
            liquidacion.periodo.year,
            liquidacion.periodo.month,
        )[1]
        if dia_inicio > ultimo_dia:
            raise ValidationError({
                "dia_inicio": (
                    "El día de inicio debe estar dentro del período liquidado."
                )
            })

    def __str__(self):
        return f"Situación de Revista"

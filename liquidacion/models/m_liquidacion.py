from django.db import models
from django.core.exceptions import ValidationError

from liquidacion.choices import TipoEnvio, TipoLiquidacion
from liquidacion.validators.v_liquidacion import validar_fechas


class Liquidacion(models.Model):
    class Estado(models.TextChoices):
        BORRADOR = "borrador", "Borrador"
        EN_RECTIFICACION = "en_rectificacion", "En Rectificación"
        CERRADA = "cerrada", "Cerrada"

    id = models.BigAutoField(
        primary_key=True,
    )

    empresa = models.ForeignKey(
        "empresa.Empresa",
        on_delete=models.PROTECT,
        related_name="liquidaciones",
    )

    # Decision deliberada: Esta fecha puede ser del futuro puesto que
    # puede ser válido preparar una liquidación anticipadamente
    periodo = models.DateField(
        null=False,
        blank=False,
    )

    numero = models.PositiveIntegerField(
        null=True,
        blank=True,
        default=None,
    )

    fecha_pago = models.DateField(
        null=False,
        blank=False,
    )

    estado = models.CharField(
        max_length=30,
        choices=Estado.choices,
        null=False,
        blank=False,
    )

    tipo_envio = models.CharField(
        max_length=10,
        choices=TipoEnvio.choices,
        null=False,
        blank=False,
    )

    tipo_liquidacion = models.CharField(
        max_length=10,
        choices=TipoLiquidacion.choices,
        null=False,
        blank=True,
    )

    domicilio_empresa = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        editable=False,
        help_text="Domicilio de la empresa al momento de realizar la liquidación.",
    )

    def editable(self):
        estado_db = self._estado_db()

        if estado_db is None:
            return True

        return estado_db != self.Estado.CERRADA

    def cerrar(self):
        estado_db = self._estado_db()

        if estado_db == self.Estado.CERRADA:
            return

        self.estado = self.Estado.CERRADA
        self.save(update_fields=["estado"], _transition=True)

    def rectificar(self):
        estado_db = self._estado_db()

        if estado_db == self.Estado.EN_RECTIFICACION:
            return

        if estado_db != self.Estado.CERRADA:
            raise ValidationError(
                "La liquidacion no puede pasar a estado 'En Rectificación' porque todavía no esta cerrada"
            )

        self.estado = self.Estado.EN_RECTIFICACION
        self.save(update_fields=["estado"], _transition=True)

    def _estado_db(self):
        if self.pk is None:
            return None

        return type(self).objects.only("estado").get(pk=self.pk).estado

    class Meta:
        verbose_name = "liquidación"
        verbose_name_plural = "liquidaciones"

        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "periodo", "numero"],
                name="unique_liquidacion_por_empresa_periodo_numero",
            ),
        ]

    def clean(self):
        super().clean()

        if not self.editable():
            raise ValidationError(
                "Esta liquidación no se puede modificar."
            )

        if self.periodo.day != 1:
            raise ValidationError(
                "El periodo de liquidacion debe comenzar en el primer dia del rango."
            )

        if self.periodo and self.fecha_pago:
            validar_fechas(periodo=self.periodo, fecha_pago=self.fecha_pago)

        if self.tipo_envio == TipoEnvio.RE and self.tipo_liquidacion != "":
            raise ValidationError({
                "tipo_liquidacion": (
                    "El tipo de liquidación debe quedar vacio cuando el tipo de envío es 'RE'."
                )
            })

        if self.tipo_envio == TipoEnvio.RE and self.numero:
            raise ValidationError({
                "numero": (
                    "El numero de liquidacion no debe especificarse cuando el tipo de envío es 'RE'."
                )
            })

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.estado = self.Estado.BORRADOR
            self.domicilio_empresa = self.empresa.domicilio

            if self.tipo_envio == TipoEnvio.SJ:
                ultima = (
                    type(self).objects
                    .filter(
                        empresa=self.empresa,
                        periodo=self.periodo,
                        tipo_envio=TipoEnvio.SJ,
                    )
                    .order_by("-numero")
                    .first()
                )

                self.numero = (ultima.numero if ultima else 0) + 1
            else:
                self.numero = None
        else:
            transition = kwargs.pop("_transition", False)
            if not self.editable() and not transition:
                raise ValidationError(
                    "Esta liquidación no se puede modificar."
                )

            original = type(self).objects.get(pk=self.pk)

            if self.empresa_id != original.empresa_id:
                raise ValueError(
                    "La empresa de una liquidación no puede ser modificada."
                )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.periodo:%Y-%m} - {self.empresa}"

from django.db import models
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from concepto.models import VersionConcepto
from concepto.validation import validar_unidades
from core.models import ValidatingModel
from liquidacion.validators.v_detalles import validar_debito_credito
from liquidacion.validators.v_expresiones import validar_formula
from liquidacion.choices import UnidadesLsd, DebitoCredito


class PlantillaLiquidacion(ValidatingModel):
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


class DetallePlantillaLiquidacion(ValidatingModel):
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
        help_text="Precisión de hasta 5 decimales",
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

        try:
            plantilla = self.plantilla
        except ObjectDoesNotExist:
            plantilla = None

        try:
            concepto = self.concepto
        except ObjectDoesNotExist:
            concepto = None

        if (
            plantilla
            and concepto
            and plantilla.empresa_id != concepto.empresa_id
        ):
            raise ValidationError(
                "El concepto asociado no pertenece a la empresa de la plantilla."
            )

        if concepto:
            version = concepto.versiones.ultima()
            if version is None:
                raise ValidationError({
                    "concepto": "El concepto no tiene una versión vigente."
                })

            validar_unidades(version.unidad, self.unidades)
            validar_debito_credito(version.codigo_arca, self.debito_credito)

        if self.formula_base:
            validar_formula(self.formula_base)

    def __str__(self):
        version = (
            VersionConcepto.todos
            .filter(concepto_id=self.concepto_id)
            .ultima()
        )
        identificador = (
            version.identificador_concepto
            if version
            else f"concepto {self.concepto_id}"
        )
        return f"identificador: {identificador}"

from django.db import models, transaction
from django.db.models import OuterRef, Subquery
from django.core.validators import MinValueValidator, RegexValidator
from base_imponible.models import BaseImponible
from concepto.choices import Categoria, Tipo, Unidad
from concepto.rules import validar_tipo_categoria
from concepto.validators import validar_no_remuneracion
from core.utils import normalizar_identificador
from core.models import ValidatingModel


class ConceptoQuerySet(models.QuerySet):
    def activos(self):
        return self.filter(eliminado=False)

    def eliminados(self):
        return self.filter(eliminado=True)

    def delete(self):
        self.update(eliminado=True)

    @transaction.atomic
    def hard_delete(self):
        for concepto in self:
            VersionConcepto.todos.filter(concepto=concepto).delete()

        return super().delete()


class ConceptoManager(models.Manager.from_queryset(ConceptoQuerySet)):
    def get_queryset(self):
        return super().get_queryset().activos()


class Concepto(ValidatingModel):
    objects = ConceptoManager()
    todos = ConceptoQuerySet.as_manager()

    id = models.BigAutoField(
        primary_key=True,
    )

    empresa = models.ForeignKey(
        "empresa.Empresa",
        on_delete=models.PROTECT,
        related_name="conceptos",
    )

    eliminado = models.BooleanField(
        default=False
    )

    def save(self, *args, **kwargs):
        if self.pk is not None:
            original = type(self).objects.get(pk=self.pk)

            if self.empresa_id != original.empresa_id:
                raise ValueError(
                    "El concepto no se puede cambiar de empresa."
                )

        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        self.eliminado = True
        self.save(
            using=using,
            update_fields=["eliminado"],
        )

    @transaction.atomic
    def hard_delete(self):
        VersionConcepto.todos.filter(concepto=self).delete()
        return super().delete()

    def __str__(self):
        version = VersionConcepto.todos.filter(concepto=self).ultima()
        return version.denominacion if version else f"Concepto {self.pk}"


class VersionConceptoQuerySet(models.QuerySet):
    def activos(self):
        return self.filter(concepto__eliminado=False)

    def eliminados(self):
        return self.filter(concepto__eliminado=True)

    # aplicarse sobre un QuerySet de VersionConcepto y obtener la última de cada uno
    def ultima_version(self):
        ultima_version = (
            VersionConcepto.todos
            .filter(concepto=OuterRef("concepto"))
            .order_by("-version")
            .values("pk")[:1]
        )

        return self.filter(pk=Subquery(ultima_version))

    # dado un Concepto, obtener su última versión
    def ultima(self):
        return self.order_by("-version").first()


class VersionConceptoManager(models.Manager.from_queryset(VersionConceptoQuerySet)):
    def get_queryset(self):
        return super().get_queryset().activos()


class VersionConcepto(ValidatingModel):
    objects = VersionConceptoManager()
    todos = VersionConceptoQuerySet.as_manager()

    id = models.BigAutoField(
        primary_key=True,
    )

    concepto = models.ForeignKey(
        "concepto.Concepto",
        on_delete=models.DO_NOTHING,  # soft delete
        related_name="versiones",
    )

    bases_imponibles = models.ManyToManyField(
        BaseImponible,
        blank=True,
        related_name="versiones_concepto",
    )

    grupo = models.ForeignKey(
        "grupo_concepto.GrupoConcepto",
        on_delete=models.PROTECT,
        related_name="versiones_concepto",
        null=True,
        blank=True,
    )

    version = models.PositiveIntegerField(
        null=False,
        blank=False,
        editable=False,
        validators=[MinValueValidator(1)],
    )

    denominacion = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        validators=[validar_no_remuneracion, ]
    )

    # ARCA define el Código de concepto de sueldo ARCA como un campo alfanumérico de longitud 6
    codigo_arca = models.CharField(
        max_length=6,
        null=False,
        blank=True,
        default="",
        validators=[
            RegexValidator(
                regex=r"^[A-Za-z0-9]{6}$",
                message="El código ARCA debe contener exactamente 6 caracteres alfanuméricos.",
            ),
        ],
    )

    categoria = models.CharField(
        max_length=50,
        choices=Categoria.choices,
        null=False,
        blank=False,
    )

    tipo = models.CharField(
        max_length=50,
        choices=Tipo.choices,
        null=False,
        blank=False,
    )

    unidad = models.CharField(
        max_length=50,
        choices=Unidad.choices,
        null=False,
        blank=False,
    )

    @property
    def identificador_concepto(self):
        return f"{normalizar_identificador(self.denominacion)}_{self.concepto_id}"

    @property
    def identificador_version(self):
        return f"{normalizar_identificador(self.denominacion)}_{self.id}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["concepto", "version"],
                name="unique_version_por_concepto",
            ),
        ]
        ordering = ("-version",)

    def clean(self):
        super().clean()

        validar_tipo_categoria(tipo=self.tipo, categoria=self.categoria)

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.version = 1

            ultima_version = (
                type(self).objects.filter(concepto_id=self.concepto_id)
                .ultima()
            )

            if ultima_version:
                self.version = (ultima_version.version or 0) + 1
        else:
            raise ValueError(
                "Esta entidad no es editable."
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.denominacion}"

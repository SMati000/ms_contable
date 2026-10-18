from django.db import models
from django.db.models import OuterRef, Subquery
from django.contrib import admin
from django.core.validators import MinValueValidator
from core.utils import format_cuil
from core.validators import validar_dni, validar_cuil, no_fecha_futura, validar_cbu
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from empleado.choices import FormaPago
from empleado.rules import validar_forma_pago_cbu, validar_dni_cuil
from core.models import ValidatingModel


class Empleado(ValidatingModel):
    id = models.BigAutoField(
        primary_key=True,
    )

    empresa = models.ForeignKey(
        "empresa.Empresa",
        on_delete=models.PROTECT,
        related_name="empleados",
    )

    dni = models.CharField(
        max_length=8,
        null=False,
        blank=False,
        validators=[validar_dni],
    )

    cuil = models.CharField(
        max_length=11,
        null=False,
        blank=False,
        validators=[validar_cuil],
    )

    apellidos = models.CharField(
        max_length=255,
        null=False,
        blank=False,
    )

    nombres = models.CharField(
        max_length=255,
        null=False,
        blank=False,
    )

    legajo = models.CharField(
        max_length=50,
        null=False,
        blank=False,
    )

    fecha_ingreso = models.DateField(
        null=False,
        blank=False,
        validators=[no_fecha_futura],
    )

    @property
    @admin.display(description="Cuil")
    def cuil_display(self):
        return format_cuil(self.cuil)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "legajo"],
                name="unique_legajo_por_empresa",
            ),
            models.UniqueConstraint(
                fields=["empresa", "dni"],
                name="unique_dni_por_empresa",
            ),
        ]

    def clean(self):
        super().clean()
        validar_dni_cuil(dni=self.dni, cuil=self.cuil)

    def save(self, *args, **kwargs):
        if self.pk is not None:
            original = type(self).objects.get(pk=self.pk)

            if self.empresa_id != original.empresa_id:
                raise ValueError(
                    "El empleado no se puede cambiar de empresa."
                )

            immutable_fields = [
                "dni",
                "cuil",
                "apellidos",
                "nombres",
                "legajo",
                "fecha_ingreso",
            ]

            for field in immutable_fields:
                if getattr(self, field) != getattr(original, field):
                    raise ValueError(
                        f"El campo '{field}' de un empleado es inmutable."
                    )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.apellidos}, {self.nombres}"


class VersionEmpleadoQuerySet(models.QuerySet):
    # aplicarse sobre un QuerySet de VersionEmpleado y obtener la última de cada uno
    def ultima_version(self):
        ultima_version = (
            VersionEmpleado.todos
            .filter(empleado=OuterRef("empleado"))
            .order_by("-version")
            .values("pk")[:1]
        )

        return self.filter(pk=Subquery(ultima_version))

    # dado un Empleado, obtener su última versión
    def ultima(self):
        return self.order_by("-version").first()


class VersionEmpleadoManager(models.Manager.from_queryset(VersionEmpleadoQuerySet)):
    pass


class VersionEmpleado(ValidatingModel):
    objects = VersionEmpleadoManager()
    todos = VersionEmpleadoQuerySet.as_manager()

    id = models.BigAutoField(
        primary_key=True,
    )

    empleado = models.ForeignKey(
        "empleado.Empleado",
        on_delete=models.CASCADE,
        related_name="versiones",
    )

    version = models.PositiveIntegerField(
        null=False,
        blank=False,
        editable=False,
        validators=[MinValueValidator(1)],
    )

    conyuge = models.BooleanField(
        default=False
    )

    cantidad_hijos = models.PositiveIntegerField(
        null=False,
        blank=False,
        default=0
    )

    codigo_obra_social = models.CharField(
        max_length=6,
        null=False,
        blank=True,
    )

    categoria_laboral = models.ForeignKey(
        "categoria_laboral.CategoriaLaboral",
        on_delete=models.PROTECT,
        related_name="empleados",
    )

    dependencia_revista = models.CharField(
        max_length=255,
        null=False,
        blank=True,
    )

    banco_de_cobro = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        help_text="Ej: Nacion, Bco. Pcia. BS AS, Santander, etc",
    )

    cbu = models.CharField(
        max_length=22,
        null=False,
        blank=True,
        validators=[validar_cbu, ]
    )

    forma_de_pago = models.IntegerField(
        choices=FormaPago.choices,
        null=False,
        blank=False,
    )

    cct = models.BooleanField(
        default=False
    )

    cobertura_scvo = models.BooleanField(
        default=False
    )

    corresponde_reduccion = models.BooleanField(
        default=False
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["empleado", "version"],
                name="unique_version_por_empleado",
            ),
        ]
        ordering = ("-version",)

    def clean(self):
        super().clean()

        try:
            empleado = self.empleado
        except ObjectDoesNotExist:
            empleado = None

        try:
            categoria_laboral = self.categoria_laboral
        except ObjectDoesNotExist:
            categoria_laboral = None

        if (
            empleado
            and categoria_laboral
            and empleado.empresa_id != categoria_laboral.empresa_id
        ):
            raise ValidationError(
                "La cateogoria laboral asociada no pertenece a la misma empresa que este empleado."
            )

        validar_forma_pago_cbu(
            forma_de_pago=self.forma_de_pago,
            cbu=self.cbu,
        )

    def save(self, *args, **kwargs):
        if self.pk is None:
            ultima_version = (
                type(self).objects.filter(empleado_id=self.empleado_id)
                .ultima()
            )

            self.version = (ultima_version.version + 1 if ultima_version else 1)
        else:
            raise ValueError("Esta entidad no es editable.")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.empleado.apellidos}, {self.empleado.nombres} ({self.version})"

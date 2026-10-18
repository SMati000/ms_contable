from datetime import date
from django import forms
from django.core.exceptions import ValidationError
from categoria_laboral.models import CategoriaLaboral
from .choices import FormaPago
from .models import Empleado, VersionEmpleado
from .rules import validar_forma_pago_cbu


class ReadOnlyDateWidget(forms.TextInput):
    def format_value(self, value):
        if value is None:
            return ""

        if isinstance(value, date):
            return value.strftime("%d/%m/%Y")

        return value

    def __init__(self, attrs=None):
        attrs = attrs or {}
        attrs["class"] = "campo-no-editable"
        super().__init__(attrs)


class EmpleadoAdminForm(forms.ModelForm):
    dependencia_revista = forms.CharField(
        label="Dependencia de revista",
        max_length=VersionEmpleado._meta.get_field("dependencia_revista").max_length,
    )

    categoria_laboral = forms.ModelChoiceField(
        label="Categoría laboral",
        queryset=CategoriaLaboral.objects.none(),
    )

    conyuge = forms.BooleanField(
        label="Cónyuge",
        required=False,
    )

    cantidad_hijos = forms.IntegerField(
        label="Cantidad de hijos",
        min_value=0,
    )

    banco_de_cobro = forms.CharField(
        label="Banco de cobro",
        max_length=VersionEmpleado._meta.get_field("banco_de_cobro").max_length,
    )

    cbu = forms.CharField(
        label="CBU/CVU",
        max_length=VersionEmpleado._meta.get_field("cbu").max_length,
        validators=VersionEmpleado._meta.get_field("cbu").validators,
        required=False,
    )

    forma_de_pago = forms.ChoiceField(
        label="Forma de pago",
        choices=FormaPago.choices,
    )

    cct = forms.BooleanField(
        label="CCT",
        required=False,
    )

    cobertura_scvo = forms.BooleanField(
        label="Cobertura SCVO",
        required=False,
    )

    corresponde_reduccion = forms.BooleanField(
        label="Corresponde reducción",
        required=False,
    )

    codigo_obra_social = forms.CharField(
        label="Código de obra social",
        max_length=VersionEmpleado._meta.get_field("codigo_obra_social").max_length,
        required=False,
    )

    class Meta:
        model = Empleado
        fields = [
            "empresa",
            "dni",
            "cuil",
            "apellidos",
            "nombres",
            "legajo",
            "fecha_ingreso",
            "dependencia_revista",
            "categoria_laboral",
            "conyuge",
            "cantidad_hijos",
            "banco_de_cobro",
            "cbu",
            "forma_de_pago",
            "cct",
            "cobertura_scvo",
            "corresponde_reduccion",
            "codigo_obra_social",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["categoria_laboral"].queryset = (
            CategoriaLaboral.objects.none()
        )

        if self.instance and self.instance.pk:
            campos_inmutables = (
                "empresa",
                "dni",
                "cuil",
                "apellidos",
                "nombres",
                "legajo",
            )

            for campo in campos_inmutables:
                self.fields[campo].disabled = True
                self.fields[campo].widget.attrs["class"] = (
                    self.fields[campo].widget.attrs.get("class", "")
                    + " campo-no-editable"
                )

            self.fields["fecha_ingreso"].widget = ReadOnlyDateWidget(
                attrs={"readonly": "readonly"}
            )

            self.fields["categoria_laboral"].queryset = (
                CategoriaLaboral.objects.filter(
                    empresa=self.instance.empresa
                )
            )

            version = (
                VersionEmpleado.objects
                .filter(empleado=self.instance)
                .ultima()
            )

            if version:
                self.initial.update({
                    "dependencia_revista": version.dependencia_revista,
                    "categoria_laboral": version.categoria_laboral,
                    "conyuge": version.conyuge,
                    "cantidad_hijos": version.cantidad_hijos,
                    "banco_de_cobro": version.banco_de_cobro,
                    "cbu": version.cbu,
                    "forma_de_pago": version.forma_de_pago,
                    "cct": version.cct,
                    "cobertura_scvo": version.cobertura_scvo,
                    "corresponde_reduccion": version.corresponde_reduccion,
                    "codigo_obra_social": version.codigo_obra_social,
                })
        else:
            # Para alta, la empresa todavía puede venir del POST.
            empresa_id = self.data.get("empresa")

            if empresa_id:
                try:
                    empresa = self.fields["empresa"].clean(empresa_id)
                except ValidationError:
                    pass
                else:
                    self.fields["categoria_laboral"].queryset = (
                        CategoriaLaboral.objects.filter(empresa=empresa)
                    )

            self.initial.update({
                "cantidad_hijos": 0,
            })

    def clean(self):
        cleaned_data = super().clean()
        validar_forma_pago_cbu(
            forma_de_pago=cleaned_data.get("forma_de_pago"),
            cbu=cleaned_data.get("cbu"),
        )
        return cleaned_data

from django import forms
from django.forms.models import BaseInlineFormSet
from base_imponible.models import ResultadoBaseImponible
from core.forms import DecimalInputField
from empleado.models import Empleado
from ..models import TramoSituacionRevista
from ..models.m_liquidacion_empleado import LiquidacionEmpleado
from ..services.LiquidacionEmpleadoService import LiquidacionEmpleadoService


def _decimal_input_for(model, field_name):
    model_field = model._meta.get_field(field_name)
    return DecimalInputField(
        label=model_field.verbose_name.capitalize(),
        max_digits=model_field.max_digits,
        decimal_places=model_field.decimal_places,
        required=not model_field.blank,
    )


class LiquidacionEmpleadoForm(forms.ModelForm):
    aporte_adicional_obra_social = _decimal_input_for(
        LiquidacionEmpleado,
        "aporte_adicional_obra_social",
    )
    contrib_adicional_obra_social = _decimal_input_for(
        LiquidacionEmpleado,
        "contrib_adicional_obra_social",
    )
    base_calc_diferencial_aportes_obra_social_fsr = _decimal_input_for(
        LiquidacionEmpleado,
        "base_calc_diferencial_aportes_obra_social_fsr",
    )
    base_calc_diferencial_contrib_obra_social_fsr = _decimal_input_for(
        LiquidacionEmpleado,
        "base_calc_diferencial_contrib_obra_social_fsr",
    )
    base_calc_diferencial_ley_riesgos_trabajo = _decimal_input_for(
        LiquidacionEmpleado,
        "base_calc_diferencial_ley_riesgos_trabajo",
    )
    remuneracion_maternidad_anses = _decimal_input_for(
        LiquidacionEmpleado,
        "remuneracion_maternidad_anses",
    )
    base_calc_diferencial_aportes_seg_social = _decimal_input_for(
        LiquidacionEmpleado,
        "base_calc_diferencial_aportes_seg_social",
    )
    base_calc_diferencial_contrib_seg_social = _decimal_input_for(
        LiquidacionEmpleado,
        "base_calc_diferencial_contrib_seg_social",
    )

    class Meta:
        model = LiquidacionEmpleado
        fields = "__all__"
        widgets = {
            "observaciones_recibo": forms.Textarea(
                attrs={
                    "rows": 2,
                }
            ),
            "observaciones_lsd": forms.Textarea(
                attrs={
                    "rows": 2,
                }
            ),
        }

    class Media:
        js = ("core/js/decimal_input.js",)


class LiquidacionEmpleadoInlineForm(forms.ModelForm):
    class Meta:
        model = LiquidacionEmpleado
        fields = "__all__"

    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)

        if empresa:
            self.fields["empleado"].queryset = Empleado.objects.filter(
                empresa=empresa
            )
        else:
            self.fields["empleado"].queryset = Empleado.objects.none()

        # Una vez creado, el empleado no se puede cambiar.
        if self.instance.pk:
            self.fields["empleado"].disabled = True


class LiquidacionEmpleadoInlineFormSet(BaseInlineFormSet):

    def save_new(self, form, commit=True):
        liquidacion_empleado = super().save_new(form, commit=False,)

        LiquidacionEmpleadoService(liquidacion_empleado).crear(commit=commit)

        return liquidacion_empleado

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)

        if self.instance.empresa_id:
            kwargs["empresa"] = self.instance.empresa
        else:
            kwargs["empresa"] = None

        return kwargs


class TramoSituacionRevistaInlineForm(forms.ModelForm):
    class Meta:
        model = TramoSituacionRevista
        fields = ("codigo_situacion", "dia_inicio",)


class ImporteResultadoWidget(forms.NumberInput):
    template_name = "admin/widgets/importe_resultado.html"


class ResultadoBaseImponibleInlineForm(forms.ModelForm):
    importe = DecimalInputField(
        label="Importe",
        max_digits=ResultadoBaseImponible._meta.get_field("importe").max_digits,
        decimal_places=ResultadoBaseImponible._meta.get_field("importe").decimal_places,
        required=True,
        widget=ImporteResultadoWidget(),
    )

    class Meta:
        model = ResultadoBaseImponible
        fields = "__all__"

    class Media:
        js = ("core/js/decimal_input.js",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            self.initial["importe"] = self.instance.importe

            if self.instance.base_imponible.identificador == "detracciones":
                self.fields["importe"].widget.attrs["data_sugerencias"] = (
                    "Valores sugeridos: 7003.68 (jornada completa), "
                    "4692.47 (media jornada)"
                )
            else:
                self.fields["importe"].disabled = True
                self.fields["importe"].widget.attrs["class"] = (
                    self.fields["importe"].widget.attrs.get("class", "")
                    + " importe-no-editable"
                )

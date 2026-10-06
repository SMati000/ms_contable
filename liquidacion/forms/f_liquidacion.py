from django import forms
from liquidacion.models import Liquidacion


class LiquidacionForm(forms.ModelForm):

    class Meta:
        model = Liquidacion
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()

        empresa = cleaned_data.get("empresa") or self.instance.empresa
        periodo = cleaned_data.get("periodo")
        numero = cleaned_data.get("numero")

        if empresa and periodo and numero:
            qs = Liquidacion.objects.filter(
                empresa=empresa,
                periodo=periodo,
                numero=numero,
            )

            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise forms.ValidationError(
                    "Ya existe una liquidación para esa empresa y período con el mismo numero."
                )

        return cleaned_data

from django import forms
from liquidacion.models import Liquidacion


class LiquidacionForm(forms.ModelForm):

    class Meta:
        model = Liquidacion
        fields = "__all__"

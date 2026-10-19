from django import forms
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from decimal import Decimal


class DecimalInputField(forms.DecimalField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", forms.TextInput())
        super().__init__(*args, **kwargs)

        self.widget.attrs.setdefault("class", "decimal-input")
        self.widget.attrs.setdefault("inputmode", "decimal")
        self.widget.attrs.setdefault(
            "data-decimal-places", str(self.decimal_places or 2),
        )

    def prepare_value(self, value):
        if value is None:
            return value

        precision = max(self.decimal_places or 0, 2)
        formatted = f"{Decimal(value):.{precision}f}"

        integer, decimals = formatted.split(".")

        while len(decimals) > 2 and decimals.endswith("0"):
            decimals = decimals[:-1]

        return f"{integer}.{decimals}"


class FirstAdminAccountForm(UserCreationForm):
    remember_session = forms.BooleanField(
        required=False,
        label="Recordar sesión en este dispositivo",
    )

    class Meta(UserCreationForm.Meta):
        fields = ("username",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Usuario"
        self.fields["username"].help_text = ""
        self.fields["username"].widget.attrs.update(
            {"autofocus": True, "autocomplete": "username"}
        )
        self.fields["password1"].label = "Contraseña"
        self.fields["password1"].help_text = (
            "Usá al menos 8 caracteres y evitá una contraseña común o fácil de adivinar."
        )
        self.fields["password1"].widget.attrs.update(
            {"autocomplete": "new-password"}
        )
        self.fields["password2"].label = "Confirmar contraseña"
        self.fields["password2"].help_text = ""
        self.fields["password2"].widget.attrs.update(
            {"autocomplete": "new-password"}
        )


class RememberSessionAdminAuthenticationForm(AdminAuthenticationForm):
    remember_session = forms.BooleanField(
        required=False,
        label="Recordar sesión en este dispositivo",
    )

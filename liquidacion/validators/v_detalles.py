from django.core.exceptions import ValidationError


def validar_debito_credito(codigo_arca, debito_credito):
    if codigo_arca and not debito_credito:
        raise ValidationError({
            "debito_credito": (
                "Este campo es obligatorio para conceptos que tienen asociado "
                "un código de ARCA."
            )
        })

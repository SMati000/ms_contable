from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError

from concepto.choices import Unidad


def validar_unidades(unidad_valor, unidades):
    try:
        unidad = Unidad(unidad_valor)
    except (TypeError, ValueError):
        raise ValidationError({"concepto": "La unidad del concepto no es válida."})

    try:
        unidades = Decimal(str(unidades))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError({"unidades": "Debe ingresar un valor numérico válido."})

    if not unidades.is_finite():
        raise ValidationError({"unidades": "Debe ingresar un valor numérico finito."})

    if not unidad.constraint(unidades):
        raise ValidationError({
            "unidades": (
                f"El valor no es válido para la unidad {unidad.label}."
            )
        })

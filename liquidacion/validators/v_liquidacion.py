from django.core.exceptions import ValidationError
from datetime import date


def validar_fechas(periodo: date, fecha_pago: date):
    if fecha_pago.month == 1 and periodo.month == 12 and fecha_pago.year == (periodo.year + 1):
        return

    if fecha_pago.year == periodo.year and fecha_pago.month in (periodo.month, periodo.month + 1):
        return

    raise ValidationError({
        "fecha_pago": (
            "La fecha de pago debe estar dentro del período "
            "de la liquidación, o del siguiente."
        )
    })

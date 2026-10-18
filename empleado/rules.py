from django.core.exceptions import ValidationError
from empleado.choices import FormaPago


def validar_dni_cuil(dni, cuil):
    if not dni or not cuil:
        return

    dni = str(dni).strip()
    cuil = str(cuil).strip()
    dni_cuil = cuil[2:10]
    coincide = dni == dni_cuil or (
        len(dni) == 7
        and dni_cuil == f"0{dni}"
    )

    if not coincide:
        raise ValidationError({
            "cuil": "El CUIL no se corresponde con el DNI."
        })


def validar_forma_pago_cbu(forma_de_pago, cbu):
    try:
        forma_de_pago = int(forma_de_pago)
    except (TypeError, ValueError, OverflowError):
        raise ValidationError({
            "forma_de_pago": (
                "La Forma de Pago es inválida."
            )
        })

    if forma_de_pago == FormaPago.ACREDITACION_EN_CUENTA:
        if not cbu:
            raise ValidationError({
                "cbu": (
                    "Si la forma de pago es Acreditación en Cuenta, debe especificar el CBU/CVU."
                )
            })

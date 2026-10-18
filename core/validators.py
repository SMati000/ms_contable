from django.core.exceptions import ValidationError
from django.utils import timezone


def no_fecha_futura(value):
    if value > timezone.localdate():
        raise ValidationError("La fecha de ingreso no puede ser futura.")


def es_dni_valido(value):
    if value is None:
        return False

    value = str(value).strip()

    return (
        value.isascii()
        and value.isdigit()
        and 7 <= len(value) <= 8
    )


def validar_dni(value):
    if not es_dni_valido(value):
        raise ValidationError("El DNI debe contener entre 7 y 8 dígitos.")


def es_cuit_valido(value):
    return es_cuil_valido(value)


def validar_cuit(value):
    if not es_cuit_valido(value):
        raise ValidationError("El CUIT no es válido.")


def es_cuil_valido(value):
    if value is None:
        return False

    value = str(value).strip()

    if len(value) != 11 or not value.isascii() or not value.isdigit():
        return False

    # Los primeros 10 dígitos se utilizan para calcular el dígito verificador.
    digitos = [int(d) for d in value]

    ponderadores = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]

    suma = sum(
        digito * ponderador
        for digito, ponderador in zip(digitos[:10], ponderadores)
    )

    resto = suma % 11
    digito_verificador = 11 - resto

    if digito_verificador == 11:
        digito_verificador = 0
    elif digito_verificador == 10:
        # El CUIL no es válido con esta combinación.
        return False

    return digito_verificador == digitos[10]


def validar_cuil(value):
    if not es_cuil_valido(value):
        raise ValidationError(
            "El CUIL no es válido (ingreselo sin guiones)."
        )


def validar_cbu(cbu: str) -> None:  # tmb sirve para cvu's
    if (
        not isinstance(cbu, str)
        or len(cbu) != 22
        or not cbu.isascii()
        or not cbu.isdigit()
    ):
        raise ValidationError("El CBU no es válido.")

    if not cbu_digito_verificador_1_valido(cbu) or not cbu_digito_verificador_2_valido(cbu):
        raise ValidationError("El CBU no es válido.")


def cbu_digito_verificador_1_valido(cbu: str) -> bool:
    """
    Valida el primer dígito verificador del CBU.

    Estructura:
        posiciones 1-3: código de entidad
        posiciones 4-7: código de sucursal
        posición 8:     dígito verificador
    """
    datos = cbu[:7]
    digito_esperado = int(cbu[7])

    ponderadores = (7, 1, 3, 9, 7, 1, 3)

    suma = sum(
        int(digito) * ponderador
        for digito, ponderador in zip(datos, ponderadores)
    )

    digito_calculado = (10 - (suma % 10)) % 10

    return digito_calculado == digito_esperado


def cbu_digito_verificador_2_valido(cbu: str) -> bool:
    """
    Valida el segundo dígito verificador del CBU.

    Estructura:
        posiciones 9-21: número de cuenta
        posición 22:     dígito verificador
    """
    datos = cbu[8:21]
    digito_esperado = int(cbu[21])

    ponderadores = (3, 9, 7, 1, 3, 9, 7, 1, 3, 9, 7, 1, 3)

    suma = sum(
        int(digito) * ponderador
        for digito, ponderador in zip(datos, ponderadores)
    )

    digito_calculado = (10 - (suma % 10)) % 10

    return digito_calculado == digito_esperado

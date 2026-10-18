from decimal import Decimal, InvalidOperation

from ..exceptions import ExpresionBaseInvalida


def validar_rango_decimal_calculado(modelo, nombre_campo, valor):
    try:
        decimal = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ExpresionBaseInvalida(
            f"El resultado del campo '{nombre_campo}' no es un número válido."
        ) from error

    if not decimal.is_finite():
        raise ExpresionBaseInvalida(
            f"El resultado del campo '{nombre_campo}' no es un número finito."
        )

    campo = modelo._meta.get_field(nombre_campo)
    digitos_enteros = campo.max_digits - campo.decimal_places
    limite = Decimal("1").scaleb(digitos_enteros)

    if abs(decimal) >= limite:
        raise ExpresionBaseInvalida(
            f"El resultado del campo '{nombre_campo}' supera su rango de almacenamiento."
        )

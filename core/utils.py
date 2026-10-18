import re
import unicodedata
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN


def normalizar_identificador(texto):
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        caracter
        for caracter in texto
        if not unicodedata.combining(caracter)
    )

    texto = texto.lower()
    texto = re.sub(r"[^a-zA-Z0-9]+", "_", texto)
    texto = re.sub(r"_+", "_", texto)
    texto = texto.strip("_")

    return texto


def format_decimal_2(value):
    if value is None:
        return ""
    return f"{quantize_decimal(value, 2):.2f}"


def format_decimal_trimmed(value, max_places, min_places=2):
    if value is None:
        return None

    precision = max(max_places, min_places)
    formatted = f"{quantize_decimal(value, precision):.{precision}f}"
    integer, decimals = formatted.split(".")

    while len(decimals) > min_places and decimals.endswith("0"):
        decimals = decimals[:-1]

    return f"{integer}.{decimals}"


def quantize_decimal(value, decimal_places, rounding=ROUND_HALF_EVEN):
    try:
        decimal = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValueError("El valor debe ser un número decimal válido.") from error

    if not decimal.is_finite():
        raise ValueError("El valor debe ser un número decimal finito.")

    quantum = Decimal("1").scaleb(-decimal_places)
    try:
        return decimal.quantize(quantum, rounding=rounding)
    except InvalidOperation as error:
        raise ValueError("El valor supera la precisión decimal permitida.") from error


def format_cuil(cuil):
    digitos = re.sub(r"\D", "", cuil)

    if len(digitos) != 11 or not digitos.isascii() or not digitos.isdigit():
        raise ValueError("El CUIL debe contener 11 dígitos.")

    return f"{digitos[:2]}-{digitos[2:10]}-{digitos[10]}"

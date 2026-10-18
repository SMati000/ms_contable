from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


class FormateadorRegistroLsd:
    def __init__(self, datos):
        self.datos = datos

    @staticmethod
    def texto_alineado(valor, longitud, relleno=" ", alineacion="<"):
        if not valor:
            return relleno * longitud

        return format(valor, f"{relleno}{alineacion}{longitud}")

    @staticmethod
    def fecha_formateada(fecha, formato="%Y%m%d", valor_vacio=" " * 8):
        if fecha:
            return fecha.strftime(formato)

        return valor_vacio

    @staticmethod
    def bools_formateados(valor):
        return "1" if valor else "0"

    @staticmethod
    def numeros_con_decimales_formateados(
        valor,
        long_entero,
        long_decimal,
        longitud_cero=None,
    ):
        longitud_total = long_entero + long_decimal

        if valor is None:
            return "0" * (longitud_cero or longitud_total)

        if isinstance(valor, bool):
            raise ValueError("El valor debe ser un importe decimal válido.")

        try:
            decimal = Decimal(str(valor))
        except (InvalidOperation, TypeError, ValueError) as error:
            raise ValueError("El valor debe ser un importe decimal válido.") from error

        if not decimal.is_finite() or decimal < 0:
            raise ValueError("El valor debe ser finito y no negativo.")

        try:
            decimal = decimal.quantize(
                Decimal("1." + "0" * long_decimal),
                rounding=ROUND_HALF_UP,
            )
        except InvalidOperation as error:
            raise ValueError("El valor supera la precisión del campo.") from error

        cifras = f"{decimal:0{longitud_total + 1}}".replace(".", "")
        if len(cifras) > longitud_total:
            raise ValueError("El valor supera la longitud del campo decimal.")

        return cifras

    @staticmethod
    def formateado_como_entero(valor, longitud):
        if not valor:
            return "0" * longitud

        if isinstance(valor, str):
            return f"{valor:0>{longitud}}"

        return f"{valor:0{longitud}d}"

    @staticmethod
    def formateado_como_string(valor, longitud):
        if not valor:
            return " " * longitud

        if isinstance(valor, str):
            try:
                valor = int(valor)
            except ValueError:
                pass

        return f"{valor:<{longitud}}"

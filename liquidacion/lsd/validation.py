from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.core.exceptions import ValidationError

from core.validators import validar_cuil
from liquidacion.lsd.utils import validar_datos_obligatorios_dataclass


class ValidadorRegistroLsd:
    CODIFICACION_TXT = "cp1252"

    def __init__(self, datos):
        self.datos = datos

    def validar(self):
        if self.datos is None:
            raise ValueError("Los datos del registro son obligatorios.")

        try:
            validar_datos_obligatorios_dataclass(self.datos)
        except (AttributeError, TypeError) as error:
            raise ValueError("Los datos del registro tienen un formato inválido.") from error

        self.validar_campos()

    def validar_campos(self):
        raise NotImplementedError

    def _validar_cuil(self):
        self._validar_identificador_fiscal(
            "CUIL de los trabajadores",
            self.datos.cuil_trabajador,
        )

    @staticmethod
    def _validar_identificador_fiscal(nombre, valor):
        if not isinstance(valor, str) or len(valor) != 11:
            raise ValueError(f"{nombre.capitalize()} debe tener 11 dígitos.")

        try:
            validar_cuil(valor)
        except ValidationError as error:
            raise ValueError(f"El {nombre} no es válido.") from error

    @staticmethod
    def _validar_fecha(nombre, valor, *, obligatoria):
        if valor is None:
            if obligatoria:
                raise ValueError(f"{nombre.capitalize()} es obligatoria.")
            return

        if not isinstance(valor, date):
            raise ValueError(f"{nombre.capitalize()} debe ser una fecha válida.")

    @staticmethod
    def _validar_codificacion_ansi(nombre, valor):
        try:
            valor.encode(ValidadorRegistroLsd.CODIFICACION_TXT)
        except UnicodeEncodeError as error:
            raise ValueError(
                f"{nombre.capitalize()} contiene caracteres que no admite la codificación ANSI."
            ) from error

    @staticmethod
    def _validar_entero(nombre, valor, *, obligatoria, minimo, maximo):
        if valor is None:
            if obligatoria:
                raise ValueError(f"{nombre.capitalize()} es obligatorio.")
            return

        if isinstance(valor, bool) or not isinstance(valor, int):
            raise ValueError(f"{nombre.capitalize()} debe ser un número entero.")

        if not minimo <= valor <= maximo:
            raise ValueError(
                f"{nombre.capitalize()} debe estar entre {minimo} y {maximo}."
            )

    @staticmethod
    def _validar_decimal(
        nombre,
        valor,
        *,
        obligatoria,
        digitos_enteros,
        digitos_decimales,
        maximo=None,
    ):
        if valor is None:
            if obligatoria:
                raise ValueError(f"{nombre.capitalize()} es obligatorio.")
            return None

        if isinstance(valor, bool) or (
            isinstance(valor, str) and not valor.isascii()
        ):
            raise ValueError(f"{nombre.capitalize()} debe ser un valor numérico válido.")

        try:
            decimal = Decimal(str(valor))
        except (InvalidOperation, TypeError, ValueError) as error:
            raise ValueError(f"{nombre.capitalize()} debe ser un valor numérico válido.") from error

        if not decimal.is_finite():
            raise ValueError(f"{nombre.capitalize()} debe ser un valor finito.")

        limite = Decimal(10) ** digitos_enteros
        quantum = Decimal("1").scaleb(-digitos_decimales)
        try:
            redondeado = decimal.quantize(quantum, rounding=ROUND_HALF_UP)
        except InvalidOperation as error:
            raise ValueError(f"{nombre.capitalize()} supera la precisión permitida.") from error

        if decimal < 0 or decimal >= limite or redondeado >= limite:
            raise ValueError(
                f"{nombre.capitalize()} supera el rango de {digitos_enteros} dígitos enteros "
                f"y {digitos_decimales} decimales."
            )

        if maximo is not None and decimal > Decimal(str(maximo)):
            raise ValueError(f"{nombre.capitalize()} no puede superar {maximo}.")

        return decimal

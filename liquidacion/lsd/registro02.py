from dataclasses import dataclass
from typing import ClassVar
from datetime import date
from core.validators import validar_cbu
from empleado.choices import FormaPago
from liquidacion.lsd.formatting import FormateadorRegistroLsd
from liquidacion.lsd.validation import ValidadorRegistroLsd


@dataclass
class DatosRegistro02:
    # Obligatorios
    TIPO_REGISTRO: ClassVar[str] = "02"
    cuil_trabajador: str  # 11 enteros
    fecha_pago: date  # numerico, formato AAAAMMDD
    forma_pago: int
    # Optativos
    legajo_trabajador: str | None  # alfanumerico, longitud 10
    dependencia_revista_trabajador: str | None  # alfanumerico, longitud 50
    cbu_acreditacion_pago: str | None  # alfanumerico, longitud 22 - obligatorio cuando se indica Forma de pago = 3
    cantidad_dias_tope: int | None  # 3 enterios
    fecha_rubrica: date | None  # numerico, formato AAAAMMDD


class GeneradorRegistro02:
    """
    Datos generales de la liquidación de sueldo de cada trabajador.
    """
    def __init__(self, datos: DatosRegistro02):
        self.datos = datos
        self.validador = ValidadorRegistro02(datos)
        self.formateador = FormateadorRegistro02(datos)

    def generar(self):
        self.validador.validar()

        fecha_pago = self.datos.fecha_pago.strftime("%Y%m%d")

        resultado = (
            f"{self.datos.TIPO_REGISTRO}"
            f"{self.datos.cuil_trabajador}"
            f"{self.formateador.legajo_formateado()}"
            f"{self.formateador.dependencia_revista_trabajador_formateado()}"
            f"{self.formateador.cbu_acreditacion_pago_formateado()}"
            f"{self.formateador.cantidad_dias_tope_formateada()}"
            f"{fecha_pago}"
            f"{self.formateador.fecha_rubrica_formateada()}"
            f"{self.datos.forma_pago}"
        )

        if len(resultado) == 115:
            return resultado
        else:
            raise ValueError(
                "Error al generar Registro 02: longitud inválida.",
                len(resultado),
            )


class FormateadorRegistro02(FormateadorRegistroLsd):
    def legajo_formateado(self):
        return self.texto_alineado(
            self.datos.legajo_trabajador,
            10,
            relleno="0",
            alineacion=">",
        )

    def dependencia_revista_trabajador_formateado(self):
        return self.texto_alineado(
            self.datos.dependencia_revista_trabajador,
            50,
        )

    def cbu_acreditacion_pago_formateado(self):
        cbu_acreditacion_pago = self.datos.cbu_acreditacion_pago

        if not cbu_acreditacion_pago:
            return " " * 22

        return cbu_acreditacion_pago

    def cantidad_dias_tope_formateada(self):
        return self.formateado_como_entero(
            self.datos.cantidad_dias_tope,
            3,
        )

    def fecha_rubrica_formateada(self):
        return self.fecha_formateada(
            self.datos.fecha_rubrica,
            valor_vacio=" " * 8,
        )


class ValidadorRegistro02(ValidadorRegistroLsd):
    def validar_campos(self):
        self._validar_cuil()
        self._validar_forma_pago()
        self._validar_fechas()
        self._validar_legajo()
        self._validar_dependencia_revista()
        self._validar_cbu()
        self._validar_cantidad_dias_tope()

    def _validar_forma_pago(self):
        forma_pago = self.datos.forma_pago

        if (
            isinstance(forma_pago, bool)
            or not isinstance(forma_pago, int)
            or forma_pago not in FormaPago.values
        ):
            raise ValueError(
                f"La forma de pago {forma_pago} no es válida."
            )

    def _validar_fechas(self):
        self._validar_fecha("fecha de pago", self.datos.fecha_pago, obligatoria=True)
        self._validar_fecha("fecha de rúbrica", self.datos.fecha_rubrica, obligatoria=False)

    def _validar_legajo(self):
        legajo = self.datos.legajo_trabajador

        if legajo is None or legajo == "":
            return

        if not isinstance(legajo, str):
            raise ValueError("El legajo de los trabajadores debe ser texto.")

        self._validar_codificacion_ansi("legajo", legajo)

        max_long = 10
        if len(legajo) > max_long:
            raise ValueError(
                f"El legajo de los trabajadores no debe tener una longitud mayor a {max_long} digitos."
            )

    def _validar_dependencia_revista(self):
        dependencia_revista = self.datos.dependencia_revista_trabajador

        if dependencia_revista is None or dependencia_revista == "":
            return

        if not isinstance(dependencia_revista, str):
            raise ValueError("La dependencia de revista debe ser texto.")

        self._validar_codificacion_ansi(
            "dependencia de revista",
            dependencia_revista,
        )

        max_long = 50
        if len(dependencia_revista) > max_long:
            raise ValueError(
                f"La dependencia de revista de los trabajadores no debe "
                f"tener una longitud mayor a {max_long} digitos."
            )

    def _validar_cbu(self):
        cbu = self.datos.cbu_acreditacion_pago

        if cbu is None or cbu == "":
            if self.datos.forma_pago == FormaPago.ACREDITACION_EN_CUENTA:
                raise ValueError("El CBU es obligatorio para la forma de pago \"Acreditación en Cuenta\".")
            else:
                return

        if not isinstance(cbu, str) or not cbu.isascii() or not cbu.isdigit():
            raise ValueError("El CBU debe contener únicamente dígitos.")

        if len(cbu) != 22:
            raise ValueError("El CBU debe tener 22 dígitos.")

        validar_cbu(cbu)

    def _validar_cantidad_dias_tope(self):
        self._validar_entero(
            "cantidad de días tope",
            self.datos.cantidad_dias_tope,
            obligatoria=False,
            minimo=0,
            maximo=999,
        )

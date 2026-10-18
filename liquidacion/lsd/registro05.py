from dataclasses import dataclass
from typing import ClassVar
from decimal import Decimal
from datetime import date
from liquidacion.lsd.formatting import FormateadorRegistroLsd
from liquidacion.lsd.validation import ValidadorRegistroLsd


@dataclass
class DatosRegistro05:
    # Obligatorios
    TIPO_REGISTRO: ClassVar[str] = "05"
    cuil_trabajador: str  # 11 enteros
    categoria_profesional: str  # Longitud 6
    puesto_desempeniado: str  # Longitud 4
    fecha_ingreso: date  # Se informa en formato AAAAMMDD
    fecha_egreso: date  # Se informa en formato AAAAMMDD
    remuneracion: Decimal  # Longitud 15. 13 enteros, 2 decimales
    cuit_empleador: str  # 11 enteros


class GeneradorRegistro05:
    """
    información detallada de los trabajadores eventuales para la emisión del Libro Especial, Dec. 342/1992
    """
    def __init__(self, datos: DatosRegistro05):
        self.datos = datos
        self.validador = ValidadorRegistro05(datos)
        self.formateador = FormateadorRegistro05(datos)

    def generar(self):
        self.validador.validar()

        resultado = (
            f"{self.datos.TIPO_REGISTRO}"
            f"{self.datos.cuil_trabajador}"
            f"{self.formateador.categoria_profesional_formateada()}"
            f"{self.formateador.puesto_desempeniado_formateado()}"
            f"{self.formateador.fecha_formateada(self.datos.fecha_ingreso)}"
            f"{self.formateador.fecha_formateada(self.datos.fecha_egreso)}"
            f"{self.formateador.remuneracion_formateada()}"
            f"{self.datos.cuit_empleador}"
        )

        if len(resultado) == 65:
            return resultado

        raise ValueError(
            "Error al generar Registro 05: longitud inválida. "
            f"Longitud generada: {len(resultado)} caracteres."
        )


class FormateadorRegistro05(FormateadorRegistroLsd):
    def categoria_profesional_formateada(self):
        return self.texto_alineado(
            self.datos.categoria_profesional,
            6,
            relleno="0",
            alineacion=">",
        )

    def puesto_desempeniado_formateado(self):
        return self.texto_alineado(
            self.datos.puesto_desempeniado,
            4,
            relleno="0",
            alineacion=">",
        )

    def fecha_formateada(self, fecha: date):
        return super().fecha_formateada(
            fecha,
            valor_vacio="0" * 8,
        )

    def remuneracion_formateada(self):
        return self.numeros_con_decimales_formateados(
            self.datos.remuneracion,
            long_entero=13,
            long_decimal=2,
            longitud_cero=15,
        )


class ValidadorRegistro05(ValidadorRegistroLsd):
    def validar_campos(self):
        self._validar_cuil()
        self._validar_categoria_profesional()
        self._validar_puesto_desempeniado()
        self._validar_fechas()
        self._validar_remuneracion()

    def _validar_cuil(self):
        super()._validar_cuil()
        cuit_empl = self.datos.cuit_empleador

        self._validar_identificador_fiscal("CUIT del empleador", cuit_empl)

    def _validar_categoria_profesional(self):
        categoria_profesional = self.datos.categoria_profesional

        if (
            not isinstance(categoria_profesional, str)
            or not categoria_profesional.isascii()
            or not categoria_profesional.isdigit()
            or len(categoria_profesional) > 6
        ):
            raise ValueError(
                "La categoría profesional debe contener hasta 6 dígitos."
            )

    def _validar_puesto_desempeniado(self):
        puesto_desempeniado = self.datos.puesto_desempeniado

        if (
            not isinstance(puesto_desempeniado, str)
            or not puesto_desempeniado.isascii()
            or not puesto_desempeniado.isdigit()
            or len(puesto_desempeniado) > 4
        ):
            raise ValueError(
                "El puesto desempeñado debe contener hasta 4 dígitos."
            )

    def _validar_fechas(self):
        fecha_ingreso = self.datos.fecha_ingreso
        fecha_egreso = self.datos.fecha_egreso

        self._validar_fecha("fecha de ingreso", fecha_ingreso, obligatoria=True)
        self._validar_fecha("fecha de egreso", fecha_egreso, obligatoria=True)

        if fecha_egreso < fecha_ingreso:
            raise ValueError(
                "La fecha de ingreso no puede ser posterior a la de egreso."
            )

    def _validar_remuneracion(self):
        self.datos.remuneracion = self._validar_decimal(
            "remuneración",
            self.datos.remuneracion,
            obligatoria=True,
            digitos_enteros=13,
            digitos_decimales=2,
        )

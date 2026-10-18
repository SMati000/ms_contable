from dataclasses import dataclass
from typing import ClassVar
from enum import IntEnum

from liquidacion.lsd.validation import ValidadorRegistroLsd
from liquidacion.lsd.formatting import FormateadorRegistroLsd


@dataclass
class DatosRegistro06:
    # Obligatorios
    TIPO_REGISTRO: ClassVar[str] = "06"
    # id_liquidacion: str  # Longitud 15 - Omitido. Ver docs/specs_externas/txt_lsd.md#Observación sobre Registro 06
    cuil_trabajador: str  # 11 enteros
    observaciones: str  # Longitud 80


class GeneradorRegistro06:
    """
    Campo de Observaciones: Es un campo opcional a completar con información que resulte útil para el empleador.
    """
    def __init__(self, datos: DatosRegistro06):
        self.datos = datos
        self.validador = ValidadorRegistro06(datos)
        self.formateador = FormateadorRegistro06(datos)

    def generar(self):
        self.validador.validar()

        resultado = (
            f"{self.datos.TIPO_REGISTRO}"
            f"{self.datos.cuil_trabajador}"
            f"{self.formateador.observaciones_formateadas()}"
        )

        if len(resultado) == 93:  # 108 si se incluye id_liquidacion
            return resultado
        else:
            raise ValueError(
                f"Error al generar Registro 06: longitud inválida.",
                len(resultado),
                resultado
            )


class FormateadorRegistro06(FormateadorRegistroLsd):
    def observaciones_formateadas(self):
        return self.texto_alineado(
            self.datos.observaciones,
            80,
            relleno="0",
            alineacion=">",
        )


class ValidadorRegistro06(ValidadorRegistroLsd):
    def validar_campos(self):
        self._validar_cuil()
        # self._validar_id_liquidacion()
        self._validar_observaciones()

    # def _validar_id_liquidacion(self):
    #     id_liquidacion = self.datos.id_liquidacion
    #
    #     max_long = 15
    #     if len(id_liquidacion) > max_long:
    #         raise Exception(
    #             f"El id de liquidacion no debe tener una longitud mayor a {max_long} digitos."
    #         )
    #
    #     try:
    #         int(id_liquidacion)
    #     except ValueError:
    #         raise Exception(
    #             "El id de liquidacion debe ser numerico."
    #         )

    def _validar_observaciones(self):
        observaciones = self.datos.observaciones

        if not isinstance(observaciones, str):
            raise ValueError("El campo observaciones debe ser texto.")

        self._validar_codificacion_ansi("observaciones", observaciones)

        max_long = 80
        if len(observaciones) > max_long:
            raise ValueError(
                f"Las observaciones no deben tener una longitud mayor a {max_long} digitos."
            )

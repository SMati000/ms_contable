from dataclasses import dataclass
from typing import ClassVar
from datetime import date
from liquidacion.choices import TipoLiquidacion, TipoEnvio
from liquidacion.lsd.formatting import FormateadorRegistroLsd
from liquidacion.lsd.validation import ValidadorRegistroLsd


@dataclass
class DatosRegistro01:
    # Obligatorios
    TIPO_REGISTRO: ClassVar[str] = "01"
    DIAS_BASE: ClassVar[str] = "30"
    cuit_empleador: str  # 11 enteros
    tipo_envio: str
    periodo_liquidacion: date  # periodo de la liquidacion de SyJ o de la DJ. Se informa en formato AAAAMM
    """
    Si tipo_envio='SJ', es el numero de liquidacion de SyJ del empleador. De existir liquidaciones ya ingresadas para 
      el período, el número de liquidación debe ser mayor al número de las ya ingresadas.
    Si tipo_envio='RE', queda en blanco
    """
    cantidad_trabajadores: int  # cantidad de trabajadores informados en registro 04. Se informa en fomrato 6 enteros
    # Optativos
    numero_liquidacion: int | None
    tipo_liquidacion: str | None


class GeneradorRegistro01:
    """
    Datos referenciales de la liquidacion.
    """
    def __init__(self, datos: DatosRegistro01):
        self.datos = datos
        self.validador = ValidadorRegistro01(datos)
        self.formateador = FormateadorRegistro01(datos)

    def generar(self):
        self.validador.validar()

        resultado = (
            f"{self.datos.TIPO_REGISTRO}"
            f"{self.datos.cuit_empleador}"
            f"{self.datos.tipo_envio}"
            f"{self.formateador.periodo_liquidacion_formateado()}"
            f"{self.formateador.tipo_liquidacion_formateado()}"
            f"{self.formateador.numero_liquidacion_formateado()}"
            f"{self.datos.DIAS_BASE}"
            f"{self.formateador.cantidad_trabajadores_formateada()}"
        )

        if len(resultado) == 35:
            return resultado
        else:
            raise ValueError(
                "Error al generar Registro 01: longitud inválida.",
                len(resultado),
                resultado
            )


class FormateadorRegistro01(FormateadorRegistroLsd):
    def periodo_liquidacion_formateado(self):
        return self.fecha_formateada(
            self.datos.periodo_liquidacion,
            "%Y%m",
        )

    def tipo_liquidacion_formateado(self):
        tipo_liquidacion = self.datos.tipo_liquidacion

        return self.texto_alineado(tipo_liquidacion, 1)

    def numero_liquidacion_formateado(self):
        numero_liquidacion = self.datos.numero_liquidacion

        return self.formateado_como_entero(numero_liquidacion, 5)

    def cantidad_trabajadores_formateada(self):
        return self.formateado_como_entero(
            self.datos.cantidad_trabajadores,
            6,
        )


class ValidadorRegistro01(ValidadorRegistroLsd):
    def validar_campos(self):
        self._validar_cuit()
        self._validar_tipos()
        self._validar_periodo()
        self._validar_numero_liquidacion()
        self._validar_cantidad_trabajadores()

    def _validar_cuit(self):
        cuit = self.datos.cuit_empleador

        self._validar_identificador_fiscal("CUIT del empleador", cuit)

    def _validar_tipos(self):
        tipo_envio = self.datos.tipo_envio
        tipo_liq = self.datos.tipo_liquidacion

        if not isinstance(tipo_envio, str) or tipo_envio not in TipoEnvio.values:
            raise ValueError(
                f"El tipo de envío {tipo_envio} no es válido."
            )

        if tipo_liq is not None and not isinstance(tipo_liq, str):
            raise ValueError("El tipo de liquidación debe ser texto.")

        if tipo_envio == TipoEnvio.RE:
            if tipo_liq:
                raise ValueError(
                    "El tipo de liquidación debe quedar vacío cuando el tipo de envío es RE."
                )
        elif tipo_envio == TipoEnvio.SJ:
            if not tipo_liq:
                raise ValueError(
                    "El tipo de liquidación es obligatorio cuando el tipo de envío es SJ."
                )

            if tipo_liq not in TipoLiquidacion.values:
                raise ValueError(
                    f"El tipo de liquidación {tipo_liq} no es válido."
                )

    def _validar_periodo(self):
        periodo = self.datos.periodo_liquidacion
        self._validar_fecha("período de liquidación", periodo, obligatoria=True)

        if periodo.day != 1:
            raise ValueError(
                "El período de liquidación debe comenzar el primer día del mes."
            )

    def _validar_numero_liquidacion(self):
        tipo_envio = self.datos.tipo_envio
        numero_liq = self.datos.numero_liquidacion

        if tipo_envio == TipoEnvio.RE:
            if numero_liq is not None:
                self._validar_entero(
                    "número de liquidación",
                    numero_liq,
                    obligatoria=True,
                    minimo=0,
                    maximo=0,
                )

        elif tipo_envio == TipoEnvio.SJ:
            self._validar_entero(
                "número de liquidación",
                numero_liq,
                obligatoria=True,
                minimo=1,
                maximo=99999,
            )

    def _validar_cantidad_trabajadores(self):
        self._validar_entero(
            "cantidad de trabajadores",
            self.datos.cantidad_trabajadores,
            obligatoria=True,
            minimo=0,
            maximo=999999,
        )

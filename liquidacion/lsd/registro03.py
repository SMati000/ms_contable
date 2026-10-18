from dataclasses import dataclass
from typing import ClassVar
from datetime import date
from decimal import Decimal
from liquidacion.choices import UnidadesLsd, DebitoCredito
from liquidacion.lsd.formatting import FormateadorRegistroLsd
from liquidacion.lsd.validation import ValidadorRegistroLsd


CODIGOS_ARCA_QUE_REQUIEREN_CANTIDAD = {
    "123000",
    "130000",
    "130001",
    "130002",
    "130003",
    "150000",
}


@dataclass
class DatosRegistro03:
    # Obligatorios
    TIPO_REGISTRO: ClassVar[str] = "03"
    cuil_trabajador: str  # 11 enteros
    codigo_arca_concepto: str  # alfanumerico, longitud 10
    debito_credito: str
    # Optativos
    cantidad: Decimal | None  # Longitud 5: 3 enteros y 2 decimales
    unidades: str | None
    importe: Decimal | None  # Longitud 15: 13 enteros y 2 decimales
    periodo_ajuste_retractivo: date | None  # formato AAAAMM
    """
    Para los conceptos liquidados del período informado en el registro 1, este valor se informa en 0. 
    Si hace referencia a una liquidación retroactiva del concepto, 
    se debe informar el periodo. Este dato es solo informativo
    """


class GeneradorRegistro03:
    """
    Detalle de los conceptos de sueldo liquidados a cada trabajador.
    """
    def __init__(self, datos: DatosRegistro03):
        self.datos = datos
        self.validador = ValidadorRegistro03(datos)
        self.formateador = FormateadorRegistro03(datos)

    def generar(self):
        self.validador.validar()

        resultado = (
            f"{self.datos.TIPO_REGISTRO}"
            f"{self.datos.cuil_trabajador}"
            f"{self.formateador.codigo_arca_concepto_formateado()}"
            f"{self.formateador.cantidad_formateada()}"
            f"{self.formateador.unidades_formateada()}"
            f"{self.formateador.importe_formateado()}"
            f"{self.datos.debito_credito}"
            f"{self.formateador.periodo_ajuste_retractivo_formateado()}"
        )

        if len(resultado) == 51:
            return resultado
        else:
            raise ValueError(
                "Error al generar Registro 03: longitud inválida.",
                len(resultado),
                resultado
            )


class FormateadorRegistro03(FormateadorRegistroLsd):
    def codigo_arca_concepto_formateado(self):
        return self.texto_alineado(
            self.datos.codigo_arca_concepto,
            10,
        )

    def cantidad_formateada(self):
        return self.numeros_con_decimales_formateados(
            self.datos.cantidad,
            long_entero=3,
            long_decimal=2,
            longitud_cero=5,
        )

    def unidades_formateada(self):
        return self.texto_alineado(self.datos.unidades, 1)

    def importe_formateado(self):
        return self.numeros_con_decimales_formateados(
            self.datos.importe,
            long_entero=13,
            long_decimal=2,
        )

    def periodo_ajuste_retractivo_formateado(self):
        return self.fecha_formateada(
            self.datos.periodo_ajuste_retractivo,
            "%Y%m",
            " " * 6,
        )


class ValidadorRegistro03(ValidadorRegistroLsd):
    def validar_campos(self):
        self._validar_cuil()
        self._validar_codigo_arca_concepto()
        self._validar_cantidad()
        self._validar_unidades()
        self._validar_importe()
        self._validar_debito_credito()

    def _validar_codigo_arca_concepto(self):
        codigo_arca_concepto = self.datos.codigo_arca_concepto

        if not isinstance(codigo_arca_concepto, str) or not codigo_arca_concepto:
            raise ValueError("El código ARCA del concepto es obligatorio.")

        max_long = 10
        if len(codigo_arca_concepto) > max_long:
            raise ValueError(
                f"El codigo del concepto no debe tener una longitud mayor a {max_long} digitos."
            )

    def _validar_cantidad(self):
        cantidad = self._validar_decimal(
            "cantidad",
            self.datos.cantidad,
            obligatoria=False,
            digitos_enteros=3,
            digitos_decimales=2,
        )
        self.datos.cantidad = cantidad

        if cantidad is None:
            if self.datos.codigo_arca_concepto in CODIGOS_ARCA_QUE_REQUIEREN_CANTIDAD:
                raise ValueError(
                    "La cantidad es obligatoria para este código ARCA."
                )
            return

    def _validar_unidades(self):
        unidades = self.datos.unidades

        if unidades is None or unidades == "":
            return

        if not isinstance(unidades, str) or unidades not in UnidadesLsd.values:
            raise ValueError(
                f"La unidad {unidades} no es válida."
            )

    def _validar_importe(self):
        importe = self._validar_decimal(
            "importe",
            self.datos.importe,
            obligatoria=False,
            digitos_enteros=13,
            digitos_decimales=2,
        )
        self.datos.importe = importe

    def _validar_debito_credito(self):
        debito_credito = self.datos.debito_credito

        if debito_credito not in DebitoCredito.values:
            raise ValueError(
                f"El valor {debito_credito} no es válido."
            )

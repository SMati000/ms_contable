from django.db.models import Prefetch

from base_imponible.models import ResultadoBaseImponible
from liquidacion.choices import TipoEnvio
from liquidacion.lsd.registro01 import GeneradorRegistro01, DatosRegistro01
from liquidacion.lsd.registro02 import GeneradorRegistro02, DatosRegistro02
from liquidacion.lsd.registro03 import GeneradorRegistro03, DatosRegistro03
from liquidacion.lsd.registro04 import GeneradorRegistro04, DatosRegistro04
from liquidacion.lsd.registro05 import GeneradorRegistro05, DatosRegistro05
from liquidacion.lsd.registro06 import GeneradorRegistro06, DatosRegistro06
from liquidacion.lsd.mappers import (Registro01Mapper, Registro02Mapper, Registro03Mapper,
                                     Registro04Mapper, Registro06Mapper)
from liquidacion.models import Liquidacion, LiquidacionEmpleado, DetalleLiquidacion


class LsdTxtArcaService:
    """
    Archivo de texto con extensión “.txt” y formato de codificación “ANSI”
    Cada tipo de registro debe venir informado en una línea, uno debajo del otro
    Tipos de registro permitidos:
    - Registros tipo 01: Obligatorio. Para informar datos referenciales de la liquidación en el archivo a ingresar
    - Registros tipo 02: Cuando identificacion de envio='SJ'. Con datos generales de la liquidación de sueldo
      de cada trabajador
    - Registros tipo 03: Cuando identificacion de envio='SJ'. Es el detalle de los conceptos de sueldo liquidados a
      cada trabajador
    - Registros tipo 04: Obligatorio. Atributos de la relación laboral de cada trabajador para la determinación de
      las deudas con el SUSS
    - Registros tipo 05: Opcional. Información detallada de los trabajadores eventuales para la emisión del
      Libro Especial, Dec. 342/1992
    - Registros tipo 06 - Opcional. Campo de Observaciones: Es un campo opcional a completar con información que
      resulte útil para el empleador.
    """
    def __init__(self, liquidacion_pk: str):
        self.liquidacion_pk = liquidacion_pk

    def generar(self):  # TODO - registro 05 para trabajadores eventuales
        liquidacion = self._cargar_datos()

        registro01: DatosRegistro01 = Registro01Mapper.obtener_datos(liquidacion)

        lineas = [
            GeneradorRegistro01(registro01).generar(),
        ]

        if liquidacion.tipo_envio == TipoEnvio.SJ:
            registro02: list[DatosRegistro02] = Registro02Mapper.obtener_datos(liquidacion)
            for registro in registro02:
                lineas.append(GeneradorRegistro02(registro).generar())

            registro03: list[DatosRegistro03] = Registro03Mapper.obtener_datos(liquidacion)
            for registro in registro03:
                lineas.append(GeneradorRegistro03(registro).generar())

        registro04: list[DatosRegistro04] = Registro04Mapper.obtener_datos(liquidacion)
        for registro in registro04:
            lineas.append(GeneradorRegistro04(registro).generar())

        registro06: list[DatosRegistro06] = Registro06Mapper.obtener_datos(liquidacion)
        for registro in registro06:
            lineas.append(GeneradorRegistro06(registro).generar())

        return "\r\n".join(lineas) + "\r\n"

    def _cargar_datos(self):  # TODO - desacoplar la carga de datos de los mappers.
        return (
            Liquidacion.objects
            .select_related("empresa")
            .prefetch_related(
                Prefetch(
                    "empleados",
                    queryset=(
                        LiquidacionEmpleado.objects
                        .select_related(
                            "empleado",
                            "version_empleado",
                        )
                        .prefetch_related(
                            "situaciones_revista",
                            Prefetch(
                                "detalles",
                                queryset=(
                                    DetalleLiquidacion.objects
                                    .select_related(
                                        "concepto",
                                        "concepto__grupo",
                                    )
                                ),
                            ),
                            Prefetch(
                                "resultados_bases_imponibles",
                                queryset=(
                                    ResultadoBaseImponible.objects
                                    .select_related("base_imponible")
                                ),
                            ),
                        )
                    ),
                )
            )
            .get(pk=self.liquidacion_pk)
        )

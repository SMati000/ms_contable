from django.db.models import Prefetch

from base_imponible.models import ResultadoBaseImponible
from liquidacion.choices import TipoEnvio
from liquidacion.lsd.registro01 import GeneradorRegistro01
from liquidacion.lsd.registro02 import GeneradorRegistro02
from liquidacion.lsd.registro03 import GeneradorRegistro03
from liquidacion.lsd.registro04 import GeneradorRegistro04
from liquidacion.lsd.registro06 import GeneradorRegistro06
from liquidacion.lsd.mappers import (Registro01Mapper, Registro02Mapper, Registro03Mapper,
                                     Registro04Mapper, Registro06Mapper)
from liquidacion.lsd.exceptions import ErroresGeneracionLsd
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
        try:
            liquidacion = self._cargar_datos()
        except Exception as error:
            raise ErroresGeneracionLsd([
                f"No se pudieron cargar los datos de la liquidación: {self._detalle_error(error)}"
            ]) from error

        lineas = []
        errores = []

        registro01 = self._capturar(
            "Cabecera de la liquidación (registro 01)",
            lambda: GeneradorRegistro01(
                Registro01Mapper.obtener_datos(liquidacion)
            ).generar(),
            errores,
        )
        if registro01 is not None:
            lineas.append(registro01)

        if liquidacion.tipo_envio == TipoEnvio.SJ:
            self._agregar_registros(
                "registro 02",
                Registro02Mapper.obtener_datos,
                GeneradorRegistro02,
                liquidacion,
                lineas,
                errores,
            )
            self._agregar_registros(
                "registro 03",
                Registro03Mapper.obtener_datos,
                GeneradorRegistro03,
                liquidacion,
                lineas,
                errores,
                incluir_codigo_concepto=True,
            )

        self._agregar_registros(
            "registro 04",
            Registro04Mapper.obtener_datos,
            GeneradorRegistro04,
            liquidacion,
            lineas,
            errores,
        )
        self._agregar_registros(
            "registro 06",
            Registro06Mapper.obtener_datos,
            GeneradorRegistro06,
            liquidacion,
            lineas,
            errores,
        )

        if errores:
            raise ErroresGeneracionLsd(errores)

        return "\r\n".join(lineas)

    def _agregar_registros(
        self,
        nombre_registro,
        obtener_datos,
        generador,
        liquidacion,
        lineas,
        errores,
        incluir_codigo_concepto=False,
    ):
        registros = self._capturar(
            f"No se pudieron preparar los datos del {nombre_registro}",
            lambda: obtener_datos(liquidacion),
            errores,
        )
        if registros is None:
            return

        for registro in registros:
            contexto = f"{nombre_registro.capitalize()}, CUIL {registro.cuil_trabajador}"
            if incluir_codigo_concepto:
                contexto += f", concepto ARCA {registro.codigo_arca_concepto.strip()}"

            linea = self._capturar(
                contexto,
                lambda registro=registro: generador(registro).generar(),
                errores,
            )
            if linea is not None:
                lineas.append(linea)

    @staticmethod
    def _capturar(contexto, operacion, errores):
        try:
            return operacion()
        except Exception as error:
            errores.append(f"{contexto}: {LsdTxtArcaService._detalle_error(error)}")
            return None

    @staticmethod
    def _detalle_error(error):
        mensajes_validacion = getattr(error, "messages", None)
        if mensajes_validacion:
            return "; ".join(mensajes_validacion)

        if (
            len(error.args) > 1
            and isinstance(error.args[0], str)
            and error.args[0].startswith("Error al generar Registro")
        ):
            return f"{error.args[0]} Longitud generada: {error.args[1]} caracteres."
        return str(error)

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

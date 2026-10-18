from liquidacion.models.m_liquidacion_empleado import LiquidacionEmpleado
from liquidacion.lsd.registro01 import DatosRegistro01
from liquidacion.lsd.registro02 import DatosRegistro02
from liquidacion.lsd.registro03 import DatosRegistro03
from liquidacion.lsd.registro04 import DatosRegistro04
from liquidacion.lsd.registro06 import DatosRegistro06
from liquidacion.models import Liquidacion


IDENTIFICADORES_BASES_LSD = tuple(
    [f"remuneracion_{numero}" for numero in range(1, 11)] + ["detracciones"]
)

"""
Consideraciones generales:
- Los campos definidos como alfanuméricos deben informarse con espacios a la derecha hasta completar la longitud indicada
- Los campos definidos como numéricos deben informarse con ceros (0) a la izquierda hasta completar la longitud indicada
- Los campos definidos como decimales deben informarse sin separador decimal. Se consideran las dos últimas posiciones 
  del valor informado como los centavos del número.
"""


class Registro01Mapper:
    liquidacion_select_related = ("empresa",)

    @staticmethod
    def obtener_datos(liquidacion: Liquidacion) -> DatosRegistro01:
        return DatosRegistro01(
            cuit_empleador=liquidacion.empresa.cuit,
            tipo_envio=liquidacion.tipo_envio,
            periodo_liquidacion=liquidacion.periodo,
            cantidad_trabajadores=len(liquidacion.empleados.all()),
            numero_liquidacion=liquidacion.numero,
            tipo_liquidacion=liquidacion.tipo_liquidacion
        )


class Registro02Mapper:
    empleado_select_related = ("empleado", "version_empleado")

    @staticmethod
    def obtener_datos(liquidacion: Liquidacion) -> list[DatosRegistro02]:
        registros = []

        for le in liquidacion.empleados.all():
            registros.append(
                DatosRegistro02(
                    cuil_trabajador=le.empleado.cuil,
                    fecha_pago=liquidacion.fecha_pago,
                    forma_pago=le.version_empleado.forma_de_pago,
                    legajo_trabajador=le.empleado.legajo,
                    dependencia_revista_trabajador=le.version_empleado.dependencia_revista,
                    cbu_acreditacion_pago=le.version_empleado.cbu,
                    cantidad_dias_tope=le.cantidad_dias_proporcionar_tope,
                    fecha_rubrica=le.fecha_rubrica,
                )
            )

        return registros


class Registro03Mapper:
    empleado_select_related = ("empleado",)
    detalle_select_related = ("concepto", "concepto__grupo")

    @staticmethod
    def obtener_datos(liquidacion: Liquidacion) -> list[DatosRegistro03]:
        registros = {}

        for le in liquidacion.empleados.all():
            for detalle in le.detalles.all():
                if not detalle.concepto.codigo_arca:
                    continue

                key = (le.empleado.cuil, detalle.concepto.codigo_arca, )

                registro = registros.get(key)

                if registro is None:
                    registros[key] = Registro03Mapper._crear_registro(le, detalle)
                    continue

                Registro03Mapper._validar_compatibilidad(registro, le, detalle)
                registro.importe += detalle.importe

        return list(registros.values())

    @staticmethod
    def _crear_registro(le, detalle) -> DatosRegistro03:
        return DatosRegistro03(
            cuil_trabajador=le.empleado.cuil,
            codigo_arca_concepto=detalle.concepto.codigo_arca,
            cantidad=detalle.cantidad,
            unidades=detalle.unidades_lsd,
            importe=detalle.importe,
            debito_credito=detalle.debito_credito,
            periodo_ajuste_retractivo=detalle.periodo_ajuste_retroactivo,
        )

    @staticmethod
    def _validar_compatibilidad(
        registro: DatosRegistro03,
        le: LiquidacionEmpleado,
        detalle,
    ) -> None:
        if (
            registro.cantidad != detalle.cantidad
            or registro.unidades != detalle.unidades_lsd
            or registro.debito_credito != detalle.debito_credito
            or registro.periodo_ajuste_retractivo != detalle.periodo_ajuste_retroactivo
        ):
            raise ValueError(
                f"El empleado con CUIL {le.empleado.cuil} tiene más de un detalle "
                f"para el concepto ARCA {detalle.concepto.codigo_arca} con datos "
                "incompatibles; solo puede variar el importe."
            )


class Registro04Mapper:
    empleado_select_related = ("empleado", "version_empleado")
    empleado_prefetch_related = ("situaciones_revista",)
    resultado_select_related = ("base_imponible",)

    @staticmethod
    def obtener_datos(liquidacion: Liquidacion) -> list[DatosRegistro04]:
        registros = []

        for le in liquidacion.empleados.all():
            version = le.version_empleado

            bases = {
                resultado.base_imponible.identificador: resultado.importe
                for resultado in le.resultados_bases_imponibles.all()
            }
            bases_faltantes = [
                identificador
                for identificador in IDENTIFICADORES_BASES_LSD
                if identificador not in bases
            ]
            if bases_faltantes:
                raise ValueError(
                    f"El empleado con CUIL {le.empleado.cuil} no tiene resultados "
                    "para las siguientes bases imponibles requeridas: "
                    f"{', '.join(bases_faltantes)}."
                )

            tramos = sorted(
                le.situaciones_revista.all(),
                key=lambda tramo: tramo.dia_inicio,
            )

            tramo_1 = tramos[0] if len(tramos) > 0 else None
            tramo_2 = tramos[1] if len(tramos) > 1 else None
            tramo_3 = tramos[2] if len(tramos) > 2 else None

            registros.append(
                DatosRegistro04(
                    cuil_trabajador=le.empleado.cuil,
                    tipo_empleador=liquidacion.empresa.tipo_empleador,

                    codigo_situacion_revista=le.codigo_situacion,
                    codigo_condicion=le.codigo_condicion,
                    codigo_actividad=le.codigo_actividad,
                    codigo_modalidad_contratacion=le.codigo_modalidad_contratacion,
                    codigo_siniestrado=le.codigo_siniestrado,
                    codigo_localidad=le.codigo_localidad,

                    codigo_situacion_revista_1=tramo_1.codigo_situacion if tramo_1 else None,
                    dia_inicio_situacion_revista_1=tramo_1.dia_inicio if tramo_1 else None,

                    codigo_obra_social=version.codigo_obra_social,

                    remuneracion_bruta=le.bruto,

                    base_imponible_1=bases["remuneracion_1"],  # TODO - mejorar
                    base_imponible_2=bases["remuneracion_2"],
                    base_imponible_3=bases["remuneracion_3"],
                    base_imponible_4=bases["remuneracion_4"],
                    base_imponible_5=bases["remuneracion_5"],
                    base_imponible_6=bases["remuneracion_6"],
                    base_imponible_7=bases["remuneracion_7"],
                    base_imponible_8=bases["remuneracion_8"],
                    base_imponible_9=bases["remuneracion_9"],
                    base_imponible_10=bases["remuneracion_10"],

                    detracciones=bases["detracciones"],

                    conyuge=version.conyuge,
                    marca_cct=version.cct,
                    marca_scvo=version.cobertura_scvo,
                    marca_reduccion=version.corresponde_reduccion,

                    cantidad_hijos=version.cantidad_hijos,

                    codigo_situacion_revista_2=tramo_2.codigo_situacion if tramo_2 else None,
                    dia_inicio_situacion_revista_2=tramo_2.dia_inicio if tramo_2 else None,

                    codigo_situacion_revista_3=tramo_3.codigo_situacion if tramo_3 else None,
                    dia_inicio_situacion_revista_3=tramo_3.dia_inicio if tramo_3 else None,

                    cantidad_dias_trabajados=(
                        le.tiempo_trabajado
                        if le.unidad_tiempo_trabajado == LiquidacionEmpleado.UnidadTiempoTrabajado.D
                        else None
                    ),
                    cantidad_horas_trabajadas=(
                        le.tiempo_trabajado
                        if le.unidad_tiempo_trabajado == LiquidacionEmpleado.UnidadTiempoTrabajado.H
                        else None
                    ),

                    porcentaje_aporte_adicional_seg_social=(
                        le.porcentaje_aporte_adicional_ss
                    ),
                    porcentaje_contrib_tarea_diferencial=(
                        le.porcentaje_contrib_tarea_diferencial
                    ),
                    cantidad_adherentes_obra_social=(
                        le.cantidad_adherentes_obra_social
                    ),
                    aporte_adicional_obra_social=(
                        le.aporte_adicional_obra_social
                    ),
                    contrib_adicional_obra_social=(
                        le.contrib_adicional_obra_social
                    ),
                    base_calc_diferencial_aportes_obra_social_fsr=(
                        le.base_calc_diferencial_aportes_obra_social_fsr
                    ),
                    base_calc_diferencial_contrib_obra_social_fsr=(
                        le.base_calc_diferencial_contrib_obra_social_fsr
                    ),
                    base_calc_diferencial_ley_riesgos_trabajo=(
                        le.base_calc_diferencial_ley_riesgos_trabajo
                    ),
                    remuneracion_maternidad_anses=(
                        le.remuneracion_maternidad_anses
                    ),
                    base_calc_diferencial_aportes_seg_social=(
                        le.base_calc_diferencial_aportes_seg_social
                    ),
                    base_calc_diferencial_contrib_seg_social=(
                        le.base_calc_diferencial_contrib_seg_social
                    ),
                )
            )

        return registros


class Registro06Mapper:
    empleado_select_related = ("empleado",)

    @staticmethod
    def obtener_datos(liquidacion: Liquidacion) -> list[DatosRegistro06]:
        registros = []

        for le in liquidacion.empleados.all():
            if le.observaciones_lsd:
                registros.append(
                    DatosRegistro06(
                        cuil_trabajador=le.empleado.cuil,
                        observaciones=le.observaciones_lsd
                    )
                )

        return registros

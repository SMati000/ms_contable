from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.http import JsonResponse

from ..models.m_liquidacion_empleado import LiquidacionEmpleado


def liquidacion_previa_view(request, liquidacion_empleado_id):
    actual = LiquidacionEmpleado.objects.get(pk=liquidacion_empleado_id)

    liq_previa = (
        LiquidacionEmpleado.objects
        .filter(
            empleado=actual.empleado,
            liquidacion__empresa=actual.liquidacion.empresa,
        )
        .filter(
            Q(
                liquidacion__periodo__lt=actual.liquidacion.periodo,
            )
            | Q(
                liquidacion__periodo=actual.liquidacion.periodo,
                liquidacion__numero__lt=actual.liquidacion.numero,
            )
        )
        .order_by(
            "-liquidacion__periodo",
            "-liquidacion__numero",
        )
        .first()
    )

    if not liq_previa:
        return JsonResponse(
            {"liq_previa": None},
            encoder=DjangoJSONEncoder,
        )

    resultado_detracciones = (
        liq_previa.resultados_bases_imponibles
        .filter(base_imponible__identificador="detracciones")
        .values_list("importe", flat=True)
        .first()
    )

    datos = {
        "cantidad_dias_proporcionar_tope": liq_previa.cantidad_dias_proporcionar_tope,
        "unidad_tiempo_trabajado": liq_previa.unidad_tiempo_trabajado,
        "tiempo_trabajado": liq_previa.tiempo_trabajado,

        "tramos_situacion_revista": list(
            liq_previa.situaciones_revista
            .order_by("dia_inicio")
            .values("codigo_situacion", "dia_inicio")
        ),
        "detracciones": resultado_detracciones,

        "codigo_situacion": liq_previa.codigo_situacion,
        "codigo_condicion": liq_previa.codigo_condicion,
        "codigo_actividad": liq_previa.codigo_actividad,
        "codigo_modalidad_contratacion": liq_previa.codigo_modalidad_contratacion,
        "codigo_siniestrado": liq_previa.codigo_siniestrado,
        "codigo_localidad": liq_previa.codigo_localidad,

        "porcentaje_aporte_adicional_ss": liq_previa.porcentaje_aporte_adicional_ss,
        "porcentaje_contrib_tarea_diferencial": liq_previa.porcentaje_contrib_tarea_diferencial,
        "remuneracion_maternidad_anses": liq_previa.remuneracion_maternidad_anses,

        "cantidad_adherentes_obra_social": liq_previa.cantidad_adherentes_obra_social,
        "aporte_adicional_obra_social": liq_previa.aporte_adicional_obra_social,
        "contrib_adicional_obra_social": liq_previa.contrib_adicional_obra_social,

        "base_calc_diferencial_aportes_obra_social_fsr": liq_previa.base_calc_diferencial_aportes_obra_social_fsr,
        "base_calc_diferencial_contrib_obra_social_fsr": liq_previa.base_calc_diferencial_contrib_obra_social_fsr,
        "base_calc_diferencial_ley_riesgos_trabajo": liq_previa.base_calc_diferencial_ley_riesgos_trabajo,
        "base_calc_diferencial_aportes_seg_social": liq_previa.base_calc_diferencial_aportes_seg_social,
        "base_calc_diferencial_contrib_seg_social": liq_previa.base_calc_diferencial_contrib_seg_social,

        "observaciones_recibo": liq_previa.observaciones_recibo,
        "observaciones_lsd": liq_previa.observaciones_lsd,
    }

    return JsonResponse({"liq_previa": datos})

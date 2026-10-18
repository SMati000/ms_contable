from django.db.models import Prefetch

from base_imponible.models import ResultadoBaseImponible
from liquidacion.models import DetalleLiquidacion, Liquidacion, LiquidacionEmpleado
from liquidacion.lsd.mappers import (
    Registro01Mapper,
    Registro02Mapper,
    Registro03Mapper,
    Registro04Mapper,
    Registro06Mapper,
)


MAPPERS_LSD = (
    Registro01Mapper,
    Registro02Mapper,
    Registro03Mapper,
    Registro04Mapper,
    Registro06Mapper,
)


def _relaciones_requeridas(atributo):
    return tuple(sorted({
        relacion
        for mapper in MAPPERS_LSD
        for relacion in getattr(mapper, atributo, ())
    }))


def obtener_liquidacion_para_exportar(liquidacion_pk):
    detalle_queryset = DetalleLiquidacion.objects
    detalle_relaciones = _relaciones_requeridas("detalle_select_related")
    if detalle_relaciones:
        detalle_queryset = detalle_queryset.select_related(*detalle_relaciones)

    resultado_queryset = ResultadoBaseImponible.objects
    resultado_relaciones = _relaciones_requeridas("resultado_select_related")
    if resultado_relaciones:
        resultado_queryset = resultado_queryset.select_related(*resultado_relaciones)

    empleados = LiquidacionEmpleado.objects
    empleado_relaciones = _relaciones_requeridas("empleado_select_related")
    if empleado_relaciones:
        empleados = empleados.select_related(*empleado_relaciones)

    prefetch_empleados = _relaciones_requeridas("empleado_prefetch_related")
    if prefetch_empleados:
        empleados = empleados.prefetch_related(*prefetch_empleados)

    empleados = empleados.prefetch_related(
        Prefetch("detalles", queryset=detalle_queryset),
        Prefetch("resultados_bases_imponibles", queryset=resultado_queryset),
    )

    liquidaciones = Liquidacion.objects
    liquidacion_relaciones = _relaciones_requeridas("liquidacion_select_related")
    if liquidacion_relaciones:
        liquidaciones = liquidaciones.select_related(*liquidacion_relaciones)

    return liquidaciones.prefetch_related(
        Prefetch("empleados", queryset=empleados),
    ).get(pk=liquidacion_pk)

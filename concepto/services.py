from .models import VersionConcepto
from django.db import transaction
from liquidacion.models import DetalleLiquidacion, Liquidacion
from plantilla_liquidacion.models import DetallePlantillaLiquidacion
from .exceptions import ConceptoEnUsoEnLiquidacionAbierta


@transaction.atomic
def eliminar_concepto(concepto):
    if DetalleLiquidacion.objects.filter(
        concepto__concepto=concepto,
        liquidacion_empleado__liquidacion__estado=Liquidacion.Estado.BORRADOR,
    ).exists():
        raise ConceptoEnUsoEnLiquidacionAbierta()

    DetallePlantillaLiquidacion.objects.filter(
        concepto=concepto,
    ).delete()

    concepto.delete()


def actualizar_concepto(
    concepto,
    *,
    denominacion,
    codigo_arca,
    categoria,
    tipo,
    unidad,
    grupo,
    bases_imponibles,
):
    version_actual = (
        VersionConcepto.objects
        .filter(concepto=concepto)
        .order_by("-version")
        .first()
    )

    if version_actual is None:
        return crear_version_concepto(
            concepto,
            denominacion=denominacion,
            codigo_arca=codigo_arca,
            categoria=categoria,
            tipo=tipo,
            unidad=unidad,
            grupo=grupo,
            bases_imponibles=bases_imponibles,
        )

    cambios = (
        version_actual.denominacion != denominacion
        or version_actual.codigo_arca != codigo_arca
        or version_actual.categoria != categoria
        or version_actual.tipo != tipo
        or version_actual.unidad != unidad
        or version_actual.grupo_id != (grupo.id if grupo else None)
        or set(version_actual.bases_imponibles.values_list("id", flat=True))
           != {base.id for base in bases_imponibles}
    )

    if not cambios:
        return version_actual

    return crear_version_concepto(
        concepto,
        denominacion=denominacion,
        codigo_arca=codigo_arca,
        categoria=categoria,
        tipo=tipo,
        unidad=unidad,
        grupo=grupo,
        bases_imponibles=bases_imponibles,
    )


def crear_version_concepto(
    concepto,
    *,
    denominacion,
    codigo_arca,
    categoria,
    tipo,
    unidad,
    grupo,
    bases_imponibles,
):
    ultima_version = (
        VersionConcepto.objects
        .filter(concepto=concepto)
        .order_by("-version")
        .first()
    )

    siguiente_version = (
        ultima_version.version + 1
        if ultima_version
        else 1
    )

    version = VersionConcepto(
        concepto=concepto,
        version=siguiente_version,
        denominacion=denominacion,
        codigo_arca=codigo_arca,
        categoria=categoria,
        tipo=tipo,
        unidad=unidad,
        grupo=grupo,
    )

    version.save()

    version.bases_imponibles.set(bases_imponibles)

    return version

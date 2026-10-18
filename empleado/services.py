from .models import VersionEmpleado
from django.db import transaction


@transaction.atomic
def actualizar_empleado(
    empleado,
    *,
    dependencia_revista,
    categoria_laboral,
    conyuge,
    cantidad_hijos,
    banco_de_cobro,
    cbu,
    forma_de_pago,
    cct,
    cobertura_scvo,
    corresponde_reduccion,
    codigo_obra_social,
):
    version_actual = (
        VersionEmpleado.objects
        .filter(empleado=empleado)
        .order_by("-version")
        .first()
    )

    if version_actual is None:
        return crear_version_empleado(
            empleado,
            dependencia_revista=dependencia_revista,
            categoria_laboral=categoria_laboral,
            conyuge=conyuge,
            cantidad_hijos=cantidad_hijos,
            banco_de_cobro=banco_de_cobro,
            cbu=cbu,
            forma_de_pago=forma_de_pago,
            cct=cct,
            cobertura_scvo=cobertura_scvo,
            corresponde_reduccion=corresponde_reduccion,
            codigo_obra_social=codigo_obra_social,
        )

    cambios = (
        version_actual.dependencia_revista != dependencia_revista
        or version_actual.categoria_laboral_id != categoria_laboral.id
        or version_actual.conyuge != conyuge
        or version_actual.cantidad_hijos != cantidad_hijos
        or version_actual.banco_de_cobro != banco_de_cobro
        or version_actual.cbu != cbu
        or version_actual.forma_de_pago != int(forma_de_pago)
        or version_actual.cct != cct
        or version_actual.cobertura_scvo != cobertura_scvo
        or version_actual.corresponde_reduccion != corresponde_reduccion
        or version_actual.codigo_obra_social != codigo_obra_social
    )

    if not cambios:
        return version_actual

    return crear_version_empleado(
        empleado,
        dependencia_revista=dependencia_revista,
        categoria_laboral=categoria_laboral,
        conyuge=conyuge,
        cantidad_hijos=cantidad_hijos,
        banco_de_cobro=banco_de_cobro,
        cbu=cbu,
        forma_de_pago=forma_de_pago,
        cct=cct,
        cobertura_scvo=cobertura_scvo,
        corresponde_reduccion=corresponde_reduccion,
        codigo_obra_social=codigo_obra_social,
    )


def crear_version_empleado(
    empleado,
    *,
    dependencia_revista,
    categoria_laboral,
    conyuge,
    cantidad_hijos,
    banco_de_cobro,
    cbu,
    forma_de_pago,
    cct,
    cobertura_scvo,
    corresponde_reduccion,
    codigo_obra_social,
):
    ultima_version = (
        VersionEmpleado.objects
        .filter(empleado=empleado)
        .order_by("-version")
        .first()
    )

    siguiente_version = (ultima_version.version + 1 if ultima_version else 1)

    version = VersionEmpleado(
        empleado=empleado,
        version=siguiente_version,
        dependencia_revista=dependencia_revista,
        categoria_laboral=categoria_laboral,
        conyuge=conyuge,
        cantidad_hijos=cantidad_hijos,
        banco_de_cobro=banco_de_cobro,
        cbu=cbu,
        forma_de_pago=forma_de_pago,
        cct=cct,
        cobertura_scvo=cobertura_scvo,
        corresponde_reduccion=corresponde_reduccion,
        codigo_obra_social=codigo_obra_social,
    )

    version.save()

    return version

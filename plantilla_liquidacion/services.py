import re
from django.core.exceptions import ValidationError
from django.db import transaction
from concepto.models import Concepto, VersionConcepto
from .models import DetallePlantillaLiquidacion, PlantillaLiquidacion


@transaction.atomic
def agregar_conceptos_faltantes(plantilla):
    conceptos_existentes = set(
        plantilla.detalles.values_list("concepto_id", flat=True)
    )
    conceptos = (
        Concepto.objects
        .filter(empresa=plantilla.empresa)
        .exclude(pk__in=conceptos_existentes)
    )

    detalles = []
    omitidos = 0
    for concepto in conceptos:
        detalle = DetallePlantillaLiquidacion(
            plantilla=plantilla,
            concepto=concepto,
            unidades=1,
            formula_base="0",
        )
        try:
            detalle.full_clean(
                validate_unique=False,
                validate_constraints=False,
            )
        except ValidationError:
            omitidos += 1
        else:
            detalles.append(detalle)

    DetallePlantillaLiquidacion.objects.bulk_create(detalles)
    return len(detalles), omitidos


@transaction.atomic
def duplicar_plantilla(plantilla):
    detalles = [
        DetallePlantillaLiquidacion(
            plantilla=plantilla,
            concepto=detalle.concepto,
            unidades=detalle.unidades,
            formula_base=detalle.formula_base,
            cantidad=detalle.cantidad,
            unidades_lsd=detalle.unidades_lsd,
            debito_credito=detalle.debito_credito,
            periodo_ajuste_retroactivo=detalle.periodo_ajuste_retroactivo,
        )
        for detalle in plantilla.detalles.select_related("concepto")
    ]

    for detalle in detalles:
        detalle.full_clean(
            validate_unique=False,
            validate_constraints=False,
        )

    copia = PlantillaLiquidacion.objects.create(
        empresa=plantilla.empresa,
        denominacion=_denominacion_duplicada(plantilla),
    )
    for detalle in detalles:
        detalle.plantilla = copia

    DetallePlantillaLiquidacion.objects.bulk_create(detalles)
    return copia


def _denominacion_duplicada(plantilla):
    base = f"{plantilla.denominacion} (copia)"
    denominaciones = set(
        PlantillaLiquidacion.objects
        .filter(
            empresa=plantilla.empresa,
            denominacion__startswith=base,
        )
        .values_list("denominacion", flat=True)
    )

    if base not in denominaciones:
        return base

    numero = 2
    while f"{base} {numero}" in denominaciones:
        numero += 1

    return f"{base}".replace("copia", f"copia {numero}")


class PlantillaLiquidacionService:
    IDENTIFICADOR_CONCEPTO_RE = re.compile(r"\b(?P<denominacion>[a-zA-Z_][a-zA-Z0-9_]*)_(?P<id>\d+)\b")

    def __init__(self, empresa):
        self.empresa = empresa

        versiones = (
            VersionConcepto.objects
            .filter(concepto__empresa=empresa)
            .ultima_version()
        )

        self._versiones = {version.concepto_id: version.identificador_version for version in versiones}

    def reemplazar_identificadores_formula(self, formula):
        def reemplazar(match):
            denominacion = match.group("denominacion")
            concepto_id = int(match.group("id"))

            if denominacion == "remuneracion":  # no es un concepto, es una base imponible. Los conceptos no pueden tener ese identificador
                return match.string

            if concepto_id not in self._versiones.keys():
                raise ValueError(
                    f"Concepto inexistente: {denominacion}_{concepto_id}"
                )

            return self._versiones.get(concepto_id)

        return self.IDENTIFICADOR_CONCEPTO_RE.sub(reemplazar, formula)

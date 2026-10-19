from dataclasses import fields
import typing


ETIQUETAS_CAMPOS_LSD = {
    "cuit_empleador": "CUIT del empleador",
    "cuil_trabajador": "CUIL del trabajador",
    "periodo_liquidacion": "período de liquidación",
    "cantidad_trabajadores": "cantidad de trabajadores",
    "fecha_pago": "fecha de pago",
    "forma_pago": "forma de pago",
    "codigo_situacion_revista": "código de situación de revista",
    "codigo_condicion": "código de condición",
    "codigo_actividad": "código de actividad",
    "codigo_modalidad_contratacion": "código de modalidad de contratación",
    "codigo_siniestrado": "código de siniestrado",
    "codigo_localidad": "código de localidad",
    "codigo_obra_social": "código de obra social",
    "remuneracion_bruta": "remuneración bruta",
}


def validar_datos_obligatorios_dataclass(datos):
    obligatorios_faltantes = datos_obligatorios_faltantes_dataclass(datos)

    if obligatorios_faltantes:
        registro = getattr(datos, "TIPO_REGISTRO", "")
        campos = ", ".join(
            ETIQUETAS_CAMPOS_LSD.get(campo, campo.replace("_", " "))
            for campo in obligatorios_faltantes
        )
        raise ValueError(
            f"Faltan datos obligatorios del registro {registro}: {campos}."
        )


def datos_obligatorios_faltantes_dataclass(datos):
    """
    Valida que los campos obligatorios de una dataclass estén presentes.
    """
    faltantes = []
    hints = typing.get_type_hints(type(datos))

    for f in fields(datos):
        valor = getattr(datos, f.name)
        tipo = hints[f.name]
        es_opcional = type(None) in typing.get_args(tipo)

        if valor is None and not es_opcional:
            faltantes.append(f.name)

    return faltantes

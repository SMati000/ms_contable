from decimal import Decimal

from empresa.choices import TipoEmpleador
from liquidacion.lsd.registro04 import DatosRegistro04


def datos_registro04(**kwargs):
    datos = {
        "cuil_trabajador": "33693450239",
        "tipo_empleador": TipoEmpleador.ADMINISTRACION_PUBLICA,
        "codigo_situacion_revista": "1",
        "codigo_condicion": "1",
        "codigo_actividad": "1",
        "codigo_modalidad_contratacion": "1",
        "codigo_siniestrado": "0",
        "codigo_localidad": "1",
        "codigo_situacion_revista_1": "1",
        "dia_inicio_situacion_revista_1": 1,
        "codigo_obra_social": "123456",
        "remuneracion_bruta": Decimal("564893.13"),
        "base_imponible_1": Decimal("2315.21"),
        "base_imponible_2": Decimal("12.2"),
        "base_imponible_3": Decimal("751354.01"),
        "base_imponible_4": Decimal("1234567891234.21"),
        "base_imponible_5": Decimal("2135"),
        "base_imponible_6": Decimal("1"),
        "base_imponible_7": Decimal("12"),
        "base_imponible_8": Decimal("3215"),
        "base_imponible_9": Decimal("21.25"),
        "base_imponible_10": Decimal("2153"),
        "detracciones": Decimal("7003.87"),
        "conyuge": False,
        "marca_cct": False,
        "marca_scvo": False,
        "marca_reduccion": False,
        "cantidad_hijos": None,
        "codigo_situacion_revista_2": None,
        "dia_inicio_situacion_revista_2": None,
        "codigo_situacion_revista_3": None,
        "dia_inicio_situacion_revista_3": None,
        "cantidad_dias_trabajados": 30,
        "cantidad_horas_trabajadas": None,
        "porcentaje_aporte_adicional_seg_social": None,
        "porcentaje_contrib_tarea_diferencial": None,
        "cantidad_adherentes_obra_social": None,
        "aporte_adicional_obra_social": None,
        "contrib_adicional_obra_social": None,
        "base_calc_diferencial_aportes_obra_social_fsr": None,
        "base_calc_diferencial_contrib_obra_social_fsr": None,
        "base_calc_diferencial_ley_riesgos_trabajo": None,
        "remuneracion_maternidad_anses": None,
        "base_calc_diferencial_aportes_seg_social": None,
        "base_calc_diferencial_contrib_seg_social": None,
    }
    datos.update(kwargs)
    return DatosRegistro04(**datos)

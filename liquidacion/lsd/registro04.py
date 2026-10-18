from dataclasses import dataclass
from typing import ClassVar
from decimal import Decimal

from empresa.choices import TipoEmpleador
from liquidacion.lsd.formatting import FormateadorRegistroLsd
from liquidacion.lsd.validation import ValidadorRegistroLsd


@dataclass
class DatosRegistro04:
    # Obligatorios
    TIPO_REGISTRO: ClassVar[str] = "04"
    CODIGO_TIPO_OPERACION: ClassVar[bool] = False
    cuil_trabajador: str  # 11 enteros
    tipo_empleador: str
    codigo_situacion_revista: str  # Longitud 2
    codigo_condicion: str  # Longitud 2
    codigo_actividad: str  # Longitud 3
    codigo_modalidad_contratacion: str  # Longitud 3
    codigo_siniestrado: str  # Longitud 2
    codigo_localidad: str  # Longitud 2
    codigo_obra_social: str  # Longitud 6
    remuneracion_bruta: Decimal  # Longitud 15. 13 enteros, 2 decimales
    base_imponible_1: Decimal  # Longitud 15. 13 enteros, 2 decimales
    base_imponible_2: Decimal  # Longitud 15. 13 enteros, 2 decimales
    base_imponible_3: Decimal  # Longitud 15. 13 enteros, 2 decimales
    base_imponible_4: Decimal  # Longitud 15. 13 enteros, 2 decimales
    base_imponible_5: Decimal  # Longitud 15. 13 enteros, 2 decimales
    base_imponible_6: Decimal  # Longitud 15. 13 enteros, 2 decimales
    base_imponible_7: Decimal  # Longitud 15. 13 enteros, 2 decimales
    base_imponible_8: Decimal  # Longitud 15. 13 enteros, 2 decimales
    base_imponible_9: Decimal  # Longitud 15. 13 enteros, 2 decimales
    base_imponible_10: Decimal  # Longitud 15. 13 enteros, 2 decimales
    detracciones: Decimal  # Longitud 15. 13 enteros, 2 decimales
    codigo_situacion_revista_1: str | None  # Longitud 2
    dia_inicio_situacion_revista_1: int | None  # Longitud 2
    conyuge: bool | None
    marca_cct: bool | None
    marca_scvo: bool | None
    marca_reduccion: bool | None
    # Optativos
    cantidad_hijos: int | None  # Longitud 2
    codigo_situacion_revista_2: str | None # Longitud 2
    dia_inicio_situacion_revista_2: int | None  # Longitud 2
    codigo_situacion_revista_3: str | None  # Longitud 2
    dia_inicio_situacion_revista_3: int | None  # Longitud 2
    cantidad_dias_trabajados: int | None  # Longitud 2. Excluyente con cantidad_horas_trabajadas
    cantidad_horas_trabajadas: int | None  # Longitud 3. Excluyente con cantidad_dias_trabajados
    porcentaje_aporte_adicional_seg_social: Decimal | None  # Longitud 5. 3 enteros, 2 decimales
    porcentaje_contrib_tarea_diferencial: Decimal | None  # Longitud 5. 3 enteros, 2 decimales
    cantidad_adherentes_obra_social: int | None  # Longitud 2
    aporte_adicional_obra_social: Decimal | None  # Longitud 15. 13 enteros, 2 decimales
    contrib_adicional_obra_social: Decimal | None  # Longitud 15. 13 enteros, 2 decimales
    base_calc_diferencial_aportes_obra_social_fsr: Decimal | None  # Longitud 15. 13 enteros, 2 decimales
    base_calc_diferencial_contrib_obra_social_fsr: Decimal | None  # Longitud 15. 13 enteros, 2 decimales
    base_calc_diferencial_ley_riesgos_trabajo: Decimal | None  # Longitud 15. 13 enteros, 2 decimales
    remuneracion_maternidad_anses: Decimal | None  # Longitud 15. 13 enteros, 2 decimales
    base_calc_diferencial_aportes_seg_social: Decimal | None  # Longitud 15. 13 enteros, 2 decimales
    base_calc_diferencial_contrib_seg_social: Decimal | None  # Longitud 15. 13 enteros, 2 decimales


class GeneradorRegistro04:
    """
    Atributos de la relación laboral de cada trabajador para la determinación de las deudas con el SUSS.
    """
    def __init__(self, datos: DatosRegistro04):
        self.datos = datos
        self.validador = ValidadorRegistro04(datos)
        self.formateador = FormateadorRegistro04(datos)

    def generar(self):
        self.validador.validar()

        resultado = (
            f"{self.datos.TIPO_REGISTRO}"
            f"{self.datos.cuil_trabajador}"
            f"{self.formateador.bools_formateados(self.datos.conyuge)}"
            f"{self.formateador.formateado_como_entero(self.datos.cantidad_hijos, 2)}"
            f"{self.formateador.bools_formateados(self.datos.marca_cct)}"
            f"{self.formateador.bools_formateados(self.datos.marca_scvo)}"
            f"{self.formateador.bools_formateados(self.datos.marca_reduccion)}"
            f"{self.datos.tipo_empleador}"
            f"{self.formateador.bools_formateados(self.datos.CODIGO_TIPO_OPERACION)}"
            f"{self.formateador.formateado_como_entero(self.datos.codigo_situacion_revista, 2)}"
            f"{self.formateador.formateado_como_string(self.datos.codigo_condicion, 2)}"
            f"{self.formateador.formateado_como_entero(self.datos.codigo_actividad, 3)}"
            f"{self.formateador.formateado_como_string(self.datos.codigo_modalidad_contratacion, 3)}"
            f"{self.formateador.formateado_como_string(self.datos.codigo_siniestrado, 2)}"
            f"{self.formateador.formateado_como_entero(self.datos.codigo_localidad, 2)}"
            f"{self.formateador.formateado_como_entero(self.datos.codigo_situacion_revista_1, 2)}"
            f"{self.formateador.formateado_como_entero(self.datos.dia_inicio_situacion_revista_1, 2)}"
            f"{self.formateador.formateado_como_entero(self.datos.codigo_situacion_revista_2, 2)}"
            f"{self.formateador.formateado_como_entero(self.datos.dia_inicio_situacion_revista_2, 2)}"
            f"{self.formateador.formateado_como_entero(self.datos.codigo_situacion_revista_3, 2)}"
            f"{self.formateador.formateado_como_entero(self.datos.dia_inicio_situacion_revista_3, 2)}"
            f"{self.formateador.formateado_como_entero(self.datos.cantidad_dias_trabajados, 2)}"
            f"{self.formateador.formateado_como_entero(self.datos.cantidad_horas_trabajadas, 3)}"
            f"{self.formateador.numeros_con_decimales_formateados(self.datos.porcentaje_aporte_adicional_seg_social, 3, 2)}"
            f"{self.formateador.numeros_con_decimales_formateados(self.datos.porcentaje_contrib_tarea_diferencial, 3, 2)}"
            f"{self.formateador.formateado_como_entero(self.datos.codigo_obra_social, 6)}"
            f"{self.formateador.formateado_como_entero(self.datos.cantidad_adherentes_obra_social, 2)}"
            f"{self.formateador.numeros_con_decimales_formateados(self.datos.aporte_adicional_obra_social, 13, 2)}"
            f"{self.formateador.numeros_con_decimales_formateados(self.datos.contrib_adicional_obra_social, 13, 2)}"
            f"{self.formateador.numeros_con_decimales_formateados(self.datos.base_calc_diferencial_aportes_obra_social_fsr, 13, 2)}"
            f"{self.formateador.numeros_con_decimales_formateados(self.datos.base_calc_diferencial_contrib_obra_social_fsr, 13, 2)}"
            f"{self.formateador.numeros_con_decimales_formateados(self.datos.base_calc_diferencial_ley_riesgos_trabajo, 13, 2)}"
            f"{self.formateador.numeros_con_decimales_formateados(self.datos.remuneracion_maternidad_anses, 13, 2)}"            
            f"{self.formateador.numeros_con_decimales_formateados(self.datos.remuneracion_bruta, 13, 2)}"            
            f"{self.formateador.numeros_con_decimales_formateados(self.datos.base_imponible_1, 13, 2)}"            
            f"{self.formateador.numeros_con_decimales_formateados(self.datos.base_imponible_2, 13, 2)}"            
            f"{self.formateador.numeros_con_decimales_formateados(self.datos.base_imponible_3, 13, 2)}"            
            f"{self.formateador.numeros_con_decimales_formateados(self.datos.base_imponible_4, 13, 2)}"            
            f"{self.formateador.numeros_con_decimales_formateados(self.datos.base_imponible_5, 13, 2)}"            
            f"{self.formateador.numeros_con_decimales_formateados(self.datos.base_imponible_6, 13, 2)}"            
            f"{self.formateador.numeros_con_decimales_formateados(self.datos.base_imponible_7, 13, 2)}"            
            f"{self.formateador.numeros_con_decimales_formateados(self.datos.base_imponible_8, 13, 2)}"            
            f"{self.formateador.numeros_con_decimales_formateados(self.datos.base_imponible_9, 13, 2)}"
            f"{self.formateador.numeros_con_decimales_formateados(self.datos.base_calc_diferencial_aportes_seg_social, 13, 2)}"
            f"{self.formateador.numeros_con_decimales_formateados(self.datos.base_calc_diferencial_contrib_seg_social, 13, 2)}"       
            f"{self.formateador.numeros_con_decimales_formateados(self.datos.base_imponible_10, 13, 2)}"            
            f"{self.formateador.numeros_con_decimales_formateados(self.datos.detracciones, 13, 2)}"
        )

        if len(resultado) == 370:
            return resultado
        else:
            raise ValueError(
                f"Error al generar Registro 04: longitud inválida.",
                len(resultado),
                resultado
            )


class FormateadorRegistro04(FormateadorRegistroLsd):
    pass

class ValidadorRegistro04(ValidadorRegistroLsd):
    def validar_campos(self):
        self._validar_cuil()
        self._validar_tipo_empleador()
        self._validar_codigos_longitud()
        self._validar_booleanos()
        self._validar_numeros_decimales()
        self._validar_dia_inicio_situaciones_revista()
        self._validar_cantidad_hijos()
        self._validar_tiempo_trabajado()
        self._validar_cantidad_adherentes_obra_social()

    def _validar_tipo_empleador(self):
        tipo_empleador = self.datos.tipo_empleador

        if not isinstance(tipo_empleador, str) or tipo_empleador not in TipoEmpleador.values:
            raise ValueError(
                f"El tipo de empleador {tipo_empleador} no es válido."
            )

    def _validar_codigos_longitud(self):
        codigos = [
            ("codigo_situacion_revista", "Código de situación de revista", True, 2),
            ("codigo_condicion", "Código de condición", True, 2),
            ("codigo_actividad", "Código de actividad", True, 3),
            ("codigo_modalidad_contratacion", "Código de modalidad de contratación", True, 3),
            ("codigo_siniestrado", "Código de siniestrado", True, 2),
            ("codigo_localidad", "Código de localidad", True, 2),
            ("codigo_situacion_revista_1", "Código de situación de revista 1", False, 2),
            ("codigo_obra_social", "Código de obra social", True, 6),
            ("codigo_situacion_revista_2", "Código de situación de revista 2", False, 2),
            ("codigo_situacion_revista_3", "Código de situación de revista 3", False, 2),
        ]

        for campo, nombre, obligatorio, max_long in codigos:
            valor = getattr(self.datos, campo)
            if valor is None or valor == "":
                if obligatorio:
                    raise ValueError(
                        f"{nombre} es obligatorio."
                    )
                else:
                    continue

            if not isinstance(valor, str):
                raise ValueError(f"{nombre} debe ser texto.")

            if len(valor) > max_long:
                raise ValueError(
                    f"{nombre} no debe tener una longitud mayor a {max_long} digitos."
                )

            if not valor.isascii() or not valor.isdigit():
                raise ValueError(f"{nombre} debe contener únicamente dígitos ASCII.")

    def _validar_numeros_decimales(self):
        numeros_decimales = [
            ("remuneracion_bruta", "Remuneración bruta", True, 13, 2, None),
            ("base_imponible_1", "Base imponible 1", True, 13, 2, None),
            ("base_imponible_2", "Base imponible 2", True, 13, 2, None),
            ("base_imponible_3", "Base imponible 3", True, 13, 2, None),
            ("base_imponible_4", "Base imponible 4", True, 13, 2, None),
            ("base_imponible_5", "Base imponible 5", True, 13, 2, None),
            ("base_imponible_6", "Base imponible 6", True, 13, 2, None),
            ("base_imponible_7", "Base imponible 7", True, 13, 2, None),
            ("base_imponible_8", "Base imponible 8", True, 13, 2, None),
            ("base_imponible_9", "Base imponible 9", True, 13, 2, None),
            ("base_imponible_10", "Base imponible 10", True, 13, 2, None),
            ("detracciones", "Detracciones", True, 13, 2, None),
            ("porcentaje_aporte_adicional_seg_social", "Porcentaje de aporte adicional de seguridad social", False, 3, 2, 100),
            ("porcentaje_contrib_tarea_diferencial", "Porcentaje de contribución por tarea diferencial", False, 3, 2, 100),
            ("aporte_adicional_obra_social", "Aporte adicional de obra social", False, 13, 2, None),
            ("contrib_adicional_obra_social", "Contribución adicional de obra social", False, 13, 2, None),
            ("base_calc_diferencial_aportes_obra_social_fsr", "Base diferencial de aporte de obra social y FSR", False, 13, 2, None),
            ("base_calc_diferencial_contrib_obra_social_fsr", "Base diferencial de contribución de obra social y FSR", False, 13, 2, None),
            ("base_calc_diferencial_ley_riesgos_trabajo", "Base diferencial de Ley de Riesgos del Trabajo", False, 13, 2, None),
            ("remuneracion_maternidad_anses", "Remuneración por maternidad ANSeS", False, 13, 2, None),
            ("base_calc_diferencial_aportes_seg_social", "Base diferencial de aporte de seguridad social", False, 13, 2, None),
            ("base_calc_diferencial_contrib_seg_social", "Base diferencial de contribución de seguridad social", False, 13, 2, None),
        ]

        for campo, nombre, obligatorio, enteros, decimales, maximo in numeros_decimales:
            valor = self._validar_decimal(
                nombre,
                getattr(self.datos, campo),
                obligatoria=obligatorio,
                digitos_enteros=enteros,
                digitos_decimales=decimales,
                maximo=maximo,
            )
            setattr(self.datos, campo, valor)

    def _validar_booleanos(self):
        for campo in ("conyuge", "marca_cct", "marca_scvo", "marca_reduccion"):
            valor = getattr(self.datos, campo)
            if valor is not None and not isinstance(valor, bool):
                raise ValueError(f"{campo.replace('_', ' ').capitalize()} debe ser booleano.")

    def _validar_dia_inicio_situaciones_revista(self):
        for numero in (1, 2, 3):
            codigo = getattr(self.datos, f"codigo_situacion_revista_{numero}")
            campo_dia = f"dia_inicio_situacion_revista_{numero}"
            dia = getattr(self.datos, campo_dia)
            tiene_codigo = isinstance(codigo, str) and bool(codigo)

            if tiene_codigo != (dia is not None):
                raise ValueError(
                    f"El código y el día de inicio de la situación de revista {numero} deben informarse juntos."
                )

            self._validar_entero(
                f"día de inicio de situación de revista {numero}",
                dia,
                obligatoria=False,
                minimo=1,
                maximo=31,
            )

    def _validar_cantidad_hijos(self):
        self._validar_entero(
            "cantidad de hijos",
            self.datos.cantidad_hijos,
            obligatoria=False,
            minimo=0,
            maximo=99,
        )

    def _validar_tiempo_trabajado(self):
        dias = self.datos.cantidad_dias_trabajados
        horas = self.datos.cantidad_horas_trabajadas
        self._validar_entero(
            "cantidad de días trabajados",
            dias,
            obligatoria=False,
            minimo=0,
            maximo=99,
        )
        self._validar_entero(
            "cantidad de horas trabajadas",
            horas,
            obligatoria=False,
            minimo=0,
            maximo=999,
        )

        if dias and horas:
            raise ValueError(
                "La cantidad de días y de horas trabajadas son mutuamente excluyentes."
            )

    def _validar_cantidad_adherentes_obra_social(self):
        self._validar_entero(
            "cantidad de adherentes a la obra social",
            self.datos.cantidad_adherentes_obra_social,
            obligatoria=False,
            minimo=0,
            maximo=99,
        )

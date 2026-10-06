from decimal import Decimal
from num2words import num2words

from concepto.choices import Categoria, Unidad, Tipo
from concepto.models import VersionConcepto
from liquidacion.models import LiquidacionEmpleado
from liquidacion.services.GraficoCostoLaboralService import GraficoCostoLaboralService, ComposicionCostoLaboral


class ReciboSueldoService:

    def __init__(self, liquidacion_empleado):
        self.liquidacion_empleado = (
            LiquidacionEmpleado.objects
            .select_related(
                "liquidacion",
                "empleado",
                "empleado__empresa",
            )
            .prefetch_related(
                "detalles__concepto",
                "detalles__concepto__grupo",
            )
            .get(pk=liquidacion_empleado.pk)
        )

    def obtener_datos(self, tipo):
        le = self.liquidacion_empleado
        liquidacion = le.liquidacion
        empleado = le.empleado
        empresa = empleado.empresa

        detalles = list(le.detalles.all())

        remunerativos = [
            self._detalle_a_dict(detalle)
            for detalle in detalles
            if detalle.concepto.tipo == Tipo.REMUNERATIVO
        ]

        no_remunerativos = [
            self._detalle_a_dict(detalle)
            for detalle in detalles
            if detalle.concepto.tipo == Tipo.NO_REMUNERATIVO
        ]

        descuentos = [
            self._detalle_a_dict(detalle)
            for detalle in detalles
            if detalle.concepto.tipo == Tipo.DESCUENTO
        ]

        contribuciones = [
            self._detalle_a_dict(detalle)
            for detalle in detalles
            if detalle.concepto.tipo == Tipo.CONTRIBUCION
        ]

        grafico_torta_svg = GraficoCostoLaboralService(
            composicion=self.obtener_composicion_grafico(detalles, le.neto),
        ).generar_svg()

        return {
            "tipo": tipo,
            "empresa": {
                "nombre": empresa.nombre,
                "domicilio": liquidacion.domicilio_empresa,
                "cuit": empresa.cuit,
            },

            "mes": liquidacion.periodo.month,
            "anio": liquidacion.periodo.year,

            "empleado": {
                "apellido_nombre": (
                    f"{empleado.apellidos}, {empleado.nombres}"
                ),
                "legajo": empleado.legajo,
                "sueldo_bruto": self._decimal_a_string(le.bruto),
                "antiguedad": f"{self.calcular_antiguedad(empleado.fecha_ingreso, liquidacion.fecha_pago,)} AÑOS",
                "fecha_ingreso": empleado.fecha_ingreso.strftime("%d/%m/%Y"),
                "categoria": le.version_empleado.categoria_laboral,
                "cuil": empleado.cuil_display,
                "banco": le.version_empleado.banco_de_cobro,
                "periodo_pago": f"{liquidacion.fecha_pago.strftime('%d/%m/%Y')}",
            },

            "contribuciones": contribuciones,
            "remunerativos": remunerativos,
            "no_remunerativos": no_remunerativos,
            "descuentos": descuentos,

            "costo_total_empleador": self._decimal_a_string(
                le.costo_laboral
            ),
            "subtotal_contribuciones": self._decimal_a_string(
                le.contribuciones
            ),
            "sueldo_bruto": self._decimal_a_string(le.bruto),
            "total_remunerativo": self._decimal_a_string(
                le.remunerativo
            ),
            "total_no_remunerativo": self._decimal_a_string(
                le.no_remunerativo
            ),
            "total_descuentos": self._decimal_a_string(
                le.descuentos
            ),
            "sueldo_neto": self._decimal_a_string(int(le.neto)),

            "neto_en_letras": self.neto_en_letras(le.neto),

            "observaciones": le.observaciones_recibo if le.observaciones_recibo else "-",

            "detalle": self.obtener_detalle_composicion(detalles),

            "grafico_torta_svg": grafico_torta_svg,
        }

    def _detalle_a_dict(self, detalle):
        concepto = detalle.concepto

        return {
            "concepto": concepto.denominacion,
            "unidad": self._formatear_unidad(
                concepto.unidad,
                detalle.unidades,
            ),
            "base": self._decimal_a_string(detalle.base),
            "monto": self._decimal_a_string(detalle.importe),
        }

    def obtener_composicion_grafico(self, detalles, remuneracion_neta):
        grupos = self._agrupar_por_grupo(detalles)

        grupos_requeridos = {
            "sindical",
            "seguridad_social",
            "obra_social",
            "inssjp",
            "art",
            "scvo",
            "entidades_empresariales",
        }

        def total(codigo):
            return grupos.get(codigo, {}).get("total", Decimal("0"), )

        otros = sum(
            (
                datos["total"]
                for codigo, datos in grupos.items()
                if codigo not in grupos_requeridos
            ),
            Decimal("0"),
        )

        return ComposicionCostoLaboral(
            neto=remuneracion_neta,
            sindical=total("sindical"),
            seguridad_social=total("seguridad_social"),
            obra_social=total("obra_social"),
            inssjp=total("inssjp"),
            art_scvo=total("art") + total("scvo"),
            entidades_empresariales=total("entidades_empresariales"),
            otros=otros,
        )

    def obtener_detalle_composicion(self, detalles):
        grupos = self._agrupar_por_grupo(detalles)

        categorias = {
            "sindical": "Sindical",
            "seguridad_social": "Seguridad social",
            "obra_social": "Obra social",
            "inssjp": "INSSJP",
            "art": "ART",
            "scvo": "SCVO",
        }

        return {
            codigo: {
                "denominacion": denominacion,
                "total": self._decimal_a_string(
                    grupos.get(codigo, {}).get("total", Decimal("0"), )
                ),
                "empleador": self._decimal_a_string(
                    grupos.get(codigo, {}).get("empleador", Decimal("0"), )
                ),
                "trabajador": self._decimal_a_string(
                    grupos.get(codigo, {}).get("trabajador", Decimal("0"), )
                ),
            }
            for codigo, denominacion in categorias.items()
        }

    @staticmethod
    def calcular_antiguedad(fecha_ingreso, fecha_referencia):
        if fecha_ingreso > fecha_referencia:
            raise ValueError("La fecha de ingreso no puede ser posterior a la fecha de referencia.")

        anios = fecha_referencia.year - fecha_ingreso.year

        if (fecha_referencia.month, fecha_referencia.day, ) < (fecha_ingreso.month, fecha_ingreso.day, ):
            anios -= 1

        return anios

    @staticmethod
    def neto_en_letras(valor):
        return num2words(int(valor), lang="es", )

    def _agrupar_por_grupo(self, detalles):
        resultado: dict[dict[str, Decimal]] = {}

        for detalle in detalles:
            if detalle.concepto.tipo not in (Tipo.CONTRIBUCION, Tipo.DESCUENTO):
                continue

            grupo = detalle.concepto.grupo
            codigo = grupo.codigo if grupo else "sin_grupo"

            if codigo and codigo not in resultado:
                resultado[codigo] = {
                    "total": Decimal("0"),
                    "empleador": Decimal("0"),
                    "trabajador": Decimal("0"),
                }

            resultado[codigo]["total"] += detalle.importe

            if detalle.concepto.categoria == Categoria.EMPLEADOR:
                resultado[codigo]["empleador"] += detalle.importe
            else:
                resultado[codigo]["trabajador"] += detalle.importe

        return resultado

    @staticmethod
    def _formatear_unidad(unidad, unidades):
        return f"{unidades:.2f} {Unidad(unidad).sufijo}"

    @staticmethod
    def _decimal_a_string(valor):
        if valor is None:
            return None

        return str(valor)

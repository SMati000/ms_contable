from decimal import Decimal
from django.db import transaction
from django.db.models import Prefetch
from django.core.exceptions import ValidationError
from base_imponible.models import ResultadoBaseImponible
from concepto.choices import Tipo, Unidad
from liquidacion.models import LiquidacionEmpleado, DetalleLiquidacion
from ..exceptions import ErrorCalculoLiquidacion, ReferenciaInexistente
from concepto.models import VersionConcepto
from .grafo_expresiones import (
    agregar_nodo_por_identificador,
    obtener_grafo_referencias,
    obtener_orden_calculo,
)
from .validacion_calculo import validar_rango_decimal_calculado
from .evaluador_expresiones import (
    evaluar_formula as evaluar_expresion,
    obtener_importe_calculado,
    resolver_referencias as resolver_referencias_expresion,
)


class LiquidacionEmpleadoService:
    def __init__(self, liquidacion_empleado: LiquidacionEmpleado):
        self.liquidacion_empleado = liquidacion_empleado
        self.importes = {}

        self.detalles = {}
        self.resultados_bases = {}
        self.nodos_por_identificador = {}

    @transaction.atomic
    def liquidar(self):
        if not self.liquidacion_empleado.liquidacion.editable():
            raise ValidationError("Esta liquidación no se puede modificar.")

        self.calcular_importes_para_detalles()
        self.calcular_subtotales_empleado()

    def cargar_datos_calculo(self):
        """
        Carga en memoria los detalles y resultados de bases imponibles de la
        liquidación y construye el índice de nodos por identificador.

        Los identificadores de los detalles provienen del concepto utilizado
        por cada detalle, mientras que los identificadores de los resultados
        de bases imponibles provienen de su BaseImponible.

        El índice permite resolver referencias de fórmulas sin realizar
        consultas adicionales a la base de datos durante el cálculo.
        """
        self.importes.clear()

        detalles = (
            DetalleLiquidacion.objects
            .filter(liquidacion_empleado=self.liquidacion_empleado,)
            .select_related("concepto")
        )

        empresa_id = self.liquidacion_empleado.liquidacion.empresa_id

        versiones = VersionConcepto.todos.filter(concepto__empresa_id=empresa_id)

        resultados_bases = (
            ResultadoBaseImponible.objects
            .filter(liquidacion_empleado=self.liquidacion_empleado,)
            .select_related("base_imponible")
            .prefetch_related(
                Prefetch(
                    "base_imponible__versiones_concepto",
                    queryset=versiones,
                )
            )
        )

        self.detalles = {
            ("detalle", detalle.id): detalle
            for detalle in detalles
        }

        self.resultados_bases = {
            ("base", resultado.id): resultado
            for resultado in resultados_bases
        }

        self.nodos_por_identificador = {}

        for nodo, detalle in self.detalles.items():
            agregar_nodo_por_identificador(
                self.nodos_por_identificador,
                detalle.concepto.identificador_version,
                nodo,
            )

        for nodo, resultado_base in self.resultados_bases.items():
            agregar_nodo_por_identificador(
                self.nodos_por_identificador,
                resultado_base.base_imponible.identificador,
                nodo,
            )

    def calcular_subtotales_empleado(self):
        """
        Calcula y persiste los subtotales de la liquidación del empleado
        a partir de los importes de sus detalles.

        Los subtotales se agrupan según el tipo económico del concepto:
        remunerativo, no remunerativo, descuento y contribución.
        """
        detalles = self.detalles.values()

        subtotales = {
            Tipo.REMUNERATIVO: Decimal("0"),
            Tipo.NO_REMUNERATIVO: Decimal("0"),
            Tipo.DESCUENTO: Decimal("0"),
            Tipo.CONTRIBUCION: Decimal("0"),
        }

        for detalle in detalles:
            tipo = detalle.concepto.tipo

            if tipo not in subtotales:
                raise ErrorCalculoLiquidacion(
                    f"Tipo de concepto no soportado: {tipo}"
                )

            subtotales[tipo] += detalle.importe

        remunerativo = subtotales[Tipo.REMUNERATIVO]
        no_remunerativo = subtotales[Tipo.NO_REMUNERATIVO]
        descuentos = subtotales[Tipo.DESCUENTO]
        contribuciones = subtotales[Tipo.CONTRIBUCION]

        remuneracion_bruta = self.obtener_valor_base_imponible("remuneracion_total")

        remuneracion_neta = remuneracion_bruta - descuentos

        costo = remuneracion_bruta + contribuciones

        liquidacion_empleado = self.liquidacion_empleado

        subtotales = {
            "remunerativo": remunerativo,
            "no_remunerativo": no_remunerativo,
            "descuentos": descuentos,
            "contribuciones": contribuciones,
            "bruto": remuneracion_bruta,
            "neto": remuneracion_neta,
            "costo_laboral": costo,
        }

        for campo, importe in subtotales.items():
            validar_rango_decimal_calculado(
                type(liquidacion_empleado),
                campo,
                importe,
            )

        liquidacion_empleado.remunerativo = remunerativo
        liquidacion_empleado.no_remunerativo = no_remunerativo
        liquidacion_empleado.descuentos = descuentos
        liquidacion_empleado.contribuciones = contribuciones
        liquidacion_empleado.bruto = remuneracion_bruta
        liquidacion_empleado.neto = remuneracion_neta
        liquidacion_empleado.costo_laboral = costo

        liquidacion_empleado.save(
            update_fields=[
                "remunerativo",
                "no_remunerativo",
                "descuentos",
                "contribuciones",
                "bruto",
                "neto",
                "costo_laboral",
            ],
            _skip_validation=True,
        )

    def calcular_importes_para_detalles(self):
        """
        Calcula todos los detalles y resultados de bases imponibles
        respetando el orden determinado por sus dependencias.
        """
        self.cargar_datos_calculo()

        grafo_referencias = obtener_grafo_referencias(
            self.detalles,
            self.resultados_bases,
            self.nodos_por_identificador,
        )

        orden_calculos = obtener_orden_calculo(grafo_referencias)

        for nodo in orden_calculos:
            if nodo[0] == "detalle":
                self.evaluar_y_asignar_importe(self.detalles[nodo])
            elif nodo[0] == "base":
                self.calcular_y_asignar_base_imponible(self.resultados_bases[nodo])
            else:
                raise ErrorCalculoLiquidacion(
                    f"Tipo de nodo no soportado: {nodo[0]}"
                )

        for detalle in self.detalles.values():
            for campo in ("base", "importe"):
                validar_rango_decimal_calculado(
                    type(detalle),
                    campo,
                    getattr(detalle, campo),
                )

        for resultado in self.resultados_bases.values():
            validar_rango_decimal_calculado(
                type(resultado),
                "importe",
                resultado.importe,
            )

        DetalleLiquidacion.objects.bulk_update(
            self.detalles.values(),
            ["base", "importe"],
        )

        ResultadoBaseImponible.objects.bulk_update(
            self.resultados_bases.values(),
            ["importe"],
        )

    def evaluar_y_asignar_importe(self, detalle):
        """
        Evalúa la fórmula base de un detalle y calcula su importe según
        la unidad del concepto.
        """
        base = self.evaluar_formula(detalle.formula_base)
        detalle.base = base

        try:
            unidad = Unidad(detalle.concepto.unidad)
        except ValueError as error:
            raise ErrorCalculoLiquidacion(
                f"La unidad del concepto '{detalle.concepto.identificador_version}' "
                "no es válida."
            ) from error
        importe = unidad.calcular_importe(detalle.unidades, base, )

        detalle.importe = importe

        self.importes[("detalle", detalle.id)] = importe

        return importe

    def calcular_y_asignar_base_imponible(self, resultado_base):
        """
        Calcula y asigna el importe de un resultado de base imponible.

        Algunas bases tienen un cálculo específico y no se obtienen a partir
        de las versiones de conceptos asociadas a la base.
        """
        identificador = resultado_base.base_imponible.identificador

        if identificador == "detracciones": importe = resultado_base.importe

        elif identificador == "remuneracion_total": importe = self.calcular_remuneracion_total()

        elif identificador == "remuneracion_10": importe = self.calcular_remuneracion_10()

        else:
            importe = self.calcular_base_imponible_por_conceptos(resultado_base)

        resultado_base.importe = importe

        self.importes[("base", resultado_base.id)] = importe

        return importe

    def calcular_remuneracion_total(self):
        """
        Calcula la remuneración total como el bruto de la liquidación.

        El bruto está compuesto por los importes remunerativos y
        no remunerativos de los detalles de la liquidación.
        """
        importe = Decimal("0")

        for nodo, detalle in self.detalles.items():
            if detalle.concepto.tipo in (Tipo.REMUNERATIVO, Tipo.NO_REMUNERATIVO, ):
                importe += obtener_importe_calculado(
                    self.importes,
                    nodo,
                    detalle.concepto.identificador_version,
                )

        return importe

    def calcular_remuneracion_10(self):
        """
        Calcula remuneracion_10 como remuneracion_2 menos detracciones.
        """
        nodo_remuneracion_2 = self.nodos_por_identificador.get("remuneracion_2")
        nodo_detracciones = self.nodos_por_identificador.get("detracciones")

        if nodo_remuneracion_2 is None:
            raise ReferenciaInexistente("remuneracion_2")

        if nodo_detracciones is None:
            raise ReferenciaInexistente("detracciones")

        remuneracion_2 = obtener_importe_calculado(
            self.importes,
            nodo_remuneracion_2,
            "remuneracion_2",
        )
        detracciones = obtener_importe_calculado(
            self.importes,
            nodo_detracciones,
            "detracciones",
        )

        return remuneracion_2 - detracciones

    def calcular_base_imponible_por_conceptos(self, resultado_base):
        versiones = (
            resultado_base.base_imponible
            .versiones_concepto
            .all()
        )

        importe = Decimal("0")

        for version in versiones:
            nodo = self.nodos_por_identificador.get(version.identificador_version)

            if nodo:
                importe += obtener_importe_calculado(
                    self.importes,
                    nodo,
                    version.identificador_version,
                )

        return importe

    def evaluar_formula(self, formula):
        return evaluar_expresion(
            formula,
            self.importes,
            self.nodos_por_identificador,
        )

    def resolver_referencias(self, expresion):
        return resolver_referencias_expresion(
            expresion,
            self.importes,
            self.nodos_por_identificador,
        )

    def obtener_valor_base_imponible(self, identificador):
        nodo = self.nodos_por_identificador.get(identificador)

        if nodo is None:
            raise ReferenciaInexistente(identificador)

        return obtener_importe_calculado(self.importes, nodo, identificador)

from datetime import date
from decimal import Decimal

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from base_imponible.models import BaseImponible, ResultadoBaseImponible
from categoria_laboral.models import CategoriaLaboral
from concepto.choices import Categoria, Tipo, Unidad
from concepto.models import Concepto, VersionConcepto
from empleado.choices import FormaPago
from empleado.models import Empleado, VersionEmpleado
from empresa.choices import TipoEmpleador
from empresa.models import Empresa
from liquidacion.choices import (
    DebitoCredito,
    TipoEnvio,
    TipoLiquidacion,
    UnidadesLsd,
)
from liquidacion.exceptions import ReferenciaCiclica, ReferenciaInexistente
from liquidacion.models import DetalleLiquidacion, Liquidacion, LiquidacionEmpleado
from liquidacion.services.LiquidacionEmpleadoService import (
    LiquidacionEmpleadoService as CrearLiquidacionEmpleadoService,
)
from liquidacion.services.s_expresiones import LiquidacionEmpleadoService
from liquidacion.lsd.mappers import (
    Registro01Mapper,
    Registro02Mapper,
    Registro03Mapper,
    Registro04Mapper,
    Registro06Mapper,
)
from liquidacion.lsd.queries import obtener_liquidacion_para_exportar
from liquidacion.services.TxtLsdArca import LsdTxtArcaService


class CalculoIntegradoTests(TestCase):
    def setUp(self):
        empresa = Empresa.objects.create(
            cuit="20123456786",
            nombre="Empresa para cálculo integrado",
            tipo_empleador=TipoEmpleador.ADMINISTRACION_PUBLICA,
        )
        categoria_laboral = CategoriaLaboral.objects.create(
            empresa=empresa,
            denominacion="Administrativo",
        )
        empleado = Empleado.objects.create(
            empresa=empresa,
            dni="12345678",
            cuil="20123456786",
            apellidos="Prueba",
            nombres="Cálculo",
            legajo="CALC-1",
            fecha_ingreso=date(2020, 1, 1),
        )
        version_empleado = VersionEmpleado.objects.create(
            empleado=empleado,
            categoria_laboral=categoria_laboral,
            banco_de_cobro="Efectivo",
            forma_de_pago=FormaPago.EFECTIVO,
            codigo_obra_social="123456",
        )
        liquidacion = Liquidacion.objects.create(
            empresa=empresa,
            periodo=date(2025, 3, 1),
            fecha_pago=date(2025, 3, 31),
            tipo_envio=TipoEnvio.SJ,
            tipo_liquidacion=TipoLiquidacion.M,
        )
        self.liquidacion_empleado = LiquidacionEmpleado(
            liquidacion=liquidacion,
            empleado=empleado,
            version_empleado=version_empleado,
            codigo_situacion="01",
            codigo_condicion="01",
            codigo_actividad="001",
            codigo_modalidad_contratacion="001",
            codigo_siniestrado="00",
            codigo_localidad="01",
        )
        self.liquidacion_empleado.save()
        CrearLiquidacionEmpleadoService(
            self.liquidacion_empleado,
        ).crear_resultados_bases_imponibles()

    def crear_concepto_remunerativo(self, denominacion, codigo_arca=""):
        concepto = Concepto.objects.create(
            empresa=self.liquidacion_empleado.liquidacion.empresa,
        )
        return VersionConcepto.objects.create(
            concepto=concepto,
            denominacion=denominacion,
            codigo_arca=codigo_arca,
            categoria=Categoria.TRABAJADOR,
            tipo=Tipo.REMUNERATIVO,
            unidad=Unidad.CANTIDAD,
        )

    def test_calcula_dependencias_subtotales_y_persiste_importes(self):
        salario = self.crear_concepto_remunerativo("Sueldo básico")
        adicional = self.crear_concepto_remunerativo("Adicional calculado")
        remuneracion_2 = BaseImponible.objects.get(
            identificador="remuneracion_2",
        )
        remuneracion_2.versiones_concepto.add(salario, adicional)

        DetalleLiquidacion.objects.create(
            liquidacion_empleado=self.liquidacion_empleado,
            concepto=salario,
            unidades=Decimal("1"),
            formula_base="100.12345",
        )
        DetalleLiquidacion.objects.create(
            liquidacion_empleado=self.liquidacion_empleado,
            concepto=adicional,
            unidades=Decimal("1"),
            formula_base=f"{salario.identificador_version} * 1.25",
        )

        LiquidacionEmpleadoService(self.liquidacion_empleado).liquidar()

        detalles = list(
            DetalleLiquidacion.objects.filter(
                liquidacion_empleado=self.liquidacion_empleado,
            ).order_by("concepto_id")
        )
        self.assertEqual(
            [detalle.importe for detalle in detalles],
            [Decimal("100.12345"), Decimal("125.15431")],
        )

        bases = {
            resultado.base_imponible.identificador: resultado.importe
            for resultado in ResultadoBaseImponible.objects.filter(
                liquidacion_empleado=self.liquidacion_empleado,
            ).select_related("base_imponible")
        }
        self.assertEqual(bases["remuneracion_total"], Decimal("225.27776"))
        self.assertEqual(bases["remuneracion_2"], Decimal("225.27776"))
        self.assertEqual(bases["remuneracion_10"], Decimal("225.27776"))

        self.liquidacion_empleado.refresh_from_db()
        self.assertEqual(self.liquidacion_empleado.remunerativo, Decimal("225.27776"))
        self.assertEqual(self.liquidacion_empleado.bruto, Decimal("225.27776"))
        self.assertEqual(self.liquidacion_empleado.neto, Decimal("225.27776"))

    def test_rechaza_ciclo_entre_detalles_persistidos(self):
        concepto_a = self.crear_concepto_remunerativo("Concepto circular A")
        concepto_b = self.crear_concepto_remunerativo("Concepto circular B")
        detalle_a = DetalleLiquidacion.objects.create(
            liquidacion_empleado=self.liquidacion_empleado,
            concepto=concepto_a,
            unidades=Decimal("1"),
            formula_base=concepto_b.identificador_version,
        )
        detalle_b = DetalleLiquidacion.objects.create(
            liquidacion_empleado=self.liquidacion_empleado,
            concepto=concepto_b,
            unidades=Decimal("1"),
            formula_base=concepto_a.identificador_version,
        )

        with self.assertRaises(ReferenciaCiclica):
            LiquidacionEmpleadoService(self.liquidacion_empleado).liquidar()

        detalle_a.refresh_from_db()
        detalle_b.refresh_from_db()
        self.assertEqual(detalle_a.importe, Decimal("0"))
        self.assertEqual(detalle_b.importe, Decimal("0"))

    def test_falla_de_subtotal_revierte_las_escrituras_masivas_previas(self):
        salario = self.crear_concepto_remunerativo("Sueldo sujeto a reversión")
        detalle = DetalleLiquidacion.objects.create(
            liquidacion_empleado=self.liquidacion_empleado,
            concepto=salario,
            unidades=Decimal("1"),
            formula_base="42.12567",
        )
        BaseImponible.objects.get(identificador="remuneracion_total").resultados.filter(
            liquidacion_empleado=self.liquidacion_empleado,
        ).delete()

        with self.assertRaises(ReferenciaInexistente):
            LiquidacionEmpleadoService(self.liquidacion_empleado).liquidar()

        detalle.refresh_from_db()
        self.liquidacion_empleado.refresh_from_db()
        self.assertEqual(detalle.importe, Decimal("0"))
        self.assertEqual(self.liquidacion_empleado.remunerativo, Decimal("0"))
        self.assertEqual(self.liquidacion_empleado.bruto, Decimal("0"))

    def test_mappers_no_consultan_la_base_despues_de_precargar_datos(self):
        concepto = self.crear_concepto_remunerativo("Concepto para exportación")
        DetalleLiquidacion.objects.create(
            liquidacion_empleado=self.liquidacion_empleado,
            concepto=concepto,
            unidades=Decimal("1"),
            formula_base="10",
        )
        liquidacion = obtener_liquidacion_para_exportar(
            self.liquidacion_empleado.liquidacion_id,
        )

        with CaptureQueriesContext(connection) as consultas:
            Registro01Mapper.obtener_datos(liquidacion)
            Registro02Mapper.obtener_datos(liquidacion)
            Registro03Mapper.obtener_datos(liquidacion)
            Registro04Mapper.obtener_datos(liquidacion)
            Registro06Mapper.obtener_datos(liquidacion)

        self.assertEqual(len(consultas), 0)

    def test_exporta_txt_completo_con_registros_y_centavos_redondeados(self):
        salario = self.crear_concepto_remunerativo(
            "Sueldo para TXT",
            codigo_arca="ABC123",
        )
        DetalleLiquidacion.objects.create(
            liquidacion_empleado=self.liquidacion_empleado,
            concepto=salario,
            unidades=Decimal("1"),
            formula_base="123.45678",
            cantidad=Decimal("1.23"),
            unidades_lsd=UnidadesLsd.MONEDA,
            debito_credito=DebitoCredito.CREDITO,
        )
        self.liquidacion_empleado.observaciones_lsd = "Exportación de prueba"
        self.liquidacion_empleado.save(update_fields=["observaciones_lsd"])
        LiquidacionEmpleadoService(self.liquidacion_empleado).liquidar()

        contenido = LsdTxtArcaService(
            str(self.liquidacion_empleado.liquidacion_id),
        ).generar()
        lineas = contenido.split("\r\n")

        self.assertEqual([linea[:2] for linea in lineas], ["01", "02", "03", "04", "06"])
        self.assertEqual([len(linea) for linea in lineas], [35, 115, 51, 370, 93])
        self.assertEqual(lineas[2][29:44], "000000000012346")

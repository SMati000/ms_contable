from django.test import SimpleTestCase
from decimal import Decimal
from liquidacion.lsd.registro04 import GeneradorRegistro04
from empresa.choices import TipoEmpleador
from liquidacion.tests.lsd.fixtures_registro04 import datos_registro04


class TestGeneradorRegistro04(SimpleTestCase):
    def datos_registro(self, **kwargs):
        return datos_registro04(**kwargs)

    def test_generar(self):
        casos = [
            (
                "original",
                {},
                "043369345023900000000011 0011  0 01010100000000300000000000000123456000000000000000000000000000000000"
                "0000000000000000000000000000000000000000000000000000000000000000005648931300000000023152100000000000"
                "1220000000075135401123456789123421000000000213500000000000000100000000000001200000000000321500000000"
                "000002125000000000000000000000000000000000000000215300000000000700387",
            ),
            (
                "otro_tipo_empleador",
                {
                    "tipo_empleador": TipoEmpleador.ENSENIANZA_PRIVADA,
                },
                "043369345023900000070011 0011  0 01010100000000300000000000000123456000000000000000000000000000000000"
                "0000000000000000000000000000000000000000000000000000000000000000005648931300000000023152100000000000"
                "1220000000075135401123456789123421000000000213500000000000000100000000000001200000000000321500000000"
                "000002125000000000000000000000000000000000000000215300000000000700387",
            ),
            (
                "valores_booleanos_true",
                {
                    "conyuge": True,
                    "marca_cct": True,
                    "marca_scvo": True,
                    "marca_reduccion": True,
                },
                "043369345023910011100011 0011  0 010101000000003000000000000001234560000000000000000000000000000000000"
                "00000000000000000000000000000000000000000000000000000000000000000564893130000000002315210000000000012"
                "20000000075135401123456789123421000000000213500000000000000100000000000001200000000000321500000000000"
                "002125000000000000000000000000000000000000000215300000000000700387",
            ),
            (
                "cantidad_hijos",
                {
                    "cantidad_hijos": 3,
                },
                "043369345023900300000011 0011  0 01010100000000300000000000000123456000000000000000000000000000000000"
                "0000000000000000000000000000000000000000000000000000000000000000005648931300000000023152100000000000"
                "1220000000075135401123456789123421000000000213500000000000000100000000000001200000000000321500000000"
                "000002125000000000000000000000000000000000000000215300000000000700387",
            ),
            (
                "segunda_situacion_revista",
                {
                    "codigo_situacion_revista_2": "2",
                    "dia_inicio_situacion_revista_2": 15,
                    "codigo_situacion_revista_3": "3",
                    "dia_inicio_situacion_revista_3": 20,
                },
                "043369345023900000000011 0011  0 01010102150320300000000000000123456000000000000000000000000000000000"
                "0000000000000000000000000000000000000000000000000000000000000000005648931300000000023152100000000000"
                "1220000000075135401123456789123421000000000213500000000000000100000000000001200000000000321500000000"
                "000002125000000000000000000000000000000000000000215300000000000700387",
            ),
            (
                "horas_trabajadas",
                {
                    "cantidad_dias_trabajados": None,
                    "cantidad_horas_trabajadas": 176,
                },
                "043369345023900000000011 0011  0 010101000000000017600000000001234560000000000000000000000000000000000"
                "000000000000000000000000000000000000000000000000000000000000000005648931300000000023152100000000000"
                "122000000007513540112345678912342100000000021350000000000000010000000000000120000000000032150000000"
                "0000002125000000000000000000000000000000000000000215300000000000700387",
            ),
            (
                "porcentajes",
                {
                    "porcentaje_aporte_adicional_seg_social": Decimal("5.50"),
                    "porcentaje_contrib_tarea_diferencial": Decimal("3.25"),
                },
                "043369345023900000000011 0011  0 01010100000000300000055000325123456000000000000000000000000000000000"
                "0000000000000000000000000000000000000000000000000000000000000000005648931300000000023152100000000000"
                "1220000000075135401123456789123421000000000213500000000000000100000000000001200000000000321500000000"
                "000002125000000000000000000000000000000000000000215300000000000700387",
            ),
            (
                "importes_adicionales_obra_social",
                {
                    "cantidad_adherentes_obra_social": 2,
                    "aporte_adicional_obra_social": Decimal("1500.25"),
                    "contrib_adicional_obra_social": Decimal("2300.75"),
                },
                "043369345023900000000011 0011  0 010101000000003000000000000001234560200000000015002500000000023007500"
                "000000000000000000000000000000000000000000000000000000000000000005648931300000000023152100000000000122"
                "000000007513540112345678912342100000000021350000000000000010000000000000120000000000032150000000000000"
                "2125000000000000000000000000000000000000000215300000000000700387",
            ),
            (
                "bases_diferenciales_obra_social",
                {
                    "base_calc_diferencial_aportes_obra_social_fsr": Decimal("125000.50"),
                    "base_calc_diferencial_contrib_obra_social_fsr": Decimal("130000.75"),
                    "base_calc_diferencial_ley_riesgos_trabajo": Decimal("145000.00"),
                    "remuneracion_maternidad_anses": Decimal("95000.25"),
                },
                "043369345023900000000011 0011  0 010101000000003000000000000001234560000000000000000000000000000000000"
                "000001250005000000001300007500000001450000000000000950002500000005648931300000000023152100000000000122"
                "000000007513540112345678912342100000000021350000000000000010000000000000120000000000032150000000000000"
                "2125000000000000000000000000000000000000000215300000000000700387",
            ),
            (
                "bases_diferenciales_seguridad_social",
                {
                    "base_calc_diferencial_aportes_seg_social": Decimal("120000.00"),
                    "base_calc_diferencial_contrib_seg_social": Decimal("125000.50"),
                },
                "043369345023900000000011 0011  0 01010100000000300000000000000123456000000000000000000000000000000000"
                "0000000000000000000000000000000000000000000000000000000000000000005648931300000000023152100000000000"
                "1220000000075135401123456789123421000000000213500000000000000100000000000001200000000000321500000000"
                "000002125000000012000000000000012500050000000000215300000000000700387",
            ),
            (
                "importes_con_decimales",
                {
                    "remuneracion_bruta": Decimal("1234567890123.45"),
                    "base_imponible_1": Decimal("9876543210987.65"),
                    "detracciones": Decimal("12345.67"),
                },
                "043369345023900000000011 0011  0 010101000000003000000000000001234560000000000000000000000000000000000"
                "00000000000000000000000000000000000000000000000000000000001234567890123459876543210987650000000000012"
                "2000000007513540112345678912342100000000021350000000000000010000000000000120000000000032150000000000"
                "0002125000000000000000000000000000000000000000215300000000001234567",
            ),
            (
                "bases_imponibles_distintas",
                {
                    "base_imponible_1": Decimal("100000.00"),
                    "base_imponible_2": Decimal("95000.50"),
                    "base_imponible_3": Decimal("90000.25"),
                    "base_imponible_4": Decimal("85000.75"),
                    "base_imponible_5": Decimal("80000.00"),
                    "base_imponible_6": Decimal("75000.50"),
                    "base_imponible_7": Decimal("70000.25"),
                    "base_imponible_8": Decimal("65000.75"),
                    "base_imponible_9": Decimal("60000.00"),
                    "base_imponible_10": Decimal("55000.50"),
                },
                "043369345023900000000011 0011  0 010101000000003000000000000001234560000000000000000000000000000000000"
                "000000000000000000000000000000000000000000000000000000000000000005648931300000001000000000000000950005"
                "00000000090000250000000085000750000000080000000000000075000500000000070000250000000065000750000000060"
                "00000000000000000000000000000000000000000005500050000000000700387",
            ),
            (
                "codigos_distintos",
                {
                    "codigo_situacion_revista": "5",
                    "codigo_condicion": "2",
                    "codigo_actividad": "123",
                    "codigo_modalidad_contratacion": "456",
                    "codigo_siniestrado": "01",
                    "codigo_localidad": "99",
                    "codigo_situacion_revista_1": "5",
                    "codigo_obra_social": "654321",
                    "dia_inicio_situacion_revista_1": 28,
                },
                "043369345023900000000052 1234561 99052800000000300000000000000654321000000000000000000000000000000000"
                "0000000000000000000000000000000000000000000000000000000000000000005648931300000000023152100000000000"
                "12200000000751354011234567891234210000000002135000000000000001000000000000012000000000003215000000000"
                "00002125000000000000000000000000000000000000000215300000000000700387",
            ),
            (
                "todos_los_opcionales",
                {
                    "cantidad_hijos": 4,
                    "codigo_situacion_revista_2": "2",
                    "dia_inicio_situacion_revista_2": 10,
                    "codigo_situacion_revista_3": "3",
                    "dia_inicio_situacion_revista_3": 20,
                    "cantidad_dias_trabajados": 20,
                    "porcentaje_aporte_adicional_seg_social": Decimal("2.50"),
                    "porcentaje_contrib_tarea_diferencial": Decimal("1.75"),
                    "cantidad_adherentes_obra_social": 2,
                    "aporte_adicional_obra_social": Decimal("1000.00"),
                    "contrib_adicional_obra_social": Decimal("2000.00"),
                    "base_calc_diferencial_aportes_obra_social_fsr": Decimal("110000.00"),
                    "base_calc_diferencial_contrib_obra_social_fsr": Decimal("115000.00"),
                    "base_calc_diferencial_ley_riesgos_trabajo": Decimal("120000.00"),
                    "remuneracion_maternidad_anses": Decimal("90000.00"),
                    "base_calc_diferencial_aportes_seg_social": Decimal("105000.00"),
                    "base_calc_diferencial_contrib_seg_social": Decimal("110000.00"),
                },
                "043369345023900400000011 0011  0 01010102100320200000025000175123456020000000001000000000000002000000"
                "0000001100000000000001150000000000001200000000000000900000000000005648931300000000023152100000000000"
                "12200000000751354011234567891234210000000002135000000000000001000000000000012000000000003215000000000"
                "00002125000000010500000000000011000000000000000215300000000000700387",
            ),
        ]

        for nombre, cambios, esperado in casos:
            with self.subTest(nombre):
                datos = self.datos_registro(**cambios)
                registro = GeneradorRegistro04(datos).generar()

                self.assertEqual(registro, esperado)

    def test_tiempos_trabajados_invalidos(self):
        cambios = {
            "cantidad_dias_trabajados": 30,
            "cantidad_horas_trabajadas": 120,
        }

        datos = self.datos_registro(**cambios)

        self.assertRaises(Exception, lambda: GeneradorRegistro04(datos).generar())

    def test_long_codigos_invalidos(self):
        casos = [
            (
                "codigo_situacion_revista",
                {"codigo_situacion_revista": "113"},
                Exception
            ),
            (
                "codigo_situacion_revista_1",
                {"codigo_situacion_revista_1": "qwes"},
                Exception
            ),
            (
                "codigo_situacion_revista_2",
                {"codigo_situacion_revista_2": "a54s"},
                Exception
            ),
            (
                "codigo_situacion_revista_3",
                {"codigo_situacion_revista_3": ",2.s"},
                Exception
            ),
            (
                "codigo_condicion",
                {"codigo_condicion": "87621"},
                Exception
            ),
            (
                "codigo_actividad",
                {"codigo_actividad": "32.0"},
                Exception
            ),
            (
                "codigo_modalidad_contratacion",
                {"codigo_modalidad_contratacion": "32a0"},
                Exception
            ),
            (
                "codigo_siniestrado",
                {"codigo_siniestrado": "32135"},
                Exception
            ),
            (
                "codigo_localidad",
                {"codigo_localidad": "asdwasd"},
                Exception
            ),
            (
                "codigo_obra_social",
                {"codigo_obra_social": "52701438"},
                Exception
            ),
        ]

        for nombre, cambios, esperado in casos:
            with self.subTest(nombre):
                datos = self.datos_registro(**cambios)
                self.assertRaises(Exception, lambda: GeneradorRegistro04(datos).generar())

    def test_cantidades_invalidas(self):
        casos = [
            (
                "cantidad_hijos_tope",
                {"cantidad_hijos": 100},
                Exception
            ),
            (
                "cantidad_hijos_negativo",
                {"cantidad_hijos": -1},
                Exception
            ),
            (
                "dia_inicio_situacion_revista_2_tope",
                {"dia_inicio_situacion_revista_2": 875320},
                Exception
            ),
            (
                "dia_inicio_situacion_revista_2_negativo",
                {"dia_inicio_situacion_revista_2": -5},
                Exception
            ),
            (
                "dia_inicio_situacion_revista_3_tope",
                {"dia_inicio_situacion_revista_3": 238},
                Exception
            ),
            (
                "dia_inicio_situacion_revista_3_negativo",
                {"dia_inicio_situacion_revista_3": -54},
                Exception
            ),
            (
                "cantidad_dias_trabajados_tope",
                {"cantidad_dias_trabajados": 3258},
                Exception
            ),
            (
                "cantidad_dias_trabajados_negativo",
                {"cantidad_dias_trabajados": -0.5},
                Exception
            ),
            (
                "cantidad_horas_trabajadas_tope",
                {"cantidad_horas_trabajadas": 8321},
                Exception
            ),
            (
                "cantidad_horas_trabajadas_negativo",
                {"cantidad_horas_trabajadas": -87},
                Exception
            ),
            (
                "cantidad_adherentes_obra_social_tope",
                {"cantidad_adherentes_obra_social": 582},
                Exception
            ),
            (
                "cantidad_adherentes_obra_social_negativo",
                {"cantidad_adherentes_obra_social": -12.1},
                Exception
            ),
        ]

        for nombre, cambios, esperado in casos:
            with self.subTest(nombre):
                datos = self.datos_registro(**cambios)
                self.assertRaises(Exception, lambda: GeneradorRegistro04(datos).generar())


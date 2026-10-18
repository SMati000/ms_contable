from types import SimpleNamespace

from django.test import SimpleTestCase

from liquidacion.exceptions import (
    ExpresionBaseInvalida,
    IdentificadorCalculoDuplicado,
    ReferenciaCiclica,
    ReferenciaInexistente,
    ReferenciaNoCalculada,
)
from liquidacion.services.grafo_expresiones import (
    agregar_nodo_por_identificador,
    normalizar_formula,
    obtener_grafo_referencias,
    obtener_identificadores,
    obtener_orden_calculo,
)


class GrafoExpresionesTests(SimpleTestCase):
    def test_formula_historica_nula_es_un_error_de_dominio(self):
        with self.assertRaises(ExpresionBaseInvalida):
            normalizar_formula(None)

    def test_normaliza_espacios_y_extrae_identificadores(self):
        formula = normalizar_formula(" sueldo_base * 2 + adicional ")

        self.assertEqual(formula, "sueldo_base*2+adicional")
        self.assertEqual(
            obtener_identificadores(formula),
            {"sueldo_base", "adicional"},
        )

    def test_orden_calcula_primero_las_dependencias(self):
        orden = obtener_orden_calculo({"detalle": ["base"], "base": []})

        self.assertLess(orden.index("base"), orden.index("detalle"))

    def test_orden_rechaza_referencias_ciclicas(self):
        with self.assertRaises(ReferenciaCiclica):
            obtener_orden_calculo({"a": ["b"], "b": ["a"]})

    def test_grafo_rechaza_referencias_inexistentes(self):
        detalle = SimpleNamespace(formula_base="concepto_ausente + 1")

        with self.assertRaises(ReferenciaInexistente):
            obtener_grafo_referencias(
                {("detalle", 1): detalle},
                {},
                {},
            )

    def test_grafo_expone_formula_sintacticamente_invalida_como_error_de_dominio(self):
        detalle = SimpleNamespace(formula_base="sueldo_base +")

        with self.assertRaises(ExpresionBaseInvalida):
            obtener_grafo_referencias(
                {("detalle", 1): detalle},
                {},
                {},
            )

    def test_rechaza_identificadores_duplicados_con_error_de_dominio(self):
        nodos = {}
        agregar_nodo_por_identificador(nodos, "sueldo_base", ("detalle", 1))

        with self.assertRaises(IdentificadorCalculoDuplicado):
            agregar_nodo_por_identificador(
                nodos,
                "sueldo_base",
                ("detalle", 2),
            )

    def test_referencia_existente_aun_no_calculada_tiene_error_tipado(self):
        from liquidacion.services.s_expresiones import LiquidacionEmpleadoService

        servicio = LiquidacionEmpleadoService(None)
        servicio.nodos_por_identificador["sueldo_base"] = ("detalle", 1)

        with self.assertRaises(ReferenciaNoCalculada):
            servicio.resolver_referencias("sueldo_base")

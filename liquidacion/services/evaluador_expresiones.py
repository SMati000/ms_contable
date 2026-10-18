import ast
import operator
from decimal import Decimal

from django.core.exceptions import ValidationError
from simpleeval import SimpleEval

from ..exceptions import (
    ExpresionBaseInvalida,
    ReferenciaInexistente,
    ReferenciaNoCalculada,
)
from ..validators.v_expresiones import preparar_formula
from .grafo_expresiones import normalizar_formula, obtener_identificadores


OPERADORES = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
    ast.Pow: operator.pow,
}


def evaluar_formula(formula, importes, nodos_por_identificador):
    try:
        formula_normalizada = normalizar_formula(formula)
        referencias = resolver_referencias(
            formula_normalizada,
            importes,
            nodos_por_identificador,
        )
        expresion_evaluable, valores_numericos = preparar_formula(
            formula_normalizada
        )
        evaluador = SimpleEval(
            operators=OPERADORES,
            names={**referencias, **valores_numericos},
        )
        return evaluador.eval(expr=expresion_evaluable)
    except (
        ValidationError,
        ArithmeticError,
        SyntaxError,
        TypeError,
        ValueError,
    ) as error:
        if isinstance(error, ValidationError):
            detalle = "; ".join(error.messages)
        else:
            detalle = str(error)

        raise ExpresionBaseInvalida(
            f"No se pudo evaluar la fórmula: {detalle}"
        ) from error


def resolver_referencias(expresion, importes, nodos_por_identificador):
    referencias = {}
    for identificador in obtener_identificadores(expresion):
        try:
            nodo = nodos_por_identificador[identificador]
        except KeyError as error:
            raise ReferenciaInexistente(identificador) from error

        referencias[identificador] = obtener_importe_calculado(
            importes,
            nodo,
            identificador,
        )

    return referencias


def obtener_importe_calculado(importes, nodo, identificador):
    try:
        return importes[nodo]
    except KeyError as error:
        raise ReferenciaNoCalculada(
            f"El nodo '{identificador}' todavía no fue calculado."
        ) from error

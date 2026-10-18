from decimal import Decimal, InvalidOperation
import ast

from django.core.exceptions import ValidationError


OPERADORES_BINARIOS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)
OPERADORES_UNARIOS = (ast.USub,)
NODOS_EXPRESION = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Name,
    ast.Load,
    ast.Constant,
    *OPERADORES_BINARIOS,
    *OPERADORES_UNARIOS,
)


def _decimal_del_literal(expresion, nodo):
    if isinstance(nodo.value, int):
        return Decimal(nodo.value)

    literal = ast.get_source_segment(expresion, nodo)
    return Decimal(literal)


def validar_formula(expresion):
    try:
        tree = ast.parse(expresion, mode="eval")
    except (SyntaxError, TypeError, ValueError) as error:
        raise ValidationError({
            "formula_base": "La fórmula no tiene una sintaxis válida."
        }) from error

    for nodo in ast.walk(tree):
        if not isinstance(nodo, NODOS_EXPRESION):
            raise ValidationError({
                "formula_base": "La fórmula contiene una operación no permitida."
            })

        if isinstance(nodo, ast.Constant):
            if isinstance(nodo.value, bool) or not isinstance(nodo.value, (int, float)):
                raise ValidationError({
                    "formula_base": "La fórmula solo puede contener números y referencias."
                })

            try:
                numero = _decimal_del_literal(expresion, nodo)
            except (InvalidOperation, TypeError, ValueError) as error:
                raise ValidationError({
                    "formula_base": "La fórmula contiene un número inválido."
                }) from error

            if not numero.is_finite():
                raise ValidationError({
                    "formula_base": "La fórmula contiene un número no finito."
                })

        if isinstance(nodo, ast.BinOp) and not isinstance(nodo.op, OPERADORES_BINARIOS):
            raise ValidationError({
                "formula_base": "La fórmula contiene un operador no permitido."
            })

        if isinstance(nodo, ast.UnaryOp) and not isinstance(nodo.op, OPERADORES_UNARIOS):
            raise ValidationError({
                "formula_base": "La fórmula contiene un operador no permitido."
            })

    return tree


def preparar_formula(expresion):
    tree = validar_formula(expresion)

    transformador = ReemplazarNumeros(expresion)
    tree = transformador.visit(tree)
    ast.fix_missing_locations(tree)

    expresion_transformada = ast.unparse(tree)

    return expresion_transformada, transformador.numeros


class ReemplazarNumeros(ast.NodeTransformer):
    def __init__(self, expresion):
        self.expresion = expresion
        self.numeros = {}

    def visit_Constant(self, node):
        if (
            isinstance(node.value, (int, float))
            and not isinstance(node.value, bool)
        ):
            identificador = f"_numero_{len(self.numeros) + 1}"
            self.numeros[identificador] = _decimal_del_literal(
                self.expresion,
                node,
            )

            return ast.copy_location(
                ast.Name(id=identificador, ctx=ast.Load()),
                node,
            )

        return node

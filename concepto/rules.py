from django.core.exceptions import ValidationError
from concepto.choices import Categoria, Tipo


def validar_tipo_categoria(tipo, categoria):
    if not tipo or not categoria:
        return

    if tipo == Tipo.CONTRIBUCION:
        if categoria != Categoria.EMPLEADOR:
            raise ValidationError({
                "categoria": (
                    "Los conceptos de tipo contribución "
                    "deben corresponder a la categoría empleador."
                )
            })
    elif categoria != Categoria.TRABAJADOR:
        raise ValidationError({
            "categoria": (
                "Los conceptos que no son contribuciones "
                "deben corresponder a la categoría trabajador."
            )
        })

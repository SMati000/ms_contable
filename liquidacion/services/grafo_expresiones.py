import ast
from django.core.exceptions import ValidationError

from concepto.choices import Tipo
from ..exceptions import (
    ExpresionBaseInvalida,
    IdentificadorCalculoDuplicado,
    ReferenciaCiclica,
    ReferenciaInexistente,
)
from ..validators.v_expresiones import validar_formula


def normalizar_formula(formula):
    if not isinstance(formula, str):
        raise ExpresionBaseInvalida("La fórmula debe ser texto.")

    return "".join(formula.split())


def obtener_identificadores(expresion):
    try:
        tree = validar_formula(expresion)
    except ValidationError as error:
        detalle = "; ".join(error.messages)
        raise ExpresionBaseInvalida(
            f"No se pudo evaluar la fórmula: {detalle}"
        ) from error

    return {
        nodo.id
        for nodo in ast.walk(tree)
        if isinstance(nodo, ast.Name)
    }


def obtener_orden_calculo(grafo):
    """
    Valida que el grafo de dependencias de una liquidación de empleado no contenga ciclos y obtiene un orden
    válido para realizar los cálculos.

    El grafo puede contener dos tipos de nodos:
        - DetalleLiquidacion.
        - ResultadoBaseImponible.

    Cada nodo representa un valor que debe ser calculado y cada arista dirigida representa una dependencia desde
    el nodo origen hacia el nodo requerido para calcularlo.

    La dirección de las aristas es: nodo -> dependencia

    Por ejemplo: obra_social -> remuneracion_1 -> sueldo_basico

    El grafo se representa como un diccionario de adyacencia:
        {
            nodo_origen: [nodo_dependencia, ...],
            ...
        }

    El orden devuelto garantiza que una dependencia aparezca antes que cualquier nodo que necesite su resultado.
    Esto permite calcular secuencialmente todos los nodos sin intentar utilizar un valor que aún no haya sido obtenido.

    La validación se realiza sobre todos los nodos del grafo, incluyendo componentes que no estén conectados entre sí.
    De esta forma se garantiza que ninguna dependencia circular quede sin detectar.

    Raises:
        ReferenciaCiclica: si se encuentra un ciclo de dependencias.
    """
    visitados = set()
    en_camino = []
    orden = []

    def visitar(nodo):
        if nodo in en_camino:
            indice = en_camino.index(nodo)
            ciclo = en_camino[indice:] + [nodo]
            raise ReferenciaCiclica(f"Las referencias en las formulas generan una dependencia circular: {ciclo}")

        if nodo in visitados:
            return

        en_camino.append(nodo)

        for dependencia in grafo.get(nodo, []):
            visitar(dependencia)

        en_camino.pop()
        visitados.add(nodo)
        orden.append(nodo)

    for nodo in grafo:
        visitar(nodo)

    return orden


def obtener_grafo_referencias(
    detalles,
    resultados_bases,
    nodos_por_identificador,
):
    """
    Construye el grafo de dependencias de una liquidación a partir de los
    datos previamente cargados en memoria.

    El grafo contiene como nodos los detalles de liquidación y los
    resultados de bases imponibles. Cada nodo apunta a los nodos de los
    que depende.

    Las dependencias de los detalles surgen de los identificadores
    utilizados en sus fórmulas.

    Las dependencias de los resultados de bases imponibles surgen de los
    conceptos que componen cada base imponible. Una base puede estar
    asociada a distintas versiones de un mismo concepto; en ese caso,
    se utiliza como dependencia la versión que fue utilizada en la
    liquidación.

    La dirección de las aristas es:

        nodo -> dependencia

    Args:
        detalles: Diccionario de nodos de tipo "detalle", indexados por
            ("detalle", id).
        resultados_bases: Diccionario de nodos de tipo "base", indexados
            por ("base", id).
        nodos_por_identificador: Índice que relaciona cada identificador
            con su nodo correspondiente.

    Raises:
        ReferenciaInexistente: si una fórmula referencia un identificador
            que no existe.
        VersionConceptoNoLiquidada: si una base imponible referencia un
            concepto para el cual ninguna de sus versiones fue utilizada
            en la liquidación.
    """

    grafo = {
        nodo: []
        for nodo in (*detalles.keys(), *resultados_bases.keys(), )
    }

    for nodo, detalle in detalles.items():
        formula_normalizada = normalizar_formula(detalle.formula_base)

        identificadores = obtener_identificadores(formula_normalizada)

        for identificador in identificadores:
            try:
                nodo_referenciado = nodos_por_identificador[identificador]
            except KeyError:
                raise ReferenciaInexistente(identificador)

            grafo[nodo].append(nodo_referenciado)

    for nodo, resultado_base in resultados_bases.items():
        identificador_base = resultado_base.base_imponible.identificador

        if identificador_base == "detracciones":
            continue

        if identificador_base == "remuneracion_10":
            for identificador in ("remuneracion_2", "detracciones",):
                try:
                    nodo_referenciado = nodos_por_identificador[identificador]
                except KeyError:
                    raise ReferenciaInexistente(identificador)

                grafo[nodo].append(nodo_referenciado)

            continue

        if identificador_base == "remuneracion_total":
            for nodo_detalle, detalle in detalles.items():
                if detalle.concepto.tipo in (Tipo.REMUNERATIVO, Tipo.NO_REMUNERATIVO, ):
                    grafo[nodo].append(nodo_detalle)

            continue

        # todas las versiones de concepto que el usuario marco para que computen como parte del resultado_base
        versiones = resultado_base.base_imponible.versiones_concepto.all()

        # Una base sin conceptos asociados no tiene dependencias.
        if not versiones:
            continue

        versiones_por_concepto = {}

        for version in versiones:
            versiones_por_concepto.setdefault(version.concepto_id, []).append(version)

        for versiones_concepto in versiones_por_concepto.values():
            for version in versiones_concepto:
                nodo_referenciado = nodos_por_identificador.get(version.identificador_version)

                if nodo_referenciado is not None:
                    # agregar los detalles de liquidacion y bases que seran dependencias para poder calcular
                    # la base en cuestion
                    grafo[nodo].append(nodo_referenciado)

    return grafo


def agregar_nodo_por_identificador(
    nodos_por_identificador,
    identificador,
    nodo,
):
    if identificador in nodos_por_identificador:
        raise IdentificadorCalculoDuplicado(
            f"El identificador '{identificador}' está definido para más de un nodo."
        )

    nodos_por_identificador[identificador] = nodo

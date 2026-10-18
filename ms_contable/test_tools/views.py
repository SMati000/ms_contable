from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseNotAllowed, JsonResponse

from .data_generator import borrar_datos_de_negocio, generar_datos, resumen_datos, validar_base_test


def test_tools_action(request, action):
    if not settings.DEBUG:
        raise Http404
    if not request.user.is_superuser:
        raise PermissionDenied
    validar_base_test()

    if request.method == "GET" and action == "status":
        return JsonResponse({"counts": resumen_datos()})
    if request.method != "POST":
        return HttpResponseNotAllowed(["GET", "POST"])

    if action == "replace":
        resultado = generar_datos(reemplazar=True)
        mensaje = "Se reemplazaron los datos de negocio por un conjunto de prueba."
    elif action == "append":
        resultado = generar_datos()
        mensaje = "Se agregó un nuevo lote de datos ficticios."
    elif action == "clear":
        borrar_datos_de_negocio()
        resultado = {"empresas": []}
        mensaje = "Se borraron los datos de negocio de la base de test."
    else:
        raise Http404

    return JsonResponse({
        "message": mensaje,
        "result": resultado,
        "counts": resumen_datos(),
    })

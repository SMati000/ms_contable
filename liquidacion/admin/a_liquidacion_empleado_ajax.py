from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse

from core.utils import format_decimal_2
from ..models.m_detalles_liquidacion import DetalleLiquidacion
from ..services.s_expresiones import LiquidacionEmpleadoService


class LiquidacionEmpleadoAjaxMixin:
    @staticmethod
    def _es_solicitud_ajax(request):
        return request.headers.get("x-requested-with") == "XMLHttpRequest"

    def render_change_form(
        self,
        request,
        context,
        add=False,
        change=False,
        form_url="",
        obj=None,
    ):
        if request.method == "POST" and self._es_solicitud_ajax(request):
            return JsonResponse({
                "ok": False,
                "message": "Revisá los campos marcados para continuar.",
                "errors": self._errores_formulario(context),
            })

        return super().render_change_form(
            request,
            context,
            add=add,
            change=change,
            form_url=form_url,
            obj=obj,
        )

    def response_change(self, request, obj):
        es_ajax = self._es_solicitud_ajax(request)

        if "_calcular" in request.POST:
            try:
                LiquidacionEmpleadoService(obj).liquidar()
                if es_ajax:
                    return JsonResponse({
                        "ok": True,
                        "message": "Liquidación calculada correctamente.",
                        "resultados": self._resultados_calculo(obj),
                    })

                self.message_user(
                    request,
                    "Liquidación calculada correctamente.",
                    messages.SUCCESS,
                )
            except Exception as error:
                if es_ajax:
                    return JsonResponse({
                        "ok": False,
                        "message": str(error),
                        "level": "error",
                    })

                self.message_user(request, str(error), messages.ERROR)

            return HttpResponseRedirect(request.path)

        if es_ajax:
            return JsonResponse({
                "ok": True,
                "message": "Los cambios se guardaron correctamente.",
            })

        return super().response_change(request, obj)

    @staticmethod
    def _errores_formulario(context):
        errores = []
        formulario = context["adminform"].form

        for nombre, mensajes_error in formulario.errors.items():
            errores.append({
                "name": formulario.add_prefix(nombre) if nombre != "__all__" else None,
                "messages": [str(mensaje) for mensaje in mensajes_error],
            })

        for inline_admin_formset in context.get("inline_admin_formsets", []):
            formset = inline_admin_formset.formset
            for indice, errores_form in enumerate(formset.errors):
                formulario_inline = formset.forms[indice]
                for nombre, mensajes_error in errores_form.items():
                    errores.append({
                        "name": formulario_inline.add_prefix(nombre) if nombre != "__all__" else None,
                        "group": f"{formset.prefix}-group" if nombre == "__all__" else None,
                        "messages": [str(mensaje) for mensaje in mensajes_error],
                    })

            mensajes_generales = formset.non_form_errors()
            if mensajes_generales:
                errores.append({
                    "group": f"{formset.prefix}-group",
                    "messages": [str(mensaje) for mensaje in mensajes_generales],
                })

        return errores

    @staticmethod
    def _resultados_calculo(obj):
        nombres_totales = (
            "remunerativo",
            "no_remunerativo",
            "bruto",
            "descuentos",
            "neto",
            "contribuciones",
            "costo_laboral",
        )

        return {
            "totales": {
                nombre: getattr(obj, f"{nombre}_display")
                for nombre in nombres_totales
            },
            "detalles": {
                str(detalle.concepto_id): {
                    "base": detalle.base_display,
                    "importe": detalle.importe_display,
                }
                for detalle in DetalleLiquidacion.objects.filter(
                    liquidacion_empleado=obj,
                )
            },
            "bases": {
                str(resultado.pk): format_decimal_2(resultado.importe)
                for resultado in obj.resultados_bases_imponibles.all()
            },
        }

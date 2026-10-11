from urllib.parse import unquote

from django.contrib.admin import AdminSite
from django.contrib.admin.apps import AdminConfig
from django.http import Http404
from django.urls import include, path, re_path
from django.urls.resolvers import URLPattern, URLResolver
from django.views.generic import RedirectView


class MSContableAdminConfig(AdminConfig):
    default_site = "ms_contable.admin_site.MSContableAdminSite"


class MSContableAdminSite(AdminSite):
    app_route_slugs = {
        "admin": "administracion",
        "base_imponible": "parametros-salariales",
        "categoria_laboral": "estructura-laboral",
        "concepto": "configuracion-salarial",
        "empleado": "personal",
        "empresa": "organizacion",
        "grupo_concepto": "organizacion-de-conceptos",
        "liquidacion": "procesos-de-liquidacion",
        "plantilla_liquidacion": "configuracion-de-liquidaciones",
    }
    admin_route_slugs = {
        "login/": "ingresar/",
        "logout/": "cerrar-sesion/",
        "password_change/": "cambiar-clave/",
        "password_change/done/": "clave-actualizada/",
        "autocomplete/": "autocompletar/",
        "jsi18n/": "traducciones-js/",
    }
    model_action_route_slugs = {
        "add/": "agregar/",
        "<path:object_id>/history/": "<path:object_id>/historial/",
        "<path:object_id>/delete/": "<path:object_id>/eliminar/",
        "<path:object_id>/change/": "<path:object_id>/editar/",
    }
    model_route_slugs = {
        ("admin", "logentry"): "registro-de-actividad",
        ("base_imponible", "baseimponible"): "bases-imponibles",
        ("categoria_laboral", "categorialaboral"): "categorias-laborales",
        ("concepto", "concepto"): "conceptos",
        ("empleado", "empleado"): "empleados",
        ("empresa", "empresa"): "empresas",
        ("grupo_concepto", "grupoconcepto"): "grupos-de-conceptos",
        ("liquidacion", "liquidacion"): "liquidaciones",
        ("liquidacion", "liquidacionempleado"): "liquidaciones-por-empleado",
        ("plantilla_liquidacion", "plantillaliquidacion"): "plantillas-de-liquidacion",
    }

    def app_index(self, request, app_label, extra_context=None):
        if app_label == "admin":
            extra_context = {
                **(extra_context or {}),
                "title": "Registro de actividad",
            }
        return super().app_index(request, app_label, extra_context)

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)
        if app_label not in (None, "plantilla_liquidacion"):
            return app_list

        combined_app_list = (
            app_list
            if app_label is None
            else super().get_app_list(request)
        )
        apps_by_label = {app["app_label"]: app for app in combined_app_list}
        liquidation_app = apps_by_label.get("liquidacion")
        templates_app = apps_by_label.get("plantilla_liquidacion")
        if liquidation_app is None or templates_app is None:
            return app_list

        templates_app["models"].extend(liquidation_app["models"])
        templates_app["models"].sort(key=lambda model: model["name"])
        if app_label == "plantilla_liquidacion":
            return [templates_app]

        visible_app_list = [
            app for app in app_list if app["app_label"] != "liquidacion"
        ]
        if app_label is None:
            parameters_app = apps_by_label.get("base_imponible")
            templates_index = next(
                (
                    index
                    for index, app in enumerate(visible_app_list)
                    if app["app_label"] == "plantilla_liquidacion"
                ),
                None,
            )
            if parameters_app is not None and templates_index is not None:
                visible_app_list.remove(parameters_app)
                visible_app_list.insert(templates_index, parameters_app)

        return visible_app_list

    def get_urls(self):
        urls = super().get_urls()
        route_slugs = {
            f"{app_label}/{model_name}/": slug
            for (app_label, model_name), slug in self.model_route_slugs.items()
        }
        custom_urls = []

        for url in urls:
            route = getattr(getattr(url, "pattern", None), "_route", None)
            slug = route_slugs.get(route)
            if isinstance(url, URLResolver) and slug:
                model_urls = []
                for pattern in url.url_patterns:
                    model_urls.extend(
                        self._replace_route(pattern, self.model_action_route_slugs)
                    )
                custom_urls.append(path(f"{slug}/", include(model_urls)))
            elif isinstance(url, URLPattern) and url.name == "app_list":
                registered_apps = {
                    model._meta.app_label for model in self._registry
                }
                for app_label, app_slug in self.app_route_slugs.items():
                    if app_label in registered_apps:
                        custom_urls.append(
                            path(
                                f"{app_slug}/",
                                url.callback,
                                {"app_label": app_label},
                                name=url.name,
                            )
                        )
                custom_urls.append(
                    re_path(
                        url.pattern.regex.pattern,
                        RedirectView.as_view(
                            pattern_name=f"{self.name}:{url.name}",
                            permanent=False,
                            query_string=True,
                        ),
                    )
                )
            elif isinstance(url, URLPattern):
                custom_urls.extend(self._replace_route(url, self.admin_route_slugs))
            else:
                custom_urls.append(url)

        return custom_urls

    def _replace_route(self, url, route_slugs):
        route = getattr(url.pattern, "_route", None)
        model_admin = getattr(url.callback, "model_admin", None)
        callback = url.callback
        if model_admin is not None and "<path:object_id>" in (route or ""):
            callback = self.admin_view(
                self._missing_object_404_view(callback, model_admin)
            )

        if route == "<path:object_id>/" and url.name is None:
            if model_admin is not None:
                return [path(route, callback)]

        localized_route = route_slugs.get(route)
        if localized_route is None:
            if callback is not url.callback:
                return [path(route, callback, url.default_args, name=url.name)]
            return [url]
        localized_url = path(
            localized_route, callback, url.default_args, name=url.name
        )
        if url.name is None:
            return [localized_url]
        legacy_url = path(
            route,
            RedirectView.as_view(
                pattern_name=f"{self.name}:{url.name}",
                permanent=False,
                query_string=True,
            ),
        )
        return [localized_url, legacy_url]

    def _missing_object_404_view(self, view, model_admin):
        def show_not_found(request, object_id, *args, **kwargs):
            if (
                model_admin.has_view_or_change_permission(request)
                or model_admin.has_delete_permission(request)
            ) and model_admin.get_object(request, unquote(object_id)) is None:
                raise Http404
            return view(request, object_id, *args, **kwargs)

        return show_not_found

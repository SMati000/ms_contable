from functools import update_wrapper

from django.conf import settings
from django.contrib import admin
from django.http import Http404, HttpResponseRedirect
from django.urls import include, path
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect


admin.site.site_header = settings.APP_NAME
admin.site.site_title = settings.APP_NAME
admin.site.index_title = "Panel de Administración"


def test_admin_view(view, cacheable=False):
    def inner(request, *args, **kwargs):
        if request.path_info.rstrip("/") == "/test/login":
            raise Http404

        if not admin.site.has_permission(request):
            return HttpResponseRedirect("/")

        return view(request, *args, **kwargs)

    if not cacheable:
        inner = never_cache(inner)
    if not getattr(view, "csrf_exempt", False):
        inner = csrf_protect(inner)
    return update_wrapper(inner, view)


def test_login(request):
    if request.method == "GET" and request.GET.get("next") == "/test/":
        return HttpResponseRedirect("/")
    return admin.site.login(request)


if settings.DEBUG:
    admin.site.admin_view = test_admin_view
    each_context = admin.site.each_context

    def test_each_context(request):
        context = each_context(request)
        context["show_test_devtools"] = (
            request.path_info.startswith("/test/")
            and request.user.is_authenticated
            and request.user.is_superuser
        )
        return context

    admin.site.each_context = test_each_context
    admin_patterns, admin_app_name, admin_namespace = admin.site.urls
    admin_patterns = [
        pattern
        for pattern in admin_patterns
        if getattr(pattern, "name", None) != "login"
    ]
    from .test_tools.views import test_tools_action

    urlpatterns = [
        path("", test_login, name="test_login"),
        path(
            "test/__devtools/<str:action>/",
            admin.site.admin_view(test_tools_action),
            name="test_devtools_action",
        ),
        path("test/", include((admin_patterns, admin_app_name), namespace=admin_namespace)),
    ]
else:
    urlpatterns = []

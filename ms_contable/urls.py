from django.contrib import admin
from django.conf import settings
from django.urls import path
from django.views.generic.base import RedirectView

from core.forms import RememberSessionAdminAuthenticationForm
from core.views import admin_login, first_run
from ms_contable.views import check_for_app_update


admin.site.site_header = settings.APP_NAME
admin.site.site_title = settings.APP_NAME
admin.site.index_title = "Panel de Administración"
admin.site.login_form = RememberSessionAdminAuthenticationForm


urlpatterns = [
    path("", RedirectView.as_view(pattern_name="first-run", permanent=False)),
    path("crear_cuenta/", first_run, name="first-run"),
    path("api/version/", check_for_app_update, name="check-app-update"),
    path("admin/ingresar/", admin_login, name="admin-login"),
    path("admin/", admin.site.urls),
]

handler404 = "ms_contable.views.page_not_found"
handler500 = "ms_contable.views.server_error"

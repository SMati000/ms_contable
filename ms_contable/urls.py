from django.contrib import admin
from django.conf import settings
from django.urls import path
from django.views.generic.base import RedirectView

from core.forms import RememberSessionAdminAuthenticationForm
from core.views import admin_login, first_run


admin.site.site_header = settings.APP_NAME
admin.site.site_title = settings.APP_NAME
admin.site.index_title = "Panel de Administración"
admin.site.login_form = RememberSessionAdminAuthenticationForm


urlpatterns = [
    path("", RedirectView.as_view(pattern_name="first-run", permanent=False)),
    path("create/", first_run, name="first-run"),
    path("admin/login/", admin_login, name="admin-login"),
    path("admin/", admin.site.urls),
]

from pathlib import Path
from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import get_template
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(
    STORAGES={
        **settings.STORAGES,
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
)
class AdminThemeToggleTemplateTests(TestCase):
    def test_custom_theme_toggle_template_is_used(self):
        """
        Comprobar que el template resuelto sea el personalizado y no el por defecto de Django
        """

        template = get_template("admin/color_theme_toggle.html")

        expected_path = (
            Path(settings.BASE_DIR)
            / "templates"
            / "admin"
            / "color_theme_toggle.html"
        )

        self.assertEqual(
            Path(template.origin.name).resolve(),
            expected_path.resolve(),
        )

    def test_theme_toggle_is_rendered_in_admin(self):
        """
        Comprobar que el admin renderice el template personalizado al mostrar su página principal
        """

        User = get_user_model()
        user = User.objects.create_superuser(
            username="testadmin",
            email="admin@example.com",
            password="test-password",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "admin/color_theme_toggle.html",
        )

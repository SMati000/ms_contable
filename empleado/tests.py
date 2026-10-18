from django.test import TestCase

from .forms import EmpleadoAdminForm


class EmpleadoAdminFormTests(TestCase):
    def test_empresa_mal_formada_produce_error_de_formulario(self):
        form = EmpleadoAdminForm(data={"empresa": "no-es-un-id"})

        self.assertFalse(form.is_valid())
        self.assertIn("empresa", form.errors)

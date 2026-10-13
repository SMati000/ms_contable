import os
from pathlib import Path


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ms_contable.settings_test")

import django

django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command


def ensure_test_account():
    username = settings.TEST_ACCOUNT_USERNAME
    if not username.strip():
        raise SystemExit("MS_CONTABLE_TEST_USERNAME no puede estar vacío.")

    user_model = get_user_model()
    user = user_model.objects.filter(username=username).first()

    if user is None:
        user = user_model.objects.create_superuser(
            username=username,
            email="",
            password=settings.TEST_ACCOUNT_PASSWORD,
        )
    else:
        changed_fields = []
        for field in ("is_active", "is_staff", "is_superuser"):
            if not getattr(user, field):
                setattr(user, field, True)
                changed_fields.append(field)
        user.set_password(settings.TEST_ACCOUNT_PASSWORD)
        changed_fields.append("password")
        if changed_fields:
            user.save(update_fields=changed_fields)

    print(f"Cuenta de prueba lista: {username}")


def main():
    if not settings.DEBUG:
        raise SystemExit(
            "La instancia de test solo puede iniciarse con DEBUG=True en ms_contable/settings.py."
        )

    if not 1 <= settings.TEST_SERVER_PORT <= 65535:
        raise SystemExit("MS_CONTABLE_TEST_PORT debe estar entre 1 y 65535.")

    test_database = Path(settings.DATABASES["default"]["NAME"]).resolve()
    expected_test_database = (settings.BASE_DIR / "data" / "db_test.sqlite3").resolve()
    original_database = (settings.BASE_DIR / "data" / "db.sqlite3").resolve()

    if test_database != expected_test_database or test_database == original_database:
        raise SystemExit("La instancia de prueba no está configurada con una base aislada.")

    call_command("migrate", interactive=False)
    ensure_test_account()
    address = f"127.0.0.1:{settings.TEST_SERVER_PORT}"
    print(f"Acceso de prueba: http://{address}/ (panel tras iniciar sesión: /test/)")
    call_command("runserver", address, use_reloader=False)


if __name__ == "__main__":
    main()

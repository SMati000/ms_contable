from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ms_contable.database_encryption import prepare_encrypted_databases
from ms_contable.database_keys import load_or_create_database_key


class Command(BaseCommand):
    help = "Cifra la base de MS Contable y sus respaldos con SQLCipher."
    requires_system_checks = []

    def handle(self, *args, **options):
        key_path = getattr(settings, "DATABASE_KEY_FILE", None)
        if key_path is None:
            raise CommandError("Este comando requiere ms_contable.settings_windows.")

        database_path = settings.DATABASES["default"]["NAME"]
        paths = [database_path]
        paths.extend(Path(f"{database_path}{suffix}") for suffix in (".1.bak", ".2.bak"))
        try:
            prepare_encrypted_databases(paths, key_path, load_or_create_database_key)
        except Exception as error:
            raise CommandError(str(error)) from error
        self.stdout.write(self.style.SUCCESS("Base y respaldos preparados con SQLCipher."))

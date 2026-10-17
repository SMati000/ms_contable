import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.db import connections
from django.test import SimpleTestCase, override_settings
from sqlcipher3 import dbapi2 as Database

from ms_contable.backends.sqlcipher.base import DatabaseWrapper
from ms_contable.database_encryption import (
    encrypt_plaintext_database,
    is_plaintext_sqlite,
    prepare_encrypted_databases,
)
from ms_contable.database_keys import load_or_create_database_key


KEY = "7f" * 32


class DatabaseEncryptionTests(SimpleTestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)

    def create_plain_database(self, path):
        connection = sqlite3.connect(path)
        try:
            connection.executescript(
                """
                CREATE TABLE sample (id INTEGER PRIMARY KEY, value TEXT NOT NULL);
                INSERT INTO sample (value) VALUES ('dato conservado');
                CREATE TRIGGER sample_uppercase AFTER INSERT ON sample
                BEGIN
                    UPDATE sample SET value = upper(value) WHERE id = NEW.id;
                END;
                """
            )
        finally:
            connection.close()

    def test_converts_sqlite_with_schema_data_and_triggers(self):
        path = self.root / "db.sqlite3"
        self.create_plain_database(path)

        encrypt_plaintext_database(path, KEY)

        self.assertFalse(is_plaintext_sqlite(path))
        connection = Database.connect(str(path))
        try:
            connection.execute(f"PRAGMA key = '{KEY}'")
            self.assertEqual(
                connection.execute("SELECT value FROM sample WHERE id = 1").fetchone(),
                ("dato conservado",),
            )
            connection.execute("INSERT INTO sample (value) VALUES ('trigger')")
            self.assertEqual(
                connection.execute("SELECT value FROM sample WHERE id = 2").fetchone(),
                ("TRIGGER",),
            )
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone(), ("ok",))
        finally:
            connection.close()

    def test_wrong_key_fails_without_changing_encrypted_database(self):
        path = self.root / "db.sqlite3"
        self.create_plain_database(path)
        encrypt_plaintext_database(path, KEY)
        original = path.read_bytes()

        with self.assertRaises(Database.Error):
            connection = Database.connect(str(path))
            try:
                connection.execute(f"PRAGMA key = '{'00' * 32}'")
                connection.execute("SELECT count(*) FROM sqlite_master").fetchone()
            finally:
                connection.close()

        self.assertEqual(path.read_bytes(), original)

    def test_converts_database_and_legacy_backups_once(self):
        database = self.root / "db.sqlite3"
        backup = self.root / "db.sqlite3.1.bak"
        self.create_plain_database(database)
        self.create_plain_database(backup)
        key_path = self.root / "config" / "database-key.dpapi"

        def load_test_key(path):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch(exist_ok=True)
            return KEY

        prepare_encrypted_databases(
            [database, backup], key_path, load_test_key
        )
        prepare_encrypted_databases([database, backup], key_path, load_test_key)

        self.assertFalse(is_plaintext_sqlite(database))
        self.assertFalse(is_plaintext_sqlite(backup))

    def test_refuses_unknown_database_when_protected_key_is_missing(self):
        path = self.root / "db.sqlite3"
        path.write_bytes(b"not a SQLite header")

        with self.assertRaisesRegex(RuntimeError, "falta la clave protegida"):
            prepare_encrypted_databases(
                [path], self.root / "missing-key.dpapi", lambda _: self.fail("No debe crear clave")
            )

        self.assertEqual(path.read_bytes(), b"not a SQLite header")

    def test_protects_and_reuses_database_key_with_windows_dpapi(self):
        path = self.root / "config" / "database-key.dpapi"

        first_key = load_or_create_database_key(path)
        second_key = load_or_create_database_key(path)

        self.assertEqual(first_key, second_key)
        self.assertEqual(len(first_key), 64)
        self.assertNotIn(bytes.fromhex(first_key), path.read_bytes())

    def test_django_sqlcipher_backend_executes_queries(self):
        path = self.root / "db.sqlite3"
        self.create_plain_database(path)
        encrypt_plaintext_database(path, KEY)
        database_settings = connections.databases["default"].copy()
        database_settings["ENGINE"] = "ms_contable.backends.sqlcipher"
        database_settings["NAME"] = str(path)
        database_settings["OPTIONS"] = {}

        with override_settings(DATABASE_KEY_FILE=self.root / "database-key.dpapi"):
            connection = DatabaseWrapper(database_settings, "sqlcipher_test")
            self.addCleanup(connection.close)
            with patch(
                "ms_contable.backends.sqlcipher.base.load_or_create_database_key",
                return_value=KEY,
            ):
                with connection.cursor() as cursor:
                    cursor.execute("SELECT value FROM sample WHERE id = %s", (1,))
                    self.assertEqual(cursor.fetchone(), ("dato conservado",))

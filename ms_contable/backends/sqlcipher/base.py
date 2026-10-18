from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.backends.sqlite3.base import DatabaseWrapper as SQLiteDatabaseWrapper
from django.db.backends.sqlite3.base import register_functions
from django.utils.asyncio import async_unsafe
from sqlcipher3 import dbapi2 as Database

from ms_contable.database_keys import load_or_create_database_key, sqlcipher_key_pragma

from .cursor import SQLCipherCursorWrapper


class DatabaseWrapper(SQLiteDatabaseWrapper):
    Database = Database

    def create_cursor(self, name=None):
        return self.connection.cursor(factory=SQLCipherCursorWrapper)

    @async_unsafe
    def get_new_connection(self, conn_params):
        connection = Database.connect(**conn_params)
        try:
            key = load_or_create_database_key(settings.DATABASE_KEY_FILE)
            connection.execute(sqlcipher_key_pragma(key))
            connection.execute("SELECT count(*) FROM sqlite_master").fetchone()
            register_functions(connection)
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA legacy_alter_table = OFF")
            for init_command in self.init_commands:
                if init_command := init_command.strip():
                    connection.execute(init_command)
            return connection
        except Database.Error as error:
            connection.close()
            raise ImproperlyConfigured(
                "No se pudo abrir la base de MS Contable con la clave SQLCipher. "
                "Verificá el archivo de clave protegido y la base importada."
            ) from error

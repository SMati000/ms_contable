import uuid
from pathlib import Path

from sqlcipher3 import dbapi2 as Database

from ms_contable.database_keys import sqlcipher_key_pragma


SQLITE_HEADER = b"SQLite format 3\x00"


def is_plaintext_sqlite(path):
    try:
        with Path(path).open("rb") as database_file:
            return database_file.read(len(SQLITE_HEADER)) == SQLITE_HEADER
    except FileNotFoundError:
        return False


def _verify_encrypted_database(path, key):
    connection = Database.connect(str(path))
    try:
        connection.execute(sqlcipher_key_pragma(key))
        connection.execute("SELECT count(*) FROM sqlite_master").fetchone()
        result = connection.execute("PRAGMA integrity_check").fetchone()
        if result != ("ok",):
            raise RuntimeError(f"La comprobación de integridad falló para {path}: {result}")
    finally:
        connection.close()


def encrypt_plaintext_database(path, key):
    path = Path(path)
    if not is_plaintext_sqlite(path):
        raise RuntimeError(f"No se reconoce una base SQLite sin cifrar: {path}")

    encrypted_path = path.with_name(f"{path.name}.{uuid.uuid4().hex}.encrypted")
    try:
        connection = Database.connect(str(path))
        attached = False
        try:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()
            if integrity != ("ok",):
                raise RuntimeError(f"La base SQLite tiene errores de integridad: {path}")

            escaped_path = str(encrypted_path).replace("'", "''")
            escaped_key = key.replace("'", "''")
            connection.execute(
                f"ATTACH DATABASE '{escaped_path}' AS encrypted KEY '{escaped_key}'"
            )
            attached = True
            connection.execute("SELECT sqlcipher_export('encrypted')").fetchone()
            connection.execute("DETACH DATABASE encrypted")
            attached = False
        except Exception:
            if attached:
                try:
                    connection.execute("DETACH DATABASE encrypted")
                except Database.Error:
                    pass
            raise
        finally:
            connection.close()

        if is_plaintext_sqlite(encrypted_path):
            raise RuntimeError("SQLCipher produjo un archivo sin cifrar.")
        _verify_encrypted_database(encrypted_path, key)
        for suffix in ("-wal", "-shm", "-journal"):
            sidecar = Path(f"{path}{suffix}")
            if sidecar.exists():
                raise RuntimeError(
                    f"Quedó un archivo SQLite auxiliar; no se reemplazó la base original: {sidecar}"
                )
        encrypted_path.replace(path)
    finally:
        encrypted_path.unlink(missing_ok=True)


def prepare_encrypted_databases(paths, key_path, key_loader):
    paths = [Path(path) for path in paths]
    existing = [path for path in paths if path.exists()]
    if existing and not Path(key_path).exists():
        unknown = [path for path in existing if not is_plaintext_sqlite(path)]
        if unknown:
            raise RuntimeError(
                "Hay una base que no es SQLite sin cifrar y falta la clave protegida. "
                "Se conservó el archivo; restaurá la clave original antes de continuar."
            )

    key = key_loader(key_path)
    for path in existing:
        if is_plaintext_sqlite(path):
            encrypt_plaintext_database(path, key)
        else:
            _verify_encrypted_database(path, key)
    return key

import ctypes
import os
import secrets
import sys
import time
from ctypes import wintypes
from pathlib import Path


_KEY_FILE_MAGIC = b"MSCONT-SQLCIPHER-KEY\x01"
_CRYPTPROTECT_UI_FORBIDDEN = 0x1


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def _blob(data):
    buffer = ctypes.create_string_buffer(data)
    return _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte))), buffer


def _protect(data):
    if sys.platform != "win32":
        raise RuntimeError("La protección de la clave de base requiere Windows.")

    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    input_blob, input_buffer = _blob(data)
    output_blob = _DataBlob()
    if not crypt32.CryptProtectData(
        ctypes.byref(input_blob),
        "MS Contable SQLCipher",
        None,
        None,
        None,
        _CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(output_blob),
    ):
        raise ctypes.WinError(ctypes.get_last_error())

    try:
        return ctypes.string_at(output_blob.pbData, output_blob.cbData)
    finally:
        kernel32.LocalFree(output_blob.pbData)
        del input_buffer


def _unprotect(data):
    if sys.platform != "win32":
        raise RuntimeError("La protección de la clave de base requiere Windows.")

    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    input_blob, input_buffer = _blob(data)
    output_blob = _DataBlob()
    description = wintypes.LPWSTR()
    if not crypt32.CryptUnprotectData(
        ctypes.byref(input_blob),
        ctypes.byref(description),
        None,
        None,
        None,
        _CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(output_blob),
    ):
        raise ctypes.WinError(ctypes.get_last_error())

    try:
        return ctypes.string_at(output_blob.pbData, output_blob.cbData)
    finally:
        kernel32.LocalFree(output_blob.pbData)
        if description:
            kernel32.LocalFree(description)
        del input_buffer


def _read_key(path):
    contents = path.read_bytes()
    if not contents.startswith(_KEY_FILE_MAGIC):
        raise RuntimeError(f"El archivo de clave de la base no tiene un formato válido: {path}")

    key = _unprotect(contents[len(_KEY_FILE_MAGIC) :])
    if len(key) != 32:
        raise RuntimeError(f"La clave protegida de la base no tiene un tamaño válido: {path}")
    return key.hex()


def load_or_create_database_key(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    for _ in range(250):
        if path.exists():
            return _read_key(path)

        key = secrets.token_bytes(32)
        protected = _KEY_FILE_MAGIC + _protect(key)
        try:
            descriptor = path.open("xb")
        except FileExistsError:
            time.sleep(0.02)
            continue

        try:
            with descriptor:
                descriptor.write(protected)
                descriptor.flush()
                os.fsync(descriptor.fileno())
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return key.hex()

    raise RuntimeError(f"No se pudo leer o crear la clave protegida de la base: {path}")


def sqlcipher_key_pragma(key):
    if len(key) != 64 or any(character not in "0123456789abcdefABCDEF" for character in key):
        raise ValueError("La clave de SQLCipher debe contener 32 bytes en hexadecimal.")
    return f"PRAGMA key = '{key}'"

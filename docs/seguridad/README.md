# Cifrado de la base local con SQLCipher

## Alcance

La integración se usa en la instalación nativa de Windows mediante `ms_contable.settings_windows`. El desarrollo y Docker siguen usando SQLite estándar. SQLCipher conserva el formato y el comportamiento de SQLite, pero cifra el archivo de la base en disco.

## Cómo se conecta Django

```text
Django ORM → ms_contable.backends.sqlcipher → sqlcipher3 → SQLCipher → db.sqlite3 cifrada
```

Django no incluye soporte nativo para SQLCipher. `ms_contable.backends.sqlcipher` adapta la conexión: hereda el backend SQLite de Django para conservar sus operaciones, transacciones y soporte de migraciones, y sustituye el controlador estándar por `sqlcipher3`. Su cursor adapta los parámetros SQL que genera Django al formato que espera el controlador.

Al abrir la conexión, el backend obtiene la clave, ejecuta `PRAGMA key` antes de leer metadatos de la base y configura las funciones y opciones que Django espera. Desde ese momento, el ORM consulta y actualiza la base normalmente; SQLCipher cifra y descifra sus páginas de forma transparente mientras lee y escribe.

## Clave

En el primer inicio se genera una clave aleatoria de 32 bytes. Windows DPAPI la protege para el usuario actual y se guarda en:

```text
%LOCALAPPDATA%\MSContable\config\database-key.dpapi
```

La clave no se guarda en el repositorio ni junto a la base en texto plano. Para recuperar o trasladar una instalación hay que conservar la base **y** el archivo protegido de clave. DPAPI vincula esa clave al perfil de Windows que la creó; copiar esos archivos a otro usuario o PC requiere un procedimiento de traslado compatible.

## Conversión y migraciones

El comando `prepare_encrypted_database` prepara la base existente y los respaldos `.1.bak` y `.2.bak` antes de las migraciones de Django. Si encuentra una base SQLite sin cifrar, SQLCipher exporta su esquema y datos a un archivo cifrado temporal; luego se valida la integridad antes de reemplazar la original. La operación se puede repetir sobre bases ya cifradas.

La dependencia `sqlcipher3` está fijada en `requirements-windows.txt`. El SQLite estándar no puede abrir directamente los archivos cifrados: para trabajar con ellos hay que usar la configuración Windows y el controlador SQLCipher.

## Archivos relacionados

- `ms_contable/backends/sqlcipher/`: conexión y cursor compatibles con Django.
- `ms_contable/database_keys.py`: generación y protección DPAPI de la clave.
- `ms_contable/database_encryption.py`: conversión y validación de bases y respaldos.
- `ms_contable/settings_windows.py`: selección del backend y rutas de configuración.
- `core/management/commands/prepare_encrypted_database.py`: preparación antes de migrar.
- `core/tests/test_database_encryption.py`: pruebas de conversión y compatibilidad.

El cifrado protege la base almacenada en disco. No cifra automáticamente archivos exportados (por ejemplo, PDF o TXT), y mientras MS Contable está ejecutándose el proceso necesita acceso a la clave para consultar los datos.

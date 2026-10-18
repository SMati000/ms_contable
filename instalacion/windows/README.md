# Instalador nativo de Windows

El instalador usa Inno Setup, un runtime de Python embebido y Caddy. No requiere Docker. Está localizado en español y solicita permisos de administrador para instalar los binarios en `Program Files` y registrar el nombre local en `hosts`.

## Preparar y compilar

Ejecutá `build.ps1` desde PowerShell con CPython x64 3.11.9 a 3.13. El script prepara el runtime embebido, instala las dependencias de `requirements-windows.txt`, copia el código fuente sin datos locales y genera los archivos estáticos. Busca Inno Setup en `.tools` o en el `PATH`; si está en otra ubicación, indicá su ruta con `-InnoCompiler`. Caddy se reutiliza desde `build\caddy` o se descarga desde el sitio oficial junto con su licencia.

La versión del instalador se toma de `APP_VERSION` en `ms_contable/settings.py`. El ejecutable queda en `dist\https\MSContable-Setup-version.exe`. Cada compilación exitosa reemplaza la salida anterior y deja un solo instalador en `dist`; la limpieza se hace después de verificar que el nuevo ejecutable se haya generado correctamente.

El instalador incluye SQLCipher Community Edition y su licencia en `licenses\SQLCipher-LICENSE.txt`. La base de datos y sus dos respaldos se cifran con SQLCipher. La clave aleatoria se protege con DPAPI de Windows para el usuario que ejecuta la aplicación y se guarda en `%LOCALAPPDATA%\MSContable\config\database-key.dpapi`; no se escribe la clave en texto plano. Al importar una base SQLite anterior, el inicializador exporta y comprueba la base y los respaldos cifrados antes de continuar con las migraciones. Si una conversión falla, conserva el archivo de origen y cancela la inicialización.

## HTTPS local

Caddy escucha solo en loopback y publica la aplicación en `https://mscontable` por el puerto HTTPS estándar 443. El instalador agrega `mscontable` al archivo `hosts` de Windows apuntando a `127.0.0.1` y `::1`; al desinstalar, quita únicamente el bloque que agregó. Waitress acepta conexiones solo desde `127.0.0.1:8000`; el puerto HTTP queda interno y no se abre en la red local. El panel administrativo de Caddy está desactivado.

Durante la instalación, el instalador agrega la autoridad certificadora local de Caddy al almacén `Root` del usuario actual, sin abrir el aviso de confianza de Windows. El certificado y su clave privada se conservan bajo `%LOCALAPPDATA%\MSContable\caddy`; el desinstalador quita la confianza y elimina esa carpeta. La base cifrada y los logs permanecen bajo `%LOCALAPPDATA%\MSContable\data` y `%LOCALAPPDATA%\MSContable\logs`. La clave secreta de Django se genera una vez y se conserva en `%LOCALAPPDATA%\MSContable\config\django-secret-key`.

La clave de base depende del perfil de Windows que la creó. Para restaurar datos en otro perfil o en otra PC hará falta un mecanismo de migración/exportación que traslade la base y su clave de forma controlada; copiar solo el archivo SQLite no alcanza. El proyecto todavía no incluye ese flujo de traslado.

La configuración inicial permite importar opcionalmente una base anterior y aplicar las migraciones. No abre una consola ni solicita crear el usuario administrador: la primera cuenta se crea desde la página de bienvenida al abrir MS Contable. La instalación crea el acceso directo del menú Inicio; la casilla del escritorio y la opción de abrir la app al finalizar son independientes.

El certificado local habilita HTTPS entre el navegador y Caddy. Caddy reenvía a Waitress por HTTP en loopback; ambos puertos están limitados a este equipo.

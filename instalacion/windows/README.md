# Instalador nativo de Windows

El instalador copia una distribución portable de CPython, las dependencias de `requirements-windows.txt` y el código de MS Contable. Waitress ejecuta Django en `127.0.0.1:8000`. La computadora donde se instala no necesita Python, Docker ni conexión a Internet.

## Construcción

Antes de construir por primera vez, instalá las herramientas de desarrollo dentro del proyecto:

```powershell
.\instalacion\windows\setup-build-tools.ps1
```

Python e Inno Setup quedan en `instalacion/windows/.tools`, excluidos de Git. El script comprueba sus firmas y no modifica el `PATH`.

En Windows de 64 bits, el script deja CPython 3.13 e Inno Setup dentro del repositorio. Para construir necesita conexión a Internet para descargar el runtime embebible de Python y las dependencias fijadas.

Desde la raíz del repositorio, ejecutá:

```powershell
.\instalacion\windows\build.ps1
```

El proceso prepara el runtime, copia el código sin incluir las carpetas locales de datos ni archivos PDF, ejecuta `collectstatic` y compila:

```text
instalacion/windows/dist/MSContable-Setup-version.exe
```

La aplicación usa la variable de entorno `APP_VERSION` cuando contiene una versión concreta. Si no está definida o vale `latest`, usa `DEFAULT_APP_VERSION` en `ms_contable/settings.py`.

En cada push o pull request, GitHub Actions instala las dependencias en Windows, valida Python y Django, corre los tests, revisa la sintaxis de PowerShell, construye el `.exe` y lo instala en modo silencioso para probar migraciones, Waitress, la bienvenida inicial y los archivos estáticos. Si todo pasa, publica el instalador como artefacto descargable durante 14 días. Para reconstruirlo localmente después de un cambio, ejecutá otra vez `build.ps1`.

## Instalación y uso

El instalador es por usuario y no requiere permisos de administrador. Al terminar, ofrece inicializar la base y abrir MS Contable. En el primer inicio, la pantalla de bienvenida permite crear la cuenta administradora. Si se migra desde Docker, detené la aplicación anterior y pegá la ruta completa a `data\db.sqlite3` cuando lo solicite.

El menú Inicio contiene accesos para abrir MS Contable sin mostrar una terminal, detener el servidor e inicializar o actualizar la base. Este último abre PowerShell para solicitar los datos de configuración. Los datos y logs se conservan en:

```text
%LOCALAPPDATA%\MSContable\data
%LOCALAPPDATA%\MSContable\logs
```

Cada actualización detiene la instancia activa, conserva dos respaldos SQLite y ejecuta las migraciones. La desinstalación conserva datos, respaldos y logs.

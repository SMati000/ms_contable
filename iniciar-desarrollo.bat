@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo No se encontro el entorno virtual .venv.
    echo Crea el entorno e instala requirements.txt antes de iniciar.
    pause
    exit /b 1
)

set "DJANGO_SECRET_KEY=dev-only-local"
set "DJANGO_DEBUG=1"

echo Iniciando MS Contable en http://127.0.0.1:8001
echo Para detenerlo, presiona Ctrl+C.
echo.

".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8001
pause

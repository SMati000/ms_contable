#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

COMPOSE_FILE="$SCRIPT_DIR/compose.yaml"
ENV_FILE="$SCRIPT_DIR/.env"

DATA_DIR="$SCRIPT_DIR/data"
LOGS_DIR="$SCRIPT_DIR/logs"

DB_FILE="$DATA_DIR/db.sqlite3"
BACKUP1="$DATA_DIR/db.sqlite3.1.bak"
BACKUP2="$DATA_DIR/db.sqlite3.2.bak"


pause_script() {
    echo
    read -r -p "Presione ENTER para continuar..."
}


test_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo
        echo "ERROR: Docker no esta disponible."
        echo "Verifique que Docker este instalado y ejecutandose."
        return 1
    fi

    if ! docker compose version >/dev/null 2>&1; then
        echo
        echo "ERROR: Docker Compose no esta disponible."
        return 1
    fi

    return 0
}


get_app_version() {
    if [[ ! -f "$ENV_FILE" ]]; then
        echo "ERROR: No existe el archivo .env." >&2
        return 1
    fi

    local version
    version="$(grep -E '^[[:space:]]*APP_VERSION[[:space:]]*=' "$ENV_FILE" \
        | head -n 1 \
        | cut -d '=' -f 2- \
        | xargs)"

    if [[ -z "$version" ]]; then
        echo "ERROR: No se encontro APP_VERSION en .env." >&2
        return 1
    fi

    echo "$version"
}


ensure_django_secret_key() {
    if grep -Eq '^[[:space:]]*DJANGO_SECRET_KEY[[:space:]]*=[[:space:]]*[^[:space:]]' "$ENV_FILE"; then
        return 0
    fi

    if ! command -v openssl >/dev/null 2>&1; then
        echo "ERROR: Se necesita OpenSSL para generar la clave secreta." >&2
        return 1
    fi

    local secret_key
    local temp_file
    secret_key="$(openssl rand -base64 48 | tr -d '\r\n')"

    if [[ -z "$secret_key" ]]; then
        echo "ERROR: No se pudo generar la clave secreta." >&2
        return 1
    fi

    temp_file="$ENV_FILE.tmp"
    sed -E '/^[[:space:]]*DJANGO_SECRET_KEY[[:space:]]*=/d' "$ENV_FILE" > "$temp_file"
    printf 'DJANGO_SECRET_KEY=%s\n' "$secret_key" >> "$temp_file"
    chmod 600 "$temp_file"
    mv "$temp_file" "$ENV_FILE"

    echo "Se genero una clave secreta y se guardo en .env."
}


get_app_port() {
    if [[ ! -f "$ENV_FILE" ]]; then
        echo "8000"
        return
    fi

    local port
    port="$(grep -E '^[[:space:]]*PORT[[:space:]]*=' "$ENV_FILE" \
        | head -n 1 \
        | cut -d '=' -f 2- \
        | xargs)"

    if [[ -z "$port" ]]; then
        echo "8000"
    else
        echo "$port"
    fi
}


ensure_directories() {
    mkdir -p "$DATA_DIR"
    mkdir -p "$LOGS_DIR"
}


invoke_compose() {
    docker compose -f "$COMPOSE_FILE" "$@"
}


get_container_status() {
    docker compose -f "$COMPOSE_FILE" ps
}


backup_database() {
    if [[ ! -f "$DB_FILE" ]]; then
        echo "No existe una base de datos para respaldar."
        return
    fi

    echo "Creando backup de SQLite..."

    if [[ -f "$BACKUP1" ]]; then
        if [[ -f "$BACKUP2" ]]; then
            rm -f "$BACKUP2"
        fi

        mv "$BACKUP1" "$BACKUP2"
    fi

    cp "$DB_FILE" "$BACKUP1"

    echo "Backup creado: $BACKUP1"
}


wait_for_application() {
    local max_attempts=30
    local port
    port="$(get_app_port)"

    echo
    echo "Esperando que la aplicacion este disponible..."

    for ((i = 1; i <= max_attempts; i++)); do
        if curl -fsS --max-time 2 "http://localhost:$port" >/dev/null 2>&1; then
            echo "Aplicacion disponible en http://localhost:$port"
            return 0
        fi

        sleep 2
    done

    echo "La aplicacion no respondio dentro del tiempo esperado."
    return 1
}


initialize_superuser() {
    echo
    echo "Inicializacion del usuario administrador"
    echo

    read -r -p "Usuario administrador: " username

    if [[ -z "$username" ]]; then
        echo "ERROR: El usuario no puede estar vacio."
        return 1
    fi

    read -r -s -p "Password: " password
    echo

    read -r -s -p "Confirmar password: " password_confirmation
    echo

    if [[ "$password" != "$password_confirmation" ]]; then
        echo "ERROR: Las passwords no coinciden."
        return 1
    fi

    if [[ -z "$password" ]]; then
        echo "ERROR: La password no puede estar vacia."
        return 1
    fi

    echo
    echo "Creando superusuario..."

    export DJANGO_SUPERUSER_USERNAME="$username"
    export DJANGO_SUPERUSER_PASSWORD="$password"
    export DJANGO_SUPERUSER_EMAIL="placeholder@email.com"

    invoke_compose run --rm \
        -e DJANGO_SUPERUSER_USERNAME \
        -e DJANGO_SUPERUSER_PASSWORD \
        -e DJANGO_SUPERUSER_EMAIL \
        ms_contable \
        python manage.py createsuperuser --noinput

    unset DJANGO_SUPERUSER_USERNAME
    unset DJANGO_SUPERUSER_PASSWORD
    unset DJANGO_SUPERUSER_EMAIL

    echo "Superusuario creado."
}


install_app() {
    ensure_directories

    local version
    version="$(get_app_version)"

    echo
    echo "========================================"
    echo " Instalacion"
    echo "========================================"
    echo
    echo "Version: $version"
    echo

    if [[ -f "$DB_FILE" ]]; then
        echo "Ya existe una base de datos."
        echo "La instalacion inicial no se realizara para evitar sobrescribir datos."
        return
    fi

    echo "Descargando imagen..."
    invoke_compose pull

    echo
    echo "Ejecutando migraciones..."
    invoke_compose run --rm \
        ms_contable \
        python manage.py migrate --noinput

    initialize_superuser

    echo
    echo "Iniciando aplicacion..."
    invoke_compose up -d

    if ! wait_for_application; then
        echo
        echo "La aplicacion fue iniciada pero no se pudo verificar su disponibilidad."
        return
    fi

    echo
    echo "Instalacion completada correctamente."
}


update_app() {
    ensure_directories

    local version
    version="$(get_app_version)"

    echo
    echo "========================================"
    echo " Actualizacion"
    echo "========================================"
    echo
    echo "Version objetivo: $version"
    echo

    echo "Deteniendo aplicacion..."
    invoke_compose down

    backup_database

    echo
    echo "Descargando imagen $version..."
    invoke_compose pull

    echo
    echo "Ejecutando migraciones..."
    invoke_compose run --rm \
        ms_contable \
        python manage.py migrate --noinput

    echo
    echo "Iniciando nueva version..."
    invoke_compose up -d

    if ! wait_for_application; then
        echo
        echo "ATENCION: la nueva version no pudo ser verificada."
        echo "El backup se encuentra en:"
        echo "  $BACKUP1"
        return
    fi

    echo
    echo "Actualizacion completada correctamente."
}


start_app() {
    ensure_directories

    echo
    echo "Iniciando aplicacion..."

    invoke_compose up -d

    wait_for_application || true
}


stop_app() {
    echo
    echo "Deteniendo aplicacion..."

    invoke_compose stop

    echo "Aplicacion detenida."
}


uninstall_app() {
    echo
    echo "========================================"
    echo " Desinstalacion"
    echo "========================================"
    echo
    echo "Esto eliminara los containers de Docker."
    echo "Los datos de SQLite y los logs NO seran eliminados."
    echo

    read -r -p "Escriba DESINSTALAR para confirmar: " confirmation

    if [[ "$confirmation" != "DESINSTALAR" ]]; then
        echo "Operacion cancelada."
        return
    fi

    invoke_compose down

    echo
    echo "Aplicacion desinstalada."
    echo "Los datos permanecen en:"
    echo "  $DATA_DIR"
    echo "  $LOGS_DIR"
}


show_status() {
    echo
    echo "========================================"
    echo " Estado"
    echo "========================================"
    echo

    local version
    local port

    version="$(get_app_version)"
    port="$(get_app_port)"

    echo "Version configurada: $version"
    echo "Puerto: $port"
    echo

    if [[ -f "$DB_FILE" ]]; then
        echo "Base de datos: OK"
    else
        echo "Base de datos: NO INSTALADA"
    fi

    echo
    echo "Containers:"
    echo

    get_container_status

    echo

    if curl -fsS --max-time 2 "http://localhost:$port" >/dev/null 2>&1; then
        echo "Aplicacion: RESPONDIENDO"
    else
        echo "Aplicacion: NO RESPONDE"
    fi
}


show_menu() {
    clear

    local version
    version="$(get_app_version)"

    echo "========================================"
    echo " Sistema de Liquidacion"
    echo "========================================"
    echo
    echo "Version configurada: $version"
    echo
    echo "1. Iniciar aplicacion"
    echo "2. Detener aplicacion"
    echo "3. Instalar"
    echo "4. Actualizar"
    echo "5. Desinstalar"
    echo "6. Ver estado"
    echo "7. Salir"
    echo
}


# ============================================================
# Inicio
# ============================================================

if ! test_docker; then
    exit 1
fi

if [[ ! -f "$COMPOSE_FILE" ]]; then
    echo "ERROR: No se encontro compose.yaml."
    exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: No se encontro .env."
    exit 1
fi

ensure_django_secret_key || exit 1


while true; do
    show_menu

    read -r -p "Seleccione una opcion: " option

    case "$option" in
        1)
            start_app
            pause_script
            ;;
        2)
            stop_app
            pause_script
            ;;
        3)
            install_app
            pause_script
            ;;
        4)
            update_app
            pause_script
            ;;
        5)
            uninstall_app
            pause_script
            ;;
        6)
            show_status
            pause_script
            ;;
        7)
            exit 0
            ;;
        *)
            echo
            echo "Opcion invalida."
            pause_script
            ;;
    esac
done

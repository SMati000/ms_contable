$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$ComposeFile = Join-Path $ScriptDir "compose.yaml"
$EnvFile     = Join-Path $ScriptDir ".env"
$DataDir     = Join-Path $ScriptDir "data"
$LogsDir     = Join-Path $ScriptDir "logs"
$DbFile      = Join-Path $DataDir "db.sqlite3"
$Backup1     = Join-Path $DataDir "db.sqlite3.1.bak"
$Backup2     = Join-Path $DataDir "db.sqlite3.2.bak"

function Pause-Script {
    Write-Host ""
    Read-Host "Presione ENTER para continuar"
}

function Test-Docker {
    try {
        docker info *> $null

        if ($LASTEXITCODE -ne 0) {
            throw
        }

        docker compose version *> $null

        if ($LASTEXITCODE -ne 0) {
            throw
        }

        return $true
    }
    catch {
        Write-Host ""
        Write-Host "ERROR: Docker no esta disponible." -ForegroundColor Red
        Write-Host "Verifique que Docker Desktop este instalado y ejecutandose."
        return $false
    }
}

function Get-AppVersion {
    if (-not (Test-Path $EnvFile)) {
        throw "No existe el archivo .env"
    }

    $line = Get-Content $EnvFile |
        Where-Object { $_ -match '^\s*APP_VERSION\s*=' } |
        Select-Object -First 1

    if (-not $line) {
        throw "No se encontro APP_VERSION en .env"
    }

    $version = ($line -split '=', 2)[1].Trim()

    if ([string]::IsNullOrWhiteSpace($version)) {
        throw "APP_VERSION esta vacio en .env"
    }

    return $version
}

function Ensure-DjangoSecretKey {
    $lines = [System.Collections.Generic.List[string]]::new()
    foreach ($line in [System.IO.File]::ReadAllLines($EnvFile)) {
        $lines.Add($line)
    }

    $keyLineIndex = -1
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^\s*DJANGO_SECRET_KEY\s*=(.*)$') {
            if (-not [string]::IsNullOrWhiteSpace($Matches[1])) {
                return
            }

            $keyLineIndex = $i
            break
        }
    }

    $randomBytes = New-Object byte[] 48
    $randomGenerator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $randomGenerator.GetBytes($randomBytes)
    }
    finally {
        $randomGenerator.Dispose()
    }

    $secretKey = [Convert]::ToBase64String($randomBytes)
    $keyLine = "DJANGO_SECRET_KEY=$secretKey"

    if ($keyLineIndex -ge 0) {
        $lines[$keyLineIndex] = $keyLine
    }
    else {
        $lines.Add($keyLine)
    }

    [System.IO.File]::WriteAllLines(
        $EnvFile,
        $lines.ToArray(),
        [System.Text.UTF8Encoding]::new($false)
    )

    Write-Host "Se genero una clave secreta y se guardo en .env." -ForegroundColor Green
}

function Ensure-Directories {
    if (-not (Test-Path $DataDir)) {
        New-Item -ItemType Directory -Path $DataDir | Out-Null
    }

    if (-not (Test-Path $LogsDir)) {
        New-Item -ItemType Directory -Path $LogsDir | Out-Null
    }
}

function Invoke-Compose {
    param(
        [Parameter(Mandatory = $true)]
        [string[]] $Arguments
    )

    & docker compose -f $ComposeFile @Arguments

    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose fallo."
    }
}

function Get-ContainerStatus {
    & docker compose -f $ComposeFile ps
}

function Backup-Database {
    if (-not (Test-Path $DbFile)) {
        Write-Host "No existe una base de datos para respaldar."
        return
    }

    Write-Host "Creando backup de SQLite..."

    if (Test-Path $Backup1) {
        if (Test-Path $Backup2) {
            Remove-Item $Backup2 -Force
        }

        Move-Item $Backup1 $Backup2 -Force
    }

    Copy-Item $DbFile $Backup1 -Force

    Write-Host "Backup creado: $Backup1" -ForegroundColor Green
}

function Wait-ForApplication {
    param(
        [int] $MaxAttempts = 30
    )

    $port = Get-AppPort

    Write-Host ""
    Write-Host "Esperando que la aplicacion este disponible..."

    for ($i = 1; $i -le $MaxAttempts; $i++) {
        try {
            $response = Invoke-WebRequest `
                -Uri "http://localhost:$port" `
                -UseBasicParsing `
                -TimeoutSec 2

            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                Write-Host "Aplicacion disponible en http://localhost:$port" -ForegroundColor Green
                return $true
            }
        }
        catch {
            # Todavia no esta disponible.
        }

        Start-Sleep -Seconds 2
    }

    Write-Host "La aplicacion no respondio dentro del tiempo esperado." -ForegroundColor Yellow
    return $false
}

function Get-AppPort {
    if (-not (Test-Path $EnvFile)) {
        return 8000
    }

    $line = Get-Content $EnvFile |
        Where-Object { $_ -match '^\s*PORT\s*=' } |
        Select-Object -First 1

    if (-not $line) {
        return 8000
    }

    return ($line -split '=', 2)[1].Trim()
}

function Install-App {
    Ensure-Directories

    $version = Get-AppVersion

    Write-Host ""
    Write-Host "========================================"
    Write-Host " Instalacion"
    Write-Host "========================================"
    Write-Host ""
    Write-Host "Version: $version"
    Write-Host ""

    if (Test-Path $DbFile) {
        Write-Host "Ya existe una base de datos."
        Write-Host "La instalacion inicial no se realizara para evitar sobrescribir datos."
        return
    }

    Write-Host "Descargando imagen..."
    Invoke-Compose @("pull")

    Write-Host ""
    Write-Host "Ejecutando migraciones..."
    Invoke-Compose @(
        "run",
        "--rm",
        "ms_contable",
        "python",
        "manage.py",
        "migrate",
        "--noinput"
    )

    Write-Host ""
    Write-Host "Iniciando aplicacion..."
    Invoke-Compose @("up", "-d")

    if (-not (Wait-ForApplication)) {
        Write-Host ""
        Write-Host "La aplicacion fue iniciada pero no se pudo verificar su disponibilidad." -ForegroundColor Yellow
        return
    }

    Write-Host ""
    Write-Host "Instalacion completada correctamente." -ForegroundColor Green
}

function Update-App {
    Ensure-Directories

    $version = Get-AppVersion

    Write-Host ""
    Write-Host "========================================"
    Write-Host " Actualizacion"
    Write-Host "========================================"
    Write-Host ""
    Write-Host "Version objetivo: $version"
    Write-Host ""

    Write-Host "Deteniendo aplicacion..."
    Invoke-Compose @("down")

    Backup-Database

    Write-Host ""
    Write-Host "Descargando imagen $version..."
    Invoke-Compose @("pull")

    Write-Host ""
    Write-Host "Ejecutando migraciones..."
    Invoke-Compose @(
        "run",
        "--rm",
        "ms_contable",
        "python",
        "manage.py",
        "migrate",
        "--noinput"
    )

    Write-Host ""
    Write-Host "Iniciando nueva version..."
    Invoke-Compose @("up", "-d")

    if (-not (Wait-ForApplication)) {
        Write-Host ""
        Write-Host "ATENCION: la nueva version no pudo ser verificada." -ForegroundColor Yellow
        Write-Host "El backup se encuentra en:"
        Write-Host "  $Backup1"
        return
    }

    Write-Host ""
    Write-Host "Actualizacion completada correctamente." -ForegroundColor Green
}

function Start-App {
    Ensure-Directories

    Write-Host ""
    Write-Host "Iniciando aplicacion..."

    Invoke-Compose @("up", "-d")

    Wait-ForApplication | Out-Null
}

function Stop-App {
    Write-Host ""
    Write-Host "Deteniendo aplicacion..."

    Invoke-Compose @("stop")

    Write-Host "Aplicacion detenida." -ForegroundColor Green
}

function Uninstall-App {
    Write-Host ""
    Write-Host "========================================"
    Write-Host " Desinstalacion"
    Write-Host "========================================"
    Write-Host ""
    Write-Host "Esto eliminara los containers de Docker."
    Write-Host "Los datos de SQLite y los logs NO seran eliminados."
    Write-Host ""

    $confirmation = Read-Host "Escriba DESINSTALAR para confirmar"

    if ($confirmation -ne "DESINSTALAR") {
        Write-Host "Operacion cancelada."
        return
    }

    Invoke-Compose @("down")

    Write-Host ""
    Write-Host "Aplicacion desinstalada." -ForegroundColor Green
    Write-Host "Los datos permanecen en:"
    Write-Host "  $DataDir"
    Write-Host "  $LogsDir"
}

function Show-Status {
    Write-Host ""
    Write-Host "========================================"
    Write-Host " Estado"
    Write-Host "========================================"
    Write-Host ""

    $version = Get-AppVersion
    $port = Get-AppPort

    Write-Host "Version configurada: $version"
    Write-Host "Puerto: $port"
    Write-Host ""

    if (Test-Path $DbFile) {
        Write-Host "Base de datos: OK" -ForegroundColor Green
    }
    else {
        Write-Host "Base de datos: NO INSTALADA" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "Containers:"
    Write-Host ""

    Get-ContainerStatus

    Write-Host ""

    try {
        $response = Invoke-WebRequest `
            -Uri "http://localhost:$port" `
            -UseBasicParsing `
            -TimeoutSec 2

        Write-Host "Aplicacion: RESPONDIENDO" -ForegroundColor Green
    }
    catch {
        Write-Host "Aplicacion: NO RESPONDE" -ForegroundColor Yellow
    }
}

function Show-Menu {
    Clear-Host

    $version = Get-AppVersion

    Write-Host "========================================"
    Write-Host "       Sistema de Liquidacion"
    Write-Host "========================================"
    Write-Host ""
    Write-Host "Version configurada: $version"
    Write-Host ""

    Write-Host "1. Iniciar aplicacion"
    Write-Host "2. Detener aplicacion"
    Write-Host "3. Instalar"
    Write-Host "4. Actualizar"
    Write-Host "5. Desinstalar"
    Write-Host "6. Ver estado"
    Write-Host "7. Salir"
    Write-Host ""
}

# ============================================================
# Inicio
# ============================================================

if (-not (Test-Docker)) {
    exit 1
}

if (-not (Test-Path $ComposeFile)) {
    Write-Host "ERROR: No se encontro compose.yaml." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $EnvFile)) {
    Write-Host "ERROR: No se encontro .env." -ForegroundColor Red
    exit 1
}

Ensure-DjangoSecretKey

while ($true) {
    try {
        Show-Menu

        $option = Read-Host "Seleccione una opcion"

        switch ($option) {
            "1" {
                Start-App
                Pause-Script
            }

            "2" {
                Stop-App
                Pause-Script
            }

            "3" {
                Install-App
                Pause-Script
            }

            "4" {
                Update-App
                Pause-Script
            }

            "5" {
                Uninstall-App
                Pause-Script
            }

            "6" {
                Show-Status
                Pause-Script
            }

            "7" {
                exit 0
            }

            default {
                Write-Host ""
                Write-Host "Opcion invalida." -ForegroundColor Yellow
                Pause-Script
            }
        }
    }
    catch {
        Write-Host ""
        Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        Pause-Script
    }
}

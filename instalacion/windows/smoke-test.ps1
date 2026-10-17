param(
    [Parameter(Mandatory = $true)]
    [string] $SetupExe
)

$ErrorActionPreference = "Stop"
$SetupExe = (Resolve-Path -LiteralPath $SetupExe).Path
$testId = [guid]::NewGuid().ToString("N")
$TempRoot = if ([string]::IsNullOrWhiteSpace($env:RUNNER_TEMP)) { [System.IO.Path]::GetTempPath() } else { $env:RUNNER_TEMP }
$TestRoot = Join-Path $TempRoot "MSContable-smoke-$testId"
$InstallDir = Join-Path $TestRoot "app"
$DataDir = Join-Path $TestRoot "data"
$LogsDir = Join-Path $TestRoot "logs"
$previousLocalAppData = $env:LOCALAPPDATA
$previousSkipDatabaseImport = $env:MSCONTABLE_SKIP_DATABASE_IMPORT
$IsolatedLocalAppData = Join-Path $TestRoot "localappdata"
New-Item -ItemType Directory -Force -Path $TestRoot | Out-Null
New-Item -ItemType Directory -Force -Path $IsolatedLocalAppData | Out-Null
$env:LOCALAPPDATA = $IsolatedLocalAppData
$env:MSCONTABLE_SKIP_DATABASE_IMPORT = "1"
$installed = $false

$installer = Start-Process `
    -FilePath $SetupExe `
    -ArgumentList @(
        "/VERYSILENT",
        "/SUPPRESSMSGBOXES",
        "/NORESTART",
        "/NOICONS",
        "/SMOKETEST=1",
        "/DIR=`"$InstallDir`""
    ) `
    -Wait `
    -PassThru

if ($installer.ExitCode -ne 0) {
    throw "El instalador terminó con código $($installer.ExitCode)."
}
$installed = $true

$Python = Join-Path $InstallDir "python\python.exe"
$previousDataDir = $env:MSCONTABLE_DATA_DIR
$previousLogsDir = $env:MSCONTABLE_LOG_DIR
$previousSettingsModule = $env:DJANGO_SETTINGS_MODULE
$listener = $null
$server = $null
Push-Location $InstallDir

try {
    if (-not (Test-Path $Python -PathType Leaf)) {
        throw "El instalador no dejó el runtime de Python en $InstallDir."
    }

    $launcherScript = Join-Path $InstallDir "windows\launch-hidden.vbs"
    if (-not (Test-Path $launcherScript -PathType Leaf)) {
        throw "El instalador no incluyó el lanzador oculto de MS Contable."
    }

    $env:MSCONTABLE_DATA_DIR = $DataDir
    $env:MSCONTABLE_LOG_DIR = $LogsDir
    $env:DJANGO_SETTINGS_MODULE = "ms_contable.settings"

    & $Python manage.py migrate --noinput
    if ($LASTEXITCODE -ne 0) { throw "No se pudo preparar una base SQLite anterior para la prueba de actualización." }
    Copy-Item (Join-Path $DataDir "db.sqlite3") (Join-Path $DataDir "db.sqlite3.1.bak")

    $env:DJANGO_SETTINGS_MODULE = "ms_contable.settings_windows"
    $PowerShell = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
    & $PowerShell -NoProfile -STA -ExecutionPolicy Bypass -WindowStyle Hidden -File (Join-Path $InstallDir "windows\initialize.ps1")
    if ($LASTEXITCODE -ne 0) { throw "No se pudo cifrar y actualizar la base de datos instalada." }

    & $Python manage.py check
    if ($LASTEXITCODE -ne 0) { throw "Django no pasó manage.py check desde el paquete instalado." }

    & $Python manage.py migrate --noinput
    if ($LASTEXITCODE -ne 0) { throw "El paquete no pudo crear o migrar la base SQLite." }

    & $Python manage.py collectstatic --noinput
    if ($LASTEXITCODE -ne 0) { throw "El runtime instalado no pudo cargar los archivos estáticos." }

    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
    $listener.Start()
    $port = $listener.LocalEndpoint.Port
    $listener.Stop()
    $listener = $null

    $server = Start-Process `
        -FilePath $Python `
        -ArgumentList @(
            "-m", "waitress", "--listen=127.0.0.1:$port",
            "--trusted-proxy=127.0.0.1", "--trusted-proxy-headers=x-forwarded-proto",
            "ms_contable.wsgi:application"
        ) `
        -WorkingDirectory $InstallDir `
        -WindowStyle Hidden `
        -PassThru `
        -RedirectStandardOutput (Join-Path $LogsDir "smoke.out.log") `
        -RedirectStandardError (Join-Path $LogsDir "smoke.err.log")

    $response = $null
    $requestHeaders = @{ "X-Forwarded-Proto" = "https" }
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        if ($server.HasExited) {
            $errorLog = Join-Path $LogsDir "smoke.err.log"
            $details = if (Test-Path $errorLog) { Get-Content $errorLog -Raw } else { "sin log de error" }
            throw "Waitress terminó antes de responder: $details"
        }

        try {
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:$port/admin/login/" -Headers $requestHeaders -TimeoutSec 2
            if ($response.StatusCode -eq 200 -and $response.Content -match 'name="username"') {
                break
            }
        }
        catch {
            Start-Sleep -Seconds 1
        }
    }

    if (-not $response -or $response.StatusCode -ne 200 -or $response.Content -notmatch 'name="username"') {
        throw "La pantalla de acceso de Django no respondió correctamente desde Waitress."
    }

    $stylesheet = [regex]::Match($response.Content, 'href="(?<url>/static/[^\"]+\.css)"')
    if (-not $stylesheet.Success) {
        throw "La pantalla de acceso no contiene una URL de estilos estáticos."
    }

    $assetResponse = Invoke-WebRequest -Uri "http://127.0.0.1:$port$($stylesheet.Groups['url'].Value)" -Headers $requestHeaders -TimeoutSec 5
    if ($assetResponse.StatusCode -ne 200 -or [string]::IsNullOrWhiteSpace($assetResponse.Content)) {
        throw "Waitress no pudo servir los archivos estáticos del admin."
    }

    if (-not (Test-Path (Join-Path $DataDir "db.sqlite3") -PathType Leaf)) {
        throw "La base de datos no se creó en el directorio de datos configurado."
    }

    foreach ($databaseName in @("db.sqlite3", "db.sqlite3.1.bak", "db.sqlite3.2.bak")) {
        $databasePath = Join-Path $DataDir $databaseName
        if (-not (Test-Path $databasePath -PathType Leaf)) {
            throw "La inicialización no conservó el archivo esperado: $databaseName"
        }
        $header = [System.IO.File]::ReadAllBytes($databasePath)[0..15]
        if ([System.Text.Encoding]::ASCII.GetString($header) -eq "SQLite format 3`0") {
            throw "El archivo quedó sin cifrar: $databaseName"
        }
    }
}
finally {
    if ($listener) { $listener.Stop() }
    if ($server -and -not $server.HasExited) {
        Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
        $server.WaitForExit()
    }
    Pop-Location

    if ($installed) {
        $uninstallerPath = Join-Path $InstallDir "unins000.exe"
        if (Test-Path $uninstallerPath -PathType Leaf) {
            $uninstaller = Start-Process -FilePath $uninstallerPath -ArgumentList @("/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART") -Wait -PassThru
            if ($uninstaller.ExitCode -ne 0) { Write-Warning "El desinstalador de prueba terminó con código $($uninstaller.ExitCode)." }
        }
    }

    if ($null -eq $previousDataDir) {
        Remove-Item Env:MSCONTABLE_DATA_DIR -ErrorAction SilentlyContinue
    }
    else {
        $env:MSCONTABLE_DATA_DIR = $previousDataDir
    }

    if ($null -eq $previousLogsDir) {
        Remove-Item Env:MSCONTABLE_LOG_DIR -ErrorAction SilentlyContinue
    }
    else {
        $env:MSCONTABLE_LOG_DIR = $previousLogsDir
    }

    if ($null -eq $previousSettingsModule) {
        Remove-Item Env:DJANGO_SETTINGS_MODULE -ErrorAction SilentlyContinue
    }
    else {
        $env:DJANGO_SETTINGS_MODULE = $previousSettingsModule
    }

    if ($null -eq $previousLocalAppData) {
        Remove-Item Env:LOCALAPPDATA -ErrorAction SilentlyContinue
    }
    else {
        $env:LOCALAPPDATA = $previousLocalAppData
    }

    if ($null -eq $previousSkipDatabaseImport) {
        Remove-Item Env:MSCONTABLE_SKIP_DATABASE_IMPORT -ErrorAction SilentlyContinue
    }
    else {
        $env:MSCONTABLE_SKIP_DATABASE_IMPORT = $previousSkipDatabaseImport
    }

    if (Test-Path $TestRoot) {
        $tempRootPath = [System.IO.Path]::GetFullPath($TempRoot)
        $testRootPath = [System.IO.Path]::GetFullPath($TestRoot)
        $expectedPrefix = Join-Path $tempRootPath "MSContable-smoke-"
        if (-not $testRootPath.StartsWith($expectedPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "La ruta de limpieza quedó fuera del directorio temporal: $testRootPath"
        }
        Remove-Item -LiteralPath $testRootPath -Recurse -Force
    }
}

Write-Host "Instalador validado: migraciones, inicio de Waitress, login y CSS estático respondieron correctamente."

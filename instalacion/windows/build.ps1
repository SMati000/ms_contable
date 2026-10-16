param(
    [string] $PythonCommand = "",
    [string] $InnoCompiler = ""
)

$ErrorActionPreference = "Stop"
$InstallerRoot = (Resolve-Path $PSScriptRoot).Path
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$BuildRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "build\release"))
$InstallerScript = Join-Path $PSScriptRoot "MSContable.iss"
$InstallerIcon = Join-Path $PSScriptRoot "mscontable-setup.ico"
$OutputDir = Join-Path $PSScriptRoot "dist\https"
$SettingsFile = Join-Path $ProjectRoot "ms_contable\settings.py"

if (-not $BuildRoot.StartsWith("$InstallerRoot\", [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "La carpeta temporal de compilación debe permanecer dentro de instalacion\windows."
}
if (-not (Test-Path $InstallerScript -PathType Leaf)) {
    throw "No se encontró MSContable.iss."
}
if (-not (Test-Path $InstallerIcon -PathType Leaf)) {
    throw "No se encontró el icono del instalador: $InstallerIcon"
}

if ([string]::IsNullOrWhiteSpace($PythonCommand)) {
    $localPython = Get-ChildItem (Join-Path $PSScriptRoot ".tools") -Directory -Filter "python-*" -ErrorAction SilentlyContinue |
        Where-Object { Test-Path (Join-Path $_.FullName "python.exe") } |
        Sort-Object { [version]($_.Name -replace '^python-', '') } -Descending |
        ForEach-Object { Join-Path $_.FullName "python.exe" } |
        Select-Object -First 1
    $PythonCommand = if ($localPython) { $localPython } else { "python" }
}

$Python = (Get-Command $PythonCommand -ErrorAction Stop).Source
$versionText = & $Python -c "import platform; print(platform.python_version())"
$architecture = & $Python -c "import platform; print(platform.architecture()[0])"
$implementation = & $Python -c "import platform; print(platform.python_implementation())"
$pythonVersion = [version]$versionText

if ($implementation -ne "CPython" -or $pythonVersion -lt [version]"3.11.9" -or $pythonVersion.Major -ne 3 -or $pythonVersion.Minor -gt 13) {
    throw "La compilación requiere CPython 3.11.9 a 3.13 x64. Detectado: $implementation $versionText."
}
if ($architecture -ne "64bit") {
    throw "El instalador requiere CPython x64. Detectado: $architecture."
}

if (Test-Path $BuildRoot) {
    Remove-Item -LiteralPath $BuildRoot -Recurse -Force
}

$Payload = Join-Path $BuildRoot "payload"
$AppPayload = Join-Path $Payload "app"
$Runtime = Join-Path $Payload "python"
$SitePackages = Join-Path $Runtime "Lib\site-packages"
$CaddyDir = Join-Path $BuildRoot "caddy"
$CaddyExe = Join-Path $CaddyDir "caddy.exe"
$CaddyLicense = Join-Path $CaddyDir "LICENSE"
$PythonZip = Join-Path $BuildRoot "python-embed.zip"
New-Item -ItemType Directory -Force -Path $SitePackages, $CaddyDir | Out-Null

$pythonVersionForUrl = $pythonVersion.ToString(3)
$pythonRuntimeUrl = "https://www.python.org/ftp/python/$pythonVersionForUrl/python-$pythonVersionForUrl-embed-amd64.zip"
Invoke-WebRequest -UseBasicParsing -Uri $pythonRuntimeUrl -OutFile $PythonZip
Expand-Archive -LiteralPath $PythonZip -DestinationPath $Runtime

$pythonTag = "python$($pythonVersion.Major)$($pythonVersion.Minor)"
$pythonPathFile = Join-Path $Runtime "$pythonTag._pth"
if (-not (Test-Path $pythonPathFile -PathType Leaf)) {
    throw "El runtime descargado no contiene $pythonTag._pth."
}
Set-Content -Path $pythonPathFile -Encoding ASCII -Value @(
    "$pythonTag.zip",
    ".",
    "..\app",
    "..",
    "Lib\site-packages",
    "import site"
)

& $Python -m pip install --disable-pip-version-check --no-compile --target $SitePackages -r (Join-Path $ProjectRoot "requirements-windows.txt")
if ($LASTEXITCODE -ne 0) {
    throw "No se pudieron instalar las dependencias de Windows en el runtime del instalador."
}

$excludedRoots = @(
    ".git", ".github", ".venv", "venv", "env", "data", "logs", "staticfiles", "docs",
    "instalacion", "node_modules", ".playwright-cli", ".ruff_cache", ".pytest_cache",
    "tmp", ".idea", ".vscode", "build", "dist"
)
$trackedFiles = & git -C $ProjectRoot ls-files --cached --others --exclude-standard
if ($LASTEXITCODE -ne 0) {
    throw "No se pudo obtener la lista de archivos del repositorio."
}

foreach ($relativePath in $trackedFiles) {
    $normalizedPath = $relativePath.Replace("/", "\")
    $rootName = $normalizedPath.Split("\")[0]
    $fileName = [System.IO.Path]::GetFileName($normalizedPath)

    if ($excludedRoots -contains $rootName -or $fileName -match '^(\.env(\..*)?|local_settings\.py)$') {
        continue
    }
    if ($normalizedPath -match '(?i)(^|\\)tests?(\\|$)|(^|\\)test[^\\]*\.py$' -or $fileName -match '(?i)\.(pyc|pyo|sqlite3.*|db|bak|log|pdf)$') {
        continue
    }

    $sourceFile = Join-Path $ProjectRoot $normalizedPath
    if (-not (Test-Path $sourceFile -PathType Leaf)) {
        continue
    }
    $destinationFile = Join-Path $AppPayload $normalizedPath
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destinationFile) | Out-Null
    Copy-Item -LiteralPath $sourceFile -Destination $destinationFile
}

$AppWindows = Join-Path $AppPayload "windows"
New-Item -ItemType Directory -Force -Path $AppWindows | Out-Null
Copy-Item (Join-Path $PSScriptRoot "launch.ps1") $AppWindows
Copy-Item (Join-Path $PSScriptRoot "launch-hidden.vbs") $AppWindows
Copy-Item (Join-Path $PSScriptRoot "initialize.ps1") $AppWindows

$previousDataDir = $env:MSCONTABLE_DATA_DIR
$previousLogDir = $env:MSCONTABLE_LOG_DIR
$env:MSCONTABLE_DATA_DIR = Join-Path $BuildRoot "data"
$env:MSCONTABLE_LOG_DIR = Join-Path $BuildRoot "logs"
New-Item -ItemType Directory -Force -Path $env:MSCONTABLE_DATA_DIR, $env:MSCONTABLE_LOG_DIR | Out-Null
Push-Location $AppPayload
try {
    & (Join-Path $Runtime "python.exe") manage.py collectstatic --noinput
    if ($LASTEXITCODE -ne 0) {
        throw "No se pudieron preparar los archivos estáticos."
    }
}
finally {
    Pop-Location
    if ($null -eq $previousDataDir) { Remove-Item Env:MSCONTABLE_DATA_DIR -ErrorAction SilentlyContinue }
    else { $env:MSCONTABLE_DATA_DIR = $previousDataDir }
    if ($null -eq $previousLogDir) { Remove-Item Env:MSCONTABLE_LOG_DIR -ErrorAction SilentlyContinue }
    else { $env:MSCONTABLE_LOG_DIR = $previousLogDir }
}

$sharedCaddy = Join-Path $PSScriptRoot "build\caddy\caddy.exe"
$sharedCaddyLicense = Join-Path $PSScriptRoot "build\caddy\LICENSE"
if (Test-Path $sharedCaddy -PathType Leaf) {
    Copy-Item -LiteralPath $sharedCaddy -Destination $CaddyExe
}
else {
    Invoke-WebRequest -UseBasicParsing `
        -Uri "https://caddyserver.com/api/download?os=windows&arch=amd64" `
        -OutFile $CaddyExe
}
if (Test-Path $sharedCaddyLicense -PathType Leaf) {
    Copy-Item -LiteralPath $sharedCaddyLicense -Destination $CaddyLicense
}
else {
    $caddyVersionOutput = & $CaddyExe version
    $caddyVersion = [regex]::Match(($caddyVersionOutput -join " "), 'v\d+\.\d+\.\d+')
    if (-not $caddyVersion.Success) {
        throw "No se pudo identificar la versión de Caddy para obtener su licencia."
    }
    Invoke-WebRequest -UseBasicParsing `
        -Uri "https://raw.githubusercontent.com/caddyserver/caddy/$($caddyVersion.Value)/LICENSE" `
        -OutFile $CaddyLicense
}

if (-not $InnoCompiler) {
    $localCompiler = Join-Path $PSScriptRoot ".tools\innosetup-7.1.0\ISCC.exe"
    if (Test-Path $localCompiler -PathType Leaf) {
        $InnoCompiler = $localCompiler
    }
    else {
        $command = Get-Command ISCC.exe -ErrorAction SilentlyContinue
        if ($command) {
            $InnoCompiler = $command.Source
        }
        else {
            $candidates = @(
                (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 7\ISCC.exe"),
                (Join-Path $env:ProgramFiles "Inno Setup 7\ISCC.exe"),
                (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
                (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe")
            )
            $InnoCompiler = $candidates | Where-Object { Test-Path $_ -PathType Leaf } | Select-Object -First 1
        }
    }
}
if (-not $InnoCompiler -or -not (Test-Path $InnoCompiler -PathType Leaf)) {
    throw "No se encontró ISCC.exe. Instalá Inno Setup o indicá su ruta con -InnoCompiler."
}

$versionMatch = Select-String -Path $SettingsFile -Pattern '^APP_VERSION\s*=\s*"([^"]+)"' | Select-Object -First 1
if (-not $versionMatch) {
    throw "No se pudo leer APP_VERSION desde $SettingsFile."
}
$AppVersion = $versionMatch.Matches[0].Groups[1].Value
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$CompilerArgs = @(
    "/DAppVersion=$AppVersion"
    "/DPayloadDir=$Payload"
    "/DCaddyExePath=$CaddyExe"
    "/DCaddyLicensePath=$CaddyLicense"
    "/O$OutputDir"
    $InstallerScript
)
& $InnoCompiler @CompilerArgs
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup no pudo compilar MS Contable."
}

Write-Host "Instalador generado en $(Join-Path $OutputDir "MSContable-Setup-$AppVersion.exe")"

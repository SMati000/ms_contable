param(
    [string] $PythonVersion = "3.13.14",
    [string] $InnoVersion = "7.1.0"
)

$ErrorActionPreference = "Stop"
$ToolsRoot = Join-Path $PSScriptRoot ".tools"
$Downloads = Join-Path $ToolsRoot "downloads"
$PythonRoot = Join-Path $ToolsRoot "python-$PythonVersion"
$InnoRoot = Join-Path $ToolsRoot "innosetup-$InnoVersion"
New-Item -ItemType Directory -Force -Path $Downloads | Out-Null

function Install-SignedTool {
    param(
        [string] $Url,
        [string] $InstallerPath,
        [string[]] $Arguments,
        [string] $Name
    )

    Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $InstallerPath
    $signature = Get-AuthenticodeSignature -FilePath $InstallerPath
    if ($signature.Status -ne "Valid") {
        throw "No se pudo validar la firma digital de ${Name}: $($signature.StatusMessage)"
    }

    $process = Start-Process -FilePath $InstallerPath -ArgumentList $Arguments -Wait -PassThru
    if ($process.ExitCode -ne 0) {
        throw "La instalación local de $Name terminó con código $($process.ExitCode)."
    }

    Remove-Item -LiteralPath $InstallerPath -Force
}

$pythonExe = Join-Path $PythonRoot "python.exe"
if (-not (Test-Path $pythonExe -PathType Leaf)) {
    $pythonInstaller = Join-Path $Downloads "python-$PythonVersion-amd64.exe"
    $pythonUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-amd64.exe"
    $pythonArguments = @(
        "/quiet",
        "InstallAllUsers=0",
        "TargetDir=`"$PythonRoot`"",
        "Include_launcher=0",
        "InstallLauncherAllUsers=0",
        "PrependPath=0",
        "Include_test=0",
        "Include_pip=1",
        "Include_doc=0",
        "Shortcuts=0"
    )
    Install-SignedTool -Url $pythonUrl -InstallerPath $pythonInstaller -Arguments $pythonArguments -Name "Python $PythonVersion"
}

if (-not (Test-Path $pythonExe -PathType Leaf)) {
    throw "No se encontró Python en la ruta local del proyecto: $pythonExe"
}

$pythonDetails = & $pythonExe -c "import platform; print(platform.python_version(), platform.architecture()[0], platform.python_implementation())"
if ($LASTEXITCODE -ne 0 -or $pythonDetails -ne "$PythonVersion 64bit CPython") {
    throw "La instalación local de Python no coincide con la versión y arquitectura requeridas: $pythonDetails"
}

$iscc = Join-Path $InnoRoot "ISCC.exe"
if (-not (Test-Path $iscc -PathType Leaf)) {
    $innoInstaller = Join-Path $Downloads "innosetup-$InnoVersion-x64.exe"
    $innoUrl = "https://github.com/jrsoftware/issrc/releases/download/is-7_1_0/innosetup-$InnoVersion-x64.exe"
    $innoArguments = @(
        "/VERYSILENT",
        "/SUPPRESSMSGBOXES",
        "/NORESTART",
        "/DIR=`"$InnoRoot`""
    )
    Install-SignedTool -Url $innoUrl -InstallerPath $innoInstaller -Arguments $innoArguments -Name "Inno Setup $InnoVersion"
}

if (-not (Test-Path $iscc -PathType Leaf)) {
    throw "No se encontró el compilador local de Inno Setup: $iscc"
}

Write-Host "Herramientas locales listas. Python: $pythonExe"
Write-Host "Compilador local: $iscc"

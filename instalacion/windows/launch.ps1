param(
    [ValidateSet("Start", "Stop")]
    [string] $Action = "Start"
)

$ErrorActionPreference = "Stop"
$InstallDir = Split-Path -Parent $PSScriptRoot
$AppDir = $InstallDir
$Python = Join-Path $InstallDir "python\python.exe"
$Caddy = Join-Path $InstallDir "caddy\caddy.exe"
$Caddyfile = Join-Path $InstallDir "caddy\Caddyfile"
$DataRoot = Join-Path $env:LOCALAPPDATA "MSContable"
$DataDir = Join-Path $DataRoot "data"
$LogsDir = Join-Path $DataRoot "logs"
$CaddyDataHome = $DataRoot
$CaddyStorage = Join-Path $CaddyDataHome "caddy"
$RootCertificate = Join-Path $CaddyStorage "pki\authorities\local\root.crt"
$WaitressPidFile = Join-Path $DataDir "waitress.pid"
$CaddyPidFile = Join-Path $DataDir "caddy.pid"
$CaddyThumbprintFile = Join-Path $DataDir "caddy-ca-thumbprint.txt"
$BackendPort = 8000
$HttpsPort = 443
$SiteHost = "mscontable"
$startedWaitress = $null
$startedCaddy = $null

function Get-ManagedProcess {
    param(
        [int] $ProcessId,
        [string] $Executable,
        [string] $CommandMarker
    )

    $processInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction SilentlyContinue
    if (-not $processInfo -or -not [string]::Equals($processInfo.ExecutablePath, $Executable, [StringComparison]::OrdinalIgnoreCase)) {
        return $null
    }

    if ($processInfo.CommandLine.IndexOf($CommandMarker, [StringComparison]::OrdinalIgnoreCase) -lt 0) {
        return $null
    }

    return Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
}

function Stop-ManagedProcess {
    param(
        [string] $PidFile,
        [string] $Executable,
        [string] $CommandMarker
    )

    if (-not (Test-Path $PidFile)) {
        return
    }

    $processId = 0
    if ([int]::TryParse((Get-Content $PidFile -Raw), [ref]$processId)) {
        $process = Get-ManagedProcess -ProcessId $processId -Executable $Executable -CommandMarker $CommandMarker
        if ($process) {
            Stop-Process -Id $process.Id -Force
            $process.WaitForExit()
        }
    }

    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

function Test-RootCertificateTrusted {
    if (-not (Test-Path $RootCertificate)) {
        return $false
    }

    $certificate = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new($RootCertificate)
    $store = [System.Security.Cryptography.X509Certificates.X509Store]::new("Root", "CurrentUser")
    $store.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadOnly)
    try {
        return $store.Certificates.Find(
            [System.Security.Cryptography.X509Certificates.X509FindType]::FindByThumbprint,
            $certificate.Thumbprint,
            $false
        ).Count -gt 0
    }
    finally {
        $store.Close()
    }
}

function Wait-ForCaddyCertificate {
    param([System.Diagnostics.Process] $CaddyProcess)

    $callback = [System.Net.Security.RemoteCertificateValidationCallback] {
        param($sender, $certificate, $chain, $errors)
        return $true
    }

    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        if ($CaddyProcess.HasExited) {
            throw "Caddy se cerró al iniciar. Revisá los logs en $LogsDir."
        }

        $client = [System.Net.Sockets.TcpClient]::new()
        $stream = $null
        try {
            $client.Connect([System.Net.IPAddress]::Loopback, $HttpsPort)
            $stream = [System.Net.Security.SslStream]::new($client.GetStream(), $false, $callback)
            $stream.AuthenticateAsClient($SiteHost)
            $certificate = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new($stream.RemoteCertificate)
            if ($certificate.GetNameInfo([System.Security.Cryptography.X509Certificates.X509NameType]::DnsName, $false) -ne $SiteHost) {
                throw "Caddy presentó un certificado para otro nombre."
            }
            if (Test-Path $RootCertificate) {
                return
            }
        }
        catch {
            Start-Sleep -Seconds 1
        }
        finally {
            if ($stream) {
                $stream.Dispose()
            }
            $client.Dispose()
        }
    }

    throw "Caddy no pudo emitir el certificado local. Revisá los logs en $LogsDir."
}

function Show-StartupError {
    param([string] $Message)

    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show(
        $Message,
        "MS Contable",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Error
    ) | Out-Null
}

if ($Action -eq "Stop") {
    Stop-ManagedProcess -PidFile $CaddyPidFile -Executable $Caddy -CommandMarker $Caddyfile
    Stop-ManagedProcess -PidFile $WaitressPidFile -Executable $Python -CommandMarker "ms_contable.wsgi:application"
    return
}

try {
    if (-not (Test-Path $Python) -or -not (Test-Path $Caddy) -or -not (Test-Path $Caddyfile)) {
        throw "Faltan archivos de MS Contable o Caddy. Reinstalá la aplicación."
    }

    New-Item -ItemType Directory -Force -Path $DataDir, $LogsDir, $CaddyStorage | Out-Null
    if (-not (Test-RootCertificateTrusted)) {
        throw "No se encontró el certificado HTTPS de MS Contable. Volvé a ejecutar el instalador para reparar la configuración."
    }

    $env:MSCONTABLE_DATA_DIR = $DataDir
    $env:MSCONTABLE_LOG_DIR = $LogsDir
    $env:DJANGO_SETTINGS_MODULE = "ms_contable.settings_windows"
    $env:XDG_DATA_HOME = $CaddyDataHome
    $env:XDG_CONFIG_HOME = $DataRoot
    $waitressStdout = Join-Path $LogsDir "waitress.out.log"
    $waitressStderr = Join-Path $LogsDir "waitress.err.log"
    $caddyStdout = Join-Path $LogsDir "caddy.out.log"
    $caddyStderr = Join-Path $LogsDir "caddy.err.log"

    $waitressProcess = $null
    if (Test-Path $WaitressPidFile) {
        $processId = 0
        if ([int]::TryParse((Get-Content $WaitressPidFile -Raw), [ref]$processId)) {
            $waitressProcess = Get-ManagedProcess -ProcessId $processId -Executable $Python -CommandMarker "ms_contable.wsgi:application"
        }
    }
    if (-not $waitressProcess) {
        Remove-Item $WaitressPidFile -Force -ErrorAction SilentlyContinue
        $waitressProcess = Start-Process `
            -FilePath $Python `
            -ArgumentList @(
                "-m", "waitress", "--listen=127.0.0.1:$BackendPort",
                "--trusted-proxy=127.0.0.1", "--trusted-proxy-headers=x-forwarded-proto",
                "ms_contable.wsgi:application"
            ) `
            -WorkingDirectory $AppDir `
            -WindowStyle Hidden `
            -PassThru `
            -RedirectStandardOutput $waitressStdout `
            -RedirectStandardError $waitressStderr
        $startedWaitress = $waitressProcess
        Set-Content -Path $WaitressPidFile -Value $waitressProcess.Id -Encoding ASCII
    }

    $serverReady = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        if ($waitressProcess.HasExited) {
            break
        }
        try {
            $response = Invoke-WebRequest `
                -Uri "http://127.0.0.1:$BackendPort/admin/login/" `
                -Headers @{ "X-Forwarded-Proto" = "https" } `
                -UseBasicParsing `
                -TimeoutSec 1
            if ($response.StatusCode -eq 200) {
                $serverReady = $true
                break
            }
        }
        catch {
            Start-Sleep -Seconds 1
        }
    }
    if (-not $serverReady) {
        throw "Waitress no pudo iniciar en el puerto $BackendPort. Revisá los logs en $LogsDir."
    }

    $caddyProcess = $null
    if (Test-Path $CaddyPidFile) {
        $processId = 0
        if ([int]::TryParse((Get-Content $CaddyPidFile -Raw), [ref]$processId)) {
            $caddyProcess = Get-ManagedProcess -ProcessId $processId -Executable $Caddy -CommandMarker $Caddyfile
        }
    }
    if (-not $caddyProcess) {
        Remove-Item $CaddyPidFile -Force -ErrorAction SilentlyContinue
        $caddyProcess = Start-Process `
            -FilePath $Caddy `
            -ArgumentList @("run", "--config", "`"$Caddyfile`"", "--adapter", "caddyfile") `
            -WorkingDirectory (Split-Path -Parent $Caddy) `
            -WindowStyle Hidden `
            -PassThru `
            -RedirectStandardOutput $caddyStdout `
            -RedirectStandardError $caddyStderr
        $startedCaddy = $caddyProcess
        Set-Content -Path $CaddyPidFile -Value $caddyProcess.Id -Encoding ASCII
    }

    Wait-ForCaddyCertificate -CaddyProcess $caddyProcess

    Start-Process ("https://" + $SiteHost + "/admin/login/")
}
catch {
    if ($startedCaddy -and -not $startedCaddy.HasExited) {
        Stop-Process -Id $startedCaddy.Id -Force -ErrorAction SilentlyContinue
        Remove-Item $CaddyPidFile -Force -ErrorAction SilentlyContinue
    }
    if ($startedWaitress -and -not $startedWaitress.HasExited) {
        Stop-Process -Id $startedWaitress.Id -Force -ErrorAction SilentlyContinue
        Remove-Item $WaitressPidFile -Force -ErrorAction SilentlyContinue
    }
    Show-StartupError -Message $_.Exception.Message
    exit 1
}

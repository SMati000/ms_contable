$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms

$InstallDir = Split-Path -Parent $PSScriptRoot
$DataRoot = Join-Path $env:LOCALAPPDATA "MSContable"
$DataDir = Join-Path $DataRoot "data"
$LogsDir = Join-Path $DataRoot "logs"
$Caddy = Join-Path $InstallDir "caddy\caddy.exe"
$Caddyfile = Join-Path $InstallDir "caddy\Caddyfile"
$CaddyStorage = Join-Path $DataRoot "caddy"
$RootCertificate = Join-Path $CaddyStorage "pki\authorities\local\root.crt"
$ThumbprintFile = Join-Path $DataDir "caddy-ca-thumbprint.txt"
$CaddyProcess = $null

function Show-Message {
    param(
        [string] $Message,
        [string] $Title,
        [System.Windows.Forms.MessageBoxButtons] $Buttons,
        [System.Windows.Forms.MessageBoxIcon] $Icon
    )

    return [System.Windows.Forms.MessageBox]::Show($Message, $Title, $Buttons, $Icon)
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

function Add-RootCertificateToCurrentUser {
    $certificate = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new($RootCertificate)
    $certutil = Join-Path $env:SystemRoot "System32\certutil.exe"
    $stdout = Join-Path $LogsDir "cert-install.out.log"
    $stderr = Join-Path $LogsDir "cert-install.err.log"
    $process = Start-Process `
        -FilePath $certutil `
        -ArgumentList @("-addstore", "-f", "-user", "Root", "`"$RootCertificate`"") `
        -WindowStyle Hidden `
        -PassThru `
        -Wait `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr

    if ($process.ExitCode -ne 0 -or -not (Test-RootCertificateTrusted)) {
        throw "Windows no pudo instalar silenciosamente el certificado local de MS Contable. Revisá los registros en $LogsDir."
    }

    Set-Content -Path $ThumbprintFile -Value $certificate.Thumbprint -Encoding ASCII
}

function Wait-ForCaddyCertificate {
    param([System.Diagnostics.Process] $Process)

    $callback = [System.Net.Security.RemoteCertificateValidationCallback] {
        param($sender, $certificate, $chain, $errors)
        return $true
    }

    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        if ($Process.HasExited) {
            throw "Caddy se cerró durante la preparación de HTTPS. Revisá los registros en $LogsDir."
        }

        $client = [System.Net.Sockets.TcpClient]::new()
        $stream = $null
        try {
            $client.Connect([System.Net.IPAddress]::Loopback, 443)
            $stream = [System.Net.Security.SslStream]::new($client.GetStream(), $false, $callback)
            $stream.AuthenticateAsClient("mscontable")
            $certificate = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new($stream.RemoteCertificate)
            if ($certificate.GetNameInfo([System.Security.Cryptography.X509Certificates.X509NameType]::DnsName, $false) -ne "mscontable") {
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

    throw "Caddy no pudo preparar el certificado HTTPS. Revisá los registros en $LogsDir."
}

try {
    New-Item -ItemType Directory -Force -Path $DataDir, $LogsDir, $CaddyStorage | Out-Null
    $env:XDG_DATA_HOME = $DataRoot
    $env:XDG_CONFIG_HOME = $DataRoot

    if (Test-RootCertificateTrusted) {
        $certificate = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new($RootCertificate)
        Set-Content -Path $ThumbprintFile -Value $certificate.Thumbprint -Encoding ASCII
        exit 0
    }

    if (-not (Test-Path $Caddy) -or -not (Test-Path $Caddyfile)) {
        throw "No se encontraron los archivos de Caddy incluidos con MS Contable."
    }

    $caddyStdout = Join-Path $LogsDir "caddy-install.out.log"
    $caddyStderr = Join-Path $LogsDir "caddy-install.err.log"
    $CaddyProcess = Start-Process `
        -FilePath $Caddy `
        -ArgumentList @("run", "--config", "`"$Caddyfile`"", "--adapter", "caddyfile") `
        -WorkingDirectory (Split-Path -Parent $Caddy) `
        -WindowStyle Hidden `
        -PassThru `
        -RedirectStandardOutput $caddyStdout `
        -RedirectStandardError $caddyStderr

    Wait-ForCaddyCertificate -Process $CaddyProcess
    Add-RootCertificateToCurrentUser
}
catch {
    Show-Message `
        -Message $_.Exception.Message `
        -Title "No se pudo configurar HTTPS" `
        -Buttons ([System.Windows.Forms.MessageBoxButtons]::OK) `
        -Icon ([System.Windows.Forms.MessageBoxIcon]::Error) | Out-Null
    exit 1
}
finally {
    if ($CaddyProcess -and -not $CaddyProcess.HasExited) {
        Stop-Process -Id $CaddyProcess.Id -Force -ErrorAction SilentlyContinue
        $CaddyProcess.WaitForExit()
    }
}

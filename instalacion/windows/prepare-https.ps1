$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms
$NoUI = $args -contains "-NoUI"

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
    if (-not $certificate.Subject.StartsWith(
        "CN=Caddy Local Authority",
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        throw "El certificado HTTPS local no pertenece a la autoridad de Caddy esperada."
    }

    $previousThumbprint = ""
    if (Test-Path $ThumbprintFile) {
        $previousThumbprint = (Get-Content $ThumbprintFile -Raw).Trim()
    }

    $store = [System.Security.Cryptography.X509Certificates.X509Store]::new("Root", "CurrentUser")
    $store.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)
    try {
        $current = $store.Certificates.Find(
            [System.Security.Cryptography.X509Certificates.X509FindType]::FindByThumbprint,
            $certificate.Thumbprint,
            $false
        )
        if ($current.Count -eq 0) {
            $store.Add($certificate)
        }

        $current = $store.Certificates.Find(
            [System.Security.Cryptography.X509Certificates.X509FindType]::FindByThumbprint,
            $certificate.Thumbprint,
            $false
        )
        if ($current.Count -eq 0) {
            throw "Windows no pudo confiar en el certificado HTTPS local de MS Contable."
        }

        if ($previousThumbprint -and $previousThumbprint -ne $certificate.Thumbprint) {
            $previous = $store.Certificates.Find(
                [System.Security.Cryptography.X509Certificates.X509FindType]::FindByThumbprint,
                $previousThumbprint,
                $false
            )
            foreach ($oldCertificate in $previous) {
                if ($oldCertificate.Subject.StartsWith(
                    "CN=Caddy Local Authority",
                    [System.StringComparison]::OrdinalIgnoreCase
                )) {
                    $store.Remove($oldCertificate)
                }
            }
        }
    }
    finally {
        $store.Close()
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
        Add-RootCertificateToCurrentUser
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
    if (-not $NoUI) {
        Show-Message `
            -Message $_.Exception.Message `
            -Title "No se pudo configurar HTTPS" `
            -Buttons ([System.Windows.Forms.MessageBoxButtons]::OK) `
            -Icon ([System.Windows.Forms.MessageBoxIcon]::Error) | Out-Null
    }
    exit 1
}
finally {
    if ($CaddyProcess -and -not $CaddyProcess.HasExited) {
        Stop-Process -Id $CaddyProcess.Id -Force -ErrorAction SilentlyContinue
        $CaddyProcess.WaitForExit()
    }
}

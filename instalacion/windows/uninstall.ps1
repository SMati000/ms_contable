$ErrorActionPreference = "Continue"
$DataRoot = Join-Path $env:LOCALAPPDATA "MSContable"
$CaddyStorage = Join-Path $DataRoot "caddy\pki\authorities\local"
$CaddyThumbprintFile = Join-Path $DataRoot "data\caddy-ca-thumbprint.txt"
$env:XDG_DATA_HOME = $DataRoot
$env:XDG_CONFIG_HOME = $DataRoot

& (Join-Path $PSScriptRoot "launch.ps1") -Action Stop

if (Test-Path $CaddyThumbprintFile) {
    try {
        $thumbprint = (Get-Content $CaddyThumbprintFile -Raw).Trim()
        $store = [System.Security.Cryptography.X509Certificates.X509Store]::new("Root", "CurrentUser")
        $store.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadOnly)
        try {
            $matches = $store.Certificates.Find(
                [System.Security.Cryptography.X509Certificates.X509FindType]::FindByThumbprint,
                $thumbprint,
                $false
            )
        }
        finally {
            $store.Close()
        }
        if ($matches.Count -gt 0) {
            $certutil = Join-Path $env:SystemRoot "System32\certutil.exe"
            $process = Start-Process `
                -FilePath $certutil `
                -ArgumentList @("-delstore", "-f", "-user", "Root", $thumbprint) `
                -WindowStyle Hidden `
                -PassThru `
                -Wait
            if ($process.ExitCode -ne 0) {
                throw "Windows no pudo quitar silenciosamente el certificado de MS Contable."
            }
        }
    }
    catch {
        Add-Content -Path (Join-Path $DataRoot "logs\uninstall.log") -Value $_.Exception.Message
    }
}

Remove-Item (Join-Path $DataRoot "caddy") -Recurse -Force -ErrorAction SilentlyContinue

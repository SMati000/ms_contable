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
        $store.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)
        try {
            $matches = $store.Certificates.Find(
                [System.Security.Cryptography.X509Certificates.X509FindType]::FindByThumbprint,
                $thumbprint,
                $false
            )
            foreach ($match in $matches) {
                $store.Remove($match)
            }
        }
        finally {
            $store.Close()
        }
    }
    catch {
        Add-Content -Path (Join-Path $DataRoot "logs\uninstall.log") -Value $_.Exception.Message
    }
}

Remove-Item (Join-Path $DataRoot "caddy") -Recurse -Force -ErrorAction SilentlyContinue

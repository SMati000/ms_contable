param(
    [ValidateSet("Add", "Remove")]
    [string] $Action
)

$ErrorActionPreference = "Stop"
$HostsPath = Join-Path $env:SystemRoot "System32\drivers\etc\hosts"
$SiteHost = "mscontable"
$StartMarker = "# BEGIN MS Contable managed host"
$EndMarker = "# END MS Contable managed host"

function Read-HostsFile {
    $bytes = [System.IO.File]::ReadAllBytes($HostsPath)
    $encoding = [System.Text.Encoding]::Default
    $offset = 0

    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        $encoding = [System.Text.UTF8Encoding]::new($true)
        $offset = 3
    }
    elseif ($bytes.Length -ge 2 -and $bytes[0] -eq 0xFF -and $bytes[1] -eq 0xFE) {
        $encoding = [System.Text.UnicodeEncoding]::new($false, $true)
        $offset = 2
    }
    elseif ($bytes.Length -ge 2 -and $bytes[0] -eq 0xFE -and $bytes[1] -eq 0xFF) {
        $encoding = [System.Text.UnicodeEncoding]::new($true, $true)
        $offset = 2
    }

    [pscustomobject]@{
        Text = $encoding.GetString($bytes, $offset, $bytes.Length - $offset)
        Encoding = $encoding
    }
}

function Save-HostsFile {
    param(
        [string] $Text,
        [System.Text.Encoding] $Encoding
    )

    [System.IO.File]::WriteAllText($HostsPath, $Text, $Encoding)
}

function Add-HostsEntry {
    $file = Read-HostsFile
    $startCount = [regex]::Matches($file.Text, "(?m)^$([regex]::Escape($StartMarker))\r?$").Count
    $endCount = [regex]::Matches($file.Text, "(?m)^$([regex]::Escape($EndMarker))\r?$").Count

    if ($startCount -eq 1 -and $endCount -eq 1) {
        return
    }
    if ($startCount -ne 0 -or $endCount -ne 0) {
        throw "El archivo hosts contiene un bloque de MS Contable incompleto. No se modificó."
    }

    foreach ($line in ($file.Text -split "`r`n|`n|`r")) {
        $entry = ($line -split "#", 2)[0].Trim()
        if (-not $entry) {
            continue
        }

        $parts = $entry -split "\s+"
        if ($parts.Length -lt 2 -or $parts[1..($parts.Length - 1)] -notcontains $SiteHost) {
            continue
        }

        $address = $null
        if (-not [System.Net.IPAddress]::TryParse($parts[0], [ref]$address) -or -not [System.Net.IPAddress]::IsLoopback($address)) {
            throw "El nombre mscontable ya está asignado a otra dirección en el archivo hosts. No se modificó."
        }
        return
    }

    $lineEnding = [regex]::Match($file.Text, "`r`n|`n|`r").Value
    if (-not $lineEnding) {
        $lineEnding = [Environment]::NewLine
    }

    $content = $file.Text
    if ($content.Length -gt 0 -and $content -notmatch "(?:`r`n|`n|`r)$") {
        $content += $lineEnding
    }
    $content += @(
        $StartMarker
        "127.0.0.1 $SiteHost"
        "::1 $SiteHost"
        $EndMarker
    ) -join $lineEnding
    $content += $lineEnding
    Save-HostsFile -Text $content -Encoding $file.Encoding
}

function Remove-HostsEntry {
    $file = Read-HostsFile
    $startCount = [regex]::Matches($file.Text, "(?m)^$([regex]::Escape($StartMarker))\r?$").Count
    $endCount = [regex]::Matches($file.Text, "(?m)^$([regex]::Escape($EndMarker))\r?$").Count

    if ($startCount -eq 0 -and $endCount -eq 0) {
        return
    }
    if ($startCount -ne 1 -or $endCount -ne 1) {
        throw "El bloque administrado de MS Contable está incompleto. No se modificó."
    }

    $pattern = "(?ms)^$([regex]::Escape($StartMarker))\r?\n.*?^$([regex]::Escape($EndMarker))(?:\r?\n|$)"
    $content = [regex]::Replace($file.Text, $pattern, "", 1)
    Save-HostsFile -Text $content -Encoding $file.Encoding
}

if (-not (Test-Path $HostsPath)) {
    throw "No se encontró el archivo hosts de Windows: $HostsPath"
}

if ($Action -eq "Add") {
    Add-HostsEntry
}
else {
    Remove-HostsEntry
}

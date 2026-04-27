param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$DownloadUrl,
    [Parameter(Mandatory = $true, Position = 1)]
    [string]$OutputPath
)

$ErrorActionPreference = "Stop"

Write-Host "Downloading from: $DownloadUrl"
Write-Host "Saving to: $OutputPath"

try {
    $directory = Split-Path -Parent $OutputPath
    if ($directory) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }

    Invoke-WebRequest -Uri $DownloadUrl -OutFile $OutputPath -MaximumRedirection 10

    if (Test-Path $OutputPath) {
        $size = (Get-Item $OutputPath).Length
        Write-Host "✓ Successfully downloaded to $OutputPath"
        Write-Host "  File size: $size bytes"
        exit 0
    }

    Write-Host "✗ Download failed"
    exit 1
}
catch {
    Write-Host "✗ Download failed"
    Write-Host $_.Exception.Message
    exit 1
}

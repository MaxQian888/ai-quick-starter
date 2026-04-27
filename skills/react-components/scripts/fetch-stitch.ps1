param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Url,
    [Parameter(Mandatory = $true, Position = 1)]
    [string]$OutputPath
)

$ErrorActionPreference = "Stop"

Write-Host "Initiating high-reliability fetch for Stitch HTML..."

try {
    $directory = Split-Path -Parent $OutputPath
    if ($directory) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }

    Invoke-WebRequest -Uri $Url -OutFile $OutputPath -MaximumRedirection 10
    Write-Host "✅ Successfully retrieved HTML at: $OutputPath"
    exit 0
}
catch {
    Write-Host "❌ Error: Failed to retrieve content. Check TLS/SNI or URL expiration."
    Write-Host $_.Exception.Message
    exit 1
}

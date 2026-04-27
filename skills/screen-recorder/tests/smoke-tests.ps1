[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$skillRoot = Split-Path -Path $PSScriptRoot -Parent
$scriptPath = Join-Path -Path $skillRoot -ChildPath "scripts/record_screen.ps1"
$workspace = Join-Path -Path $PSScriptRoot -ChildPath ".tmp-smoke"

if (Test-Path -LiteralPath $workspace) {
    Remove-Item -LiteralPath $workspace -Recurse -Force
}

New-Item -ItemType Directory -Path $workspace -Force | Out-Null

try {
    $requestedDir = Join-Path -Path $workspace -ChildPath "captures"
    New-Item -ItemType Directory -Path $requestedDir -Force | Out-Null
    $output = & $scriptPath -Capture desktop -DryRun -Path $requestedDir 2>&1
    $text = ($output | Out-String)

    if ($text -notmatch "Backend:") {
        throw "Dry-run output did not report a backend. Output: $text"
    }

    if (-not (Test-Path -LiteralPath $requestedDir)) {
        throw "Requested capture directory was not created."
    }
}
finally {
    if (Test-Path -LiteralPath $workspace) {
        Remove-Item -LiteralPath $workspace -Recurse -Force
    }
}

Write-Host "Screen recorder smoke tests passed."

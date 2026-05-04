[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$Path,

  [ValidateRange(1, 1000)]
  [int]$Columns = 80,

  [ValidateSet("truecolor", "none")]
  [string]$ColorMode = "truecolor",

  [string]$Background = "#000000",

  [switch]$AllowUpscale
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$libraryPath = Join-Path $PSScriptRoot "lib\pixel_art_renderer.ps1"
. $libraryPath

$lines = Convert-ImageFileToPixelArt -Path $Path -Columns $Columns -ColorMode $ColorMode -Background $Background -AllowUpscale:$AllowUpscale
foreach ($line in $lines) {
  Write-Output $line
}

$scriptPath = Join-Path $PSScriptRoot "take_screenshot.ps1"
$scriptContent = Get-Content -Raw $scriptPath
$bootstrap = ($scriptContent -split '(?m)^\$hasWindowHandle\s*=', 2)[0]

Invoke-Expression $bootstrap

Describe "take_screenshot.ps1 bootstrap helpers" {
  It "resolves the default screenshot directory without colliding with HOME" {
    { Get-DefaultDirectory } | Should Not Throw

    $defaultDirectory = Get-DefaultDirectory

    $defaultDirectory | Should Not BeNullOrEmpty
  }
}
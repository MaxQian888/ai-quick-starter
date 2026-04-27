[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$ProjectRoot,

    [string]$WorkflowName = "powershell-ci",

    [string]$Branch = "main",

    [string]$QualityGateScriptRelativePath = "scripts/invoke-pwsh-quality-gate.ps1",

    [string]$TestsPath = "tests",

    [switch]$SkipPester,

    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($WorkflowName -notmatch "^[A-Za-z0-9._-]+$") {
    throw "WorkflowName '$WorkflowName' contains invalid characters."
}

$resolvedRoot = Resolve-Path -Path $ProjectRoot -ErrorAction SilentlyContinue
$root = if ($resolvedRoot) {
    $resolvedRoot.Path
}
else {
    [System.IO.Path]::GetFullPath($ProjectRoot)
}

if (-not (Test-Path -LiteralPath $root)) {
    New-Item -ItemType Directory -Path $root -Force | Out-Null
}

$workflowDir = Join-Path -Path $root -ChildPath ".github/workflows"
New-Item -ItemType Directory -Path $workflowDir -Force | Out-Null

$workflowPath = Join-Path -Path $workflowDir -ChildPath "$WorkflowName.yml"
if ((Test-Path -LiteralPath $workflowPath) -and -not $Force) {
    throw "Workflow file '$workflowPath' already exists. Use -Force to overwrite."
}

$testStep = if ($SkipPester) {
@"
      - name: Skip Pester
        shell: pwsh
        run: |
          Write-Host "Pester step skipped by template option."
"@
}
else {
@"
      - name: Run Pester tests when present
        shell: pwsh
        run: |
          if (Test-Path -LiteralPath "__TESTS_PATH__") {
            Set-PSRepository -Name PSGallery -InstallationPolicy Trusted
            Install-Module -Name Pester -Scope CurrentUser -Force
            Invoke-Pester -Path "__TESTS_PATH__" -Output Detailed
          }
          else {
            Write-Host "No tests directory found at __TESTS_PATH__. Skip Pester."
          }
"@
}

$template = @"
name: __WORKFLOW_NAME__

on:
  push:
    branches: ["__BRANCH__"]
  pull_request:
    branches: ["__BRANCH__"]

permissions:
  contents: read

jobs:
  lint-and-test:
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
    runs-on: `${{ matrix.os }}

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Install PSScriptAnalyzer
        shell: pwsh
        run: |
          Set-PSRepository -Name PSGallery -InstallationPolicy Trusted
          Install-Module -Name PSScriptAnalyzer -Scope CurrentUser -Force

      - name: Run quality gate
        shell: pwsh
        run: |
          if (-not (Test-Path -LiteralPath "__QUALITY_SCRIPT__")) {
            throw "Quality gate script not found: __QUALITY_SCRIPT__"
          }
          & pwsh -NoLogo -NoProfile -File "__QUALITY_SCRIPT__" -Path "." -Recurse -FailOnWarning

__TEST_STEP__
"@

$qualityPath = ($QualityGateScriptRelativePath -replace "\\", "/")
$testsPathNormalized = ($TestsPath -replace "\\", "/")
$testStep = $testStep.Replace("__TESTS_PATH__", $testsPathNormalized)

$content = $template.Replace("__WORKFLOW_NAME__", $WorkflowName).
    Replace("__BRANCH__", $Branch).
    Replace("__QUALITY_SCRIPT__", $qualityPath).
    Replace("__TEST_STEP__", $testStep)

Set-Content -LiteralPath $workflowPath -Value $content -Encoding UTF8

Write-Host "Created CI workflow template: $workflowPath"
exit 0

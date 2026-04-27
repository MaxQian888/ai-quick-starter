[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidatePattern("^[A-Za-z][A-Za-z0-9-]*$")]
    [string]$ModuleName,

    [Parameter(Mandatory)]
    [string]$RootPath,

    [string[]]$Functions = @(),

    [string]$Author = "Unknown",

    [string]$Description = "PowerShell module scaffold",

    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-DefaultFunctionName {
    param(
        [Parameter(Mandatory)]
        [string]$InputModuleName
    )

    $base = ($InputModuleName -replace "[^A-Za-z0-9]", "")
    if ([string]::IsNullOrWhiteSpace($base)) {
        $base = "Sample"
    }
    return "Get-$base`Info"
}

function New-FunctionFile {
    param(
        [Parameter(Mandatory)]
        [string]$FunctionName,
        [Parameter(Mandatory)]
        [string]$OutputPath
    )

    $content = @"
function $FunctionName {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]`$Name
    )

    begin {
        Set-StrictMode -Version Latest
        `$ErrorActionPreference = "Stop"
    }

    process {
        [pscustomobject]@{
            Name      = `$Name
            Function  = "$FunctionName"
            Timestamp = Get-Date
        }
    }
}
"@

    Set-Content -LiteralPath $OutputPath -Value $content -Encoding UTF8
}

$resolvedRoot = Resolve-Path -Path $RootPath -ErrorAction SilentlyContinue
$rootBase = if ($resolvedRoot) {
    $resolvedRoot.Path
}
else {
    [System.IO.Path]::GetFullPath($RootPath)
}

if (-not (Test-Path -LiteralPath $rootBase)) {
    New-Item -ItemType Directory -Path $rootBase -Force | Out-Null
}

$moduleRoot = Join-Path -Path $rootBase -ChildPath $ModuleName
if ((Test-Path -LiteralPath $moduleRoot) -and -not $Force) {
    throw "Module directory '$moduleRoot' already exists. Use -Force to overwrite."
}

if ((Test-Path -LiteralPath $moduleRoot) -and $Force) {
    [System.IO.Directory]::Delete($moduleRoot, $true)
}

New-Item -ItemType Directory -Path $moduleRoot -Force | Out-Null
$publicDir = Join-Path -Path $moduleRoot -ChildPath "Public"
$privateDir = Join-Path -Path $moduleRoot -ChildPath "Private"
$testsDir = Join-Path -Path $moduleRoot -ChildPath "Tests"

New-Item -ItemType Directory -Path $publicDir -Force | Out-Null
New-Item -ItemType Directory -Path $privateDir -Force | Out-Null
New-Item -ItemType Directory -Path $testsDir -Force | Out-Null

$rawFunctionNames = if ($Functions.Count -gt 0) { $Functions } else { @(Get-DefaultFunctionName -InputModuleName $ModuleName) }
$functionNames = @()
foreach ($entry in $rawFunctionNames) {
    if ([string]::IsNullOrWhiteSpace($entry)) {
        continue
    }
    $functionNames += ($entry -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ })
}

$functionNames = @($functionNames | Select-Object -Unique)
foreach ($fn in $functionNames) {
    if ($fn -notmatch "^[A-Za-z]+-[A-Za-z0-9]+$") {
        throw "Function name '$fn' must follow Verb-Noun format."
    }
}

foreach ($fn in $functionNames) {
    $functionFile = Join-Path -Path $publicDir -ChildPath "$fn.ps1"
    New-FunctionFile -FunctionName $fn -OutputPath $functionFile
}

$moduleFile = Join-Path -Path $moduleRoot -ChildPath "$ModuleName.psm1"
$moduleContent = @'
$public = Get-ChildItem -Path (Join-Path -Path $PSScriptRoot -ChildPath "Public") -Filter *.ps1 -File -ErrorAction SilentlyContinue
$private = Get-ChildItem -Path (Join-Path -Path $PSScriptRoot -ChildPath "Private") -Filter *.ps1 -File -ErrorAction SilentlyContinue

foreach ($file in @($private + $public)) {
    . $file.FullName
}

Export-ModuleMember -Function $public.BaseName
'@
Set-Content -LiteralPath $moduleFile -Value $moduleContent -Encoding UTF8

$manifestFile = Join-Path -Path $moduleRoot -ChildPath "$ModuleName.psd1"
New-ModuleManifest `
    -Path $manifestFile `
    -RootModule "$ModuleName.psm1" `
    -ModuleVersion "0.1.0" `
    -Guid ([guid]::NewGuid()) `
    -Author $Author `
    -Description $Description `
    -FunctionsToExport $functionNames `
    -PowerShellVersion "5.1"

$firstFunction = $functionNames[0]
$testFile = Join-Path -Path $testsDir -ChildPath "$firstFunction.Tests.ps1"
$testContent = @"
# Requires -Modules Pester

BeforeAll {
    `$modulePath = Join-Path -Path `$PSScriptRoot -ChildPath "..\$ModuleName.psd1"
    Import-Module -Name `$modulePath -Force
}

Describe "$firstFunction" {
    It "returns object output on happy path" {
        `$result = $firstFunction -Name "demo"
        `$result | Should -Not -BeNullOrEmpty
        `$result.Name | Should -Be "demo"
    }
}
"@
Set-Content -LiteralPath $testFile -Value $testContent -Encoding UTF8

Write-Host "Created module scaffold: $moduleRoot"
Write-Host "Public functions: $($functionNames -join ', ')"
exit 0

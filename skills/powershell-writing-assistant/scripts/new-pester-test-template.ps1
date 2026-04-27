[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidatePattern("^[A-Za-z]+-[A-Za-z0-9]+$")]
    [string]$FunctionName,

    [Parameter(Mandatory)]
    [string]$OutputPath,

    [string]$SourcePath = "",

    [switch]$HasShouldProcess,

    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-TestTemplateContent {
    param(
        [Parameter(Mandatory)]
        [string]$CommandName,
        [string]$CommandSourcePath,
        [switch]$WithShouldProcess
    )

    $sourceBlock = if ([string]::IsNullOrWhiteSpace($CommandSourcePath)) {
@"
    # TODO: Dot-source or import the command under test.
    # Example:
    # . (Join-Path -Path `$PSScriptRoot -ChildPath "..\src\$CommandName.ps1")
"@
    }
    else {
@"
    . (Resolve-Path -LiteralPath "$CommandSourcePath").Path
"@
    }

    $shouldProcessContext = if ($WithShouldProcess) {
@"

    Context "ShouldProcess behavior" {
        It "supports -WhatIf without throwing" {
            { $CommandName -Name "demo" -WhatIf } | Should -Not -Throw
        }
    }
"@
    }
    else {
        ""
    }

@"
# Requires -Modules Pester

BeforeAll {
$sourceBlock
}

Describe "$CommandName" {
    Context "Parameter validation" {
        It "throws when required parameter is missing" {
            { $CommandName } | Should -Throw
        }
    }

    Context "Output contract" {
        It "returns object(s) with stable properties on happy path" {
            `$result = $CommandName -Name "demo"
            `$result | Should -Not -BeNullOrEmpty
            (`$result | Get-Member -MemberType NoteProperty, Property).Name | Should -Contain "Name"
        }
    }$shouldProcessContext
}
"@
}

$resolvedOutput = Resolve-Path -Path $OutputPath -ErrorAction SilentlyContinue
if ($resolvedOutput -and -not $Force) {
    throw "Output file '$OutputPath' already exists. Use -Force to overwrite."
}

$outputFile = if ($resolvedOutput) {
    $resolvedOutput.Path
}
else {
    [System.IO.Path]::GetFullPath($OutputPath)
}

$outputDirectory = Split-Path -Path $outputFile -Parent
if (-not [string]::IsNullOrWhiteSpace($outputDirectory) -and -not (Test-Path -LiteralPath $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
}

$content = Get-TestTemplateContent -CommandName $FunctionName -CommandSourcePath $SourcePath -WithShouldProcess:$HasShouldProcess
Set-Content -LiteralPath $outputFile -Value $content -Encoding UTF8

Write-Host "Created pester test template: $outputFile"
exit 0

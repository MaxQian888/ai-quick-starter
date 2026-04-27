[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$skillRoot = Split-Path -Path $PSScriptRoot -Parent
$workspace = Join-Path -Path $PSScriptRoot -ChildPath ".tmp-smoke"

function Assert-PathExists {
    param(
        [Parameter(Mandatory)]
        [string]$LiteralPath,
        [Parameter(Mandatory)]
        [string]$Message
    )

    if (-not (Test-Path -LiteralPath $LiteralPath)) {
        throw $Message
    }
}

if (Test-Path -LiteralPath $workspace) {
    Remove-Item -LiteralPath $workspace -Recurse -Force
}

New-Item -ItemType Directory -Path $workspace -Force | Out-Null

try {
    $functionTemplate = Join-Path -Path $skillRoot -ChildPath "scripts/new-advanced-function-template.ps1"
    $pesterTemplate = Join-Path -Path $skillRoot -ChildPath "scripts/new-pester-test-template.ps1"
    $moduleTemplate = Join-Path -Path $skillRoot -ChildPath "scripts/new-module-template.ps1"
    $ciTemplate = Join-Path -Path $skillRoot -ChildPath "scripts/new-ci-pipeline-template.ps1"

    $functionOutput = Join-Path -Path $workspace -ChildPath "Get-ExampleItem.ps1"
    & $functionTemplate -Name Get-ExampleItem -OutputPath $functionOutput -SupportsShouldProcess
    Assert-PathExists -LiteralPath $functionOutput -Message "Function template was not created."
    if ((Get-Content -Raw -LiteralPath $functionOutput) -notmatch "function Get-ExampleItem") {
        throw "Function template content does not include the requested function name."
    }

    $testOutput = Join-Path -Path $workspace -ChildPath "Get-ExampleItem.Tests.ps1"
    & $pesterTemplate -FunctionName Get-ExampleItem -OutputPath $testOutput -SourcePath $functionOutput -HasShouldProcess
    Assert-PathExists -LiteralPath $testOutput -Message "Pester test template was not created."
    if ((Get-Content -Raw -LiteralPath $testOutput) -notmatch 'Describe "Get-ExampleItem"') {
        throw "Pester test template content does not include the requested describe block."
    }

    $moduleRoot = Join-Path -Path $workspace -ChildPath "modules"
    & $moduleTemplate -ModuleName ContosoTools -RootPath $moduleRoot -Functions Get-ContosoStatus,Set-ContosoStatus
    $moduleDir = Join-Path -Path $moduleRoot -ChildPath "ContosoTools"
    Assert-PathExists -LiteralPath (Join-Path -Path $moduleDir -ChildPath "ContosoTools.psm1") -Message "Module file was not created."
    Assert-PathExists -LiteralPath (Join-Path -Path $moduleDir -ChildPath "ContosoTools.psd1") -Message "Module manifest was not created."
    Assert-PathExists -LiteralPath (Join-Path -Path $moduleDir -ChildPath "Tests/Get-ContosoStatus.Tests.ps1") -Message "Module test file was not created."

    & $ciTemplate -ProjectRoot $workspace -WorkflowName powershell-ci -SkipPester
    $workflowPath = Join-Path -Path $workspace -ChildPath ".github/workflows/powershell-ci.yml"
    Assert-PathExists -LiteralPath $workflowPath -Message "CI workflow was not created."
    if ((Get-Content -Raw -LiteralPath $workflowPath) -notmatch "Run quality gate") {
        throw "CI workflow content does not include the quality gate step."
    }
}
finally {
    if (Test-Path -LiteralPath $workspace) {
        Remove-Item -LiteralPath $workspace -Recurse -Force
    }
}

Write-Host "PowerShell writing assistant smoke tests passed."

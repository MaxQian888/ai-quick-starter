[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$Path,

    [switch]$Recurse,

    [switch]$FailOnWarning
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-GateFailure {
    param(
        [Parameter(Mandatory)]
        [string]$Message
    )
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Get-PowerShellTargets {
    param(
        [Parameter(Mandatory)]
        [string]$InputPath,
        [switch]$IncludeRecurse
    )

    $resolved = Resolve-Path -Path $InputPath -ErrorAction Stop
    $extensionSet = @(".ps1", ".psm1", ".psd1")
    $files = [System.Collections.Generic.List[string]]::new()

    foreach ($item in $resolved) {
        $target = Get-Item -LiteralPath $item.Path -ErrorAction Stop
        if ($target.PSIsContainer) {
            $children = Get-ChildItem -LiteralPath $target.FullName -File -Recurse:$IncludeRecurse
            foreach ($child in $children) {
                if ($extensionSet -contains $child.Extension.ToLowerInvariant()) {
                    $files.Add($child.FullName)
                }
            }
            continue
        }

        if ($extensionSet -contains $target.Extension.ToLowerInvariant()) {
            $files.Add($target.FullName)
        }
    }

    return $files | Sort-Object -Unique
}

function Get-ParseResult {
    param(
        [Parameter(Mandatory)]
        [string]$FilePath
    )

    $tokens = $null
    $parseErrors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile(
        $FilePath,
        [ref]$tokens,
        [ref]$parseErrors
    )

    return [pscustomobject]@{
        Path            = $FilePath
        ParseErrorCount = @($parseErrors).Count
        ParseErrors     = @($parseErrors)
    }
}

$targets = @(Get-PowerShellTargets -InputPath $Path -IncludeRecurse:$Recurse)
if ($targets.Count -eq 0) {
    Write-GateFailure "No .ps1/.psm1/.psd1 files found under '$Path'."
    exit 2
}

$parseResults = @(foreach ($target in $targets) {
    Get-ParseResult -FilePath $target
})

$parseErrorCount = [int](($parseResults | Measure-Object -Property ParseErrorCount -Sum).Sum)
$hasFailures = $false

if ($parseErrorCount -gt 0) {
    Write-GateFailure "Parser validation failed with $parseErrorCount error(s)."
    foreach ($result in $parseResults) {
        foreach ($parseError in $result.ParseErrors) {
            $line = $parseError.Extent.StartLineNumber
            $column = $parseError.Extent.StartColumnNumber
            Write-GateFailure ("{0}:{1}:{2} {3}" -f $result.Path, $line, $column, $parseError.Message)
        }
    }
    $hasFailures = $true
}

$analyzerAvailable = [bool](Get-Module -ListAvailable -Name PSScriptAnalyzer | Select-Object -First 1)
$analyzerResults = @()

if ($analyzerAvailable) {
    $analyzerPath = if ((Get-Item -LiteralPath (Resolve-Path -Path $Path).Path).PSIsContainer) {
        (Resolve-Path -Path $Path).Path
    }
    else {
        $targets
    }

    $invokeParams = @{
        Path     = $analyzerPath
        Severity = @("Warning", "Error")
        Recurse  = [bool]$Recurse
    }

    try {
        $analyzerResults = @(Invoke-ScriptAnalyzer @invokeParams)
    }
    catch {
        Write-Warning "Invoke-ScriptAnalyzer failed: $($_.Exception.Message)"
    }
}
else {
    Write-Warning "PSScriptAnalyzer is not installed. Skip lint checks and keep parser checks only."
}

$analyzerErrorCount = @($analyzerResults | Where-Object { $_.Severity -eq "Error" }).Count
$analyzerWarningCount = @($analyzerResults | Where-Object { $_.Severity -eq "Warning" }).Count

if ($analyzerErrorCount -gt 0 -or ($FailOnWarning -and $analyzerWarningCount -gt 0)) {
    $message = if ($FailOnWarning) {
        "ScriptAnalyzer found $analyzerErrorCount error(s) and $analyzerWarningCount warning(s)."
    }
    else {
        "ScriptAnalyzer found $analyzerErrorCount error(s)."
    }
    Write-GateFailure $message

    foreach ($finding in $analyzerResults) {
        if ($finding.Severity -eq "Error" -or ($FailOnWarning -and $finding.Severity -eq "Warning")) {
            Write-GateFailure ("{0}:{1}:{2} [{3}] {4}" -f $finding.ScriptPath, $finding.Line, $finding.Column, $finding.RuleName, $finding.Message)
        }
    }

    $hasFailures = $true
}

$summary = [pscustomobject]@{
    FilesScanned      = @($targets).Count
    ParseErrors       = $parseErrorCount
    AnalyzerAvailable = $analyzerAvailable
    AnalyzerErrors    = $analyzerErrorCount
    AnalyzerWarnings  = $analyzerWarningCount
    FailOnWarning     = [bool]$FailOnWarning
}

$summary | Format-List | Out-Host

if ($hasFailures) {
    exit 1
}

Write-Host "PowerShell quality gate passed."
exit 0

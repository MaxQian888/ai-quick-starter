[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidatePattern("^[A-Za-z]+-[A-Za-z0-9]+$")]
    [string]$Name,

    [Parameter(Mandatory)]
    [string]$OutputPath,

    [switch]$SupportsShouldProcess,

    [switch]$AcceptPipelineInput,

    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-TemplateContent {
    param(
        [Parameter(Mandatory)]
        [string]$FunctionName,
        [switch]$WithShouldProcess,
        [switch]$WithPipelineInput
    )

    $cmdletBinding = if ($WithShouldProcess) {
        "[CmdletBinding(SupportsShouldProcess, ConfirmImpact = `"Medium`")]"
    }
    else {
        "[CmdletBinding()]"
    }

    $pipelineParameter = if ($WithPipelineInput) {
@"
        [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName)]
        [Alias("InputObject", "Item")]
        [string]`$Name
"@
    }
    else {
@"
        [Parameter(Mandatory)]
        [string]`$Name
"@
    }

    $processBody = if ($WithShouldProcess) {
@"
        if (-not `$PSCmdlet.ShouldProcess(`$Name, "Process item")) {
            return
        }

        [pscustomobject]@{
            Name      = `$Name
            Processed = `$true
            Timestamp = Get-Date
        }
"@
    }
    else {
@"
        [pscustomobject]@{
            Name      = `$Name
            Processed = `$true
            Timestamp = Get-Date
        }
"@
    }

@"
function $FunctionName {
    $cmdletBinding
    param(
$pipelineParameter
    )

    begin {
        Set-StrictMode -Version Latest
        `$ErrorActionPreference = "Stop"
    }

    process {
        $processBody
    }
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

$content = Get-TemplateContent -FunctionName $Name -WithShouldProcess:$SupportsShouldProcess -WithPipelineInput:$AcceptPipelineInput
Set-Content -LiteralPath $outputFile -Value $content -Encoding UTF8

Write-Host "Created function template: $outputFile"
exit 0

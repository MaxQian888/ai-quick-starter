param(
  [Parameter(Mandatory = $true, Position = 0)][string]$CommandName,
  [Parameter(ValueFromRemainingArguments = $true)][string[]]$RemainingArgs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "read_pdf.py"

function Test-CommandAvailable {
  param([string]$Name)
  return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

if (Test-CommandAvailable "uv") {
  & uv run --quiet --with pymupdf --with pypdf python $scriptPath $CommandName @RemainingArgs
  exit $LASTEXITCODE
}

if (Test-CommandAvailable "py") {
  & py -3 $scriptPath $CommandName @RemainingArgs
  exit $LASTEXITCODE
}

if (Test-CommandAvailable "python") {
  & python $scriptPath $CommandName @RemainingArgs
  exit $LASTEXITCODE
}

Write-Error @"
No Python runner was found for read_pdf.ps1.

Try one of these direct commands instead:
  inspect: pdfinfo <file.pdf>
  text:    pdftotext -layout <file.pdf> -
  render:  pdftoppm -png <file.pdf> <output-prefix>
"@

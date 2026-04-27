# Pipeline And Functions

## Function Skeleton

Use this baseline for reusable commands:

```powershell
function Get-ExampleItem {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Name
    )

    Set-StrictMode -Version Latest
    $ErrorActionPreference = "Stop"

    process {
        [pscustomobject]@{
            Name = $Name
        }
    }
}
```

## Pipeline Input Patterns

Use `ValueFromPipeline` when accepting full objects:

```powershell
[Parameter(ValueFromPipeline)]
[pscustomobject]$InputObject
```

Use `ValueFromPipelineByPropertyName` when mapping incoming properties:

```powershell
[Parameter(ValueFromPipelineByPropertyName)]
[Alias("ComputerName", "Server")]
[string]$Name
```

Prefer explicit parameter sets when supporting multiple input modes:

```powershell
[CmdletBinding(DefaultParameterSetName = "ByName")]
param(
    [Parameter(ParameterSetName = "ByName", Mandatory)]
    [string]$Name,

    [Parameter(ParameterSetName = "ById", Mandatory)]
    [int]$Id
)
```

## Begin Process End

Use lifecycle blocks to separate concerns:

- `begin`: Initialize expensive resources once.
- `process`: Handle one pipeline item at a time.
- `end`: Flush buffers or emit aggregate output.

Pattern:

```powershell
begin {
    $buffer = [System.Collections.Generic.List[object]]::new()
}
process {
    $buffer.Add($InputObject)
}
end {
    $buffer
}
```

## ShouldProcess Pattern

Use this for mutating commands:

```powershell
[CmdletBinding(SupportsShouldProcess, ConfirmImpact = "Medium")]
param([string]$Name)

if ($PSCmdlet.ShouldProcess($Name, "Remove item")) {
    Remove-Item -LiteralPath $Name -Force
}
```

## Output Contract Rules

- Return objects, not formatted text, from reusable functions.
- Keep output property names stable across versions.
- Emit one object shape per command unless documented otherwise.
- Add inline comments only for non-obvious behavior.

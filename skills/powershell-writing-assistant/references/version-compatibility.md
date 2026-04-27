# Version Compatibility

## Target Decision

Choose one target up front:

- Windows PowerShell 5.1 only.
- PowerShell 7+ only.
- Dual support (5.1 and 7+).

Default to dual support when the user does not specify a version and the script has no 7-only requirement.

## High-Impact Differences

- `ForEach-Object -Parallel` is PowerShell 7+ only.
- Ternary operator `condition ? a : b` is PowerShell 7+ only.
- Null-coalescing operators `??` and `??=` are PowerShell 7+ only.
- `Get-Error` is PowerShell 7+ only.
- Module availability differs by platform and version.
- Encoding defaults differ across versions; set encoding explicitly for file IO.

## Cross-Platform Guidance

- Use .NET APIs or PowerShell cmdlets instead of shell-specific tools when possible.
- Avoid hard-coded Windows paths or backslashes for reusable scripts.
- Use `Join-Path` and `Split-Path` instead of string concatenation.
- Handle line endings and case sensitivity differences in file operations.

## Safe Dual-Support Patterns

Prefer explicit runtime checks for 7+ features:

```powershell
if ($PSVersionTable.PSVersion.Major -ge 7) {
    # PowerShell 7+ path
}
else {
    # Windows PowerShell 5.1 fallback
}
```

Use explicit encoding:

```powershell
Set-Content -LiteralPath $Path -Value $Content -Encoding UTF8
```

Avoid feature assumptions in module code paths unless guarded by version checks.

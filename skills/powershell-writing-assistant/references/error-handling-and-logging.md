# Error Handling And Logging

## Error Strategy

Choose one strategy per command path:

- Continue on recoverable record-level failures and emit warnings.
- Stop immediately on contract violations, security-sensitive actions, or state corruption risks.

Set predictable defaults:

```powershell
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
```

Use `-ErrorAction Stop` for cmdlets that otherwise emit non-terminating errors.

## Try Catch Finally Pattern

Use `try/catch/finally` around side effects:

```powershell
try {
    Invoke-RestMethod -Uri $Uri -Method Get -ErrorAction Stop
}
catch {
    $message = "Failed to query API for '$Uri': $($_.Exception.Message)"
    throw [System.InvalidOperationException]::new($message, $_.Exception)
}
finally {
    # Close/dispose transient resources when needed.
}
```

## Exception Guidance

- Throw specific .NET exception types when possible.
- Include actionable context: target, operation, and failing identifier.
- Preserve inner exceptions when rethrowing wrapped failures.

## Logging Guidance

Use channel-specific logging:

- `Write-Verbose`: detailed execution steps for debugging.
- `Write-Information`: user-facing progress messages that are not warnings.
- `Write-Warning`: recoverable problems or degraded behavior.
- `Write-Error`: non-terminating error records when continuing.

Use structured messages with stable key terms to aid filtering.

## Native Command Pattern

When invoking native tools:

```powershell
$null = & git status --short
if ($LASTEXITCODE -ne 0) {
    throw "git status failed with exit code $LASTEXITCODE."
}
```

Do not assume native command failures throw exceptions automatically.

## Retry Guidance

Retry only transient operations (network, lock contention, throttling).
Use bounded retries and exponential backoff with jitter when practical.
Fail fast for validation errors and deterministic business-rule violations.

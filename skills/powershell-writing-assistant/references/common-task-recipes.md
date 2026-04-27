# Common Task Recipes

## File Discovery With Filters

```powershell
Get-ChildItem -LiteralPath $RootPath -File -Recurse |
    Where-Object { $_.Extension -in @(".log", ".txt") } |
    Select-Object FullName, Length, LastWriteTime
```

Use `-LiteralPath` for user-provided paths.
Use extension allow-lists instead of wildcard-heavy filters for predictable behavior.

## Read And Write JSON Safely

```powershell
$data = Get-Content -LiteralPath $JsonPath -Raw | ConvertFrom-Json
$data.LastUpdatedUtc = [DateTime]::UtcNow
$data | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $JsonPath -Encoding UTF8
```

Set `-Depth` explicitly to avoid silent truncation for nested objects.

## CSV Roundtrip

```powershell
$rows = Import-Csv -LiteralPath $CsvPath
$filtered = $rows | Where-Object { [int]$_.Score -ge 80 }
$filtered | Export-Csv -LiteralPath $OutPath -NoTypeInformation -Encoding UTF8
```

Cast numeric fields before comparison to avoid lexical comparison mistakes.

## REST Call With Timeout And Headers

```powershell
$headers = @{
    Authorization = "Bearer $Token"
    Accept        = "application/json"
}

$response = Invoke-RestMethod -Uri $Uri -Method Get -Headers $headers -TimeoutSec 30 -ErrorAction Stop
```

Always set timeout and `-ErrorAction Stop` for API calls.

## Bounded Retry Wrapper

```powershell
for ($attempt = 1; $attempt -le 4; $attempt++) {
    try {
        return Invoke-RestMethod -Uri $Uri -Method Get -TimeoutSec 30 -ErrorAction Stop
    }
    catch {
        if ($attempt -eq 4) { throw }
        Start-Sleep -Seconds ([Math]::Pow(2, $attempt))
    }
}
```

Retry only transient operations. Do not retry validation failures.

## Native Command Wrapper

```powershell
$output = & git rev-parse --short HEAD 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "git rev-parse failed with exit code $LASTEXITCODE. Output: $output"
}
```

Capture output and include it in failure messages.

## Hashtables To Objects

```powershell
[pscustomobject]@{
    Name       = $Name
    Status     = $Status
    Retrieved  = Get-Date
    SourcePath = $Path
}
```

Use stable property names for downstream automation.

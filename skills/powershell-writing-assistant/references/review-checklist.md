# Review Checklist

Run this checklist before returning a script.

## Contract

- Confirm input contract, output contract, and target runtime version.
- Confirm whether the command is interactive or automation-safe.
- Confirm whether destructive actions require confirmation (`SupportsShouldProcess`).

## Parameters

- Use explicit parameter types.
- Use validation attributes for known constraints.
- Use parameter sets when multiple input modes exist.
- Add aliases only when they improve interoperability.

## Pipeline Behavior

- Confirm pipeline input mode (`ValueFromPipeline` vs `ValueFromPipelineByPropertyName`).
- Keep one logical object shape for output unless documented.
- Avoid formatting cmdlets in reusable functions.

## Error Handling

- Set strict mode and deterministic error behavior.
- Use `try/catch` around side effects.
- Throw actionable messages with context.
- Check `$LASTEXITCODE` after native command calls.

## Logging

- Use `Write-Verbose` for debug detail.
- Use `Write-Warning` for recoverable issues.
- Avoid `Write-Host` except explicit interactive UX.

## Safety And Maintainability

- Keep functions focused and composable.
- Avoid global state mutation unless required.
- Keep naming aligned with approved verbs.
- Add minimal comments only where behavior is non-obvious.

## Security

- Confirm no secrets are hardcoded.
- Confirm destructive actions support `-WhatIf` and `ShouldProcess`.
- Confirm least-privilege assumptions are documented.
- Confirm external calls use explicit timeout and safe error messages.

## Validation

- Run `scripts/invoke-pwsh-quality-gate.ps1` on changed files.
- Confirm parser errors are zero.
- If ScriptAnalyzer is available, confirm error count is zero.

## Tests

- Add or update Pester tests for reusable commands.
- Cover required parameter behavior and output contract.
- Cover `-WhatIf` and `ShouldProcess` paths for mutating commands.
- Keep tests deterministic by mocking external side effects.

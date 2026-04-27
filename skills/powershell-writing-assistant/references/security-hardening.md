# Security Hardening

## Secret Handling

- Never hardcode tokens, passwords, or private keys in scripts.
- Accept secrets via secure channels: environment variables, secret stores, or CI secret injection.
- Use `Get-Credential` only for interactive flows; avoid for headless automation.
- Redact sensitive values in logs and thrown messages.

## Execution Policy And Signing

- Prefer signed scripts in enterprise environments.
- Treat `Bypass` execution policy as a temporary local development exception, not a default.
- Document required policy assumptions in script/module usage notes.

## Privilege Boundaries

- Run with least privilege by default.
- Do not require admin rights unless the operation explicitly needs elevation.
- Add explicit checks and actionable error messages when elevation is mandatory.

## Input Validation

- Validate all external inputs (paths, URLs, identifiers, and file names).
- Use `-LiteralPath` for filesystem paths from users.
- Use allow-lists where practical (`ValidateSet`, regex allow patterns).

## Safe Side Effects

- Guard destructive operations with `SupportsShouldProcess`.
- Provide `-WhatIf` support for delete/overwrite/mutation actions.
- Avoid broad wildcard deletes and recursive operations without clear constraints.

## External Calls

- Set explicit timeout for network calls.
- Validate endpoint scheme and host constraints when endpoints are user-supplied.
- Check native command exit codes and include non-sensitive diagnostics on failure.

## CI Security Baseline

- Keep dependencies pinned where possible.
- Run static checks in CI before publish/deploy steps.
- Restrict workflow permissions to the minimum needed.

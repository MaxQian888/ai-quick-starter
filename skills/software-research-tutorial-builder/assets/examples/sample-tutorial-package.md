# Acme CLI Tutorial Package

## 1. What This Software Is For

Acme CLI is a command-line tool for managing local profiles and workspace-scoped automation from a Windows shell.

Use it when you want a scriptable profile workflow instead of manual setup steps. Do not use it as a first choice when you need a hosted dashboard, GUI-only onboarding, or a zero-install browser flow.

## 2. When To Use It And When Not To

Use Acme CLI when:
- you already work in PowerShell,
- you want repeatable local setup,
- and you need profile-aware automation.

Avoid Acme CLI when:
- the team requires a managed web console,
- local environment variables are tightly restricted,
- or the workflow must stay fully GUI-driven.

## 3. Environment And Prerequisites

- Windows PowerShell 7 or Windows PowerShell with profile-edit permissions
- Python 3.11
- network access for the first install

## 4. Installation Or Setup

Install the CLI:

```powershell
uv tool install acme-cli
```

Set the local home directory before first run if the Windows environment does not create it automatically:

```powershell
$env:ACME_HOME="$HOME\.acme"
```

## 5. First Runnable Example

Minimal runnable case:

```powershell
acme --help
```

Success signal:
- the CLI prints command help instead of a missing-path or missing-runtime error.

## 6. Practical Workflow Example

Practical workflow case:

```powershell
acme profile init demo
acme profile list
```

Expected result:
- a `demo` profile is created,
- and `acme profile list` shows it in the local profile inventory.

## 7. Common Mistakes And Troubleshooting

Symptom:
- the CLI installs successfully but fails on first run because the home directory or profile path is missing.

Likely cause:
- the Windows shell session does not define `ACME_HOME`, or the expected directory was never created.

Fix:

```powershell
$env:ACME_HOME="$HOME\.acme"
New-Item -ItemType Directory -Force -Path $env:ACME_HOME | Out-Null
```

Fix worked when:
- `acme --help` or `acme profile list` runs without the path error.

## 8. Extension Paths And Further Reading

- Review official install and command reference docs for version-specific changes.
- Review community Windows setup notes before teaching this to mixed Windows/macOS teams.
- Add one team-oriented workflow example after the local profile path is stable.

## Support-Material Checklist

- [x] Environment variable example
- [x] Starter command blocks
- [ ] Sample config fragment
- [ ] Sample input/output files
- [x] Cleanup steps

Cleanup:

```powershell
uv tool uninstall acme-cli
Remove-Item -LiteralPath $env:ACME_HOME -Recurse -Force
```

## Verification Summary

Executed locally in this repository:
- helper scripts that build the normalized research brief and tutorial outline.

Source-backed but not executed in this repository:
- `uv tool install acme-cli`
- `acme --help`
- `acme profile init demo`
- `acme profile list`

Unresolved:
- whether `ACME_HOME` is still required on macOS or only on Windows-specific setups.

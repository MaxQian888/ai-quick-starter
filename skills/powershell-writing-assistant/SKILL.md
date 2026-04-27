---
name: powershell-writing-assistant
description: |
  Use whenever you need to draft, review, refactor, or debug PowerShell scripts, functions, and modules, convert shell logic to PowerShell, add parameter validation or pipeline support, improve error handling and logging, or troubleshoot execution in Windows PowerShell 5.1 or PowerShell 7+. Make sure to use this skill whenever the user asks for a "PowerShell script", "PS1", "cmdlet", "module", "pipeline", "error handling", "logging", "PSScriptAnalyzer", "Pester tests", or "CI pipeline for PowerShell" — even for one-liners or quick fixes. Also trigger for cross-platform PowerShell concerns, execution policy questions, secret handling, or converting bash/cmd scripts to PowerShell. Covers scripts, advanced functions, reusable modules, tests, and CI workflows.
---

# PowerShell Writing Assistant

## Overview

Write production-grade PowerShell with advanced functions, predictable error behavior, and reusable patterns.
Use the workflow below and load reference files only when needed.

## Adaptive Detection

Before writing PowerShell, detect the environment:

1. **PowerShell version**: Determine if the target is Windows PowerShell 5.1 or PowerShell 7+.
2. **Operating system**: Note if the script must run on Windows only, Linux only, or cross-platform.
3. **Existing conventions**: Check for existing `.ps1`, `.psm1`, or `*.Tests.ps1` files in the repo.
4. **CI context**: Look for GitHub Actions, Azure Pipelines, or other CI configs that may run the scripts.
5. **Security posture**: Check for existing secret management, execution policy notes, or signing requirements.

Use these signals to choose compatible syntax, module availability, and security controls.

## Workflow

1. Restate target behavior and runtime constraints (PowerShell version, operating system, and input/output contract).
2. Select compatibility target using `references/version-compatibility.md` before writing code.
3. Choose output shape: one-liner, standalone script, advanced function, or module function.
4. Generate a baseline function file with `scripts/new-advanced-function-template.ps1` when the request is a reusable command.
5. Generate a module scaffold with `scripts/new-module-template.ps1` when the request is multi-command or reusable distribution.
6. Apply pipeline-safe function patterns from `references/pipeline-and-functions.md`.
7. Add robust error handling and logging patterns from `references/error-handling-and-logging.md`.
8. Apply reusable task recipes from `references/common-task-recipes.md` for file, API, and retry workflows.
9. Generate Pester tests with `scripts/new-pester-test-template.ps1` for reusable functions.
10. Generate CI workflow with `scripts/new-ci-pipeline-template.ps1` when the request includes repo automation.
11. Apply security controls from `references/security-hardening.md` for secrets, execution policy, and least privilege.
12. Run `scripts/invoke-pwsh-quality-gate.ps1` to parse and lint before finalizing.
13. Use `references/incident-playbook.md` when failures appear in runtime, tests, or CI to drive triage and rollback decisions.
14. Run `references/review-checklist.md` and return usage examples, expected output shape, and edge-case notes.

## Default Authoring Rules

- Prefer approved verb plus singular noun naming (for example, `Get-ItemState`, `Set-ItemState`).
- Use `[CmdletBinding(SupportsShouldProcess)]` for commands that mutate state.
- Add real parameter validation attributes (`ValidateSet`, `ValidatePattern`, `ValidateRange`, `ValidateScript`) when constraints are known.
- Keep functions small and composable; split collection, transformation, and side effects.
- Emit objects to the pipeline from reusable code; avoid formatting cmdlets inside library functions.
- Use `Write-Verbose`, `Write-Information`, and `Write-Warning` for diagnostics; reserve `Write-Host` for explicit interactive prompts.
- Treat native commands as fallible; check exit codes explicitly.
- Keep output property names stable and deterministic.

## Quality Gate

Run the quality gate script:

```powershell
pwsh -NoLogo -NoProfile -File scripts/invoke-pwsh-quality-gate.ps1 -Path <target-file-or-folder> -Recurse
```

Use `-FailOnWarning` to fail CI for warnings in addition to errors.
Expect parser validation in all environments and ScriptAnalyzer linting when `PSScriptAnalyzer` is installed.
Install analyzer when missing:

```powershell
Install-Module -Name PSScriptAnalyzer -Scope CurrentUser -Force
```

## Examples

### Example 1: Generate an advanced function scaffold

```powershell
pwsh -NoLogo -NoProfile -File scripts/new-advanced-function-template.ps1 -Name Get-ExampleItem -OutputPath ./Get-ExampleItem.ps1 -SupportsShouldProcess
```

### Example 2: Generate a Pester test scaffold

```powershell
pwsh -NoLogo -NoProfile -File scripts/new-pester-test-template.ps1 -FunctionName Get-ExampleItem -OutputPath ./Get-ExampleItem.Tests.ps1
```

### Example 3: Generate a reusable module

```powershell
pwsh -NoLogo -NoProfile -File scripts/new-module-template.ps1 -ModuleName ContosoTools -RootPath ./modules -Functions Get-ContosoStatus,Set-ContosoStatus
```

## Reference Files

- `references/pipeline-and-functions.md`: Use for advanced function templates, pipeline input patterns, and `begin/process/end` design.
- `references/error-handling-and-logging.md`: Use for terminating vs non-terminating error strategy, exception handling, and logging conventions.
- `references/version-compatibility.md`: Use for Windows PowerShell 5.1 vs PowerShell 7+ feature choices and cross-platform command behavior.
- `references/review-checklist.md`: Use as final pre-delivery checklist for correctness, maintainability, and safety.
- `references/testing-with-pester.md`: Use for Pester 5 test structure, mocking patterns, and behavior-focused assertions.
- `references/common-task-recipes.md`: Use for proven snippets covering files, JSON/CSV, REST calls, retries, and native command wrapping.
- `references/security-hardening.md`: Use for secret handling, signature policy, constrained execution, and privilege boundaries.
- `references/incident-playbook.md`: Use for runtime/CI failure triage, containment, rollback criteria, and post-incident hardening.

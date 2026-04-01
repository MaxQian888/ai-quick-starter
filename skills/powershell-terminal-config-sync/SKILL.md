---
name: powershell-terminal-config-sync
description: Discover, bundle, and safely sync PowerShell profile files plus Windows Terminal settings for a Windows user environment. Use when Codex needs to copy an existing PowerShell and terminal setup to another machine or account, audit which dependent files a profile references, recover from shell startup drift caused by missing config files, or generate a non-destructive sync script instead of guessing paths by hand.
---

# PowerShell Terminal Config Sync

## Overview

Discover live PowerShell and Windows Terminal configuration, capture dependent files, and emit a reviewable sync bundle plus a `ShouldProcess`-safe PowerShell copy script.
Use the helper script first, review the JSON bundle before copying anything, and keep missing or machine-specific references explicit.

## Quick Start

1. Inspect the current machine without loading the live profile:

```powershell
python scripts/build_shell_config_sync_plan.py --source-home "$env:USERPROFILE" --source-localappdata "$env:LOCALAPPDATA" --output-dir .\artifacts\shell-config
```

2. Read `shell-config-sync-bundle.json` first.
3. Review `shell-config-sync-bundle.md` for blockers, unresolved references, and manual review items.
4. Run the generated script in preview mode on the destination machine:

```powershell
pwsh -NoLogo -NoProfile -File .\artifacts\shell-config\sync-shell-config.ps1 -TargetHome "C:\Users\OtherUser" -WhatIf
```

5. Only remove `-WhatIf` after the destination paths look correct.

## Workflow

### 1. Discover Before Copying

Check the real Windows paths first:

- `Documents\WindowsPowerShell\*.ps1`
- `Documents\PowerShell\*.ps1`
- `%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json`
- `%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminalPreview_8wekyb3d8bbwe\LocalState\settings.json`
- `%LOCALAPPDATA%\Microsoft\Windows Terminal\settings.json`

Do not assume the user only uses PowerShell 7 or only uses the stable Windows Terminal package.

### 2. Parse Dependencies Conservatively

The helper scans:

- `oh-my-posh ... --config <path>`
- dot-sourced scripts such as `. "$HOME\Documents\WindowsPowerShell\aliases.ps1"`
- quoted file paths inside profile files
- path-like values inside Windows Terminal `settings.json`
- imported module names for manual follow-up

Treat missing files and machine-specific absolute paths as review items, not as silent skips.

### 3. Generate The Sync Bundle

The helper writes:

- `shell-config-sync-bundle.json`
- `shell-config-sync-bundle.md`
- `sync-shell-config.ps1`

The JSON bundle is the source of truth for automation and verification.

### 4. Review Before Executing

Check these sections first:

- `profiles`
- `terminal_settings`
- `copy_mappings`
- `manual_review`
- `unresolved_references`
- `blockers`

If the profile references files outside the source home or `LocalAppData`, do not pretend the generated sync script fully reproduces the environment.

### 5. Execute With `-NoProfile`

When reading or running live profile-related commands, prefer `pwsh -NoLogo -NoProfile`.
If the source machine profile is already broken, `-NoProfile` prevents startup failures from masking the real file layout.

## Guardrails

- Do not overwrite destination files blindly without a `-WhatIf` preview first.
- Do not claim module installation is covered. Imported modules are reported, not installed.
- Do not mutate Windows Terminal settings inline when file copying is enough.
- Do not hide unresolved references such as missing theme JSON or external scripts under `C:\Tools`.
- Do not delete destination files to "match" the source machine.

## References

- Read `references/path-discovery.md` for the path priority list and dependency parsing rules.
- Read `references/sync-guardrails.md` before editing the generated script or widening sync behavior.
- Read `scripts/build_shell_config_sync_plan.py` for the actual bundle and script contract.

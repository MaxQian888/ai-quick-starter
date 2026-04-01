# Sync Guardrails

Use this file before changing the helper script or executing the generated sync script on a destination machine.

## Safety Contract

- Preview first with `-WhatIf`.
- Copy only existing files discovered from the source machine.
- Keep manual review items explicit when a file lives outside the source home or `LocalAppData`.
- Keep unresolved references explicit when a profile points to missing files.
- Avoid destructive cleanup on the destination machine.

## Non-Goals

- Module installation
- Font installation
- Registry edits
- Rewriting machine-specific command lines inside Windows Terminal settings
- Deleting destination files that are absent on the source machine

## Practical Notes

- Use `pwsh -NoLogo -NoProfile` during source inspection to avoid broken profiles blocking discovery.
- Windows Terminal settings are usually JSONC, so comment stripping and trailing-comma tolerance are required.
- A copied profile can still fail on the destination machine if external executables such as `oh-my-posh.exe` are not installed.

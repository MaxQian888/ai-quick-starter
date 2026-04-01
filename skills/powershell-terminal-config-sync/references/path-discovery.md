# Path Discovery

Use this file when the machine has more than one PowerShell host or Windows Terminal install path.

## Priority Order

1. `Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1`
2. `Documents\WindowsPowerShell\profile.ps1`
3. `Documents\PowerShell\Microsoft.PowerShell_profile.ps1`
4. `Documents\PowerShell\profile.ps1`
5. `%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json`
6. `%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminalPreview_8wekyb3d8bbwe\LocalState\settings.json`
7. `%LOCALAPPDATA%\Microsoft\Windows Terminal\settings.json`

## Dependency Rules

- Capture `oh-my-posh --config` targets.
- Capture dot-sourced scripts.
- Capture quoted absolute or environment-expanded file paths.
- Capture path-like values from Windows Terminal JSON fields such as `backgroundImage`, `icon`, `commandline`, and `startingDirectory`.
- Record imported module names separately because modules usually need installation, not file copying.

## Resolution Rules

- Expand `$HOME`, `$env:USERPROFILE`, and `%USERPROFILE%` to the source home root.
- Expand `$env:LOCALAPPDATA` and `%LOCALAPPDATA%` to the source LocalAppData root.
- Expand `$env:APPDATA` and `%APPDATA%` to the source roaming AppData root.
- Resolve relative paths against the file that referenced them.
- Treat paths outside the source home and LocalAppData roots as manual review items.

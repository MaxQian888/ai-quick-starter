# Windows Recording Fallbacks

Use this reference when `ffmpeg` is missing, window capture is unreliable, or the user needs a specific Windows-native fallback.

## Backend Order

1. `ffmpeg` via `scripts/record_screen.ps1`
2. Windows Problem Steps Recorder (`psr.exe`) via the same script
3. Manual fallback with Xbox Game Bar or Snipping Tool

## Why The Helper Prefers ffmpeg

- Produces `.mp4` output directly
- Supports desktop, region, and fixed window-bounds capture
- Can add optional audio
- Works well for short bug repro clips

## Why PSR Is The Automatic Fallback

- Ships with Windows
- Captures click-by-click repro artifacts without extra installs
- Saves a `.zip` artifact that is easy to share

Tradeoff: PSR is not continuous video. It captures screenshots, annotations, and input steps.

## Manual Windows Fallbacks

### Xbox Game Bar

Use when the user needs real video but `ffmpeg` is unavailable.

1. Focus the target app window.
2. Press `Win + G`.
3. Start recording from the Capture widget or press `Win + Alt + R`.
4. Stop recording with `Win + Alt + R`.
5. Find output under `Videos\Captures`.

Notes:
- Game Bar is best for one app window.
- It may refuse to capture File Explorer or the full desktop.

### Snipping Tool Screen Recording

Use when the user wants a quick manual region recording.

1. Open Snipping Tool.
2. Switch to the record tab.
3. Select the region.
4. Start and stop recording from the tool UI.
5. Save the resulting video where needed.

Notes:
- Region is selected manually.
- Automation is weak compared with `ffmpeg`.

## Multi-Window Guidance

- If an app opens many similar windows, do not guess.
- Run:

```powershell
pwsh -ExecutionPolicy Bypass -File <path-to-skill>/scripts/record_screen.ps1 -ListWindows -App "MyApp"
```

- Then rerun with the exact handle:

```powershell
pwsh -ExecutionPolicy Bypass -File <path-to-skill>/scripts/record_screen.ps1 -Capture window -WindowHandle 0x00123456
```

- If the user cannot keep one window stable, prefer `-Capture desktop`.

## Audio Notes

- The helper only supports audio when `ffmpeg` is available.
- Enumerate devices with:

```powershell
pwsh -ExecutionPolicy Bypass -File <path-to-skill>/scripts/record_screen.ps1 -ListAudioDevices
```

- Then pass the exact device name:

```powershell
pwsh -ExecutionPolicy Bypass -File <path-to-skill>/scripts/record_screen.ps1 -Capture desktop -IncludeAudio -AudioDevice "Stereo Mix (Realtek(R) Audio)"
```

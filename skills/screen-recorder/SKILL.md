---
name: screen-recorder
description: |
  Use whenever you need to capture desktop or window or region recordings for software debugging and repro artifacts, record a bug repro video, capture a UI workflow, or fall back to Windows click-trace tooling when ffmpeg-backed recording is unavailable. Make sure to use this skill whenever the user says "record screen", "capture video", "bug repro", "screen recording", "record my app", "make a video", or "record this window" — even for short clips or single-window captures. Also trigger when the user needs to record a tutorial, document a UI bug, or capture a workflow for a pull request. Covers full desktop, single window, region capture, and audio recording on Windows.
---

# Screen Recorder

## Overview

Record reproducible debug artifacts for desktop software. Prefer the bundled Windows PowerShell helper, which uses `ffmpeg` when present and otherwise falls back to Windows Problem Steps Recorder (PSR) plus manual system-tool guidance.

## Adaptive Detection

Before recording, detect the environment:

1. **ffmpeg availability**: Check if `ffmpeg` is on PATH with `ffmpeg -version`.
2. **Target window**: Determine if the user wants full desktop, a specific window, or a region.
3. **Audio needs**: Ask if audio capture is required.
4. **Output preference**: Note if the user needs a specific file path or format.
5. **App type**: Identify if the target is a desktop app, browser window, or terminal.

Use these signals to choose the best capture mode and fallback strategy.

## Quick Start

- Windows helper:

```powershell
pwsh -ExecutionPolicy Bypass -File <path-to-skill>/scripts/record_screen.ps1 -Capture auto -App "MyApp" -DurationSeconds 20
```

- Inspect matching windows before locking to one:

```powershell
pwsh -ExecutionPolicy Bypass -File <path-to-skill>/scripts/record_screen.ps1 -ListWindows -App "MyApp"
```

- Lock to one window by handle:

```powershell
pwsh -ExecutionPolicy Bypass -File <path-to-skill>/scripts/record_screen.ps1 -Capture window -WindowHandle 0x00123456 -DurationSeconds 15
```

- Record the whole desktop directly:

```powershell
pwsh -ExecutionPolicy Bypass -File <path-to-skill>/scripts/record_screen.ps1 -Capture desktop -DurationSeconds 30
```

- Dry-run the chosen backend without starting capture:

```powershell
pwsh -ExecutionPolicy Bypass -File <path-to-skill>/scripts/record_screen.ps1 -Capture auto -App "MyApp" -DryRun
```

## Workflow

1. Prefer `ffmpeg` when it is on `PATH`. The helper records to `.mp4`, supports full desktop, region, or fixed window bounds, and optionally adds audio.
2. If the user points at an app and multiple windows match, run `-ListWindows` first, then rerun with `-WindowHandle`. Do not guess.
3. If no exact window can be chosen in `-Capture auto`, let the helper fall back to desktop capture instead of risking the wrong window.
4. If `ffmpeg` is unavailable, let the helper fall back to PSR. Be explicit that PSR produces a click-by-click `.zip` report, not continuous video.
5. If the user truly needs continuous video and `ffmpeg` is missing, tell them to install `ffmpeg` or use Xbox Game Bar / Snipping Tool manually. See `references/windows-fallbacks.md`.

## Common Tasks

- Default output location:
  - `-Mode default` writes to `Videos\Captures` when it exists, otherwise `Videos`.
  - `-Mode temp` writes to the temp directory.
  - `-Path` overrides both.

- Multi-window app:
  - Run `-ListWindows -App "<name>"`.
  - Prefer `-WindowHandle` for the final capture.
  - Use `-Capture auto` if you want safe fallback to desktop when the app has too many similar windows.

- Region capture:

```powershell
pwsh -ExecutionPolicy Bypass -File <path-to-skill>/scripts/record_screen.ps1 -Capture region -Region 100,200,1280,720 -DurationSeconds 20
```

- Audio capture is opt-in and Windows-only through `ffmpeg`:

```powershell
pwsh -ExecutionPolicy Bypass -File <path-to-skill>/scripts/record_screen.ps1 -ListAudioDevices
pwsh -ExecutionPolicy Bypass -File <path-to-skill>/scripts/record_screen.ps1 -Capture desktop -IncludeAudio -AudioDevice "Stereo Mix (Realtek(R) Audio)" -DurationSeconds 20
```

## Limits

- Window capture on Windows uses the window's current bounds. If the window moves, resizes, or is covered during capture, the recording does not magically follow it. In that case, prefer desktop capture.
- `ffmpeg` is not bundled. Probe with `record_screen.ps1 -DryRun` or `ffmpeg -version`.
- PSR fallback is useful for reproducing click flows, but it is not a substitute for a real video when animation timing matters.

## Troubleshooting

- Wrong window selected:
  - Rerun with `-ListWindows`.
  - Filter more narrowly with `-WindowTitle`.
  - Use `-WindowHandle` for the final run.

- No audio device works:
  - Run `-ListAudioDevices`.
  - Pass the exact DirectShow device name with `-AudioDevice`.
  - If no device appears, record video-only or switch to an external tool.

- Need stronger fallback guidance:
  - Read `references/windows-fallbacks.md`.

## Examples

### Example 1: List windows for an app

```powershell
pwsh -ExecutionPolicy Bypass -File scripts/record_screen.ps1 -ListWindows -App "Chrome"
```

### Example 2: Record desktop with audio

```powershell
pwsh -ExecutionPolicy Bypass -File scripts/record_screen.ps1 -Capture desktop -IncludeAudio -AudioDevice "Stereo Mix (Realtek(R) Audio)" -DurationSeconds 20
```

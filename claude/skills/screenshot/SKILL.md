---
name: "screenshot"
description: >
  Capture desktop screenshots, app windows, screen regions, the active/focused window, or
  multi-display setups across macOS, Windows, and Linux. Make sure to use this skill whenever
  the user asks to "take a screenshot", "show me what's on screen", "capture this window",
  "grab my desktop", "snip a region", "save a screen recording frame", or anything similar -
  also when they want a visual check, UI comparison, or desktop-app debugging artifact and
  no tool-specific capture (Figma MCP, Playwright/agent-browser, IDE tools) fits the target.
  Bundles platform helpers so capture, multi-display handling, region selection, and macOS
  permission preflight all happen through one consistent CLI surface.
---

# Screenshot Capture

## Tool priority (read this first)

1. Prefer a tool-specific capture when the target is a browser/Electron app (Playwright, agent-browser), a Figma file (Figma MCP), or an IDE preview - those produce cleaner, deterministic images.
2. Use this skill when there is no better-integrated capture, when the user explicitly asks for a screenshot, or for whole-system desktop captures.

## Adaptive detection

Before capturing, decide:

- **OS**: `macOS` → Python helper, `Windows` → PowerShell helper, `Linux` → Python helper (delegates to `scrot`/`gnome-screenshot`/`import`).
- **Save location** (apply in order):
  1. User specified a path → save there.
  2. User wants a screenshot but didn't specify a path → OS default screenshot folder (`--mode default`).
  3. The agent itself needs to inspect the image → temp directory (`--mode temp`).
- **Target**: full desktop, specific app/window, region, or active window.
- **Multi-display**: macOS and Windows save one file per display by default (suffixes `-d1`, `-d2`, …). Pass `-VirtualDesktop` (Windows) to stitch into one image; macOS captures all displays automatically. Linux always captures the virtual desktop.
- **macOS permission**: run the preflight once before window/app capture (see below).

## macOS / Linux helper (Python)

`<path-to-skill>` refers to the directory containing this `SKILL.md`.

```bash
python3 <path-to-skill>/scripts/take_screenshot.py [flags]
```

| Goal | Flags |
|---|---|
| Default location (user asked for "a screenshot") | *(no flags)* |
| Temp location (your own visual check) | `--mode temp` |
| Explicit path | `--path output/screen.png` |
| App/window by name (macOS only) | `--app "Codex"` |
| Specific window title within an app (macOS only) | `--app "Codex" --window-name "Settings"` |
| List window ids before capturing (macOS only) | `--list-windows --app "Codex"` |
| Pixel region | `--region x,y,w,h` |
| Focused/active window | `--active-window` |
| Specific window id | `--window-id 12345` |

The script prints one path per line. With multiple windows or displays it emits multiple lines and adds suffixes such as `-w<windowId>` or `-d<display>`. View each path in turn; do not edit the image unless the user asks.

### macOS permission preflight

Run this once per session before any window/app capture - it requests Screen Recording in one place and routes Swift's module cache to `$TMPDIR/codex-swift-module-cache` to avoid sandbox prompts.

```bash
bash <path-to-skill>/scripts/ensure_macos_permissions.sh
```

To collapse permission prompts, chain it with the capture:

```bash
bash <path-to-skill>/scripts/ensure_macos_permissions.sh && \
  python3 <path-to-skill>/scripts/take_screenshot.py --app "<App>" --mode temp
```

### Linux prerequisites

The helper auto-selects the first available tool: `scrot` → `gnome-screenshot` → ImageMagick `import`. Region capture needs `scrot` or `import`. `--app`, `--window-name`, and `--list-windows` are macOS-only; on Linux use `--active-window` or `--window-id`. If none of the tools are installed, ask the user to install one and retry.

## Windows helper (PowerShell)

```powershell
pwsh -ExecutionPolicy Bypass -File <path-to-skill>/scripts/take_screenshot.ps1 [flags]
```

Use stock `powershell.exe -ExecutionPolicy Bypass -File ...` if PowerShell 7 (`pwsh`) is not installed.

| Goal | Flags |
|---|---|
| Default location | *(no flags)* |
| Temp location | `-Mode temp` |
| Explicit path (POSIX or Windows `~`) | `-Path "C:\Temp\screen.png"` |
| Force a single stitched virtual-desktop image | `-Mode temp -VirtualDesktop` |
| Pixel region | `-Region "x,y,w,h"` |
| Active/focused window | `-ActiveWindow` |
| Specific window handle | `-WindowHandle 123456` |

By default a multi-monitor capture writes one file per display (`-d1`, `-d2`, …) so mixed-DPI offsets stay correct.

## Direct OS commands (last-resort fallback)

When the helpers cannot run (sandbox, missing Python/PowerShell), fall back to:

- macOS full screen: `screencapture -x output/screen.png`
- macOS region: `screencapture -x -R<x>,<y>,<w>,<h> output/region.png`
- macOS window id: `screencapture -x -l<id> output/window.png`
- Linux: `scrot file.png` / `gnome-screenshot -f file.png` / `import -window root file.png` (use `-a x,y,w,h`, `-u`, `-w` for region/active variants)

## Error handling

- macOS sandbox / permission errors (`screen capture checks are blocked`, `could not create image from display`, Swift `ModuleCache` permission errors): rerun with escalated permissions, or run the preflight script.
- macOS `--app` or `--window-name` returns no matches: rerun with `--list-windows --app "<App>"` to inspect ids, then `--window-id <id>`. Make sure the window is on screen and not minimised.
- Linux region/window capture fails: check `command -v scrot`, `command -v gnome-screenshot`, `command -v import`.
- Windows `-ActiveWindow` or `-WindowHandle` fails: confirm the window is visible and not minimised.
- Windows multi-monitor offset issues: drop `-VirtualDesktop` to fall back to per-display files.
- Saving to the OS default location fails (sandbox): rerun with escalated permissions.
- Always print the saved file path in the response.

## Examples

**Capture the full desktop**
```
User: "Take a screenshot of my desktop."
Agent: Run the platform helper with no flags, save to the OS default location, report each saved path (one per display on macOS/Windows).
```

**Inspect a specific app**
```
User: "Take a look at Codex and tell me what you see."
Agent: macOS preflight + take_screenshot.py --app "Codex" --mode temp, then view each printed path in order.
```

**Compare a Figma design with the running app**
```
User: "The design from Figma is not matching what is implemented."
Agent: Use the Figma MCP/skill to capture the design first, then this skill in temp mode for the running app, and compare the raw screenshots before any manipulation.
```

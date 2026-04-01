---
name: image-to-terminal-pixel-art
description: Use when Codex needs to turn a local image or a fresh screenshot into terminal-friendly pixel art, especially for CLI previews, text-only visual reviews, quick image diffs, or sharing image content without opening a GUI viewer.
---

# Image To Terminal Pixel Art

## Overview

Render an image as terminal pixel art with either ANSI truecolor half blocks or a grayscale text fallback. Prefer the bundled PowerShell renderer on Windows because it works with `System.Drawing` and does not require `chafa`, ImageMagick, or Python image packages.

## Quick Start

Render an existing image:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File <path-to-skill>\scripts\render_image_as_pixel_art.ps1 -Path .\image.png -Columns 80
```

Fall back to grayscale when ANSI color would be noisy or stripped:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File <path-to-skill>\scripts\render_image_as_pixel_art.ps1 -Path .\image.png -Columns 80 -ColorMode none
```

## Workflow

1. Start from a concrete image path.
2. Default to `-ColorMode truecolor` for interactive terminal previews.
3. Use `-ColorMode none` when the output will be copied into logs, Markdown, or terminals that strip ANSI escape sequences.
4. Keep `-Columns` in the `40-100` range unless the user explicitly wants a very wide render.
5. Leave `-AllowUpscale` off unless the user asks for a bigger preview than the source image can naturally support.

## Reuse Existing Tools

When the user wants a live desktop or app snapshot rendered in the terminal, reuse the repo-local `screenshot` skill or its PowerShell helper first, then pass the saved file into this renderer.

Example flow:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File <repo-root>\screenshot\scripts\take_screenshot.ps1 -Mode temp -ActiveWindow
powershell -NoProfile -ExecutionPolicy Bypass -File <path-to-skill>\scripts\render_image_as_pixel_art.ps1 -Path <captured-file> -Columns 80
```

## Scripts

- `scripts/render_image_as_pixel_art.ps1`: CLI entrypoint that prints the rendered rows.
- `scripts/lib/pixel_art_renderer.ps1`: reusable rendering helpers for tests and future wrappers.

## Guardrails

- Treat this as a preview tool, not an image editor.
- The main implementation path is Windows-first. It depends on PowerShell plus `System.Drawing`.
- Transparent pixels are blended over the requested `-Background` color before rendering.
- If the terminal wraps lines, rerun with a smaller `-Columns` value instead of trusting the wrapped output.
- Read `references/rendering.md` when you need renderer details, terminal compatibility notes, or validation commands.

---
name: image-to-terminal-pixel-art
description: |
  Turn images and screenshots into terminal-friendly pixel art using ANSI truecolor half blocks or a clean grayscale fallback.
  Make sure to use this skill whenever the user wants to preview an image in the terminal, compare screenshots as text,
  render a photo without opening a GUI viewer, or share visual content in a text-only environment.
  Also trigger when the user says "show me this image", "what does this look like", "can you display this picture",
  "terminal image preview", "pixel art conversion", "render screenshot in CLI", or "quick image diff".
  Covers Windows PowerShell + System.Drawing as the primary path, with chafa/timg fallbacks on other platforms.
---

# Image to Terminal Pixel Art

## Overview

Turn any local image or screenshot into pixel art that renders right inside the terminal. The bundled PowerShell renderer produces sharp ANSI truecolor output using half-block characters — two image rows packed into one text row — with an automatic grayscale fallback for environments that strip color codes.

On Windows, this is the preferred path because it relies on `System.Drawing` (built into .NET) and avoids extra dependencies like `chafa`, ImageMagick, or Python image packages.

## Adaptive Detection

Before rendering, detect the environment and image characteristics:

1. **Platform**: Windows (PowerShell + System.Drawing) vs macOS/Linux (suggest `chafa` or `timg` fallback).
2. **Output destination**: interactive terminal preview (`-ColorMode truecolor`) vs logs/Markdown/copy-paste (`-ColorMode none`).
3. **Terminal width**: choose `-Columns` between 40 and 100 to avoid line wrapping distortion.
4. **Transparency**: check if the image has transparent pixels and set `-Background` to match the intended backdrop.
5. **Image size**: enable `-AllowUpscale` only if the user wants a larger preview than the source supports.

## Quick Start

Preview an existing image in color:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File <path-to-skill>\scripts\render_image_as_pixel_art.ps1 -Path .\image.png -Columns 80
```

Switch to grayscale when the output will be copied into logs, Markdown, or terminals that strip ANSI codes:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File <path-to-skill>\scripts\render_image_as_pixel_art.ps1 -Path .\image.png -Columns 80 -ColorMode none
```

## Examples

**Preview a screenshot in the terminal:**
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File <path-to-skill>\scripts\render_image_as_pixel_art.ps1 -Path .\screenshot.png -Columns 80 -ColorMode truecolor
```

**Render for a GitHub issue comment (no ANSI):**
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File <path-to-skill>\scripts\render_image_as_pixel_art.ps1 -Path .\diagram.png -Columns 60 -ColorMode none
```

## Workflow

1. **Start with a concrete image path.** If the user refers to a screenshot they just took, capture it first (see below) and then pass the saved file to the renderer.
2. **Default to `-ColorMode truecolor`** for interactive terminal previews — the colors are accurate and the half-block packing gives good vertical resolution.
3. **Switch to `-ColorMode none`** when the output is headed for logs, issue comments, copy-paste, or any terminal that might strip escape sequences.
4. **Keep `-Columns` between 40 and 100** unless the user explicitly asks for a very wide render. Narrower previews are usually more readable in split terminals or dense CLI sessions.
5. **Leave `-AllowUpscale` off** unless the user wants a bigger preview than the source image can naturally support. Upscaling soft edges slightly; the default downscale path is sharper.

## Pairing with Screenshot Capture

When the user wants a live desktop or app snapshot rendered in the terminal, reuse the repo-local `screenshot` skill first, then feed the captured file into this renderer.

Example flow:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File <repo-root>\screenshot\scripts\take_screenshot.ps1 -Mode temp -ActiveWindow
powershell -NoProfile -ExecutionPolicy Bypass -File <path-to-skill>\scripts\render_image_as_pixel_art.ps1 -Path <captured-file> -Columns 80
```

This keeps capture and rendering separate, which makes debugging easier when one half of the pipeline fails.

## Scripts

- `scripts/render_image_as_pixel_art.ps1` — CLI entrypoint that prints rendered rows to stdout.
- `scripts/lib/pixel_art_renderer.ps1` — Reusable rendering helpers for tests and future wrappers.

## Guardrails

- Treat this as a preview tool, not an image editor. It reads images; it never modifies them.
- The primary implementation path is Windows-first (PowerShell + `System.Drawing`). On other platforms, suggest installing `chafa` or `timg` as a fallback.
- Transparent pixels are blended over the configured `-Background` color before rendering. The default background is black (`#000000`); change it when the source image has transparency against a different backdrop.
- If the terminal wraps lines, the output will look jagged. Rerun with a smaller `-Columns` value rather than trusting wrapped output.
- For side-by-side image comparison, render each image separately with the same `-Columns` value, then align the output blocks manually or pipe through a diff tool.
- Read `references/rendering.md` when you need renderer details, terminal compatibility notes, or validation commands.

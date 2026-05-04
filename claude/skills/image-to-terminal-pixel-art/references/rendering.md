# Rendering Notes

## Entrypoints

- `scripts/render_image_as_pixel_art.ps1`
- `scripts/lib/pixel_art_renderer.ps1`

## Rendering Model

- `truecolor` mode uses one `▀` character per output column.
- The top pixel is mapped to ANSI foreground color.
- The bottom pixel is mapped to ANSI background color.
- Image height is resized to an even number so every printed cell has a top and bottom pixel.

## Parameters

- `-Path`: source image file.
- `-Columns`: target output width in terminal cells. Default `80`.
- `-ColorMode truecolor|none`: choose ANSI color or grayscale text fallback.
- `-Background`: hex color used to blend transparency. Default `#000000`.
- `-AllowUpscale`: permit widening beyond the source image width.

## Terminal Compatibility

- Use Windows Terminal or another ANSI-capable terminal for `truecolor`.
- If copied output looks polluted with escape sequences, rerun with `-ColorMode none`.
- If the preview looks stretched, adjust `-Columns` first. The renderer already packs two image rows into one text row.

## Reusing Screenshot Capture

To preview the current desktop or a focused app in the terminal:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File <repo-root>\screenshot\scripts\take_screenshot.ps1 -Mode temp -ActiveWindow
powershell -NoProfile -ExecutionPolicy Bypass -File <path-to-skill>\scripts\render_image_as_pixel_art.ps1 -Path <captured-file> -Columns 80
```

This keeps screenshot capture and terminal rendering separate, which makes debugging easier when one half of the workflow fails.

## Validation

Run the renderer tests:

```powershell
Invoke-Pester image-to-terminal-pixel-art\tests\render_image_as_pixel_art.Tests.ps1
```

Run the skill validator:

```powershell
python _tmp_claude_code_templates\cli-tool\components\skills\productivity\skill-creator\scripts\quick_validate.py image-to-terminal-pixel-art
```

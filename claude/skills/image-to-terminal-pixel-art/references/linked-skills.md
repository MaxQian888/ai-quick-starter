# Linked Skills

Use this file when the image to render was just captured from the screen rather than loaded from an existing file.

## `$screenshot`

Use when:
- the user refers to a screenshot they just took or want to take,
- the image path does not yet exist and needs to be captured first,
- a live desktop or app snapshot is needed for terminal preview.

## Routing Rules

- If the user says "show me my screen" or "what does this window look like", use `$screenshot` first to capture, then pass the saved file to this renderer.
- If the image path already exists, skip `$screenshot` and render directly.
- On Windows, prefer the PowerShell screenshot helper; on macOS/Linux, use the Python helper.

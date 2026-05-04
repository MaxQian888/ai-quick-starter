# Linked Skills

Use this file when a captured screenshot needs to be previewed, compared, or shared in a terminal session.

## `$image-to-terminal-pixel-art`

Use when:
- the user wants to preview a captured screenshot directly in the terminal,
- the screenshot needs to be rendered as ASCII/grayscale or ANSI truecolor pixel art,
- a quick visual check is needed without opening a GUI image viewer.

## Routing Rules

- After capturing a screenshot, route to `$image-to-terminal-pixel-art` when the user wants inline terminal preview.
- On non-Windows platforms, suggest `chafa` or `timg` as a fallback if the pixel art renderer is unavailable.
- Keep capture and rendering separate so pipeline failures are easier to debug.

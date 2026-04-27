# Tests

This directory contains test cases for the pptx-generator skill.

## Test Cases

1. **Deck generation from scratch** — Verify compile.js produces a valid .pptx with all slide modules.
2. **MarkItDown extraction** — Confirm placeholder detection catches leftover `xxxx` or `lorem ipsum` text.
3. **Theme contract compliance** — Ensure all slides use the mandatory theme keys (`primary`, `secondary`, `accent`, `light`, `bg`).

Add tests here as the skill evolves.

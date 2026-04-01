# PDF Reading Playbook

## Goal

Use the smallest reliable path that lets the current agent understand a PDF without pretending that one backend solves every PDF.

## Decision Order

1. Run `probe`.
2. Run `inspect`.
3. Run `text` on a small page range first when the file should be text-readable.
4. Switch to `render` when the first extraction is empty, fragmented, or obviously scan-derived.

## Heuristics

### Prefer `text` first when

- the PDF came from a word processor, browser export, slide tool, or reporting system
- copy-paste from the viewer works
- metadata looks normal and file size is moderate for the page count

### Prefer `render` first when

- the file was scanned from paper
- each page looks like a single image layer
- the first extracted page contains only whitespace or random glyphs
- the next step needs visual reasoning, layout checking, or OCR from another tool

## Suggested Session Patterns

### Quick inspection

```bash
python scripts/read_pdf.py inspect ./doc.pdf --json
```

Use this when you need page count, metadata, or bookmarks before choosing the next step.

### Targeted text read

```bash
python scripts/read_pdf.py text ./doc.pdf --pages 1-2 --max-chars 6000
```

Use this when you want a low-cost sample before extracting a larger span.

### Image handoff

```bash
python scripts/read_pdf.py render ./scan.pdf --pages 1-3 --output-dir ./artifacts/scan-pages
```

Use this when another tool will inspect the saved images.

## Output Notes

- `combined_text` is meant for fast downstream consumption.
- `pages[*].text` is meant for page-aware review and targeted summarization.
- Rendered files use one file per page so later steps can inspect only the needed pages.

## Common Failure Modes

### Empty extracted text

Cause: scanned or image-only PDF.

Response: switch to `render`.

### Good metadata, bad text

Cause: embedded fonts or unusual encoding.

Response: try the same command with the preferred backend from `probe`; if that still fails, switch to `render`.

### Huge PDF

Cause: reading everything at once is expensive.

Response: inspect first, then extract or render only the target page range.

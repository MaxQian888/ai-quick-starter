---
name: pdf-reading-workflow
description: >
  Use this skill whenever you need to read, inspect, extract, or analyze content from a PDF file.
  Make sure to use it when the user asks you to look at a document, report, scan, or any PDF-based file — even if they just say "look at this file" and it happens to be a PDF.
  Covers born-digital text extraction, metadata and bookmark inspection, rendering scanned pages to images, and backend probing across Windows, macOS, and Linux.
  Also trigger for PDF-to-text conversion, page rendering for OCR, and document summarization tasks.
---

# PDF Reading Workflow

The bundled scripts are your default surface for working with PDFs. Start by inspecting
what kind of file you have, then extract text if it looks machine-readable, and fall
back to rendering pages as images when the PDF is scanned or text extraction is clearly
weak.

## Adaptive Detection

Before processing a PDF, scan for:
- Operating system (Windows, macOS, Linux) to choose the right wrapper script
- Available Python environment (uv, venv, system python3) for direct CLI use
- Installed backends via `probe` (pymupdf, pypdf, pdfinfo, pdftotext, pdftoppm)
- File size and page count to decide between text and render strategies
- Whether the PDF is born-digital or scanned based on `inspect` metadata

## Preferred Workflow

1. **Run `probe`** to see which backend is available on this machine.
2. **Run `inspect`** to check page count, metadata, and outline structure before
diving in.
3. **Run `text`** for born-digital PDFs that should be readable.
4. **Run `render`** when `text` comes back empty, garbled, or obviously incomplete.
5. **After rendering**, hand the page images to whatever image-capable tool works
best in the current environment.

## Preferred Entrypoints

Use the platform wrapper whenever you can:

**Windows (PowerShell):**
```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/read_pdf.ps1 probe --json
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/read_pdf.ps1 inspect .\report.pdf --json
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/read_pdf.ps1 text .\report.pdf --pages 1-3 --output .\artifacts\report.txt
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/read_pdf.ps1 render .\scan.pdf --pages 2-4 --output-dir .\artifacts\scan-pages
```

**macOS / Linux (bash):**
```bash
bash scripts/read_pdf.sh probe --json
bash scripts/read_pdf.sh inspect ./report.pdf --json
bash scripts/read_pdf.sh text ./report.pdf --pages 1-3 --output ./artifacts/report.txt
bash scripts/read_pdf.sh render ./scan.pdf --pages 2-4 --output-dir ./artifacts/scan-pages
```

If another workflow is already managing the Python interpreter, call the CLI directly:

```bash
python scripts/read_pdf.py probe --json
python scripts/read_pdf.py inspect ./report.pdf --json
python scripts/read_pdf.py text ./report.pdf --pages 1-3 --max-chars 6000
python scripts/read_pdf.py render ./scan.pdf --pages 2-4 --dpi 144 --output-dir ./artifacts/scan-pages
```

## Command Selection

### `probe`

Run this first when you are unsure what the environment supports. It reports which
backends are installed and which one is preferred for `inspect`, `text`, and `render`.

### `inspect`

Use this when the user asks things like:

- "Read this PDF and tell me what it contains."
- "Does this PDF have bookmarks or a table of contents?"
- "How many pages is this?"

This step is cheap and usually tells you whether the PDF is text-first or scan-first.

### `text`

Use this when the PDF is likely born-digital or when the first extracted pages look
sane.

Handy options:

- `--pages 1-3,7`
- `--max-chars 8000`
- `--output artifacts/doc.txt`
- `--json`

### `render`

Switch to this when:

- extracted text is empty or clearly wrong
- the layout is so broken it undermines understanding
- the PDF is obviously a scan
- the next step in your workflow works better from images than from raw text

Handy options:

- `--pages 2-5`
- `--dpi 144`
- `--format png`
- `--output-dir artifacts/doc-pages`
- `--prefix appendix`

## Backend Rules

- Prefer `pymupdf` for `inspect`, `text`, and `render` when it is available.
- Fall back to `pypdf` for `inspect` and `text`.
- Fall back to Poppler CLI tools for the narrower jobs they cover:
  - `pdfinfo` for `inspect`
  - `pdftotext` for `text`
  - `pdftoppm` for `render`
- OCR is out of scope for this skill's first pass. Render the pages and hand them to
  an OCR- or vision-capable tool when you need it.

## Output Contract

- `probe --json` returns the backend inventory plus the preferred backend for each
capability.
- `inspect --json` returns `page_count`, `metadata`, `toc`, and `backend`.
- `text --json` returns per-page text plus a `combined_text` field.
- `render --json` returns the saved image paths along with rendering settings.
- Non-JSON text mode prints extracted text to stdout unless `--output` is given.
- Non-JSON render mode prints one saved path per line.

## Guardrails

- Do not assume a PDF is text-readable just because it opens in a browser.
- Do not keep retrying text extraction after the first clearly empty or junk result.
  Switch to `render` instead.
- Do not claim OCR happened unless another tool actually performed it.
- Do not promise page-perfect layout reconstruction from `text`; preserve layout only
  when the backend already provides it.
- Keep output paths explicit when another tool or agent step will consume them.

## References

- Read `references/reading-playbook.md` for the decision rules that guide choosing
  between `inspect`, `text`, and `render`.
- Read `references/environment-matrix.md` for wrapper behavior, dependency strategy,
  and direct CLI fallbacks.

## Examples

**Example 1: Extract text from a born-digital report**
```
User: "Read this annual report PDF and summarize the key findings."
Agent: Run `probe --json`, then `inspect ./report.pdf --json`, then `text ./report.pdf --pages 1-10 --max-chars 8000`, and summarize the extracted content.
```

**Example 2: Handle a scanned document**
```
User: "What's in this scan.pdf? It seems to be an old contract."
Agent: Run `inspect ./scan.pdf --json`, attempt `text` first, switch to `render ./scan.pdf --pages 1-5 --dpi 144 --output-dir ./artifacts/scan-pages` when text is empty, then hand images to a vision-capable tool.
```

---
name: pdf-reading-workflow
description: Use when Codex needs to inspect or read a PDF file, extract text from born-digital PDFs, check metadata or outline structure, or render pages to images for scanned or image-only PDFs across Windows, macOS, Linux, uv, Python, or common Poppler CLI environments.
---

# PDF Reading Workflow

Use the bundled scripts as the default reading surface. Inspect the PDF first, try text extraction second, and switch to page rendering when the file is scanned, image-only, or text extraction is obviously weak.

## Preferred Workflow

1. Run `probe` to see which backend the current machine can actually use.
2. Run `inspect` to confirm page count, metadata, and outline availability before reading deeply.
3. Run `text` for born-digital PDFs.
4. Run `render` when `text` is empty, garbled, or visibly incomplete.
5. After rendering, hand the page images to the best image-capable tool in the current environment.

## Preferred Entrypoints

Use the platform wrapper when possible:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/read_pdf.ps1 probe --json
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/read_pdf.ps1 inspect .\report.pdf --json
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/read_pdf.ps1 text .\report.pdf --pages 1-3 --output .\artifacts\report.txt
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/read_pdf.ps1 render .\scan.pdf --pages 2-4 --output-dir .\artifacts\scan-pages
```

```bash
bash scripts/read_pdf.sh probe --json
bash scripts/read_pdf.sh inspect ./report.pdf --json
bash scripts/read_pdf.sh text ./report.pdf --pages 1-3 --output ./artifacts/report.txt
bash scripts/read_pdf.sh render ./scan.pdf --pages 2-4 --output-dir ./artifacts/scan-pages
```

Use the Python CLI directly when another workflow already controls the interpreter:

```bash
python scripts/read_pdf.py probe --json
python scripts/read_pdf.py inspect ./report.pdf --json
python scripts/read_pdf.py text ./report.pdf --pages 1-3 --max-chars 6000
python scripts/read_pdf.py render ./scan.pdf --pages 2-4 --dpi 144 --output-dir ./artifacts/scan-pages
```

## Command Selection

### `probe`

Run this first when the environment is unclear. It reports available backends and the preferred backend for `inspect`, `text`, and `render`.

### `inspect`

Use this when the user asks:

- "Read this PDF and tell me what it contains."
- "Check whether this PDF has bookmarks or a table of contents."
- "How many pages are in this file?"

This step is cheap and often tells you whether the PDF is text-first or scan-first.

### `text`

Use this when the PDF is likely born-digital or when the first extracted pages look sane.

Useful options:

- `--pages 1-3,7`
- `--max-chars 8000`
- `--output artifacts/doc.txt`
- `--json`

### `render`

Use this when:

- extracted text is empty
- extracted text loses layout badly enough to matter
- the PDF is obviously scanned
- the next tool in the workflow works better from images than raw text

Useful options:

- `--pages 2-5`
- `--dpi 144`
- `--format png`
- `--output-dir artifacts/doc-pages`
- `--prefix appendix`

## Backend Rules

- Prefer `pymupdf` for `inspect`, `text`, and `render` when available.
- Fall back to `pypdf` for `inspect` and `text`.
- Fall back to Poppler CLI tools for the narrow task they support:
  - `pdfinfo` for `inspect`
  - `pdftotext` for `text`
  - `pdftoppm` for `render`
- Treat OCR as out of scope for this skill's first pass. Render pages and hand them to an OCR- or vision-capable tool when needed.

## Output Contract

- `probe --json` returns backend inventory plus preferred backend by capability.
- `inspect --json` returns `page_count`, `metadata`, `toc`, and `backend`.
- `text --json` returns per-page text plus `combined_text`.
- `render --json` returns saved image paths plus rendering settings.
- Non-JSON text mode prints extracted text to stdout unless `--output` is given.
- Non-JSON render mode prints one saved path per line.

## Guardrails

- Do not assume a PDF is text-readable just because it opens in a browser.
- Do not keep retrying text extraction after the first clearly empty or junk result. Switch to `render`.
- Do not claim OCR happened unless another tool actually performed OCR.
- Do not promise page-perfect layout reconstruction from `text`; preserve it only when the backend already provides it.
- Keep output paths explicit when you expect another tool or agent step to consume them.

## References

- Read `references/reading-playbook.md` for the decision rules between `inspect`, `text`, and `render`.
- Read `references/environment-matrix.md` for wrapper behavior, dependency strategy, and direct CLI fallbacks.

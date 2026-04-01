# Environment Matrix

## Wrapper Strategy

The skill ships three execution surfaces:

- `scripts/read_pdf.ps1` for PowerShell-centric environments
- `scripts/read_pdf.sh` for macOS and Linux shells
- `scripts/read_pdf.py` as the common implementation layer

The wrappers prefer:

1. `uv run --with pymupdf --with pypdf ...`
2. local `python3` or `python`
3. a helpful error message pointing to direct CLI fallbacks

## Capability Matrix

| Backend | Inspect | Text | Render | Notes |
| --- | --- | --- | --- | --- |
| `pymupdf` | yes | yes | yes | best default when available |
| `pypdf` | yes | yes | no | good fallback for born-digital PDFs |
| `pdfinfo` | yes | no | no | Poppler metadata path |
| `pdftotext` | no | yes | no | Poppler text path |
| `pdftoppm` | no | no | yes | Poppler render path |

## Direct CLI Fallbacks

Use these when Python and `uv` are both unavailable.

### Inspect

```bash
pdfinfo ./doc.pdf
```

### Extract text

```bash
pdftotext -layout ./doc.pdf -
```

### Render pages

```bash
pdftoppm -png -f 1 -l 3 ./doc.pdf ./artifacts/doc-page
```

## Windows Notes

- Prefer `pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/read_pdf.ps1 ...`.
- If PowerShell profiles are noisy, `-NoProfile` avoids unrelated console errors.
- When `uv` is present, the wrapper can bootstrap `pymupdf` and `pypdf` without editing the local Python environment.

## macOS And Linux Notes

- Prefer `bash scripts/read_pdf.sh ...`.
- The shell wrapper works with either `uv`, `python3`, or `python`.
- Poppler utilities often come from system packages; the Python CLI will use them automatically when present.

## What This Skill Does Not Solve

- OCR
- password-protected PDF unlocking
- PDF editing, merging, form filling, or annotation workflows

Use another tool or a follow-on skill for those jobs.

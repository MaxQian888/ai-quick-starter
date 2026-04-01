#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/read_pdf.py"

if command -v uv >/dev/null 2>&1; then
  exec uv run --quiet --with pymupdf --with pypdf python "$PYTHON_SCRIPT" "$@"
fi

if command -v python3 >/dev/null 2>&1; then
  exec python3 "$PYTHON_SCRIPT" "$@"
fi

if command -v python >/dev/null 2>&1; then
  exec python "$PYTHON_SCRIPT" "$@"
fi

cat >&2 <<'EOF'
No Python runner was found for read_pdf.sh.

Try one of these direct commands instead:
  inspect: pdfinfo <file.pdf>
  text:    pdftotext -layout <file.pdf> -
  render:  pdftoppm -png <file.pdf> <output-prefix>
EOF
exit 1

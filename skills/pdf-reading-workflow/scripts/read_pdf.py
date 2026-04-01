#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


CAPABILITY_PREFERENCE = {
    "inspect": ["pymupdf", "pypdf", "pdfinfo"],
    "text": ["pymupdf", "pypdf", "pdftotext"],
    "render": ["pymupdf", "pdftoppm"],
}


class PdfWorkflowError(RuntimeError):
    pass


@dataclass
class CommandResult:
    stdout: str
    stderr: str
    returncode: int


@dataclass
class BackendSummary:
    name: str
    source: str
    capabilities: tuple[str, ...]
    detail: str


def parse_page_spec(page_spec: str | None, page_count: int | None = None) -> list[int] | None:
    if page_spec is None:
        return None

    pages: set[int] = set()
    for chunk in page_spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            start_text, end_text = chunk.split("-", 1)
            try:
                start = int(start_text)
                end = int(end_text)
            except ValueError as exc:
                raise ValueError(f"Invalid page range '{chunk}'") from exc
            if start <= 0 or end <= 0:
                raise ValueError("Page numbers must be positive")
            if end < start:
                raise ValueError(f"Descending page range '{chunk}' is not allowed")
            pages.update(range(start, end + 1))
        else:
            try:
                page = int(chunk)
            except ValueError as exc:
                raise ValueError(f"Invalid page value '{chunk}'") from exc
            if page <= 0:
                raise ValueError("Page numbers must be positive")
            pages.add(page)

    ordered = sorted(pages)
    if page_count is not None and ordered and ordered[-1] > page_count:
        raise ValueError(f"Requested page {ordered[-1]} exceeds page count {page_count}")
    return ordered


def resolve_pages(page_spec: str | None, page_count: int) -> list[int]:
    pages = parse_page_spec(page_spec, page_count)
    if pages is None:
        return list(range(1, page_count + 1))
    return pages


def truncate_text(text: str, max_chars: int | None) -> str:
    if max_chars is None or max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n...[truncated]"


def run_command(command: list[str]) -> CommandResult:
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    return CommandResult(
        stdout=completed.stdout,
        stderr=completed.stderr,
        returncode=completed.returncode,
    )


def parse_pdfinfo_output(stdout: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for raw_line in stdout.splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        metadata[key.strip()] = value.strip()
    return metadata


def normalize_metadata(raw: dict[str, object]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for key, value in raw.items():
        if value is None:
            continue
        text = str(value).strip()
        if text:
            normalized[str(key)] = text
    return normalized


def import_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def command_available(command_name: str) -> bool:
    return shutil.which(command_name) is not None


def summarize_backends() -> list[BackendSummary]:
    backends: list[BackendSummary] = []

    if import_available("fitz"):
        backends.append(
            BackendSummary(
                name="pymupdf",
                source="python",
                capabilities=("inspect", "text", "render"),
                detail="PyMuPDF via fitz",
            )
        )
    if import_available("pypdf"):
        backends.append(
            BackendSummary(
                name="pypdf",
                source="python",
                capabilities=("inspect", "text"),
                detail="pypdf",
            )
        )
    if command_available("pdfinfo"):
        backends.append(
            BackendSummary(
                name="pdfinfo",
                source="cli",
                capabilities=("inspect",),
                detail="Poppler metadata command",
            )
        )
    if command_available("pdftotext"):
        backends.append(
            BackendSummary(
                name="pdftotext",
                source="cli",
                capabilities=("text",),
                detail="Poppler text extraction command",
            )
        )
    if command_available("pdftoppm"):
        backends.append(
            BackendSummary(
                name="pdftoppm",
                source="cli",
                capabilities=("render",),
                detail="Poppler page rendering command",
            )
        )

    return backends


def select_backend(capability: str, backends: Iterable[BackendSummary]) -> BackendSummary:
    available = list(backends)
    names = {backend.name: backend for backend in available}
    for preferred in CAPABILITY_PREFERENCE[capability]:
        backend = names.get(preferred)
        if backend and capability in backend.capabilities:
            return backend
    raise PdfWorkflowError(
        f"No backend can handle '{capability}'. "
        "Try running the platform wrapper with uv, or install a suitable PDF backend."
    )


def flatten_pypdf_outline(reader: object, outline: list[object], level: int = 1) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for item in outline:
        if isinstance(item, list):
            entries.extend(flatten_pypdf_outline(reader, item, level + 1))
            continue
        title = getattr(item, "title", None)
        if not title:
            continue
        try:
            page = reader.get_destination_page_number(item) + 1
        except Exception:
            page = None
        entries.append({"level": level, "title": title, "page": page})
    return entries


def inspect_with_pymupdf(pdf_path: Path) -> dict[str, object]:
    import fitz

    with fitz.open(pdf_path) as doc:
        toc = [
            {"level": level, "title": title, "page": page}
            for level, title, page in doc.get_toc(simple=True)
        ]
        return {
            "backend": "pymupdf",
            "page_count": doc.page_count,
            "metadata": normalize_metadata(doc.metadata),
            "toc": toc,
        }


def text_with_pymupdf(pdf_path: Path, page_spec: str | None, max_chars: int | None) -> dict[str, object]:
    import fitz

    with fitz.open(pdf_path) as doc:
        pages = resolve_pages(page_spec, doc.page_count)
        page_records: list[dict[str, object]] = []
        combined_parts: list[str] = []
        for page_number in pages:
            text = doc.load_page(page_number - 1).get_text("text").strip()
            page_records.append({"page": page_number, "chars": len(text), "text": text})
            combined_parts.append(text)
        combined_text = "\n\n".join(part for part in combined_parts if part)
        return {
            "backend": "pymupdf",
            "page_count": doc.page_count,
            "pages": page_records,
            "combined_text": truncate_text(combined_text, max_chars),
        }


def render_with_pymupdf(
    pdf_path: Path,
    page_spec: str | None,
    output_dir: Path,
    image_format: str,
    dpi: int,
    prefix: str,
) -> dict[str, object]:
    import fitz

    output_dir.mkdir(parents=True, exist_ok=True)

    with fitz.open(pdf_path) as doc:
        pages = resolve_pages(page_spec, doc.page_count)
        written: list[str] = []
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        for page_number in pages:
            page = doc.load_page(page_number - 1)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            destination = output_dir / f"{prefix}-p{page_number:04d}.{image_format}"
            pixmap.save(destination)
            written.append(str(destination))
        return {
            "backend": "pymupdf",
            "page_count": doc.page_count,
            "pages": pages,
            "dpi": dpi,
            "format": image_format,
            "files": written,
        }


def inspect_with_pypdf(pdf_path: Path) -> dict[str, object]:
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    metadata = normalize_metadata(dict(reader.metadata or {}))
    toc: list[dict[str, object]] = []
    try:
        outline = reader.outline
        if isinstance(outline, list):
            toc = flatten_pypdf_outline(reader, outline)
    except Exception:
        toc = []
    return {
        "backend": "pypdf",
        "page_count": len(reader.pages),
        "metadata": metadata,
        "toc": toc,
    }


def text_with_pypdf(pdf_path: Path, page_spec: str | None, max_chars: int | None) -> dict[str, object]:
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    pages = resolve_pages(page_spec, len(reader.pages))
    page_records: list[dict[str, object]] = []
    combined_parts: list[str] = []
    for page_number in pages:
        text = (reader.pages[page_number - 1].extract_text() or "").strip()
        page_records.append({"page": page_number, "chars": len(text), "text": text})
        combined_parts.append(text)
    combined_text = "\n\n".join(part for part in combined_parts if part)
    return {
        "backend": "pypdf",
        "page_count": len(reader.pages),
        "pages": page_records,
        "combined_text": truncate_text(combined_text, max_chars),
    }


def inspect_with_pdfinfo(pdf_path: Path) -> dict[str, object]:
    result = run_command(["pdfinfo", str(pdf_path)])
    if result.returncode != 0:
        raise PdfWorkflowError(result.stderr.strip() or "pdfinfo failed")
    metadata = parse_pdfinfo_output(result.stdout)
    page_count = int(metadata.get("Pages", "0") or 0)
    return {
        "backend": "pdfinfo",
        "page_count": page_count,
        "metadata": metadata,
        "toc": [],
    }


def text_with_pdftotext(pdf_path: Path, page_spec: str | None, max_chars: int | None) -> dict[str, object]:
    inspect_payload = inspect_with_pdfinfo(pdf_path) if command_available("pdfinfo") else None
    page_count = int(inspect_payload["page_count"]) if inspect_payload else None
    pages = parse_page_spec(page_spec, page_count) if page_count is not None else parse_page_spec(page_spec)

    if not pages:
        command = ["pdftotext", "-layout", "-enc", "UTF-8", str(pdf_path), "-"]
        result = run_command(command)
        if result.returncode != 0:
            raise PdfWorkflowError(result.stderr.strip() or "pdftotext failed")
        text = result.stdout.strip()
        page_records = [{"page": None, "chars": len(text), "text": text}]
        combined_text = text
    else:
        page_records = []
        combined_parts: list[str] = []
        for page_number in pages:
            command = [
                "pdftotext",
                "-layout",
                "-enc",
                "UTF-8",
                "-f",
                str(page_number),
                "-l",
                str(page_number),
                str(pdf_path),
                "-",
            ]
            result = run_command(command)
            if result.returncode != 0:
                raise PdfWorkflowError(result.stderr.strip() or f"pdftotext failed on page {page_number}")
            text = result.stdout.strip()
            page_records.append({"page": page_number, "chars": len(text), "text": text})
            combined_parts.append(text)
        combined_text = "\n\n".join(part for part in combined_parts if part)

    return {
        "backend": "pdftotext",
        "page_count": page_count,
        "pages": page_records,
        "combined_text": truncate_text(combined_text, max_chars),
    }


def render_with_pdftoppm(
    pdf_path: Path,
    page_spec: str | None,
    output_dir: Path,
    image_format: str,
    dpi: int,
    prefix: str,
) -> dict[str, object]:
    inspect_payload = inspect_with_pdfinfo(pdf_path) if command_available("pdfinfo") else None
    page_count = int(inspect_payload["page_count"]) if inspect_payload else None
    pages = parse_page_spec(page_spec, page_count) if page_count is not None else parse_page_spec(page_spec)

    if not pages:
        if page_count is None:
            raise PdfWorkflowError("pdftoppm rendering needs either pdfinfo or an explicit page range")
        pages = list(range(1, page_count + 1))

    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    format_flag = "-png" if image_format == "png" else "-jpeg"

    for page_number in pages:
        base = output_dir / f"{prefix}-p{page_number:04d}"
        command = [
            "pdftoppm",
            format_flag,
            "-singlefile",
            "-r",
            str(dpi),
            "-f",
            str(page_number),
            "-l",
            str(page_number),
            str(pdf_path),
            str(base),
        ]
        result = run_command(command)
        if result.returncode != 0:
            raise PdfWorkflowError(result.stderr.strip() or f"pdftoppm failed on page {page_number}")
        written.append(str(base.with_suffix(f".{image_format}")))

    return {
        "backend": "pdftoppm",
        "page_count": page_count,
        "pages": pages,
        "dpi": dpi,
        "format": image_format,
        "files": written,
    }


def inspect_pdf(pdf_path: Path, backends: list[BackendSummary]) -> dict[str, object]:
    backend = select_backend("inspect", backends)
    if backend.name == "pymupdf":
        return inspect_with_pymupdf(pdf_path)
    if backend.name == "pypdf":
        return inspect_with_pypdf(pdf_path)
    if backend.name == "pdfinfo":
        return inspect_with_pdfinfo(pdf_path)
    raise PdfWorkflowError(f"Unsupported inspect backend: {backend.name}")


def extract_text(
    pdf_path: Path,
    page_spec: str | None,
    max_chars: int | None,
    backends: list[BackendSummary],
) -> dict[str, object]:
    backend = select_backend("text", backends)
    if backend.name == "pymupdf":
        return text_with_pymupdf(pdf_path, page_spec, max_chars)
    if backend.name == "pypdf":
        return text_with_pypdf(pdf_path, page_spec, max_chars)
    if backend.name == "pdftotext":
        return text_with_pdftotext(pdf_path, page_spec, max_chars)
    raise PdfWorkflowError(f"Unsupported text backend: {backend.name}")


def render_pages(
    pdf_path: Path,
    page_spec: str | None,
    output_dir: Path,
    image_format: str,
    dpi: int,
    prefix: str,
    backends: list[BackendSummary],
) -> dict[str, object]:
    backend = select_backend("render", backends)
    if backend.name == "pymupdf":
        return render_with_pymupdf(pdf_path, page_spec, output_dir, image_format, dpi, prefix)
    if backend.name == "pdftoppm":
        return render_with_pdftoppm(pdf_path, page_spec, output_dir, image_format, dpi, prefix)
    raise PdfWorkflowError(f"Unsupported render backend: {backend.name}")


def build_probe_payload(backends: list[BackendSummary]) -> dict[str, object]:
    preferred: dict[str, str | None] = {}
    for capability in CAPABILITY_PREFERENCE:
        try:
            preferred[capability] = select_backend(capability, backends).name
        except PdfWorkflowError:
            preferred[capability] = None
    return {
        "backends": [
            {
                "name": backend.name,
                "source": backend.source,
                "capabilities": list(backend.capabilities),
                "detail": backend.detail,
            }
            for backend in backends
        ],
        "preferred_backend": preferred,
    }


def format_inspect(payload: dict[str, object]) -> str:
    lines = [
        f"Backend: {payload['backend']}",
        f"Pages: {payload['page_count']}",
    ]
    metadata = payload.get("metadata") or {}
    if metadata:
        lines.append("Metadata:")
        for key, value in metadata.items():
            lines.append(f"  {key}: {value}")
    toc = payload.get("toc") or []
    if toc:
        lines.append("Outline:")
        for entry in toc:
            page = entry.get("page")
            suffix = f" (p.{page})" if page else ""
            lines.append(f"  L{entry['level']}: {entry['title']}{suffix}")
    return "\n".join(lines)


def format_probe(payload: dict[str, object]) -> str:
    lines = ["Available backends:"]
    for backend in payload["backends"]:
        capability_list = ", ".join(backend["capabilities"])
        lines.append(f"  - {backend['name']} [{backend['source']}]: {capability_list}")
    lines.append("Preferred:")
    for capability, backend_name in payload["preferred_backend"].items():
        lines.append(f"  {capability}: {backend_name or 'none'}")
    return "\n".join(lines)


def write_output(text: str, output_path: Path | None) -> None:
    if output_path is None:
        sys.stdout.write(text)
        if text and not text.endswith("\n"):
            sys.stdout.write("\n")
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    print(output_path)


def ensure_pdf_path(path_text: str) -> Path:
    pdf_path = Path(path_text).expanduser().resolve()
    if not pdf_path.exists():
        raise PdfWorkflowError(f"PDF not found: {pdf_path}")
    if pdf_path.is_dir():
        raise PdfWorkflowError(f"Expected a file, got a directory: {pdf_path}")
    return pdf_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect, extract, and render PDF files.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    probe_parser = subparsers.add_parser("probe", help="List available backends.")
    probe_parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")

    inspect_parser = subparsers.add_parser("inspect", help="Read metadata and outline information.")
    inspect_parser.add_argument("pdf", help="Path to the PDF file.")
    inspect_parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    inspect_parser.add_argument("--output", help="Write the result to a file.")

    text_parser = subparsers.add_parser("text", help="Extract text from a PDF.")
    text_parser.add_argument("pdf", help="Path to the PDF file.")
    text_parser.add_argument("--pages", help="Page list such as 1-3,5.")
    text_parser.add_argument("--max-chars", type=int, default=None, help="Trim combined text to this many characters.")
    text_parser.add_argument("--json", action="store_true", help="Emit JSON instead of plain text.")
    text_parser.add_argument("--output", help="Write the result to a file.")

    render_parser = subparsers.add_parser("render", help="Render pages to image files.")
    render_parser.add_argument("pdf", help="Path to the PDF file.")
    render_parser.add_argument("--pages", help="Page list such as 1-3,5.")
    render_parser.add_argument("--output-dir", required=True, help="Directory where page images should be saved.")
    render_parser.add_argument("--format", choices=("png", "jpg"), default="png", help="Image format.")
    render_parser.add_argument("--dpi", type=int, default=144, help="Rendering resolution.")
    render_parser.add_argument("--prefix", default="page", help="Output filename prefix.")
    render_parser.add_argument("--json", action="store_true", help="Emit JSON instead of file paths.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        backends = summarize_backends()

        if args.command == "probe":
            payload = build_probe_payload(backends)
            if args.json:
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            else:
                print(format_probe(payload))
            return 0

        pdf_path = ensure_pdf_path(args.pdf)

        if args.command == "inspect":
            payload = inspect_pdf(pdf_path, backends)
            rendered = json.dumps(payload, ensure_ascii=False, indent=2) if args.json else format_inspect(payload)
            output_path = Path(args.output).expanduser().resolve() if args.output else None
            write_output(rendered, output_path)
            return 0

        if args.command == "text":
            payload = extract_text(pdf_path, args.pages, args.max_chars, backends)
            rendered = json.dumps(payload, ensure_ascii=False, indent=2) if args.json else payload["combined_text"]
            output_path = Path(args.output).expanduser().resolve() if args.output else None
            write_output(rendered, output_path)
            return 0

        if args.command == "render":
            output_dir = Path(args.output_dir).expanduser().resolve()
            payload = render_pages(
                pdf_path,
                args.pages,
                output_dir,
                args.format,
                args.dpi,
                args.prefix,
                backends,
            )
            if args.json:
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            else:
                for file_path in payload["files"]:
                    print(file_path)
            return 0

        raise PdfWorkflowError(f"Unknown command: {args.command}")
    except (PdfWorkflowError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

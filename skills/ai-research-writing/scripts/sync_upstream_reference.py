#!/usr/bin/env python3
"""Fetch the upstream README and cache a section index for local routing."""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_UPSTREAM_URL = "https://raw.githubusercontent.com/Leey21/awesome-ai-research-writing/main/README.md"
DEFAULT_README_PATH = SKILL_ROOT / "references" / "cache" / "upstream-awesome-ai-research-writing.md"
DEFAULT_INDEX_PATH = SKILL_ROOT / "references" / "cache" / "upstream-section-index.json"


def fetch_markdown(url: str) -> str:
    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8")


def extract_section_index(markdown: str) -> list[dict[str, object]]:
    sections: list[dict[str, object]] = []
    in_fence = False
    for line_number, raw_line in enumerate(markdown.splitlines(), start=1):
        stripped = raw_line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped.startswith("# "):
            sections.append({"level": 1, "title": stripped[2:].strip(), "line_number": line_number})
        elif stripped.startswith("## "):
            sections.append({"level": 2, "title": stripped[3:].strip(), "line_number": line_number})
    return sections


def write_outputs(
    markdown: str,
    readme_path: Path,
    index_path: Path,
    source_url: str = DEFAULT_UPSTREAM_URL,
) -> dict[str, object]:
    readme_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.parent.mkdir(parents=True, exist_ok=True)

    readme_path.write_text(markdown, encoding="utf-8")
    payload = {
        "source_url": source_url,
        "readme_path": str(readme_path),
        "sections": extract_section_index(markdown),
    }
    index_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch and cache the upstream awesome-ai-research-writing README.")
    parser.add_argument("--url", default=DEFAULT_UPSTREAM_URL, help="Raw README URL to fetch.")
    parser.add_argument("--output-readme", default=str(DEFAULT_README_PATH), help="Output path for the cached README.")
    parser.add_argument("--output-index", default=str(DEFAULT_INDEX_PATH), help="Output path for the extracted section index JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    markdown = fetch_markdown(args.url)
    payload = write_outputs(markdown, Path(args.output_readme), Path(args.output_index), args.url)
    print(f"README_OUT={args.output_readme}")
    print(f"INDEX_OUT={args.output_index}")
    print(f"SECTIONS={len(payload['sections'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

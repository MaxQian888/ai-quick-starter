#!/usr/bin/env python3
"""
Build a lightweight project inventory for AI-context initialization.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

SKIP_NAMES = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".next",
    ".turbo",
    ".cache",
    ".codex-uv-cache",
    ".uv-cache",
    ".uv-cache-codex",
    ".uv-cache-local",
    ".uv-python",
    "tmp",
    "_tmp_validate",
}

SKIP_PREFIXES = (".tmp",)


def should_skip_directory(name: str) -> bool:
    return name in SKIP_NAMES or any(name.startswith(prefix) for prefix in SKIP_PREFIXES)


def classify_directory(path: Path) -> str:
    if (path / "SKILL.md").exists():
        return "skill"
    if path.name == "docs":
        return "docs"
    if path.name.startswith("_tmp"):
        return "template-or-temp"
    if (path / "AGENTS.md").exists() or (path / "CLAUDE.md").exists():
        return "context-docs"
    return "directory"


def summarize_directory(path: Path) -> dict:
    children = list(path.iterdir())
    child_dirs = sorted(item.name for item in children if item.is_dir())
    child_files = sorted(item.name for item in children if item.is_file())
    return {
        "name": path.name,
        "path": str(path),
        "kind": classify_directory(path),
        "has_skill_md": (path / "SKILL.md").exists(),
        "has_agents_openai_yaml": (path / "agents" / "openai.yaml").exists(),
        "has_references": (path / "references").is_dir(),
        "has_scripts": (path / "scripts").is_dir(),
        "has_tests": (path / "tests").is_dir(),
        "has_assets": (path / "assets").is_dir(),
        "child_dir_count": len(child_dirs),
        "child_file_count": len(child_files),
        "sample_dirs": child_dirs[:8],
        "sample_files": child_files[:8],
    }


def build_report(root: Path, max_modules: int) -> dict:
    entries = sorted(root.iterdir(), key=lambda item: item.name.lower())
    top_level_dirs = [item for item in entries if item.is_dir()]
    top_level_files = [item for item in entries if item.is_file()]

    skipped = []
    scanned = []
    suggested_modules = []

    for directory in top_level_dirs:
        if should_skip_directory(directory.name):
            skipped.append({"name": directory.name, "reason": "generated, cache, or temp"})
            continue
        summary = summarize_directory(directory)
        scanned.append(summary)
        if summary["kind"] in {"docs", "skill", "context-docs"} or summary["has_tests"]:
            suggested_modules.append(summary)

    suggested_modules.sort(
        key=lambda item: (
            item["kind"] != "docs",
            not item["has_skill_md"],
            not item["has_tests"],
            item["name"].lower(),
        )
    )

    return {
        "root": str(root),
        "total_top_level_entries": len(entries),
        "total_top_level_directories": len(top_level_dirs),
        "total_top_level_files": len(top_level_files),
        "scanned_directories": scanned,
        "skipped_directories": skipped,
        "suggested_modules": suggested_modules[:max_modules],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan a repository for AI-context initialization.")
    parser.add_argument("--root", required=True, help="Repository root to scan")
    parser.add_argument("--json-out", help="Optional path to write the JSON report")
    parser.add_argument("--max-modules", type=int, default=12, help="Maximum suggested modules")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Repository root not found: {root}")

    report = build_report(root, max_modules=args.max_modules)
    payload = json.dumps(report, indent=2)

    if args.json_out:
        output_path = Path(args.json_out).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload, encoding="utf-8")
    else:
        print(payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

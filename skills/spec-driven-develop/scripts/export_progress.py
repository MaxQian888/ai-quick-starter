#!/usr/bin/env python3
"""Export docs/progress/ Markdown files to structured JSON."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

MASTER_TITLE_RE = re.compile(r"^# (?P<title>.+?) — Progress Tracker$", re.MULTILINE)
PHASE_CHECKLIST_RE = re.compile(
    r"^- \[(?P<done>[ xX])\] Phase (?P<number>\d+): (?P<name>.+?) "
    r"\((?P<completed>\d+)/(?P<total>\d+) tasks\)",
    re.MULTILINE,
)
TASK_RE = re.compile(
    r"^- \[(?P<done>[ xX])\] (?P<task_id>T\d+\.\d+) \[(?P<priority>P\d)\] (?P<text>.+)$",
    re.MULTILINE,
)
CURRENT_PHASE_RE = re.compile(r"^- Current phase: (?P<current>.+)$", re.MULTILINE)
COMPLETED_TASKS_RE = re.compile(
    r"^- Completed tasks: (?P<completed>\d+)/(?P<total>\d+)$",
    re.MULTILINE,
)
PHASE_TITLE_RE = re.compile(r"^# Phase (?P<number>\d+): (?P<name>.+)$", re.MULTILINE)


def parse_master(master_text: str) -> dict[str, Any]:
    title_match = MASTER_TITLE_RE.search(master_text)
    if not title_match:
        raise ValueError("MASTER.md title does not match the expected format")

    current_match = CURRENT_PHASE_RE.search(master_text)
    completed_match = COMPLETED_TASKS_RE.search(master_text)
    phases = [
        {
            "number": int(match.group("number")),
            "name": match.group("name"),
            "completed": int(match.group("completed")),
            "total": int(match.group("total")),
            "done": match.group("done").lower() == "x",
        }
        for match in PHASE_CHECKLIST_RE.finditer(master_text)
    ]

    return {
        "task_name": title_match.group("title"),
        "current_phase": current_match.group("current") if current_match else None,
        "completed_tasks": int(completed_match.group("completed")) if completed_match else None,
        "total_tasks": int(completed_match.group("total")) if completed_match else None,
        "phases": phases,
    }


def parse_phase_file(phase_path: Path) -> dict[str, Any]:
    text = phase_path.read_text(encoding="utf-8-sig")
    title_match = PHASE_TITLE_RE.search(text)
    if not title_match:
        raise ValueError(f"{phase_path} does not contain a valid phase header")
    tasks = [
        {
            "id": match.group("task_id"),
            "priority": match.group("priority"),
            "text": match.group("text"),
            "done": match.group("done").lower() == "x",
        }
        for match in TASK_RE.finditer(text)
    ]
    return {
        "path": str(phase_path),
        "number": int(title_match.group("number")),
        "name": title_match.group("name"),
        "tasks": tasks,
    }


def export_progress(progress_dir: Path) -> dict[str, Any]:
    master_path = progress_dir / "MASTER.md"
    if not master_path.exists():
        raise FileNotFoundError(f"MASTER.md not found in {progress_dir}")

    master_data = parse_master(master_path.read_text(encoding="utf-8-sig"))
    phase_files = sorted(progress_dir.glob("phase-*-*.md"))
    return {
        "progress_dir": str(progress_dir),
        "master": master_data,
        "phases": [parse_phase_file(path) for path in phase_files],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "progress_dir",
        nargs="?",
        default="docs/progress",
        help="Progress directory to export. Defaults to docs/progress relative to the current working directory.",
    )
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation size")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    payload = export_progress(Path(args.progress_dir))
    print(json.dumps(payload, indent=args.indent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

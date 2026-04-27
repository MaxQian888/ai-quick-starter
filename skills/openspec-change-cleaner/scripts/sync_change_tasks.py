#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


TASK_PATTERN = re.compile(r"^(\s*[-*]\s+\[)([ xX])(\]\s+)(.+?)\s*$")
DETAIL_PATTERN = re.compile(r"^\s{2,}[-*]\s+")
HEADING_PATTERN = re.compile(r"^##\s+(.+?)\s*$")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply structured checkbox and note updates to an OpenSpec tasks.md file."
    )
    parser.add_argument("--tasks-file", required=True)
    parser.add_argument("--update-file", required=True)
    parser.add_argument("--write-in-place", action="store_true")
    parser.add_argument("--output-file")
    return parser.parse_args(argv)


def normalize_task_text(text: str) -> str:
    return " ".join(text.strip().split())


def find_task_index(lines: list[str], match_text: str) -> int:
    expected = normalize_task_text(match_text)
    for index, line in enumerate(lines):
        match = TASK_PATTERN.match(line)
        if match and normalize_task_text(match.group(4)) == expected:
            return index
    raise ValueError(f"Missing task: {match_text}")


def replace_task_detail(lines: list[str], task_index: int, detail: str | None) -> list[str]:
    insert_at = task_index + 1
    end = insert_at
    while end < len(lines) and DETAIL_PATTERN.match(lines[end]):
        end += 1
    updated = lines[:insert_at] + lines[end:]
    if detail:
        updated.insert(insert_at, f"  - {detail}")
    return updated


def append_section(lines: list[str], heading: str, new_lines: list[str]) -> list[str]:
    heading_line = f"## {heading}"
    for index, line in enumerate(lines):
        match = HEADING_PATTERN.match(line)
        if not match:
            continue
        if normalize_task_text(match.group(1)) != normalize_task_text(heading):
            continue
        section_end = index + 1
        while section_end < len(lines) and not HEADING_PATTERN.match(lines[section_end]):
            section_end += 1
        existing = set(lines[index + 1 : section_end])
        additions = [item for item in new_lines if item not in existing]
        if additions:
            insertion: list[str] = []
            if section_end > index + 1 and lines[section_end - 1] != "":
                insertion.append("")
            insertion.extend(additions)
            lines = lines[:section_end] + insertion + lines[section_end:]
        return lines

    if lines and lines[-1] != "":
        lines.append("")
    lines.append(heading_line)
    lines.extend(new_lines)
    return lines


def apply_task_updates(tasks_text: str, instructions: dict[str, Any]) -> str:
    lines = tasks_text.replace("\r\n", "\n").split("\n")
    if lines and lines[-1] == "":
        lines.pop()

    for update in instructions.get("task_updates", []):
        if not isinstance(update, dict):
            continue
        match_text = update.get("match")
        if not isinstance(match_text, str) or not match_text.strip():
            raise ValueError("Each task update must include a non-empty 'match' string.")
        task_index = find_task_index(lines, match_text)
        match = TASK_PATTERN.match(lines[task_index])
        assert match is not None
        checked = bool(update.get("checked"))
        lines[task_index] = f"{match.group(1)}{'x' if checked else ' '}{match.group(3)}{match.group(4)}"
        detail = update.get("detail")
        if detail is not None and not isinstance(detail, str):
            raise ValueError("Task update 'detail' must be a string when provided.")
        lines = replace_task_detail(lines, task_index, detail)

    for section in instructions.get("append_sections", []):
        if not isinstance(section, dict):
            continue
        heading = section.get("heading")
        raw_lines = section.get("lines", [])
        if not isinstance(heading, str) or not heading.strip():
            raise ValueError("Each append_sections entry must include a non-empty 'heading'.")
        if not isinstance(raw_lines, list) or not all(isinstance(item, str) for item in raw_lines):
            raise ValueError("append_sections 'lines' must be a list of strings.")
        lines = append_section(lines, heading, raw_lines)

    return "\n".join(lines).rstrip() + "\n"


def sync_tasks_file(tasks_file: Path, instructions: dict[str, Any]) -> str:
    original = tasks_file.read_text(encoding="utf-8")
    return apply_task_updates(original, instructions)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    tasks_file = Path(args.tasks_file).resolve()
    update_file = Path(args.update_file).resolve()
    instructions = json.loads(update_file.read_text(encoding="utf-8"))
    updated = sync_tasks_file(tasks_file, instructions)

    if args.write_in_place:
        tasks_file.write_text(updated, encoding="utf-8")
        print(f"UPDATED={tasks_file}")
    elif args.output_file:
        output_path = Path(args.output_file).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(updated, encoding="utf-8")
        print(f"OUTPUT={output_path}")
    else:
        print(updated, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

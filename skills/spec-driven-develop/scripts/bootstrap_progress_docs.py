#!/usr/bin/env python3
"""Create docs/progress/ Markdown files from a structured phase definition."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


@dataclass
class PhaseTask:
    id: str
    text: str
    priority: str = "P1"


@dataclass
class Phase:
    index: int
    name: str
    slug: str
    summary: str
    tasks: list[PhaseTask]
    verification: str
    depends_on: list[str]

    @property
    def filename(self) -> str:
        return f"phase-{self.index}-{self.slug}.md"


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "phase"


def _normalize_priority(raw: str | None) -> str:
    if not raw:
        return "P1"
    raw = raw.strip().upper()
    return raw if raw in {"P0", "P1", "P2"} else "P1"


def _normalize_task(raw_task: Any, phase_index: int, task_index: int) -> PhaseTask:
    task_id = f"T{phase_index}.{task_index}"
    if isinstance(raw_task, str):
        return PhaseTask(id=task_id, text=raw_task.strip(), priority="P1")
    if isinstance(raw_task, dict):
        text = str(raw_task.get("text", "")).strip()
        if not text:
            raise ValueError(f"Task {task_id} is missing text")
        return PhaseTask(
            id=task_id,
            text=text,
            priority=_normalize_priority(raw_task.get("priority")),
        )
    raise ValueError(f"Unsupported task shape for {task_id}: {type(raw_task).__name__}")


def load_phases(phase_file: Path) -> list[Phase]:
    payload = json.loads(phase_file.read_text(encoding="utf-8-sig"))
    raw_phases = payload["phases"] if isinstance(payload, dict) else payload
    if not isinstance(raw_phases, list) or not raw_phases:
        raise ValueError("Phase file must contain a non-empty list of phases")

    phases: list[Phase] = []
    for phase_index, raw_phase in enumerate(raw_phases, start=1):
        if not isinstance(raw_phase, dict):
            raise ValueError(f"Phase {phase_index} must be an object")
        name = str(raw_phase.get("name", "")).strip()
        if not name:
            raise ValueError(f"Phase {phase_index} is missing a name")
        raw_tasks = raw_phase.get("tasks")
        if not isinstance(raw_tasks, list) or not raw_tasks:
            raise ValueError(f"Phase {phase_index} must contain at least one task")

        tasks = [
            _normalize_task(raw_task, phase_index, task_index)
            for task_index, raw_task in enumerate(raw_tasks, start=1)
        ]
        depends_on = raw_phase.get("depends_on") or []
        if not isinstance(depends_on, list):
            raise ValueError(f"Phase {phase_index} depends_on must be a list")

        phases.append(
            Phase(
                index=phase_index,
                name=name,
                slug=slugify(name),
                summary=str(raw_phase.get("summary", "")).strip() or "Add phase notes here.",
                tasks=tasks,
                verification=str(raw_phase.get("verification", "")).strip()
                or "Record the verification boundary for this phase.",
                depends_on=[str(item).strip() for item in depends_on if str(item).strip()],
            )
        )
    return phases


def render_master(task_name: str, task_summary: str, phases: list[Phase]) -> str:
    today = date.today().isoformat()
    total_tasks = sum(len(phase.tasks) for phase in phases)
    phase_reference_lines = "\n".join(
        f"- [Phase {phase.index}: {phase.name}](./{phase.filename})" for phase in phases
    )
    phase_summary_rows = "\n".join(
        f"| {phase.index} | {phase.name} | Planned | 0/{len(phase.tasks)} | Not started |"
        for phase in phases
    )
    phase_checklist_lines = "\n".join(
        f"- [ ] Phase {phase.index}: {phase.name} (0/{len(phase.tasks)} tasks) — "
        f"[details](./{phase.filename})"
        for phase in phases
    )
    first_phase = phases[0]
    return (
        f"# {task_name} — Progress Tracker\n\n"
        "## Task\n"
        f"- Summary: {task_summary}\n\n"
        "## References\n"
        f"{phase_reference_lines}\n\n"
        "## Phase Summary\n"
        "| Phase | Name | Status | Tasks | Progress |\n"
        "| --- | --- | --- | --- | --- |\n"
        f"{phase_summary_rows}\n\n"
        "## Phase Checklist\n"
        f"{phase_checklist_lines}\n\n"
        "## Current Status\n"
        f"- Current phase: Phase {first_phase.index} - {first_phase.name}\n"
        f"- Completed tasks: 0/{total_tasks}\n\n"
        "## Next Steps\n"
        f"- Start Phase {first_phase.index}: {first_phase.name}.\n\n"
        "## Session Log\n"
        f"- [{today}] Progress docs initialized.\n"
    )


def render_phase(phase: Phase) -> str:
    task_lines = "\n".join(
        f"- [ ] {task.id} [{task.priority}] {task.text}" for task in phase.tasks
    )
    depends_on = ", ".join(phase.depends_on) if phase.depends_on else "None"
    return (
        f"# Phase {phase.index}: {phase.name}\n\n"
        "## Purpose\n"
        f"{phase.summary}\n\n"
        "## Tasks\n"
        f"{task_lines}\n\n"
        "## Dependencies\n"
        f"- Depends on: {depends_on}\n\n"
        "## Verification\n"
        f"- Verification boundary: {phase.verification}\n\n"
        "## Notes\n"
        "- Add blockers, clarifications, or handoff notes here.\n\n"
        "## Phase Completion Checklist\n"
        "- [ ] All phase tasks completed\n"
        "- [ ] Relevant verification run or marked blocked\n"
        "- [ ] MASTER.md phase count updated\n"
        "- [ ] MASTER.md current status advanced\n"
    )


def create_progress_docs(
    output_root: Path,
    task_name: str,
    task_summary: str,
    phase_file: Path,
    overwrite: bool = False,
) -> dict[str, Any]:
    phases = load_phases(phase_file)
    progress_dir = output_root / "docs" / "progress"
    master_path = progress_dir / "MASTER.md"

    if progress_dir.exists() and not overwrite:
        raise FileExistsError(
            f"{progress_dir} already exists. Pass --overwrite to replace it."
        )

    progress_dir.mkdir(parents=True, exist_ok=True)
    master_path.write_text(
        render_master(task_name=task_name, task_summary=task_summary, phases=phases),
        encoding="utf-8",
    )

    phase_paths: list[str] = []
    for phase in phases:
        phase_path = progress_dir / phase.filename
        phase_path.write_text(render_phase(phase), encoding="utf-8")
        phase_paths.append(str(phase_path))

    return {
        "progress_dir": str(progress_dir),
        "master_path": str(master_path),
        "phase_paths": phase_paths,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root",
        required=True,
        help="Repository root that will receive docs/progress/",
    )
    parser.add_argument("--task-name", required=True, help="User-facing task name")
    parser.add_argument("--task-summary", required=True, help="Short one-line task summary")
    parser.add_argument("--phase-file", required=True, help="JSON file describing the phases")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing docs/progress/ directory",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = create_progress_docs(
        output_root=Path(args.output_root),
        task_name=args.task_name,
        task_summary=args.task_summary,
        phase_file=Path(args.phase_file),
        overwrite=args.overwrite,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass


CLI_CHOICES = ("claude", "codex", "opencode")
PATTERN_CHOICES = ("sequential", "iterative-pr", "resume", "parallel-dag")


@dataclass
class Step:
    label: str
    command: str
    purpose: str


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render starter autonomous-loop commands for Claude Code, Codex CLI, or OpenCode."
    )
    parser.add_argument("--cli", choices=CLI_CHOICES, required=True)
    parser.add_argument("--pattern", choices=PATTERN_CHOICES, required=True)
    parser.add_argument("--task", required=True, help="Human-readable task or objective.")
    parser.add_argument("--notes-file", default="SHARED_TASK_NOTES.md")
    parser.add_argument("--model", default="")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args(argv)


def shell_quote(text: str) -> str:
    return json.dumps(text, ensure_ascii=False)


def build_command(cli: str, prompt: str, model: str = "", resume: bool = False) -> str:
    if cli == "claude":
        parts = ["claude"]
        if resume:
            parts.append("-c")
        parts.append("-p")
        if model:
            parts.extend(["--model", model])
        parts.append(shell_quote(prompt))
        return " ".join(parts)

    if cli == "codex":
        if resume:
            parts = ["codex", "resume", "--last"]
        else:
            parts = ["codex", "exec", "--skip-git-repo-check"]
        if model:
            parts.extend(["--model", model])
        parts.append(shell_quote(prompt))
        return " ".join(parts)

    if cli == "opencode":
        parts = ["opencode", "run"]
        if resume:
            parts.append("--continue")
        if model:
            parts.extend(["--model", model])
        parts.append(shell_quote(prompt))
        return " ".join(parts)

    raise ValueError(f"Unsupported cli: {cli}")


def notes_prefix(notes_file: str) -> str:
    return (
        f"Read {notes_file} first if it exists. Update {notes_file} before finishing with progress, "
        "verification status, blockers, and the next recommended step."
    )


def render_steps(cli: str, pattern: str, task: str, notes_file: str, model: str = "") -> list[Step]:
    prefix = notes_prefix(notes_file)

    if pattern == "sequential":
        return [
            Step(
                label="implement",
                purpose="Make one scoped implementation pass.",
                command=build_command(
                    cli,
                    f"{prefix} Implement this task in one coherent pass: {task}. Keep the scope tight and avoid unrelated refactors.",
                    model=model,
                ),
            ),
            Step(
                label="cleanup",
                purpose="Run a dedicated cleanup or review pass after implementation.",
                command=build_command(
                    cli,
                    f"{prefix} Review the changes from the previous pass. Remove unnecessary scaffolding, dead code, stray logs, and speculative checks while preserving required tests and intended behavior.",
                    model=model,
                ),
            ),
            Step(
                label="verify",
                purpose="Run the real repository checks, fix failures, and record remaining gaps honestly.",
                command=build_command(
                    cli,
                    f"{prefix} Run the repository's real verification commands for {task}. Fix any failures without changing intended behavior. Record what passed and what remains unverified.",
                    model=model,
                ),
            ),
        ]

    if pattern == "iterative-pr":
        return [
            Step(
                label="iteration",
                purpose="Run one autonomous iteration toward the goal.",
                command=build_command(
                    cli,
                    f"{prefix} Perform exactly one autonomous iteration toward this goal: {task}. Stop after one meaningful change set, and leave a concrete next-step note instead of trying to finish everything in one pass.",
                    model=model,
                ),
            ),
            Step(
                label="review",
                purpose="Run an explicit review or hardening pass before the next iteration.",
                command=build_command(
                    cli,
                    f"{prefix} Review the current working tree for regressions, risky shortcuts, missing tests, and mismatched scope related to: {task}. Apply only targeted hardening fixes.",
                    model=model,
                ),
            ),
            Step(
                label="verify",
                purpose="Run the relevant verification gate before another loop iteration.",
                command=build_command(
                    cli,
                    f"{prefix} Re-run the relevant validation commands for {task}. If failures remain, capture the real failure context in {notes_file} for the next iteration.",
                    model=model,
                ),
            ),
        ]

    if pattern == "resume":
        return [
            Step(
                label="resume",
                purpose="Continue the latest session with the same objective and a notes-file refresh.",
                command=build_command(
                    cli,
                    f"{prefix} Continue the existing session for this objective: {task}. Re-check filesystem state before making new edits.",
                    model=model,
                    resume=True,
                ),
            )
        ]

    if pattern == "parallel-dag":
        return [
            Step(
                label="decompose",
                purpose="Break the work into dependency-aware units before any parallel execution.",
                command=build_command(
                    cli,
                    f"{prefix} Decompose this task into dependency-aware work units: {task}. Produce a compact DAG with unit ids, dependencies, acceptance criteria, file-overlap risks, and the first execution layer only.",
                    model=model,
                ),
            ),
            Step(
                label="layer-execution",
                purpose="Run one dependency layer with isolated unit execution instructions.",
                command=build_command(
                    cli,
                    f"{prefix} Execute only the current ready dependency layer for: {task}. Keep each work unit isolated, preserve the declared DAG ordering, and record which units are ready, blocked, or conflicted before stopping.",
                    model=model,
                ),
            ),
            Step(
                label="merge-review",
                purpose="Prepare the merge queue and independent review pass for the completed layer.",
                command=build_command(
                    cli,
                    f"{prefix} Review the completed layer for: {task}. Prepare a merge queue, note file-overlap conflicts, identify units that need rebase or rework, and record the next layer entry criteria before finishing.",
                    model=model,
                ),
            ),
        ]

    raise ValueError(f"Unsupported pattern: {pattern}")


def as_payload(cli: str, pattern: str, task: str, notes_file: str, model: str, steps: list[Step]) -> dict[str, object]:
    return {
        "cli": cli,
        "pattern": pattern,
        "task": task,
        "notes_file": notes_file,
        "model": model or None,
        "steps": [asdict(step) for step in steps],
    }


def render_text(payload: dict[str, object]) -> str:
    lines = [
        f"CLI: {payload['cli']}",
        f"Pattern: {payload['pattern']}",
        f"Notes file: {payload['notes_file']}",
    ]
    if payload["model"]:
        lines.append(f"Model: {payload['model']}")
    lines.append("")

    for index, step in enumerate(payload["steps"], start=1):
        lines.append(f"{index}. {step['label']}")
        lines.append(f"   Purpose: {step['purpose']}")
        lines.append(f"   Command: {step['command']}")
        lines.append("")

    return "\n".join(lines).rstrip()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    steps = render_steps(
        cli=args.cli,
        pattern=args.pattern,
        task=args.task,
        notes_file=args.notes_file,
        model=args.model,
    )
    payload = as_payload(
        cli=args.cli,
        pattern=args.pattern,
        task=args.task,
        notes_file=args.notes_file,
        model=args.model,
        steps=steps,
    )

    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PLACEHOLDER_PATTERNS = (
    re.compile(r"\bTODO\b", re.IGNORECASE),
    re.compile(r"\bTBD\b", re.IGNORECASE),
    re.compile(r"placeholder", re.IGNORECASE),
    re.compile(r"replace me", re.IGNORECASE),
)
TASK_PATTERN = re.compile(r"^\s*[-*]\s+\[([ xX])\]\s+(.+?)\s*$")


@dataclass
class OpenSpecCli:
    repo_root: Path
    openspec_bin: str = "openspec"

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        executable = resolve_executable_path(self.openspec_bin)
        command = [executable, *args]
        return subprocess.run(
            command,
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

    def _run_json(self, *args: str) -> dict[str, Any]:
        result = self._run(*args, "--json")
        command = [resolve_executable_path(self.openspec_bin), *args, "--json"]
        stdout = result.stdout.strip()
        if not stdout:
            stderr = result.stderr.strip()
            raise RuntimeError(f"Command returned no JSON output: {' '.join(command)}\n{stderr}")
        try:
            return json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Failed to decode JSON from {' '.join(command)}") from exc

    def list_changes(self) -> list[dict[str, Any]]:
        payload = self._run_json("list")
        return normalize_change_list(payload)

    def show_change(self, change_name: str) -> dict[str, Any]:
        return self._run_json("show", change_name)

    def status(self, change_name: str) -> dict[str, Any]:
        return self._run_json("status", "--change", change_name)

    def validate(self, change_name: str) -> dict[str, Any]:
        return self._run_json("validate", change_name, "--no-interactive")

    def archive(self, change_name: str) -> str:
        result = self._run("archive", change_name, "-y")
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"Failed to archive {change_name}")
        return (result.stdout or "").strip()


def resolve_executable_path(executable: str) -> str:
    if Path(executable).is_file():
        return executable

    direct = shutil.which(executable)
    if direct:
        return direct

    for suffix in (".cmd", ".exe", ".bat", ".ps1"):
        resolved = shutil.which(f"{executable}{suffix}")
        if resolved:
            return resolved

    raise FileNotFoundError(f"Could not locate executable: {executable}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit OpenSpec changes and archive folders for stale or cleanable artifacts."
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--change", action="append", default=[])
    parser.add_argument("--skip-archive", action="store_true")
    parser.add_argument("--openspec-bin", default="openspec")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--json-out")
    parser.add_argument("--markdown-out")
    return parser.parse_args(argv)


def normalize_change_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        changes = payload.get("changes", [])
        if isinstance(changes, list):
            return [item for item in changes if isinstance(item, dict)]
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def find_placeholder_hits(text: str, source: str) -> list[str]:
    hits: list[str] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped:
            continue
        for pattern in PLACEHOLDER_PATTERNS:
            if pattern.search(stripped):
                hits.append(f"{source}:{line_number}: {stripped}")
                break
    return hits


def collect_change_text_files(change_dir: Path) -> list[Path]:
    files: list[Path] = []
    for name in ("proposal.md", "design.md", "tasks.md"):
        candidate = change_dir / name
        if candidate.exists():
            files.append(candidate)
    spec_dir = change_dir / "specs"
    if spec_dir.exists():
        files.extend(sorted(spec_dir.rglob("*.md")))
    return files


def summarize_placeholders(paths: list[Path], root: Path) -> list[str]:
    hits: list[str] = []
    for path in paths:
        try:
            source = str(path.relative_to(root))
        except ValueError:
            source = str(path)
        hits.extend(find_placeholder_hits(read_text(path), source))
    return hits


def analyze_task_file(tasks_path: Path) -> dict[str, Any]:
    if not tasks_path.exists():
        return {
            "exists": False,
            "path": str(tasks_path),
            "total": 0,
            "completed": 0,
            "open_tasks": [],
            "placeholder_hits": [],
        }

    text = read_text(tasks_path)
    total = 0
    completed = 0
    open_tasks: list[str] = []
    for raw_line in text.splitlines():
        match = TASK_PATTERN.match(raw_line)
        if not match:
            continue
        total += 1
        task_text = match.group(2)
        if match.group(1).lower() == "x":
            completed += 1
        else:
            open_tasks.append(task_text)

    return {
        "exists": True,
        "path": str(tasks_path),
        "total": total,
        "completed": completed,
        "open_tasks": open_tasks,
        "placeholder_hits": find_placeholder_hits(text, str(tasks_path.name)),
    }


def extract_validation_issues(payload: dict[str, Any]) -> tuple[bool | None, list[str]]:
    items = payload.get("items", [])
    if not isinstance(items, list) or not items:
        return None, []

    issues: list[str] = []
    valid: bool | None = True
    for item in items:
        if not isinstance(item, dict):
            continue
        item_valid = item.get("valid")
        if item_valid is False:
            valid = False
        item_issues = item.get("issues", [])
        if isinstance(item_issues, list):
            for issue in item_issues:
                if isinstance(issue, dict):
                    message = issue.get("message")
                    if isinstance(message, str):
                        issues.append(message)
    return valid, issues


def assess_active_change(
    *,
    raw_change: dict[str, Any],
    status_payload: dict[str, Any],
    delta_count: int,
    validation_valid: bool | None,
    tasks_info: dict[str, Any],
    placeholder_hits: list[str],
) -> dict[str, Any]:
    reasons: list[str] = []
    artifacts = status_payload.get("artifacts", [])
    if not isinstance(artifacts, list):
        artifacts = []

    blocked_artifacts = [
        artifact.get("id")
        for artifact in artifacts
        if isinstance(artifact, dict) and artifact.get("status") == "blocked"
    ]
    apply_requires = status_payload.get("applyRequires", [])
    if not isinstance(apply_requires, list):
        apply_requires = []

    if delta_count <= 0:
        reasons.append("No parsed delta requirements were found.")
    if validation_valid is False:
        reasons.append("Validation reports artifact errors.")
    if blocked_artifacts:
        reasons.append(f"Blocked artifacts remain: {', '.join(str(item) for item in blocked_artifacts)}.")
    if "tasks" in apply_requires and not tasks_info["exists"]:
        reasons.append("The schema still requires tasks, but tasks.md is missing.")
    if placeholder_hits or tasks_info["placeholder_hits"]:
        reasons.append("Placeholder content is still present inside the change artifacts.")

    if reasons:
        return {"classification": "repair-artifacts", "reasons": reasons}

    task_total = int(tasks_info["total"])
    task_completed = int(tasks_info["completed"])
    if (
        status_payload.get("isComplete") is True
        or (task_total > 0 and task_total == task_completed and validation_valid is not False)
    ):
        return {
            "classification": "ready-for-verify-or-archive",
            "reasons": [
                "Tasks and artifact status indicate the change is complete.",
                "Validation does not report structural errors.",
            ],
        }

    list_status = str(raw_change.get("status", ""))
    if task_total > task_completed or list_status not in {"complete", "no-tasks"}:
        return {
            "classification": "active-work",
            "reasons": ["The change still has outstanding implementation or checklist work."],
        }

    return {
        "classification": "review",
        "reasons": ["The change needs manual review because the signals are mixed or incomplete."],
    }


def assess_archive_entry(
    *,
    archive_dir: Path,
    spec_files: list[Path],
    placeholder_hits: list[str],
) -> dict[str, Any]:
    proposal_exists = (archive_dir / "proposal.md").exists()
    design_exists = (archive_dir / "design.md").exists()
    tasks_exists = (archive_dir / "tasks.md").exists()

    if spec_files or tasks_exists or design_exists:
        return {
            "classification": "keep-history",
            "reasons": ["Archived change still contains meaningful historical artifacts."],
        }

    if placeholder_hits or proposal_exists:
        return {
            "classification": "safe-cleanup-candidate",
            "reasons": ["Archived folder only contains placeholder or scaffold-level content."],
        }

    return {
        "classification": "review",
        "reasons": ["Archived folder is sparse but not obviously disposable."],
    }


def build_cleanup_report(
    *,
    repo_root: Path,
    cli: Any | None = None,
    include_archive: bool = True,
    change_names: list[str] | None = None,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    openspec_root = repo_root / "openspec"
    if cli is None:
        cli = OpenSpecCli(repo_root=repo_root)

    listed_changes = normalize_change_list(cli.list_changes())
    if change_names:
        wanted = set(change_names)
        listed_changes = [item for item in listed_changes if str(item.get("name")) in wanted]

    active_entries: list[dict[str, Any]] = []
    for raw_change in listed_changes:
        change_name = str(raw_change.get("name"))
        change_dir = openspec_root / "changes" / change_name
        show_payload = cli.show_change(change_name)
        status_payload = cli.status(change_name)
        validate_payload = cli.validate(change_name)
        validation_valid, validation_issues = extract_validation_issues(validate_payload)
        text_files = collect_change_text_files(change_dir)
        placeholder_hits = summarize_placeholders(text_files, repo_root)
        tasks_info = analyze_task_file(change_dir / "tasks.md")
        delta_count = int(show_payload.get("deltaCount", 0) or 0)
        spec_files = sorted((change_dir / "specs").rglob("*.md")) if (change_dir / "specs").exists() else []
        assessment = assess_active_change(
            raw_change=raw_change,
            status_payload=status_payload,
            delta_count=delta_count,
            validation_valid=validation_valid,
            tasks_info=tasks_info,
            placeholder_hits=placeholder_hits,
        )
        active_entries.append(
            {
                "name": change_name,
                "path": str(change_dir),
                "list_entry": raw_change,
                "delta_count": delta_count,
                "artifacts": status_payload.get("artifacts", []),
                "apply_requires": status_payload.get("applyRequires", []),
                "validation": {"valid": validation_valid, "issues": validation_issues},
                "task_file": tasks_info,
                "placeholder_hits": placeholder_hits,
                "spec_files": [str(path) for path in spec_files],
                "assessment": assessment,
            }
        )

    archive_entries: list[dict[str, Any]] = []
    archive_root = openspec_root / "changes" / "archive"
    if include_archive and archive_root.exists():
        for archive_dir in sorted(path for path in archive_root.iterdir() if path.is_dir()):
            text_files = collect_change_text_files(archive_dir)
            placeholder_hits = summarize_placeholders(text_files, repo_root)
            spec_files = sorted((archive_dir / "specs").rglob("*.md")) if (archive_dir / "specs").exists() else []
            assessment = assess_archive_entry(
                archive_dir=archive_dir,
                spec_files=spec_files,
                placeholder_hits=placeholder_hits,
            )
            archive_entries.append(
                {
                    "name": archive_dir.name,
                    "path": str(archive_dir),
                    "placeholder_hits": placeholder_hits,
                    "spec_files": [str(path) for path in spec_files],
                    "assessment": assessment,
                }
            )

    summary = {
        "repair_candidates": [
            entry["name"]
            for entry in active_entries
            if entry["assessment"]["classification"] == "repair-artifacts"
        ],
        "ready_candidates": [
            entry["name"]
            for entry in active_entries
            if entry["assessment"]["classification"] == "ready-for-verify-or-archive"
        ],
        "safe_cleanup_candidates": [
            entry["name"]
            for entry in archive_entries
            if entry["assessment"]["classification"] == "safe-cleanup-candidate"
        ],
        "review_candidates": [
            entry["name"]
            for entry in [*active_entries, *archive_entries]
            if entry["assessment"]["classification"] == "review"
        ],
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(repo_root),
        "openspec_root": str(openspec_root),
        "active_changes": active_entries,
        "archive_changes": archive_entries,
        "summary": summary,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenSpec Change Cleanup Report",
        "",
        f"Repo root: `{report.get('repo_root', '')}`",
    ]
    generated_at = report.get("generated_at")
    if generated_at:
        lines.append(f"Generated at: `{generated_at}`")
    lines.extend(
        [
            "",
            "## Summary",
            f"- Repair candidates: {', '.join(report.get('summary', {}).get('repair_candidates', [])) or 'none'}",
            f"- Ready candidates: {', '.join(report.get('summary', {}).get('ready_candidates', [])) or 'none'}",
            f"- Safe cleanup candidates: {', '.join(report.get('summary', {}).get('safe_cleanup_candidates', [])) or 'none'}",
        ]
    )

    active_changes = report.get("active_changes", [])
    lines.extend(["", "## Active Changes"])
    if not active_changes:
        lines.extend(["", "- None."])
    else:
        for entry in active_changes:
            assessment = entry.get("assessment", {})
            lines.extend(
                [
                    "",
                    f"### {entry.get('name', 'unknown-change')}",
                    f"- Classification: `{assessment.get('classification', 'unknown')}`",
                    f"- Task progress: {entry.get('task_file', {}).get('completed', 0)}/{entry.get('task_file', {}).get('total', 0)}",
                ]
            )
            for reason in assessment.get("reasons", []):
                lines.append(f"- Reason: {reason}")

    archive_changes = report.get("archive_changes", [])
    lines.extend(["", "## Archive Review"])
    if not archive_changes:
        lines.extend(["", "- None."])
    else:
        for entry in archive_changes:
            assessment = entry.get("assessment", {})
            lines.extend(
                [
                    "",
                    f"### {entry.get('name', 'unknown-archive')}",
                    f"- Classification: `{assessment.get('classification', 'unknown')}`",
                ]
            )
            for reason in assessment.get("reasons", []):
                lines.append(f"- Reason: {reason}")

    return "\n".join(lines).rstrip() + "\n"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    cli = OpenSpecCli(repo_root=repo_root, openspec_bin=args.openspec_bin)
    report = build_cleanup_report(
        repo_root=repo_root,
        cli=cli,
        include_archive=not args.skip_archive,
        change_names=args.change or None,
    )

    markdown = render_markdown(report)
    if args.json_out:
        json_path = Path(args.json_out).resolve()
        write_text(json_path, json.dumps(report, ensure_ascii=False, indent=2))
        print(f"JSON_OUT={json_path}")
    if args.markdown_out:
        markdown_path = Path(args.markdown_out).resolve()
        write_text(markdown_path, markdown)
        print(f"MARKDOWN_OUT={markdown_path}")

    if args.as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif not args.json_out and not args.markdown_out:
        print(markdown)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path


HUNK_PATTERN = re.compile(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


@dataclass
class LineRange:
    start: int
    end: int
    source: str
    kind: str


@dataclass
class FileScope:
    path: str
    change_sources: list[str] = field(default_factory=list)
    line_ranges: list[LineRange] = field(default_factory=list)
    treat_as_full_file: bool = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detect recently modified files and line ranges to narrow code simplification scope."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Git repository root to inspect.",
    )
    parser.add_argument(
        "--mode",
        choices=("worktree", "base-ref"),
        default="worktree",
        help="Inspect the current worktree or compare committed changes against a base ref.",
    )
    parser.add_argument(
        "--base-ref",
        help="Base ref used with --mode base-ref, such as origin/main or HEAD~1.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit structured JSON output.",
    )
    return parser.parse_args()


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def is_git_repository(root: Path) -> bool:
    probe = run_git(root, "rev-parse", "--is-inside-work-tree")
    return probe.returncode == 0 and probe.stdout.strip() == "true"


def ensure_file_scope(scopes: dict[str, FileScope], path: str, source: str) -> FileScope:
    scope = scopes.setdefault(path, FileScope(path=path))
    if source not in scope.change_sources:
        scope.change_sources.append(source)
    return scope


def parse_zero_context_patch(patch: str, source: str) -> dict[str, FileScope]:
    scopes: dict[str, FileScope] = {}
    current_path: str | None = None

    for line in patch.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            current_path = None
            if len(parts) >= 4 and parts[3].startswith("b/"):
                current_path = parts[3][2:]
                ensure_file_scope(scopes, current_path, source)
            continue

        if line.startswith("+++ "):
            candidate = line[4:]
            if candidate == "/dev/null":
                current_path = None
                continue
            if candidate.startswith("b/"):
                current_path = candidate[2:]
                ensure_file_scope(scopes, current_path, source)
            continue

        if not current_path or not line.startswith("@@ "):
            continue

        match = HUNK_PATTERN.search(line)
        if not match:
            continue

        start = int(match.group(1))
        count = int(match.group(2) or "1")
        kind = "addition_or_modification"
        end = start + count - 1 if count > 0 else start
        if count == 0:
            kind = "deletion_only"

        scope = ensure_file_scope(scopes, current_path, source)
        scope.line_ranges.append(
            LineRange(
                start=start,
                end=end,
                source=source,
                kind=kind,
            )
        )

    return scopes


def merge_line_ranges(line_ranges: list[LineRange]) -> list[LineRange]:
    if not line_ranges:
        return []

    ordered = sorted(line_ranges, key=lambda item: (item.source, item.start, item.end, item.kind))
    merged: list[LineRange] = [ordered[0]]

    for current in ordered[1:]:
        previous = merged[-1]
        if (
            previous.source == current.source
            and previous.kind == current.kind
            and current.start <= previous.end + 1
        ):
            previous.end = max(previous.end, current.end)
            continue
        merged.append(current)

    return merged


def merge_scopes(target: dict[str, FileScope], incoming: dict[str, FileScope]) -> None:
    for path, scope in incoming.items():
        destination = target.setdefault(path, FileScope(path=path))
        for source in scope.change_sources:
            if source not in destination.change_sources:
                destination.change_sources.append(source)
        destination.line_ranges.extend(scope.line_ranges)
        destination.treat_as_full_file = destination.treat_as_full_file or scope.treat_as_full_file


def collect_worktree_scope(root: Path) -> tuple[dict[str, FileScope], list[str]]:
    scopes: dict[str, FileScope] = {}

    unstaged = run_git(root, "diff", "--unified=0", "--no-color", "--relative")
    if unstaged.returncode != 0:
        raise RuntimeError(unstaged.stderr.strip() or "Failed to inspect unstaged changes.")
    merge_scopes(scopes, parse_zero_context_patch(unstaged.stdout, "unstaged"))

    staged = run_git(root, "diff", "--cached", "--unified=0", "--no-color", "--relative")
    if staged.returncode != 0:
        raise RuntimeError(staged.stderr.strip() or "Failed to inspect staged changes.")
    merge_scopes(scopes, parse_zero_context_patch(staged.stdout, "staged"))

    untracked = run_git(root, "ls-files", "--others", "--exclude-standard")
    if untracked.returncode != 0:
        raise RuntimeError(untracked.stderr.strip() or "Failed to inspect untracked files.")

    for raw_path in untracked.stdout.splitlines():
        path = raw_path.strip()
        if not path:
            continue
        scope = ensure_file_scope(scopes, path, "untracked")
        scope.treat_as_full_file = True

    return scopes, []


def collect_base_ref_scope(root: Path, base_ref: str) -> tuple[dict[str, FileScope], list[str]]:
    diff = run_git(root, "diff", "--unified=0", "--no-color", "--relative", f"{base_ref}...HEAD")
    if diff.returncode != 0:
        message = diff.stderr.strip() or diff.stdout.strip() or f"Failed to diff against {base_ref}."
        raise RuntimeError(message)
    return parse_zero_context_patch(diff.stdout, "base-ref"), []


def build_payload(root: Path, mode: str, base_ref: str | None) -> dict[str, object]:
    warnings: list[str] = []
    if not is_git_repository(root):
        warnings.append("Not a git repository. Fall back to explicit user-provided files or current-session context.")
        return {
            "repo_root": str(root),
            "mode": mode,
            "base_ref": base_ref,
            "files": [],
            "warnings": warnings,
        }

    if mode == "base-ref":
        if not base_ref:
            raise RuntimeError("--base-ref is required when --mode base-ref is used.")
        scopes, scope_warnings = collect_base_ref_scope(root, base_ref)
    else:
        scopes, scope_warnings = collect_worktree_scope(root)

    warnings.extend(scope_warnings)

    files = []
    for path in sorted(scopes):
        scope = scopes[path]
        scope.change_sources.sort()
        scope.line_ranges = merge_line_ranges(scope.line_ranges)
        files.append(
            {
                "path": scope.path,
                "change_sources": scope.change_sources,
                "line_ranges": [asdict(item) for item in scope.line_ranges],
                "treat_as_full_file": scope.treat_as_full_file,
            }
        )

    if not files:
        warnings.append("No changed files detected for the selected mode.")

    return {
        "repo_root": str(root),
        "mode": mode,
        "base_ref": base_ref,
        "files": files,
        "warnings": warnings,
    }


def print_text(payload: dict[str, object]) -> None:
    files = payload["files"]
    print(f"Mode: {payload['mode']}")
    if payload.get("base_ref"):
        print(f"Base ref: {payload['base_ref']}")
    print(f"Detected files: {len(files)}")

    for entry in files:
        path = entry["path"]
        sources = ", ".join(entry["change_sources"])
        print(f"- {path} [{sources}]")
        if entry["treat_as_full_file"]:
            print("  full file")
            continue
        for line_range in entry["line_ranges"]:
            print(
                f"  lines {line_range['start']}-{line_range['end']} "
                f"({line_range['source']}, {line_range['kind']})"
            )

    warnings = payload.get("warnings", [])
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")


def main() -> int:
    args = parse_args()
    root = Path(args.repo_root).resolve()
    if not root.exists():
        print(f"Repository root does not exist: {root}", file=sys.stderr)
        return 2

    try:
        payload = build_payload(root=root, mode=args.mode, base_ref=args.base_ref)
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 2

    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_text(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

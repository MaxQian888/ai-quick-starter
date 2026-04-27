#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import subprocess
import sys
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


SKIP_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".next",
    ".turbo",
    ".venv",
    ".venv-local",
    ".uv-cache",
    ".uv-cache-codex",
    ".uv-cache-local",
    ".uv-python",
    "__pycache__",
    "node_modules",
    "target",
}
FIXTURE_HINT_PARTS = {
    "__fixtures__",
    "example",
    "examples",
    "fixture",
    "fixtures",
    "sample",
    "samples",
    "temp",
    "test",
    "tests",
    "tmp",
}
COMMAND_ORDER = ("fmt", "clippy", "test")


@dataclass
class ManifestInfo:
    manifest_path: str
    crate_dir: str
    package_name: str | None
    kind: str
    workspace_root: str | None
    fixture_like: bool


@dataclass
class CommandCandidate:
    target_manifest: str
    target_kind: str
    package_name: str | None
    kind: str
    command: str
    cwd: str
    source: str
    reason: str
    priority: int


@dataclass
class ExecutedCommand:
    target_manifest: str
    kind: str
    command: str
    cwd: str
    source: str
    exit_code: int
    stdout_tail: str
    stderr_tail: str


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discover and optionally execute the Rust lint surface for a repository."
    )
    parser.add_argument("--root", required=True, help="Repository root to inspect.")
    parser.add_argument(
        "--target",
        help="Optional crate directory, source file inside a crate, or Cargo.toml path to narrow the scope.",
    )
    parser.add_argument(
        "--mode",
        choices=("discover", "lint", "verify"),
        default="discover",
        help="Discovery only, lint execution, or final verification execution.",
    )
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit JSON output.")
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include cargo test in lint mode. Verify mode always includes tests.",
    )
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        default=True,
        help="Elevate warnings during Clippy verification. Enabled by default.",
    )
    parser.add_argument(
        "--no-strict-warnings",
        action="store_false",
        dest="strict_warnings",
        help="Do not append -D warnings to the Clippy command.",
    )
    parser.add_argument(
        "--max-crates",
        type=int,
        default=8,
        help="Maximum number of selected crate targets when no explicit target is given.",
    )
    return parser.parse_args(argv)


def posix_relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def looks_fixture_like(path_text: str) -> bool:
    parts = [part.lower() for part in Path(path_text).parts]
    return any(part in FIXTURE_HINT_PARTS or part.startswith("_tmp") for part in parts)


def iter_manifest_paths(root: Path) -> list[Path]:
    manifests: list[Path] = []
    for current_root, dir_names, file_names in os.walk(root):
        dir_names[:] = [
            name
            for name in dir_names
            if name not in SKIP_DIR_NAMES and not name.startswith(".pytest_cache")
        ]
        if "Cargo.toml" in file_names:
            manifests.append(Path(current_root) / "Cargo.toml")
    manifests.sort()
    return manifests


def read_manifest(path: Path) -> dict[str, Any]:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def match_workspace_member(crate_dir_rel: str, pattern: str) -> bool:
    rel = crate_dir_rel.rstrip("/")
    normalized_pattern = pattern.rstrip("/")
    return fnmatch.fnmatch(rel, normalized_pattern) or fnmatch.fnmatch(
        f"{rel}/Cargo.toml", f"{normalized_pattern}/Cargo.toml"
    )


def classify_manifests(root: Path, blockers: list[str]) -> list[ManifestInfo]:
    manifests = iter_manifest_paths(root)
    parsed: dict[Path, dict[str, Any]] = {}
    for manifest_path in manifests:
        try:
            parsed[manifest_path] = read_manifest(manifest_path)
        except tomllib.TOMLDecodeError as exc:
            blockers.append(f"Failed to parse {posix_relative(manifest_path, root)}: {exc}")

    workspace_roots = {
        manifest_path: parsed_manifest
        for manifest_path, parsed_manifest in parsed.items()
        if isinstance(parsed_manifest.get("workspace"), dict)
    }

    membership: dict[Path, Path] = {}
    for workspace_manifest, parsed_manifest in workspace_roots.items():
        workspace_root = workspace_manifest.parent
        workspace_table = parsed_manifest.get("workspace")
        if not isinstance(workspace_table, dict):
            continue
        raw_members = workspace_table.get("members", [])
        raw_excludes = workspace_table.get("exclude", [])
        member_patterns = [item for item in raw_members if isinstance(item, str)]
        exclude_patterns = [item for item in raw_excludes if isinstance(item, str)]
        for manifest_path in parsed:
            if manifest_path == workspace_manifest:
                continue
            try:
                rel_dir = manifest_path.parent.relative_to(workspace_root).as_posix()
            except ValueError:
                continue
            if exclude_patterns and any(match_workspace_member(rel_dir, pattern) for pattern in exclude_patterns):
                continue
            if member_patterns and any(match_workspace_member(rel_dir, pattern) for pattern in member_patterns):
                membership[manifest_path] = workspace_manifest

    crate_targets: list[ManifestInfo] = []
    for manifest_path in manifests:
        parsed_manifest = parsed.get(manifest_path, {})
        package_table = parsed_manifest.get("package")
        package_name = package_table.get("name") if isinstance(package_table, dict) else None
        workspace_root = membership.get(manifest_path)
        if manifest_path in workspace_roots:
            kind = "workspace-root"
        elif workspace_root is not None:
            kind = "workspace-member"
        else:
            kind = "standalone"
        rel_manifest = posix_relative(manifest_path, root)
        rel_dir = posix_relative(manifest_path.parent, root)
        crate_targets.append(
            ManifestInfo(
                manifest_path=rel_manifest,
                crate_dir=rel_dir,
                package_name=package_name if isinstance(package_name, str) else None,
                kind=kind,
                workspace_root=posix_relative(workspace_root, root) if workspace_root else None,
                fixture_like=looks_fixture_like(rel_manifest),
            )
        )
    crate_targets.sort(key=lambda item: (item.manifest_path, item.kind))
    return crate_targets


def resolve_target_manifest(
    root: Path,
    target_value: str,
    manifest_index: dict[Path, ManifestInfo],
) -> ManifestInfo | None:
    target_path = Path(target_value)
    if not target_path.is_absolute():
        target_path = (root / target_path).resolve()
    else:
        target_path = target_path.resolve()

    if target_path.is_dir():
        candidate = target_path / "Cargo.toml"
        if candidate in manifest_index:
            return manifest_index[candidate]
        current = target_path
    else:
        if target_path.name == "Cargo.toml" and target_path in manifest_index:
            return manifest_index[target_path]
        current = target_path.parent

    root_resolved = root.resolve()
    while True:
        candidate = current / "Cargo.toml"
        if candidate in manifest_index:
            return manifest_index[candidate]
        if current == root_resolved or current.parent == current:
            break
        current = current.parent
    return None


def select_default_targets(crate_targets: list[ManifestInfo], max_crates: int) -> list[ManifestInfo]:
    preferred_pool = [target for target in crate_targets if not target.fixture_like]
    pool = preferred_pool or crate_targets
    selected: list[ManifestInfo] = []
    workspace_roots = [target for target in pool if target.kind == "workspace-root"]
    standalone = [target for target in pool if target.kind == "standalone"]
    if workspace_roots:
        selected.extend(workspace_roots)
        selected.extend(standalone)
    else:
        selected.extend(pool)
    if not selected:
        return []
    selected.sort(key=lambda item: (item.fixture_like, item.manifest_path))
    return selected[: max(max_crates, 1)]


def cargo_command_kind(command: str) -> str | None:
    lowered = command.lower()
    if "cargo fmt" in lowered:
        return "fmt"
    if "cargo clippy" in lowered:
        return "clippy"
    if "cargo test" in lowered:
        return "test"
    return None


def collect_ci_commands(root: Path) -> list[dict[str, str]]:
    workflow_dir = root / ".github" / "workflows"
    collected: list[dict[str, str]] = []
    if not workflow_dir.exists():
        return collected
    for workflow_path in sorted(workflow_dir.glob("*.y*ml")):
        for raw_line in workflow_path.read_text(encoding="utf-8").splitlines():
            stripped = raw_line.strip()
            if not stripped.startswith("- run:") and not stripped.startswith("run:"):
                continue
            command = stripped.split(":", 1)[1].strip().strip("'\"")
            kind = cargo_command_kind(command)
            if not kind:
                continue
            collected.append(
                {
                    "kind": kind,
                    "command": command,
                    "source": posix_relative(workflow_path, root),
                }
            )
    return collected


def build_generic_commands(root: Path, target: ManifestInfo, strict_warnings: bool) -> list[CommandCandidate]:
    cwd = str((root / target.crate_dir).resolve())
    if target.kind == "workspace-root":
        clippy_command = "cargo clippy --workspace --all-targets --all-features"
        test_command = "cargo test --workspace --all-features"
        reason = "Workspace root manifest detected."
    else:
        clippy_command = "cargo clippy --all-targets --all-features"
        test_command = "cargo test --all-features"
        reason = "Crate manifest detected."
    if strict_warnings:
        clippy_command = f"{clippy_command} -- -D warnings"
    return [
        CommandCandidate(
            target_manifest=target.manifest_path,
            target_kind=target.kind,
            package_name=target.package_name,
            kind="fmt",
            command="cargo fmt --all --check",
            cwd=cwd,
            source=target.manifest_path,
            reason=reason,
            priority=60,
        ),
        CommandCandidate(
            target_manifest=target.manifest_path,
            target_kind=target.kind,
            package_name=target.package_name,
            kind="clippy",
            command=clippy_command,
            cwd=cwd,
            source=target.manifest_path,
            reason=reason,
            priority=60,
        ),
        CommandCandidate(
            target_manifest=target.manifest_path,
            target_kind=target.kind,
            package_name=target.package_name,
            kind="test",
            command=test_command,
            cwd=cwd,
            source=target.manifest_path,
            reason=reason,
            priority=55,
        ),
    ]


def command_priority_for_target(command: str, target: ManifestInfo) -> int:
    lowered = command.lower()
    package_name = target.package_name.lower() if target.package_name else None
    manifest_path = target.manifest_path.lower()
    if target.kind == "workspace-root":
        return 100
    if package_name and (f"-p {package_name}" in lowered or f"--package {package_name}" in lowered):
        return 100
    if manifest_path in lowered:
        return 100
    if target.kind == "standalone":
        return 90
    return 50


def build_ci_commands(root: Path, target: ManifestInfo, ci_commands: list[dict[str, str]]) -> list[CommandCandidate]:
    cwd = str((root / target.crate_dir).resolve())
    candidates: list[CommandCandidate] = []
    for item in ci_commands:
        priority = command_priority_for_target(item["command"], target)
        if priority < 60 and target.kind == "workspace-member":
            continue
        candidates.append(
            CommandCandidate(
                target_manifest=target.manifest_path,
                target_kind=target.kind,
                package_name=target.package_name,
                kind=item["kind"],
                command=item["command"],
                cwd=cwd,
                source=item["source"],
                reason="Cargo command discovered in CI workflow.",
                priority=priority,
            )
        )
    return candidates


def build_recommended_commands(
    root: Path,
    selected_targets: list[ManifestInfo],
    strict_warnings: bool,
    ci_commands: list[dict[str, str]],
) -> list[CommandCandidate]:
    merged: dict[tuple[str, str, str, str], CommandCandidate] = {}
    for target in selected_targets:
        for candidate in build_generic_commands(root, target, strict_warnings) + build_ci_commands(
            root, target, ci_commands
        ):
            key = (candidate.target_manifest, candidate.kind, candidate.command, candidate.cwd)
            current = merged.get(key)
            if current is None or candidate.priority > current.priority:
                merged[key] = candidate
    order = {name: index for index, name in enumerate(COMMAND_ORDER)}
    return sorted(
        merged.values(),
        key=lambda item: (
            item.target_manifest,
            order.get(item.kind, 99),
            -item.priority,
            item.command,
        ),
    )


def summarize_output(text: str, max_lines: int = 40, max_chars: int = 4000) -> str:
    stripped = text.strip()
    if not stripped:
        return ""
    lines = stripped.splitlines()
    tail = "\n".join(lines[-max_lines:])
    if len(tail) <= max_chars:
        return tail
    return tail[-max_chars:]


def collect_warning_lines(stdout_text: str, stderr_text: str) -> list[str]:
    interesting: list[str] = []
    for line in (stdout_text + "\n" + stderr_text).splitlines():
        lowered = line.lower()
        if lowered.startswith("warning:") or lowered.startswith("error:") or "clippy::" in lowered:
            interesting.append(line.strip())
    return interesting[:10]


def infer_blockers_from_output(command_kind: str, output: str) -> list[str]:
    lowered = output.lower()
    blockers: list[str] = []
    if "no such subcommand: `clippy`" in lowered or "clippy is not installed" in lowered:
        blockers.append("Clippy component is missing from the active Rust toolchain.")
    if "no such subcommand: `fmt`" in lowered or "rustfmt" in lowered and "not installed" in lowered:
        blockers.append("rustfmt component is missing from the active Rust toolchain.")
    if "blocking waiting for file lock" in lowered or "waiting for file lock" in lowered:
        blockers.append("Cargo build directory is locked by another process.")
    if "permission denied" in lowered:
        blockers.append("Permission denied while running Cargo commands.")
    if "could not find `cargo.toml`" in lowered:
        blockers.append("Selected target did not resolve to a Cargo manifest.")
    if "toolchain" in lowered and "not installed" in lowered and not blockers:
        blockers.append("Required Rust toolchain or component is missing.")
    if command_kind == "clippy" and "warning:" in lowered and not blockers:
        blockers.append("Clippy or rustc warnings still fail the selected lint gate.")
    return blockers


def build_next_step_hint(
    selected_targets: list[ManifestInfo],
    failures: list[ExecutedCommand],
    blockers: list[str],
    warning_lines: list[str],
) -> str:
    if blockers and not failures:
        return blockers[0]
    if not selected_targets:
        return "Current repository has no Rust targets."
    if failures:
        first_failure = failures[0]
        if warning_lines:
            return (
                f"Fix the first reported issue from {first_failure.kind} in "
                f"{first_failure.target_manifest} and rerun the same command."
            )
        return (
            f"Investigate the failing {first_failure.kind} command for "
            f"{first_failure.target_manifest} before widening verification."
        )
    return "Run the recommended commands at the selected scope and fix the first failure."


def select_commands_for_execution(
    recommended_commands: list[CommandCandidate],
    mode: str,
    include_tests: bool,
) -> list[CommandCandidate]:
    if mode == "discover":
        return []
    wanted_kinds = {"fmt", "clippy"}
    if include_tests or mode == "verify":
        wanted_kinds.add("test")
    chosen: list[CommandCandidate] = []
    seen: set[tuple[str, str]] = set()
    for candidate in recommended_commands:
        key = (candidate.target_manifest, candidate.kind)
        if candidate.kind not in wanted_kinds or key in seen:
            continue
        chosen.append(candidate)
        seen.add(key)
    order = {name: index for index, name in enumerate(COMMAND_ORDER)}
    chosen.sort(key=lambda item: (item.target_manifest, order.get(item.kind, 99), -item.priority))
    return chosen


def execute_commands(commands: list[CommandCandidate]) -> tuple[list[ExecutedCommand], list[str], list[str]]:
    executed: list[ExecutedCommand] = []
    blockers: list[str] = []
    warning_lines: list[str] = []
    for candidate in commands:
        try:
            result = subprocess.run(
                candidate.command,
                cwd=candidate.cwd,
                capture_output=True,
                text=True,
                check=False,
                shell=True,
            )
        except OSError as exc:
            blockers.append(f"Failed to launch command '{candidate.command}': {exc}")
            break
        executed_item = ExecutedCommand(
            target_manifest=candidate.target_manifest,
            kind=candidate.kind,
            command=candidate.command,
            cwd=candidate.cwd,
            source=candidate.source,
            exit_code=result.returncode,
            stdout_tail=summarize_output(result.stdout),
            stderr_tail=summarize_output(result.stderr),
        )
        executed.append(executed_item)
        if result.returncode != 0:
            combined_output = f"{result.stdout}\n{result.stderr}"
            blockers.extend(infer_blockers_from_output(candidate.kind, combined_output))
            warning_lines = collect_warning_lines(result.stdout, result.stderr)
            break
    return executed, blockers, warning_lines


def human_summary(payload: dict[str, Any]) -> str:
    lines = [
        f"root: {payload['root']}",
        f"mode: {payload['mode']}",
        f"crate_count: {payload['crate_count']}",
        f"workspace_roots: {', '.join(payload['workspace_roots']) or '(none)'}",
    ]
    if payload["recommended_commands"]:
        lines.append("recommended_commands:")
        for item in payload["recommended_commands"]:
            lines.append(
                f"  - [{item['kind']}] {item['command']} (cwd={item['cwd']}, source={item['source']})"
            )
    if payload["blockers"]:
        lines.append("blockers:")
        for blocker in payload["blockers"]:
            lines.append(f"  - {blocker}")
    lines.append(f"next_step_hint: {payload['next_step_hint']}")
    return "\n".join(lines)


def inspect_repository(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    blockers: list[str] = []
    crate_targets = classify_manifests(root, blockers)
    manifest_index = {
        (root / target.manifest_path).resolve(): target for target in crate_targets
    }

    selected_targets: list[ManifestInfo]
    if args.target:
        matched = resolve_target_manifest(root, args.target, manifest_index)
        if matched is None:
            selected_targets = []
            blockers.append(f"Target did not resolve to a Cargo manifest: {args.target}")
        else:
            selected_targets = [matched]
    else:
        if crate_targets and all(target.fixture_like for target in crate_targets):
            selected_targets = []
            blockers.append("Only fixture-like Rust targets were found under this root.")
        else:
            selected_targets = select_default_targets(crate_targets, args.max_crates)

    if not crate_targets and "Current repository has no Rust targets." not in blockers:
        blockers.append("Current repository has no Rust targets.")

    ci_commands = collect_ci_commands(root)
    recommended_commands = build_recommended_commands(
        root=root,
        selected_targets=selected_targets,
        strict_warnings=args.strict_warnings,
        ci_commands=ci_commands,
    )
    commands_to_execute = select_commands_for_execution(
        recommended_commands=recommended_commands,
        mode=args.mode,
        include_tests=args.include_tests,
    )
    executed_commands, execution_blockers, warning_lines = execute_commands(commands_to_execute)
    blockers.extend(blocker for blocker in execution_blockers if blocker not in blockers)
    failures = [item for item in executed_commands if item.exit_code != 0]
    payload = {
        "root": str(root),
        "mode": args.mode,
        "crate_count": len(crate_targets),
        "workspace_roots": [
            target.manifest_path for target in crate_targets if target.kind == "workspace-root"
        ],
        "crate_targets": [asdict(target) for target in crate_targets],
        "selected_targets": [asdict(target) for target in selected_targets],
        "recommended_commands": [asdict(command) for command in recommended_commands],
        "executed_commands": [asdict(command) for command in executed_commands],
        "failures": [asdict(command) for command in failures],
        "warnings_summary": warning_lines,
        "blockers": blockers,
        "next_step_hint": build_next_step_hint(
            selected_targets=selected_targets,
            failures=failures,
            blockers=blockers,
            warning_lines=warning_lines,
        ),
    }
    return payload


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = inspect_repository(args)
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(human_summary(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

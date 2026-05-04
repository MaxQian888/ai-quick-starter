#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Set


NODE_SCRIPT_ORDER = [
    "lint",
    "typecheck",
    "test",
    "build",
    "check",
    "ci",
    "validate",
    "verify",
    "format:check",
]

NODE_SCRIPT_ALIASES = ("precommit", "pre-commit", "qa", "quality")


@dataclass(frozen=True)
class GateCommand:
    command: str
    reason: str
    source: str


@dataclass
class GateResult:
    command: str
    reason: str
    source: str
    returncode: int
    status: str
    stdout: str
    stderr: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discover and run common pre-commit quality checks."
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Repository root used for detection and command execution.",
    )
    parser.add_argument(
        "--discover-only",
        action="store_true",
        help="Print detected commands and exit without running them.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit structured JSON output.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop execution after the first failing command.",
    )
    parser.add_argument(
        "--max-output-chars",
        type=int,
        default=12000,
        help="Maximum characters kept per command output stream.",
    )
    return parser.parse_args()


def read_text_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="ignore")


def truncate_text(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    return value[:max_chars] + "\n...[truncated]..."


def append_unique(
    commands: List[GateCommand],
    seen: Set[str],
    command: str,
    reason: str,
    source: str,
) -> None:
    normalized = command.strip()
    if not normalized or normalized in seen:
        return
    commands.append(GateCommand(command=normalized, reason=reason, source=source))
    seen.add(normalized)


def is_git_repository(root: Path) -> bool:
    if shutil.which("git") is None:
        return False
    try:
        probe = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, FileNotFoundError):
        return False
    return probe.returncode == 0 and probe.stdout.strip() == "true"


def detect_python_runner(root: Path, pyproject_text: str) -> str:
    lowered = pyproject_text.lower()
    if (root / "uv.lock").exists() or "[tool.uv" in lowered:
        return "uv run "
    if (root / "poetry.lock").exists() or "[tool.poetry" in lowered:
        return "poetry run "
    if (root / "Pipfile").exists():
        return "pipenv run "
    return ""


def detect_package_manager(root: Path) -> str:
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (root / "yarn.lock").exists():
        return "yarn"
    if (root / "bun.lockb").exists() or (root / "bun.lock").exists():
        return "bun"
    return "npm"


def build_node_script_command(package_manager: str, script_name: str) -> str:
    if package_manager == "pnpm":
        return f"pnpm {script_name}"
    if package_manager == "yarn":
        return f"yarn {script_name}"
    if package_manager == "bun":
        return f"bun run {script_name}"
    return f"npm run {script_name}"


def load_package_scripts(root: Path) -> Dict[str, str]:
    package_json = root / "package.json"
    if not package_json.exists():
        return {}
    try:
        payload = json.loads(read_text_if_exists(package_json))
    except json.JSONDecodeError:
        return {}
    scripts = payload.get("scripts", {})
    if not isinstance(scripts, dict):
        return {}
    return {str(k): str(v) for k, v in scripts.items()}


def detect_commands(root: Path) -> List[GateCommand]:
    commands: List[GateCommand] = []
    seen: Set[str] = set()

    pyproject_text = read_text_if_exists(root / "pyproject.toml")
    setup_cfg_text = read_text_if_exists(root / "setup.cfg")
    requirements_text = "\n".join(
        [
            read_text_if_exists(root / "requirements.txt"),
            read_text_if_exists(root / "requirements-dev.txt"),
            read_text_if_exists(root / "dev-requirements.txt"),
        ]
    )
    python_context = f"{pyproject_text}\n{setup_cfg_text}\n{requirements_text}".lower()
    python_runner = detect_python_runner(root, pyproject_text)

    if (root / ".pre-commit-config.yaml").exists():
        append_unique(
            commands=commands,
            seen=seen,
            command=f"{python_runner}pre-commit run --all-files",
            reason="Repository defines pre-commit hooks",
            source=".pre-commit-config.yaml",
        )

    package_scripts = load_package_scripts(root)
    if package_scripts:
        package_manager = detect_package_manager(root)
        for script_name in NODE_SCRIPT_ORDER:
            if script_name in package_scripts:
                append_unique(
                    commands=commands,
                    seen=seen,
                    command=build_node_script_command(package_manager, script_name),
                    reason=f"Run package script '{script_name}'",
                    source="package.json",
                )

        for alias in NODE_SCRIPT_ALIASES:
            if alias in package_scripts:
                append_unique(
                    commands=commands,
                    seen=seen,
                    command=build_node_script_command(package_manager, alias),
                    reason=f"Run package script '{alias}'",
                    source="package.json",
                )

    has_python_project = any(
        [
            (root / "pyproject.toml").exists(),
            (root / "setup.py").exists(),
            (root / "setup.cfg").exists(),
            (root / "requirements.txt").exists(),
            (root / "requirements-dev.txt").exists(),
        ]
    )
    if has_python_project:
        # Lint / format / type checks are added only when the tool actually
        # appears in the project's declared dependencies. A bare `tests/`
        # directory is no longer enough to trigger pytest, since many
        # repositories use unittest-only or non-Python tests under that name.
        if "ruff" in python_context:
            append_unique(
                commands=commands,
                seen=seen,
                command=f"{python_runner}ruff check .",
                reason="Python project references ruff",
                source="pyproject.toml/requirements",
            )
            append_unique(
                commands=commands,
                seen=seen,
                command=f"{python_runner}ruff format --check .",
                reason="Python project references ruff (format check)",
                source="pyproject.toml/requirements",
            )
        if "black" in python_context:
            append_unique(
                commands=commands,
                seen=seen,
                command=f"{python_runner}black --check .",
                reason="Python project references black",
                source="pyproject.toml/requirements",
            )
        if "isort" in python_context:
            append_unique(
                commands=commands,
                seen=seen,
                command=f"{python_runner}isort --check-only .",
                reason="Python project references isort",
                source="pyproject.toml/requirements",
            )
        if "pytest" in python_context:
            append_unique(
                commands=commands,
                seen=seen,
                command=f"{python_runner}pytest",
                reason="Python project references pytest",
                source="pyproject.toml/requirements",
            )
        if "mypy" in python_context:
            append_unique(
                commands=commands,
                seen=seen,
                command=f"{python_runner}mypy .",
                reason="Python project references mypy",
                source="pyproject.toml/requirements",
            )
        if "pyright" in python_context:
            append_unique(
                commands=commands,
                seen=seen,
                command=f"{python_runner}pyright",
                reason="Python project references pyright",
                source="pyproject.toml/requirements",
            )

    if (root / "Cargo.toml").exists():
        append_unique(
            commands=commands,
            seen=seen,
            command="cargo fmt --all --check",
            reason="Rust formatting check",
            source="Cargo.toml",
        )
        append_unique(
            commands=commands,
            seen=seen,
            command="cargo clippy --all-targets --all-features -- -D warnings",
            reason="Rust lint check",
            source="Cargo.toml",
        )
        append_unique(
            commands=commands,
            seen=seen,
            command="cargo test",
            reason="Rust test suite",
            source="Cargo.toml",
        )

    if (root / "go.mod").exists():
        # vet first (fast static check), then the full test suite.
        append_unique(
            commands=commands,
            seen=seen,
            command="go vet ./...",
            reason="Go vet checks",
            source="go.mod",
        )
        append_unique(
            commands=commands,
            seen=seen,
            command="go test ./...",
            reason="Go test suite",
            source="go.mod",
        )

    if (root / "gradlew").exists() or (root / "gradlew.bat").exists():
        gradle_cmd = ".\\gradlew.bat check" if sys.platform.startswith("win") else "./gradlew check"
        append_unique(
            commands=commands,
            seen=seen,
            command=gradle_cmd,
            reason="Gradle check task",
            source="gradlew",
        )
    elif (root / "mvnw").exists() or (root / "mvnw.cmd").exists():
        maven_cmd = ".\\mvnw.cmd -q verify" if sys.platform.startswith("win") else "./mvnw -q verify"
        append_unique(
            commands=commands,
            seen=seen,
            command=maven_cmd,
            reason="Maven verify task",
            source="mvnw",
        )

    if any(root.glob("*.sln")) or any(root.glob("*.csproj")):
        append_unique(
            commands=commands,
            seen=seen,
            command="dotnet build --nologo",
            reason=".NET build check",
            source="solution/project file",
        )
        append_unique(
            commands=commands,
            seen=seen,
            command="dotnet test --nologo",
            reason=".NET test suite",
            source="solution/project file",
        )

    if (root / "deno.json").exists() or (root / "deno.jsonc").exists():
        append_unique(
            commands=commands,
            seen=seen,
            command="deno lint",
            reason="Deno lint",
            source="deno.json",
        )
        append_unique(
            commands=commands,
            seen=seen,
            command="deno test -A",
            reason="Deno test suite",
            source="deno.json",
        )

    if not commands:
        if is_git_repository(root):
            append_unique(
                commands=commands,
                seen=seen,
                command="git diff --check",
                reason="Fallback conflict/whitespace check",
                source="git",
            )
        else:
            append_unique(
                commands=commands,
                seen=seen,
                command="echo No known quality gate commands detected.",
                reason="No project-specific checks detected",
                source="fallback",
            )

    return commands


def run_command(root: Path, entry: GateCommand, max_output_chars: int) -> GateResult:
    completed = subprocess.run(
        entry.command,
        cwd=root,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    status = "passed" if completed.returncode == 0 else "failed"
    return GateResult(
        command=entry.command,
        reason=entry.reason,
        source=entry.source,
        returncode=completed.returncode,
        status=status,
        stdout=truncate_text(completed.stdout or "", max_output_chars),
        stderr=truncate_text(completed.stderr or "", max_output_chars),
    )


def print_discovery(commands: List[GateCommand]) -> None:
    print(f"Detected {len(commands)} quality gate command(s):")
    for index, entry in enumerate(commands, start=1):
        print(f"{index}. {entry.command}")
        print(f"   Reason: {entry.reason} ({entry.source})")


def main() -> int:
    args = parse_args()
    root = Path(args.project_root).resolve()
    if not root.exists():
        print(f"Project root does not exist: {root}", file=sys.stderr)
        return 2

    commands = detect_commands(root)
    if args.discover_only:
        if args.as_json:
            payload = {
                "project_root": str(root),
                "commands": [asdict(item) for item in commands],
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print_discovery(commands)
        return 0

    results: List[GateResult] = []
    for entry in commands:
        result = run_command(root=root, entry=entry, max_output_chars=args.max_output_chars)
        results.append(result)
        if not args.as_json:
            prefix = "[PASS]" if result.status == "passed" else "[FAIL]"
            print(f"{prefix} {entry.command}")
            if result.status != "passed":
                if result.stderr.strip():
                    print(result.stderr.strip())
                elif result.stdout.strip():
                    print(result.stdout.strip())
                print("")
        if result.status != "passed" and args.fail_fast:
            break

    passed = all(item.status == "passed" for item in results) and len(results) > 0
    if args.as_json:
        payload = {
            "project_root": str(root),
            "commands": [asdict(item) for item in commands],
            "results": [asdict(item) for item in results],
            "passed": passed,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Summary: {len(results)} command(s) run, passed={passed}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

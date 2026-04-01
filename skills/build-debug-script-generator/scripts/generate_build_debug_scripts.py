from __future__ import annotations

import argparse
import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path


CHECK_BUCKETS = ("lint", "test", "typecheck")
DEBUG_SCRIPT_NAMES = ("dev", "start:dev", "debug", "serve", "start")
BUILD_SCRIPT_NAMES = ("build", "build:prod", "compile")
MAKE_DEBUG_TARGETS = ("debug", "dev", "run", "start", "serve")


@dataclass
class Candidate:
    bucket: str
    command: str
    source: str
    evidence: list[str]
    score: int

    def to_dict(self) -> dict[str, object]:
        return {
            "command": self.command,
            "source": self.source,
            "evidence": self.evidence,
            "score": self.score,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate build and quick-debug PowerShell scripts from repository signals.")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--json-out")
    parser.add_argument("--markdown-out")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_toml(path: Path) -> dict[str, object]:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def detect_package_managers(project_root: Path) -> list[str]:
    managers: list[str] = []
    if (project_root / "pnpm-lock.yaml").exists():
        managers.append("pnpm")
    if (project_root / "bun.lockb").exists() or (project_root / "bun.lock").exists():
        managers.append("bun")
    if (project_root / "yarn.lock").exists():
        managers.append("yarn")
    if (project_root / "package-lock.json").exists():
        managers.append("npm")
    if (project_root / "package.json").exists() and "npm" not in managers and not any(
        manager in managers for manager in ("pnpm", "bun", "yarn")
    ):
        managers.append("npm")
    if (project_root / "uv.lock").exists():
        managers.append("uv")
    if (project_root / "poetry.lock").exists():
        managers.append("poetry")
    if (project_root / "pyproject.toml").exists() and not any(manager in managers for manager in ("uv", "poetry")):
        managers.append("pip")
    return managers


def choose_js_manager(managers: list[str]) -> str | None:
    for manager in ("pnpm", "bun", "yarn", "npm"):
        if manager in managers:
            return manager
    return None


def choose_python_manager(managers: list[str]) -> str | None:
    for manager in ("uv", "poetry", "pip"):
        if manager in managers:
            return manager
    return None


def render_package_script_command(package_manager: str, script_name: str) -> str:
    if package_manager == "npm":
        return f"npm run {script_name}"
    if package_manager == "bun":
        return f"bun run {script_name}"
    return f"{package_manager} {script_name}"


def wrap_python_command(command: str, python_manager: str, *, purpose: str) -> str:
    if python_manager == "uv":
        return f"uv run {command}"
    if python_manager == "poetry":
        if purpose == "build" and command == "python -m build":
            return "poetry build"
        return f"poetry run {command}"
    return command


def install_command_for(manager: str) -> str | None:
    mapping = {
        "pnpm": "pnpm install --frozen-lockfile",
        "bun": "bun install --frozen-lockfile",
        "yarn": "yarn install --immutable",
        "npm": "npm install",
        "uv": "uv sync",
        "poetry": "poetry install",
        "pip": "python -m pip install -e .",
    }
    return mapping.get(manager)


def parse_make_targets(project_root: Path) -> dict[str, str]:
    makefile = project_root / "Makefile"
    if not makefile.exists():
        return {}
    targets: dict[str, str] = {}
    for raw_line in makefile.read_text(encoding="utf-8").splitlines():
        if raw_line.startswith("\t") or not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        match = re.match(r"^([A-Za-z0-9_.-]+)\s*:(?![=])", raw_line)
        if match:
            targets[match.group(1)] = match.group(1)
    return targets


def extract_ci_run_commands(project_root: Path) -> list[str]:
    commands: list[str] = []
    workflow_root = project_root / ".github" / "workflows"
    if not workflow_root.exists():
        return commands
    for workflow in sorted(workflow_root.glob("*.y*ml")):
        for raw_line in workflow.read_text(encoding="utf-8").splitlines():
            match = re.match(r"^\s*-\s*run:\s*(.+?)\s*$", raw_line)
            if match:
                commands.append(match.group(1).strip())
    return commands


def add_candidate(candidates: dict[str, list[Candidate]], candidate: Candidate) -> None:
    candidates.setdefault(candidate.bucket, []).append(candidate)


def classify_ci_bucket(command: str) -> str | None:
    normalized = command.lower()
    if any(token in normalized for token in (" runserver", " uvicorn ", "--reload", " debugpy ", " pnpm dev", " npm run dev", " yarn dev", " bun run dev", " make debug", " make dev")):
        return "debug"
    if " build" in normalized or normalized.startswith("build ") or normalized.endswith(" build") or "vite build" in normalized or "next build" in normalized:
        return "build"
    if any(token in normalized for token in (" lint", "eslint", "ruff check")):
        return "lint"
    if any(token in normalized for token in (" typecheck", "tsc", "mypy")):
        return "typecheck"
    if any(token in normalized for token in (" pytest", " vitest", " unittest", " test")):
        return "test"
    return None


def build_candidates(project_root: Path) -> tuple[list[str], dict[str, list[Candidate]], list[str], list[str]]:
    managers = detect_package_managers(project_root)
    js_manager = choose_js_manager(managers)
    python_manager = choose_python_manager(managers)
    candidates: dict[str, list[Candidate]] = {}
    assumptions: list[str] = []
    blockers: list[str] = []

    package_json_path = project_root / "package.json"
    if package_json_path.exists():
        package_json = read_json(package_json_path)
        scripts = package_json.get("scripts", {})
        if isinstance(scripts, dict) and js_manager:
            install_command = install_command_for(js_manager)
            if install_command:
                add_candidate(
                    candidates,
                    Candidate(
                        bucket="install",
                        command=install_command,
                        source="package-manager",
                        evidence=[f"detected {js_manager} for package.json at repository root"],
                        score=95,
                    ),
                )
            for script_name in BUILD_SCRIPT_NAMES:
                if script_name in scripts:
                    add_candidate(
                        candidates,
                        Candidate(
                            bucket="build",
                            command=render_package_script_command(js_manager, script_name),
                            source="package.json:scripts",
                            evidence=[f"package.json scripts.{script_name}"],
                            score=92,
                        ),
                    )
                    break
            for script_name in DEBUG_SCRIPT_NAMES:
                if script_name in scripts:
                    add_candidate(
                        candidates,
                        Candidate(
                            bucket="debug",
                            command=render_package_script_command(js_manager, script_name),
                            source="package.json:scripts",
                            evidence=[f"package.json scripts.{script_name}"],
                            score=91,
                        ),
                    )
                    break
            for bucket in CHECK_BUCKETS:
                if bucket in scripts:
                    add_candidate(
                        candidates,
                        Candidate(
                            bucket=bucket,
                            command=render_package_script_command(js_manager, bucket),
                            source="package.json:scripts",
                            evidence=[f"package.json scripts.{bucket}"],
                            score=88,
                        ),
                    )
                elif bucket == "typecheck" and "check-types" in scripts:
                    add_candidate(
                        candidates,
                        Candidate(
                            bucket=bucket,
                            command=render_package_script_command(js_manager, "check-types"),
                            source="package.json:scripts",
                            evidence=["package.json scripts.check-types"],
                            score=87,
                        ),
                    )
            assumptions.append("Assumed the root package.json owns the main build and debug entrypoints.")

    pyproject_path = project_root / "pyproject.toml"
    if pyproject_path.exists():
        pyproject = read_toml(pyproject_path)
        tool_section = pyproject.get("tool", {}) if isinstance(pyproject, dict) else {}
        project_section = pyproject.get("project", {}) if isinstance(pyproject, dict) else {}
        dependencies = [str(item).lower() for item in project_section.get("dependencies", [])] if isinstance(project_section, dict) else []
        if python_manager:
            install_command = install_command_for(python_manager)
            if install_command:
                add_candidate(
                    candidates,
                    Candidate(
                        bucket="install",
                        command=install_command,
                        source="python-manager",
                        evidence=[f"detected {python_manager} for pyproject at repository root"],
                        score=90,
                    ),
                )
            if "build-system" in pyproject:
                add_candidate(
                    candidates,
                    Candidate(
                        bucket="build",
                        command=wrap_python_command("python -m build", python_manager, purpose="build"),
                        source="pyproject.toml",
                        evidence=["pyproject.toml contains [build-system]"],
                        score=85,
                    ),
                )
            if isinstance(tool_section, dict) and "pytest" in tool_section:
                add_candidate(
                    candidates,
                    Candidate(
                        bucket="test",
                        command=wrap_python_command("python -m pytest", python_manager, purpose="test"),
                        source="pyproject.toml",
                        evidence=["pyproject.toml contains [tool.pytest]"],
                        score=82,
                    ),
                )
            if isinstance(tool_section, dict) and "ruff" in tool_section:
                add_candidate(
                    candidates,
                    Candidate(
                        bucket="lint",
                        command=wrap_python_command("python -m ruff check .", python_manager, purpose="lint"),
                        source="pyproject.toml",
                        evidence=["pyproject.toml contains [tool.ruff]"],
                        score=82,
                    ),
                )
            if isinstance(tool_section, dict) and "mypy" in tool_section:
                add_candidate(
                    candidates,
                    Candidate(
                        bucket="typecheck",
                        command=wrap_python_command("python -m mypy .", python_manager, purpose="typecheck"),
                        source="pyproject.toml",
                        evidence=["pyproject.toml contains [tool.mypy]"],
                        score=82,
                    ),
                )
            if (project_root / "manage.py").exists():
                add_candidate(
                    candidates,
                    Candidate(
                        bucket="debug",
                        command=wrap_python_command("python manage.py runserver", python_manager, purpose="debug"),
                        source="entrypoint",
                        evidence=["manage.py detected at repository root"],
                        score=89,
                    ),
                )
            elif any("fastapi" in item or "uvicorn" in item for item in dependencies):
                if (project_root / "app.py").exists():
                    add_candidate(
                        candidates,
                        Candidate(
                            bucket="debug",
                            command=wrap_python_command("uvicorn app:app --reload", python_manager, purpose="debug"),
                            source="entrypoint",
                            evidence=["FastAPI-style dependencies detected and app.py exists"],
                            score=88,
                        ),
                    )
                elif (project_root / "main.py").exists():
                    add_candidate(
                        candidates,
                        Candidate(
                            bucket="debug",
                            command=wrap_python_command("uvicorn main:app --reload", python_manager, purpose="debug"),
                            source="entrypoint",
                            evidence=["FastAPI-style dependencies detected and main.py exists"],
                            score=87,
                        ),
                    )
            elif (project_root / "main.py").exists():
                add_candidate(
                    candidates,
                    Candidate(
                        bucket="debug",
                        command=wrap_python_command("python main.py", python_manager, purpose="debug"),
                        source="entrypoint",
                        evidence=["main.py detected at repository root"],
                        score=80,
                    ),
                )
            elif (project_root / "app.py").exists():
                add_candidate(
                    candidates,
                    Candidate(
                        bucket="debug",
                        command=wrap_python_command("python app.py", python_manager, purpose="debug"),
                        source="entrypoint",
                        evidence=["app.py detected at repository root"],
                        score=79,
                    ),
                )
            assumptions.append("Assumed the root pyproject and entrypoint files describe the main Python surface.")

    make_targets = parse_make_targets(project_root)
    if "build" in make_targets:
        add_candidate(
            candidates,
            Candidate(
                bucket="build",
                command="make build",
                source="Makefile",
                evidence=["Makefile target: build"],
                score=78,
            ),
        )
    for target_name in MAKE_DEBUG_TARGETS:
        if target_name in make_targets:
            add_candidate(
                candidates,
                Candidate(
                    bucket="debug",
                    command=f"make {target_name}",
                    source="Makefile",
                    evidence=[f"Makefile target: {target_name}"],
                    score=77,
                ),
            )
            break
    if "lint" in make_targets:
        add_candidate(
            candidates,
            Candidate(
                bucket="lint",
                command="make lint",
                source="Makefile",
                evidence=["Makefile target: lint"],
                score=76,
            ),
        )
    if "test" in make_targets:
        add_candidate(
            candidates,
            Candidate(
                bucket="test",
                command="make test",
                source="Makefile",
                evidence=["Makefile target: test"],
                score=76,
            ),
        )
    if "typecheck" in make_targets:
        add_candidate(
            candidates,
            Candidate(
                bucket="typecheck",
                command="make typecheck",
                source="Makefile",
                evidence=["Makefile target: typecheck"],
                score=76,
            ),
        )

    for ci_command in extract_ci_run_commands(project_root):
        bucket = classify_ci_bucket(ci_command)
        if not bucket:
            continue
        score = 72 if bucket in ("build", "debug") else 70
        add_candidate(
            candidates,
            Candidate(
                bucket=bucket,
                command=ci_command,
                source="github-actions",
                evidence=[f"workflow run step: {ci_command}"],
                score=score,
            ),
        )

    if "build" not in candidates:
        blockers.append("No credible build command was found from package scripts, pyproject, Makefile, or CI.")
    if "debug" not in candidates:
        blockers.append("No credible quick-debug command was found from package scripts, entrypoints, Makefile, or CI.")
    if "install" not in candidates:
        assumptions.append("No install command was selected; generated scripts will skip dependency bootstrap by default.")
    return managers, candidates, assumptions, blockers


def select_best(candidates: list[Candidate]) -> Candidate | None:
    if not candidates:
        return None
    ordered = sorted(candidates, key=lambda item: (-item.score, item.command))
    return ordered[0]


def escape_ps(value: str) -> str:
    return '"' + value.replace("`", "``").replace('"', '`"') + '"'


def render_build_script(install: Candidate | None, build: Candidate | None, checks: list[Candidate], blockers: list[str]) -> str:
    blocker_lines = ["# Blockers detected during generation:"] + [f"# - {item}" for item in blockers] if blockers else ["# No blockers detected during generation."]
    check_lines: list[str] = []
    if checks:
        for candidate in checks:
            check_lines.append(f"    Invoke-RepositoryCommand {escape_ps(candidate.command)}")
    else:
        check_lines.append('    Write-Host "No optional checks were selected." -ForegroundColor DarkYellow')
    build_lines = [f"  Invoke-RepositoryCommand {escape_ps(build.command)}"] if build else ['  Write-Error "No build command was selected for this repository."', "  exit 1"]
    lines = [
        "Set-StrictMode -Version Latest",
        '$ErrorActionPreference = "Stop"',
        "",
        "param(",
        "  [switch]$SkipInstall,",
        "  [switch]$IncludeChecks",
        ")",
        "",
        *blocker_lines,
        "",
        '$ProjectRoot = Split-Path -Parent $PSScriptRoot',
        "Push-Location $ProjectRoot",
        "try {",
        "  function Invoke-RepositoryCommand {",
        "    param([string]$Command)",
        '    Write-Host \"==> $Command\" -ForegroundColor Cyan',
        "    & $env:ComSpec /d /s /c $Command",
        "    if ($LASTEXITCODE -ne 0) {",
        '      throw \"Command failed with exit code ${LASTEXITCODE}: $Command\"',
        "    }",
        "  }",
        "",
        f"  $InstallCommand = {escape_ps(install.command) if install else '$null'}",
        "",
        "  if (-not $SkipInstall -and $InstallCommand) {",
        "    Invoke-RepositoryCommand $InstallCommand",
        "  }",
        "",
        "  if ($IncludeChecks) {",
        *check_lines,
        "  }",
        "",
        *build_lines,
        "}",
        "finally {",
        "  Pop-Location",
        "}",
        "",
    ]
    return "\n".join(lines)


def render_debug_script(install: Candidate | None, debug: Candidate | None, blockers: list[str]) -> str:
    blocker_lines = ["# Blockers detected during generation:"] + [f"# - {item}" for item in blockers] if blockers else ["# No blockers detected during generation."]
    debug_lines = [f"  Invoke-RepositoryCommand {escape_ps(debug.command)}"] if debug else ['  Write-Error "No quick-debug command was selected for this repository."', "  exit 1"]
    lines = [
        "Set-StrictMode -Version Latest",
        '$ErrorActionPreference = "Stop"',
        "",
        "param(",
        "  [switch]$SkipInstall",
        ")",
        "",
        *blocker_lines,
        "",
        '$ProjectRoot = Split-Path -Parent $PSScriptRoot',
        "Push-Location $ProjectRoot",
        "try {",
        "  function Invoke-RepositoryCommand {",
        "    param([string]$Command)",
        '    Write-Host \"==> $Command\" -ForegroundColor Cyan',
        "    & $env:ComSpec /d /s /c $Command",
        "    if ($LASTEXITCODE -ne 0) {",
        '      throw \"Command failed with exit code ${LASTEXITCODE}: $Command\"',
        "    }",
        "  }",
        "",
        f"  $InstallCommand = {escape_ps(install.command) if install else '$null'}",
        "",
        "  if (-not $SkipInstall -and $InstallCommand) {",
        "    Invoke-RepositoryCommand $InstallCommand",
        "  }",
        "",
        *debug_lines,
        "}",
        "finally {",
        "  Pop-Location",
        "}",
        "",
    ]
    return "\n".join(lines)


def render_markdown(payload: dict[str, object]) -> str:
    selected = payload["selected_commands"]
    checks = payload["optional_checks"]
    blockers = payload["blockers"]
    assumptions = payload["assumptions"]
    generated = payload["generated_files"]
    lines = [
        "# Build Debug Bundle",
        "",
        "## Project Profile",
        f"- Project root: `{payload['project_root']}`",
        f"- Package managers: {', '.join(payload['package_managers']) or '(none)'}",
        "",
        "## Selected Commands",
        f"- Install: `{selected['install']['command']}`" if selected["install"] else "- Install: `(none)`",
        f"- Build: `{selected['build']['command']}`" if selected["build"] else "- Build: `(none)`",
        f"- Debug: `{selected['debug']['command']}`" if selected["debug"] else "- Debug: `(none)`",
        "",
        "## Optional Checks",
    ]
    if checks:
        for check in checks:
            lines.append(f"- `{check['bucket']}`: `{check['command']}`")
    else:
        lines.append("- None.")
    lines.extend(["", "## Blockers"])
    if blockers:
        for blocker in blockers:
            lines.append(f"- {blocker}")
    else:
        lines.append("- None.")
    lines.extend(["", "## Assumptions"])
    if assumptions:
        for assumption in assumptions:
            lines.append(f"- {assumption}")
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Generated Files",
            f"- Build script: `{generated['build_script']}`",
            f"- Debug script: `{generated['debug_script']}`",
            f"- JSON bundle: `{generated['json_bundle']}`",
            f"- Markdown bundle: `{generated['markdown_bundle']}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(project_root: Path, output_dir: Path, json_path: Path, markdown_path: Path) -> dict[str, object]:
    package_managers, candidates, assumptions, blockers = build_candidates(project_root)
    install = select_best(candidates.get("install", []))
    build = select_best(candidates.get("build", []))
    debug = select_best(candidates.get("debug", []))
    checks: list[dict[str, object]] = []
    selected_checks: list[Candidate] = []
    for bucket in CHECK_BUCKETS:
        candidate = select_best(candidates.get(bucket, []))
        if candidate:
            selected_checks.append(candidate)
            check_payload = candidate.to_dict()
            check_payload["bucket"] = bucket
            checks.append(check_payload)

    output_dir.mkdir(parents=True, exist_ok=True)
    build_script_path = output_dir / "build.ps1"
    debug_script_path = output_dir / "debug.ps1"

    build_script_path.write_text(render_build_script(install, build, selected_checks, blockers), encoding="utf-8")
    debug_script_path.write_text(render_debug_script(install, debug, blockers), encoding="utf-8")

    payload = {
        "project_root": str(project_root),
        "package_managers": package_managers,
        "selected_commands": {
            "install": install.to_dict() if install else None,
            "build": build.to_dict() if build else None,
            "debug": debug.to_dict() if debug else None,
        },
        "optional_checks": checks,
        "assumptions": assumptions,
        "blockers": blockers,
        "generated_files": {
            "build_script": str(build_script_path),
            "debug_script": str(debug_script_path),
            "json_bundle": str(json_path),
            "markdown_bundle": str(markdown_path),
        },
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    json_path = Path(args.json_out).resolve() if args.json_out else output_dir / "build-debug-bundle.json"
    markdown_path = Path(args.markdown_out).resolve() if args.markdown_out else output_dir / "build-debug-bundle.md"
    payload = write_outputs(project_root, output_dir, json_path, markdown_path)
    print(f"JSON_OUT={payload['generated_files']['json_bundle']}")
    print(f"MARKDOWN_OUT={payload['generated_files']['markdown_bundle']}")
    print(f"BUILD_SCRIPT={payload['generated_files']['build_script']}")
    print(f"DEBUG_SCRIPT={payload['generated_files']['debug_script']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

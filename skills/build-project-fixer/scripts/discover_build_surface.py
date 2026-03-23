#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path


CATEGORIES = ("install", "build", "test", "lint", "typecheck", "verify")
NODE_LOCKFILES = (
    ("pnpm-lock.yaml", "pnpm"),
    ("package-lock.json", "npm"),
    ("yarn.lock", "yarn"),
    ("bun.lockb", "bun"),
    ("bun.lock", "bun"),
)
PYTHON_LOCKFILES = (
    ("uv.lock", "uv"),
    ("poetry.lock", "poetry"),
)
SCRIPT_CATEGORY_HINTS = {
    "build": "build",
    "compile": "build",
    "bundle": "build",
    "test": "test",
    "lint": "lint",
    "fmt": "lint",
    "format": "lint",
    "typecheck": "typecheck",
    "type-check": "typecheck",
    "check-types": "typecheck",
    "mypy": "typecheck",
    "pyright": "typecheck",
    "verify": "verify",
    "check": "verify",
    "ci": "verify",
}
COMMAND_KEYWORDS = {
    "test": ("pytest", "vitest", "jest", "unittest", "cargo test", "pnpm test", "npm test", "yarn test"),
    "lint": ("eslint", "ruff", "flake8", "golangci-lint", "pnpm lint", "npm run lint", "yarn lint"),
    "typecheck": ("mypy", "pyright", "tsc --noemit", "typecheck", "cargo check"),
    "build": (" build", "vite build", "next build", "cargo build", "python -m build", "tsc -b", "tsc --build"),
    "verify": ("check", "verify", "ci", "validate"),
}


@dataclass
class CommandCandidate:
    command: str
    source: str
    evidence: str
    priority: int


class DiscoveryState:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.package_managers: list[str] = []
        self.manifests: list[dict[str, str]] = []
        self.commands: dict[str, dict[str, CommandCandidate]] = {category: {} for category in CATEGORIES}
        self.risks: set[str] = set()

    def add_manifest(self, path: Path, kind: str) -> None:
        self.manifests.append({"path": relative_to_root(path, self.root), "kind": kind})

    def add_package_manager(self, manager: str) -> None:
        if manager not in self.package_managers:
            self.package_managers.append(manager)

    def add_command(
        self,
        category: str,
        command: str,
        source: str,
        evidence: str,
        priority: int,
    ) -> None:
        if category not in CATEGORIES:
            return
        current = self.commands[category].get(command)
        candidate = CommandCandidate(
            command=command,
            source=source,
            evidence=evidence,
            priority=priority,
        )
        if current is None or candidate.priority > current.priority:
            self.commands[category][command] = candidate


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect a repository and suggest likely build and validation commands."
    )
    parser.add_argument("--project-root", default=".")
    parser.add_argument(
        "--category",
        choices=(*CATEGORIES, "all"),
        default="all",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args(argv)


def relative_to_root(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def infer_node_package_manager(root: Path, package_data: dict[str, object]) -> list[str]:
    detected: list[str] = []
    package_manager_field = package_data.get("packageManager")
    if isinstance(package_manager_field, str):
        name = package_manager_field.split("@", 1)[0].strip()
        if name:
            detected.append(name)
    for filename, manager in NODE_LOCKFILES:
        if (root / filename).exists() and manager not in detected:
            detected.append(manager)
    if (root / "package.json").exists() and "npm" not in detected and not detected:
        detected.append("npm")
    return detected


def infer_python_manager(root: Path) -> list[str]:
    detected: list[str] = []
    for filename, manager in PYTHON_LOCKFILES:
        if (root / filename).exists():
            detected.append(manager)
    return detected


def node_script_command(manager: str, script_name: str) -> str:
    if manager == "pnpm":
        return f"pnpm {script_name}"
    if manager == "yarn":
        return f"yarn {script_name}"
    if manager == "bun":
        return f"bun run {script_name}"
    return f"npm run {script_name}"


def install_command_for_manager(manager: str, has_lockfile: bool) -> str | None:
    if manager == "pnpm":
        return "pnpm install --frozen-lockfile" if has_lockfile else "pnpm install"
    if manager == "npm":
        return "npm ci" if has_lockfile else "npm install"
    if manager == "yarn":
        return "yarn install --immutable" if has_lockfile else "yarn install"
    if manager == "bun":
        return "bun install"
    if manager == "uv":
        return "uv sync"
    if manager == "poetry":
        return "poetry install"
    return None


def classify_script_name(name: str) -> str | None:
    lowered = name.lower()
    if lowered in SCRIPT_CATEGORY_HINTS:
        return SCRIPT_CATEGORY_HINTS[lowered]
    for hint, category in SCRIPT_CATEGORY_HINTS.items():
        if hint in lowered:
            return category
    return None


def classify_command_text(command: str) -> str | None:
    lowered = f" {command.lower()} "
    for category, keywords in COMMAND_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return category
    return None


def discover_package_json(root: Path, state: DiscoveryState) -> None:
    package_json = root / "package.json"
    if not package_json.exists():
        return

    data = json.loads(package_json.read_text(encoding="utf-8"))
    state.add_manifest(package_json, "package.json")
    managers = infer_node_package_manager(root, data if isinstance(data, dict) else {})
    for manager in managers:
        state.add_package_manager(manager)

    has_lockfile = any((root / filename).exists() for filename, _ in NODE_LOCKFILES)
    if managers:
        install_command = install_command_for_manager(managers[0], has_lockfile)
        if install_command:
            state.add_command(
                category="install",
                command=install_command,
                source="package.json",
                evidence="Node package manager inferred from package.json and lockfiles.",
                priority=85,
            )

    scripts = data.get("scripts", {}) if isinstance(data, dict) else {}
    if isinstance(scripts, dict):
        primary_manager = managers[0] if managers else "npm"
        for script_name, script_body in scripts.items():
            if not isinstance(script_body, str):
                continue
            category = classify_script_name(script_name)
            if not category:
                continue
            state.add_command(
                category=category,
                command=node_script_command(primary_manager, script_name),
                source="package.json",
                evidence=f"package.json script '{script_name}' -> {script_body}",
                priority=80,
            )

    if isinstance(data, dict) and any(key in data for key in ("workspaces", "pnpm", "turbo")):
        state.risks.add("Workspace or monorepo signals detected; verify package scope before running commands.")
    if (root / "pnpm-workspace.yaml").exists() or (root / "turbo.json").exists() or (root / "nx.json").exists():
        state.risks.add("Workspace or monorepo signals detected; verify package scope before running commands.")


def discover_pyproject(root: Path, state: DiscoveryState) -> None:
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return

    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    state.add_manifest(pyproject, "pyproject.toml")
    for manager in infer_python_manager(root):
        state.add_package_manager(manager)

    install_candidates = infer_python_manager(root)
    if install_candidates:
        install_command = install_command_for_manager(install_candidates[0], has_lockfile=True)
        if install_command:
            state.add_command(
                category="install",
                command=install_command,
                source="pyproject.toml",
                evidence=f"Python environment manager inferred from {install_candidates[0]} lockfile.",
                priority=75,
            )

    tool = data.get("tool", {}) if isinstance(data, dict) else {}
    if not isinstance(tool, dict):
        tool = {}
    if "pytest" in tool or root.joinpath("tests").exists():
        state.add_command(
            category="test",
            command="python -m pytest",
            source="pyproject.toml",
            evidence="pytest configuration or tests directory detected.",
            priority=60,
        )
    if "ruff" in tool or (root / "ruff.toml").exists():
        state.add_command(
            category="lint",
            command="python -m ruff check .",
            source="pyproject.toml",
            evidence="ruff configuration detected.",
            priority=60,
        )
    if "mypy" in tool:
        state.add_command(
            category="typecheck",
            command="python -m mypy .",
            source="pyproject.toml",
            evidence="mypy configuration detected.",
            priority=60,
        )
    if "pyright" in tool:
        state.add_command(
            category="typecheck",
            command="pyright",
            source="pyproject.toml",
            evidence="pyright configuration detected.",
            priority=59,
        )
    if "build-system" in data or "project" in data:
        state.add_command(
            category="build",
            command="python -m build",
            source="pyproject.toml",
            evidence="pyproject.toml declares a buildable Python project.",
            priority=50,
        )


def discover_cargo(root: Path, state: DiscoveryState) -> None:
    cargo_toml = root / "Cargo.toml"
    if not cargo_toml.exists():
        return
    state.add_manifest(cargo_toml, "Cargo.toml")
    state.add_package_manager("cargo")
    state.add_command(
        category="build",
        command="cargo build",
        source="Cargo.toml",
        evidence="Cargo manifest detected.",
        priority=55,
    )
    state.add_command(
        category="test",
        command="cargo test",
        source="Cargo.toml",
        evidence="Cargo manifest detected.",
        priority=55,
    )
    state.add_command(
        category="verify",
        command="cargo check",
        source="Cargo.toml",
        evidence="Cargo manifest detected.",
        priority=54,
    )


def classify_make_target(target: str) -> str | None:
    return classify_script_name(target)


def discover_makefile(root: Path, state: DiscoveryState) -> None:
    makefile = root / "Makefile"
    if not makefile.exists():
        return
    state.add_manifest(makefile, "Makefile")
    pattern = re.compile(r"^([A-Za-z0-9_.-]+):(?:\s|$)")
    for line in makefile.read_text(encoding="utf-8").splitlines():
        if line.startswith("\t") or not line or line.lstrip().startswith("#") or "=" in line.split(":", 1)[0]:
            continue
        match = pattern.match(line)
        if not match:
            continue
        target = match.group(1)
        category = classify_make_target(target)
        if not category:
            continue
        state.add_command(
            category=category,
            command=f"make {target}",
            source="Makefile",
            evidence=f"Makefile target '{target}' detected.",
            priority=70,
        )


def extract_ci_commands(root: Path, state: DiscoveryState) -> None:
    workflow_dir = root / ".github" / "workflows"
    if not workflow_dir.exists():
        return

    for workflow_path in sorted(workflow_dir.glob("*.y*ml")):
        state.add_manifest(workflow_path, "github-actions-workflow")
        for raw_line in workflow_path.read_text(encoding="utf-8").splitlines():
            stripped = raw_line.strip()
            if not stripped.startswith("- run:") and not stripped.startswith("run:"):
                continue
            command = stripped.split(":", 1)[1].strip().strip("'\"")
            category = classify_command_text(command)
            if not category:
                continue
            state.add_command(
                category=category,
                command=command,
                source=relative_to_root(workflow_path, root),
                evidence=f"GitHub Actions run step in {workflow_path.name}.",
                priority=100,
            )


def finalize_payload(state: DiscoveryState, category: str) -> dict[str, object]:
    if len(state.package_managers) > 1:
        state.risks.add("Multiple package managers detected; verify the intended toolchain before installing dependencies.")

    if category == "all":
        command_categories = CATEGORIES
    else:
        command_categories = (category,)

    commands: dict[str, list[dict[str, object]]] = {}
    for command_category in command_categories:
        ranked = sorted(
            (asdict(candidate) for candidate in state.commands[command_category].values()),
            key=lambda item: (-int(item["priority"]), str(item["command"])),
        )
        if ranked:
            commands[command_category] = ranked

    if not commands:
        state.risks.add("No obvious build or validation commands were discovered; manual inspection is required.")

    return {
        "project_root": str(state.root),
        "package_managers": state.package_managers,
        "manifests": state.manifests,
        "commands": commands,
        "risks": sorted(state.risks),
    }


def inspect_repository(root: Path, category: str) -> dict[str, object]:
    state = DiscoveryState(root=root)
    discover_package_json(root, state)
    discover_pyproject(root, state)
    discover_cargo(root, state)
    discover_makefile(root, state)
    extract_ci_commands(root, state)
    return finalize_payload(state, category)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.project_root).resolve()
    payload = inspect_repository(root=root, category=args.category)

    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Project root: {payload['project_root']}")
        for category, commands in payload["commands"].items():
            print(f"{category}:")
            for command in commands:
                print(f"  - {command['command']} ({command['source']})")
        if payload["risks"]:
            print("risks:")
            for risk in payload["risks"]:
                print(f"  - {risk}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

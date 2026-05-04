#!/usr/bin/env python3
"""Inspect repository commit-check tooling and recommend a setup.

Pure standard-library script. Compatible with CPython 3.8+ and runnable as:

    python scripts/detect_commit_setup.py --project-root . --json

No third-party dependencies are required. ``uv run --python 3.11 ...`` works
too, but is not necessary.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect repository commit-check tooling and recommend a setup."
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Starting path used to inspect the repository.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit structured JSON output.",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=8,
        help="Maximum parent levels to inspect while locating the repository root.",
    )
    return parser.parse_args(argv)


@dataclass(frozen=True)
class Recommendation:
    recommendation: str
    recommended_tool: str
    supporting_tools: list[str]
    reasons: list[str]
    next_steps: list[str]


# Filename groups used by detection. Centralised here so tests and references
# stay in sync with the script.
LEFTHOOK_FILES = (
    "lefthook.yml",
    "lefthook.yaml",
    "lefthook.toml",
    ".lefthook.yml",
    ".lefthook.yaml",
    ".lefthook.toml",
)

WORKSPACE_MARKERS = (
    "pnpm-workspace.yaml",
    "pnpm-workspace.yml",
    "turbo.json",
    "nx.json",
    "lerna.json",
    "rush.json",
)

NODE_LOCKFILES = (
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lock",
    "bun.lockb",
)

PYTHON_MARKERS = (
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "requirements-dev.txt",
    "dev-requirements.txt",
    "Pipfile",
    "poetry.lock",
    "uv.lock",
)

COMMITLINT_FILES = (
    ".commitlintrc",
    ".commitlintrc.json",
    ".commitlintrc.yml",
    ".commitlintrc.yaml",
    ".commitlintrc.js",
    ".commitlintrc.cjs",
    ".commitlintrc.mjs",
    ".commitlintrc.ts",
    "commitlint.config.js",
    "commitlint.config.cjs",
    "commitlint.config.mjs",
    "commitlint.config.ts",
)


def read_text_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="ignore")


def load_package_json(root: Path) -> dict[str, Any]:
    package_json = root / "package.json"
    if not package_json.exists():
        return {}
    try:
        payload = json.loads(read_text_if_exists(package_json))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_pyproject_text(root: Path) -> str:
    return read_text_if_exists(root / "pyproject.toml")


def find_repository_root(start: Path, max_depth: int) -> Path:
    """Walk upward from ``start`` to locate a real repository root.

    Priority:
      1. A directory containing ``.git`` (file or dir — git worktrees use a
         file).
      2. A directory containing a recognised workspace marker
         (pnpm-workspace, turbo.json, nx.json, lerna.json, rush.json).
      3. Fall back to ``start`` itself.
    """
    current = start if start.is_dir() else start.parent
    current = current.resolve()
    workspace_candidate: Path | None = None
    for _ in range(max_depth + 1):
        if (current / ".git").exists():
            return current
        if workspace_candidate is None and any(
            (current / marker).exists() for marker in WORKSPACE_MARKERS
        ):
            workspace_candidate = current
        if current.parent == current:
            break
        current = current.parent
    if workspace_candidate is not None:
        return workspace_candidate
    return start.resolve() if start.is_dir() else start.parent.resolve()


def is_node_project(root: Path, package_json: dict[str, Any]) -> bool:
    if package_json:
        return True
    return any((root / marker).exists() for marker in NODE_LOCKFILES)


def is_python_project(root: Path) -> bool:
    return any((root / marker).exists() for marker in PYTHON_MARKERS)


def classify_project(root: Path, package_json: dict[str, Any]) -> str:
    node = is_node_project(root, package_json)
    python = is_python_project(root)
    if node and python:
        return "mixed"
    if node:
        return "node"
    if python:
        return "python"
    return "unknown"


def has_package_tool(package_json: dict[str, Any], tool_name: str) -> bool:
    for section in (
        "dependencies",
        "devDependencies",
        "peerDependencies",
        "optionalDependencies",
    ):
        value = package_json.get(section, {})
        if isinstance(value, dict) and tool_name in value:
            return True
    return False


def pyproject_declares(pyproject_text: str, package_name: str) -> bool:
    """Cheap textual check for a Python package declared in pyproject.toml.

    Avoids a TOML parser dependency. False positives are tolerable here — we
    only use this signal to *increase* confidence about partially-installed
    tooling, never as the sole basis for a destructive change.
    """
    if not pyproject_text:
        return False
    needle = f'"{package_name}"'
    alt = f"'{package_name}'"
    bare = f"\n{package_name} ="
    return needle in pyproject_text or alt in pyproject_text or bare in pyproject_text


@dataclass
class Detection:
    tools: list[str] = field(default_factory=list)
    evidence: dict[str, list[str]] = field(default_factory=dict)

    def add(self, tool: str, where: str) -> None:
        if tool not in self.tools:
            self.tools.append(tool)
            self.evidence[tool] = []
        if where not in self.evidence[tool]:
            self.evidence[tool].append(where)


def detect_existing_tools(
    root: Path,
    package_json: dict[str, Any],
    pyproject_text: str,
) -> tuple[list[str], dict[str, list[str]]]:
    detection = Detection()

    # Primary hook-runner config files.
    if (root / ".pre-commit-config.yaml").exists():
        detection.add("pre-commit", ".pre-commit-config.yaml")
    if (root / ".pre-commit-config.yml").exists():
        detection.add("pre-commit", ".pre-commit-config.yml")
    if (root / ".husky").is_dir():
        detection.add("husky", ".husky/")
    for filename in LEFTHOOK_FILES:
        if (root / filename).exists():
            detection.add("lefthook", filename)

    # Hook runners declared but not yet initialised. These count as evidence
    # the team picked the tool, even if config files are missing.
    if has_package_tool(package_json, "husky"):
        detection.add("husky", "package.json devDependencies")
    if has_package_tool(package_json, "lefthook"):
        detection.add("lefthook", "package.json devDependencies")
    if has_package_tool(package_json, "simple-git-hooks"):
        detection.add("simple-git-hooks", "package.json devDependencies")
    if pyproject_declares(pyproject_text, "pre-commit"):
        detection.add("pre-commit", "pyproject.toml")

    # simple-git-hooks config in package.json.
    if isinstance(package_json.get("simple-git-hooks"), dict):
        detection.add("simple-git-hooks", "package.json (simple-git-hooks key)")

    # Supporting tools.
    lint_staged_present = "lint-staged" in package_json or has_package_tool(
        package_json, "lint-staged"
    )
    if lint_staged_present:
        detection.add("lint-staged", "package.json")

    commitlint_present = any(
        (root / item).exists() for item in COMMITLINT_FILES
    ) or has_package_tool(package_json, "@commitlint/cli")
    if commitlint_present:
        where = (
            "package.json devDependencies"
            if has_package_tool(package_json, "@commitlint/cli")
            else "commitlint config file"
        )
        detection.add("commitlint", where)

    return detection.tools, detection.evidence


# Order matters: the first match wins as the "primary" hook system.
PRIMARY_TOOLS = ("pre-commit", "husky", "lefthook", "simple-git-hooks")


def choose_existing_primary(existing_tools: list[str]) -> str:
    for tool in PRIMARY_TOOLS:
        if tool in existing_tools:
            return tool
    return ""


def recommend_setup(project_type: str, existing_tools: list[str]) -> Recommendation:
    primary = choose_existing_primary(existing_tools)
    if primary == "husky":
        return Recommendation(
            recommendation="preserve-existing",
            recommended_tool="husky",
            supporting_tools=["lint-staged"] if project_type in {"node", "mixed"} else [],
            reasons=["Repository already uses husky; preserve the current hook system."],
            next_steps=[
                "Keep husky as the primary hook tool.",
                "Add only the missing hook files or package-level support such as lint-staged or commitlint.",
            ],
        )
    if primary == "pre-commit":
        return Recommendation(
            recommendation="preserve-existing",
            recommended_tool="pre-commit",
            supporting_tools=[],
            reasons=["Repository already uses pre-commit; extend the existing hook file instead of migrating."],
            next_steps=[
                "Keep .pre-commit-config.yaml as the top-level hook entry point.",
                "Add missing repos or hooks inside the existing pre-commit configuration.",
            ],
        )
    if primary == "lefthook":
        return Recommendation(
            recommendation="preserve-existing",
            recommended_tool="lefthook",
            supporting_tools=[],
            reasons=["Repository already uses lefthook; preserve the chosen hook system."],
            next_steps=[
                "Keep lefthook as the primary hook tool.",
                "Add missing commands inside the existing lefthook config instead of introducing husky or pre-commit.",
            ],
        )
    if primary == "simple-git-hooks":
        return Recommendation(
            recommendation="preserve-existing",
            recommended_tool="simple-git-hooks",
            supporting_tools=["lint-staged"] if project_type in {"node", "mixed"} else [],
            reasons=["Repository already uses simple-git-hooks; preserve the chosen hook system."],
            next_steps=[
                "Keep the simple-git-hooks key in package.json as the entry point.",
                "Add missing hook commands there; do not layer husky or pre-commit on top.",
            ],
        )

    if "lint-staged" in existing_tools and project_type in {"node", "mixed"}:
        return Recommendation(
            recommendation="complete-existing",
            recommended_tool="husky",
            supporting_tools=["lint-staged"],
            reasons=["Repository already hints at a Node commit-check stack via lint-staged but lacks a primary hook runner."],
            next_steps=[
                "Add husky and wire lint-staged through a pre-commit hook.",
                "Keep the current lint-staged rules instead of replacing them.",
            ],
        )

    if project_type == "node":
        return Recommendation(
            recommendation="add-default",
            recommended_tool="husky",
            supporting_tools=["lint-staged"],
            reasons=["Node-only repository with no existing hook tool detected."],
            next_steps=[
                "Install husky and lint-staged in package.json.",
                "Create a pre-commit hook that runs lint-staged and any existing package quality scripts.",
            ],
        )

    if project_type == "python":
        return Recommendation(
            recommendation="add-default",
            recommended_tool="pre-commit",
            supporting_tools=[],
            reasons=["Python-only repository with no existing hook tool detected."],
            next_steps=[
                "Add .pre-commit-config.yaml as the single hook entry point.",
                "Configure format, lint, and test-adjacent hooks that match the existing Python toolchain.",
            ],
        )

    if project_type == "mixed":
        return Recommendation(
            recommendation="add-default",
            recommended_tool="pre-commit",
            supporting_tools=[],
            reasons=["Mixed Node and Python repository without an existing hook tool is best served by one top-level orchestrator."],
            next_steps=[
                "Use pre-commit as the top-level orchestrator.",
                "Call both Node and Python quality commands from pre-commit hooks instead of adding competing hook systems.",
            ],
        )

    return Recommendation(
        recommendation="review-manually",
        recommended_tool="manual-review",
        supporting_tools=[],
        reasons=["Project type is unclear; choose the hook stack only after inspecting the repository manually."],
        next_steps=[
            "Inspect the repository structure and existing scripts manually.",
            "Select a hook tool only after confirming the dominant language and workflow.",
        ],
    )


def build_payload(start_root: Path, detected_root: Path) -> dict[str, Any]:
    package_json = load_package_json(detected_root)
    pyproject_text = load_pyproject_text(detected_root)
    project_type = classify_project(detected_root, package_json)
    existing_tools, evidence = detect_existing_tools(
        detected_root, package_json, pyproject_text
    )
    recommendation = recommend_setup(project_type, existing_tools)

    payload: dict[str, Any] = {
        "project_root": str(start_root),
        "detected_root": str(detected_root),
        "project_type": project_type,
        "existing_tools": existing_tools,
        "evidence": evidence,
    }
    payload.update(asdict(recommendation))
    return payload


def print_summary(payload: dict[str, Any]) -> None:
    print(f"Detected root: {payload['detected_root']}")
    print(f"Project type: {payload['project_type']}")
    print(f"Existing tools: {', '.join(payload['existing_tools']) or 'none'}")
    print(f"Recommendation: {payload['recommendation']} -> {payload['recommended_tool']}")
    for reason in payload["reasons"]:
        print(f"- {reason}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.project_root).resolve()
    detected_root = find_repository_root(root, args.max_depth)
    payload = build_payload(root, detected_root)
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_summary(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

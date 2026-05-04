#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable


DOC_EXTENSIONS = {".md", ".mdx", ".rst", ".txt", ".adoc"}
CODE_EXTENSIONS = {
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".py",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".cs",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".swift",
    ".rb",
    ".php",
}
TEST_DIRS = {"test", "tests", "__tests__", "spec", "specs"}
WORKSPACE_PREFIXES = {"apps", "packages", "services", "libs", "modules"}
GENERIC_SEGMENTS = {
    "src",
    "lib",
    "app",
    "apps",
    "packages",
    "services",
    "libs",
    "modules",
    "internal",
    "client",
    "server",
    "shared",
    "common",
    "components",
    "pages",
    "routes",
    "hooks",
    "utils",
    "helpers",
    "styles",
    "assets",
    "public",
    "feature",
    "features",
    "docs",
    "doc",
    "test",
    "tests",
    "__tests__",
    "spec",
    "specs",
}
GENERIC_FILE_STEMS = {
    "index",
    "main",
    "app",
    "page",
    "route",
    "layout",
    "types",
    "constants",
    "helpers",
    "utils",
    "readme",
}
ROOT_CONFIG_NAMES = {
    "package.json",
    "pnpm-lock.yaml",
    "package-lock.json",
    "yarn.lock",
    "bun.lock",
    "bun.lockb",
    "uv.lock",
    "poetry.lock",
    "Cargo.toml",
    "Cargo.lock",
    "go.mod",
    "go.sum",
    "pyproject.toml",
    "tsconfig.json",
    "tsconfig.base.json",
    "eslint.config.js",
    "eslint.config.mjs",
    ".eslintrc",
    ".eslintrc.js",
    ".prettierrc",
    ".prettierrc.json",
    ".pre-commit-config.yaml",
    "Makefile",
}
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


@dataclass(frozen=True)
class FileChange:
    path: str
    index_status: str
    worktree_status: str
    old_path: str | None = None

    @property
    def is_partial(self) -> bool:
        return self.index_status not in {" ", "?"} and self.worktree_status not in {" ", "?"}

    @property
    def is_rename(self) -> bool:
        return self.old_path is not None


@dataclass
class Batch:
    key: str
    label: str
    scope: str
    kind: str
    files: list[str]
    reasons: list[str]
    cautions: list[str]
    suggested_commit: dict[str, object]
    quality_gate_plan: dict[str, object]


@dataclass(frozen=True)
class GateCommand:
    command: str
    reason: str
    source: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan reviewable commit batches from a dirty git worktree."
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Git worktree to inspect.",
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
        check=False,
    )


def is_git_repository(root: Path) -> bool:
    probe = run_git(root, "rev-parse", "--is-inside-work-tree")
    return probe.returncode == 0 and probe.stdout.strip() == "true"


def normalize_path(raw_path: str) -> str:
    return raw_path.replace("\\", "/").strip()


def parse_status_lines(stdout: str) -> list[FileChange]:
    changes: list[FileChange] = []
    for raw_line in stdout.splitlines():
        if not raw_line:
            continue
        index_status = raw_line[0]
        worktree_status = raw_line[1]
        payload = raw_line[3:].strip()
        old_path = None
        path = payload
        if " -> " in payload:
            old_path, path = payload.split(" -> ", 1)
        changes.append(
            FileChange(
                path=normalize_path(path),
                old_path=normalize_path(old_path) if old_path else None,
                index_status=index_status,
                worktree_status=worktree_status,
            )
        )
    return changes


def detect_category(path: str) -> str:
    pure = PurePosixPath(path)
    name = pure.name
    suffix = pure.suffix.lower()
    parts = set(pure.parts)
    lower_name = name.lower()
    if name in ROOT_CONFIG_NAMES or lower_name.startswith(".github"):
        return "config"
    if ".github" in parts:
        return "config"
    if any(part in TEST_DIRS for part in pure.parts) or ".test." in lower_name or ".spec." in lower_name:
        return "test"
    if suffix in DOC_EXTENSIONS or lower_name in {"readme", "changelog"} or lower_name.startswith("readme."):
        return "docs"
    if name in ROOT_CONFIG_NAMES or suffix in {".yaml", ".yml", ".toml"} and len(pure.parts) <= 2:
        return "config"
    if suffix in CODE_EXTENSIONS:
        return "code"
    return "asset"


def read_text_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="ignore")


def append_unique_gate(
    commands: list[GateCommand],
    seen: set[str],
    command: str,
    reason: str,
    source: str,
) -> None:
    normalized = command.strip()
    if not normalized or normalized in seen:
        return
    commands.append(GateCommand(command=normalized, reason=reason, source=source))
    seen.add(normalized)


def detect_python_runner(root: Path, pyproject_text: str) -> str:
    lowered = pyproject_text.lower()
    if (root / "uv.lock").exists() or "[tool.uv" in lowered:
        return "uv run "
    if (root / "poetry.lock").exists() or "[tool.poetry" in lowered:
        return "poetry run "
    if (root / "Pipfile").exists():
        return "pipenv run "
    return "python -m "


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


def load_package_scripts(root: Path) -> dict[str, str]:
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


def classify_gate_command(command: str) -> str:
    lowered = command.lower()
    if "diff --check" in lowered:
        return "diffcheck"
    if any(token in lowered for token in ("eslint", "ruff", "clippy", "vet", "lint", "format --check", "format:check")):
        return "lint"
    if any(token in lowered for token in ("tsc --noemit", "typecheck", "mypy", "pyright")):
        return "typecheck"
    if any(token in lowered for token in ("pytest", "vitest", "jest", "go test", "cargo test", "dotnet test", " test")):
        return "test"
    if any(token in lowered for token in ("vite build", "build", "dotnet build")):
        return "build"
    if any(token in lowered for token in ("verify", "check", "ci", "validate")):
        return "verify"
    return "other"


def detect_quality_gate_commands(root: Path) -> list[GateCommand]:
    commands: list[GateCommand] = []
    seen: set[str] = set()

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

    ci_text = "\n".join(
        read_text_if_exists(path)
        for path in sorted((root / ".github" / "workflows").glob("*"))
        if path.is_file()
    ) if (root / ".github" / "workflows").exists() else ""
    for line in ci_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- run:"):
            command = stripped.split(":", 1)[1].strip()
            append_unique_gate(commands, seen, command, "CI workflow command", ".github/workflows")

    package_scripts = load_package_scripts(root)
    if package_scripts:
        package_manager = detect_package_manager(root)
        for script_name in NODE_SCRIPT_ORDER:
            if script_name in package_scripts:
                append_unique_gate(
                    commands,
                    seen,
                    build_node_script_command(package_manager, script_name),
                    f"Run package script '{script_name}'",
                    "package.json",
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
        if "ruff" in python_context:
            append_unique_gate(commands, seen, f"{python_runner}ruff check .", "Python lint check", "pyproject.toml/requirements")
        if "pytest" in python_context or (root / "tests").exists():
            append_unique_gate(commands, seen, f"{python_runner}pytest", "Python tests", "pyproject.toml/requirements/tests")
        if "mypy" in python_context:
            append_unique_gate(commands, seen, f"{python_runner}mypy .", "Python typecheck", "pyproject.toml/requirements")
        if "pyright" in python_context:
            append_unique_gate(commands, seen, f"{python_runner}pyright", "Python typecheck", "pyproject.toml/requirements")

    if (root / "Cargo.toml").exists():
        append_unique_gate(commands, seen, "cargo fmt --all --check", "Rust formatting check", "Cargo.toml")
        append_unique_gate(commands, seen, "cargo clippy --all-targets --all-features -- -D warnings", "Rust lint check", "Cargo.toml")
        append_unique_gate(commands, seen, "cargo test", "Rust test suite", "Cargo.toml")
    if (root / "go.mod").exists():
        append_unique_gate(commands, seen, "go test ./...", "Go test suite", "go.mod")
        append_unique_gate(commands, seen, "go vet ./...", "Go vet checks", "go.mod")
    if any(root.glob("*.sln")) or any(root.glob("*.csproj")):
        append_unique_gate(commands, seen, "dotnet build --nologo", ".NET build check", "solution/project file")
        append_unique_gate(commands, seen, "dotnet test --nologo", ".NET test suite", "solution/project file")

    if not commands:
        append_unique_gate(commands, seen, "git diff --check", "Fallback diff check", "git")

    return commands


def sanitize_scope_token(value: str) -> str:
    chars = [ch.lower() if ch.isalnum() else "-" for ch in value]
    collapsed = "".join(chars).strip("-")
    while "--" in collapsed:
        collapsed = collapsed.replace("--", "-")
    return collapsed or "root"


def informative_tokens(path: str) -> list[str]:
    pure = PurePosixPath(path)
    parts = list(pure.parts[:-1])
    stem = pure.stem.lower().replace(".test", "").replace(".spec", "")
    tokens: list[str] = []
    if len(pure.parts) >= 2 and pure.parts[0] in WORKSPACE_PREFIXES:
        tokens.append(pure.parts[1].lower())
        parts = list(pure.parts[2:-1])
    for part in parts:
        lowered = part.lower()
        if lowered in GENERIC_SEGMENTS:
            continue
        if lowered.startswith("."):
            continue
        tokens.append(lowered)
    if stem and stem not in GENERIC_FILE_STEMS and stem not in GENERIC_SEGMENTS:
        tokens.append(stem)
    return tokens


def derive_scope(path: str) -> tuple[str, str]:
    pure = PurePosixPath(path)
    tokens = informative_tokens(path)
    if tokens:
        if len(pure.parts) >= 2 and pure.parts[0] in WORKSPACE_PREFIXES and len(tokens) >= 2:
            selected = tokens[:2]
        else:
            selected = tokens[:1]
        scope = sanitize_scope_token("-".join(selected))
        label = "/".join(selected)
        return scope, label
    if len(pure.parts) >= 2 and pure.parts[0] in WORKSPACE_PREFIXES:
        fallback = sanitize_scope_token(pure.parts[1])
        return fallback, pure.parts[1]
    if pure.parts:
        fallback = sanitize_scope_token(pure.parts[0])
        return fallback, pure.parts[0]
    return "root", "root"


def batch_kind_for_categories(categories: Iterable[str]) -> str:
    unique = set(categories)
    if "code" in unique or "asset" in unique:
        return "feature"
    if unique == {"docs"}:
        return "docs"
    if unique == {"test"}:
        return "test"
    if unique == {"config"}:
        return "config"
    return "mixed"


def build_commit_suggestion(kind: str, label: str, scope: str) -> dict[str, object]:
    normalized_scope = sanitize_scope_token(scope)
    if kind == "docs":
        return {
            "type": "docs",
            "alternatives": [],
            "scope": normalized_scope,
            "subject": f"update {label} documentation",
        }
    if kind == "test":
        return {
            "type": "test",
            "alternatives": ["fix"],
            "scope": normalized_scope,
            "subject": f"expand {label} coverage",
        }
    if kind == "config":
        return {
            "type": "build",
            "alternatives": ["chore", "ci"],
            "scope": normalized_scope if normalized_scope != "root" else "tooling",
            "subject": f"align {label} tooling changes",
        }
    if kind == "mixed":
        return {
            "type": "chore",
            "alternatives": ["refactor", "fix"],
            "scope": normalized_scope,
            "subject": f"organize {label} changes",
        }
    return {
        "type": "feat",
        "alternatives": ["fix", "refactor"],
        "scope": normalized_scope,
        "subject": f"update {label} changes",
    }


def build_quality_gate_plan(kind: str, commands: list[GateCommand]) -> dict[str, object]:
    classified: dict[str, list[str]] = defaultdict(list)
    for entry in commands:
        classified[classify_gate_command(entry.command)].append(entry.command)

    ordered_full = [entry.command for entry in commands]
    narrow: list[str] = []
    if kind == "docs":
        narrow = classified["diffcheck"] or classified["lint"][:1]
    elif kind == "test":
        narrow = classified["test"][:1] + classified["lint"][:1] + classified["typecheck"][:1]
    elif kind == "config":
        narrow = classified["lint"][:1] + classified["typecheck"][:1] + classified["build"][:1]
    else:
        narrow = classified["lint"][:1] + classified["typecheck"][:1] + classified["test"][:1]

    if not narrow:
        narrow = ordered_full[:1]

    repair_loop = [
        "Stage only this batch before running checks.",
        "Run the first narrow command and fix the first real failure.",
        "Re-run that failing command directly until it passes.",
        "Run the broader command chain before committing the batch.",
    ]
    if kind == "docs":
        repair_loop[1] = "Run the lightest check first; widen only if repository hooks enforce more than docs hygiene."

    return {
        "narrow_commands": narrow,
        "full_commands": ordered_full,
        "repair_loop": repair_loop,
    }


def build_final_commit_suggestion(batches: list[Batch]) -> dict[str, object]:
    if not batches:
        return {
            "type": "chore",
            "alternatives": [],
            "scope": "workspace",
            "subject": "record grouped changes",
            "body_points": [],
        }

    feature_batches = [batch for batch in batches if batch.kind == "feature"]
    config_batches = [batch for batch in batches if batch.kind == "config"]
    test_batches = [batch for batch in batches if batch.kind == "test"]
    docs_batches = [batch for batch in batches if batch.kind == "docs"]

    if len(feature_batches) == 1 and len(batches) <= 2 and not config_batches:
        suggestion = dict(feature_batches[0].suggested_commit)
        suggestion["subject"] = f"deliver {feature_batches[0].label} updates"
        suggestion["body_points"] = [
            f"Collapse {len(batches)} temporary batch commit(s) into one final commit.",
        ]
        return suggestion

    if feature_batches:
        labels = [batch.label for batch in feature_batches[:2]]
        remainder = len(feature_batches) - len(labels)
        summary = " and ".join(labels)
        if remainder > 0:
            summary = f"{summary} and {remainder} more scope(s)"
        return {
            "type": "feat",
            "alternatives": ["fix", "chore"],
            "scope": "workspace",
            "subject": f"deliver {summary} updates",
            "body_points": [
                "Collapse temporary split-batch commits after all gates pass.",
                "Mention secondary docs, config, or test scopes in the commit body.",
            ],
        }

    if config_batches:
        return {
            "type": "build",
            "alternatives": ["chore", "ci"],
            "scope": "tooling",
            "subject": "align shared tooling updates",
            "body_points": [
                "Collapse temporary split-batch commits after all gates pass.",
            ],
        }

    if test_batches and not docs_batches:
        return {
            "type": "test",
            "alternatives": ["fix"],
            "scope": "workspace",
            "subject": "consolidate grouped coverage updates",
            "body_points": [
                "Collapse temporary split-batch commits after all gates pass.",
            ],
        }

    return {
        "type": "docs",
        "alternatives": ["chore"],
        "scope": "workspace",
        "subject": "consolidate grouped documentation updates",
        "body_points": [
            "Collapse temporary split-batch commits after all gates pass.",
        ],
    }


def clone_commit_suggestion(suggestion: dict[str, object]) -> dict[str, object]:
    body_points = suggestion.get("body_points", [])
    alternatives = suggestion.get("alternatives", [])
    return {
        "type": str(suggestion.get("type", "chore")),
        "alternatives": list(alternatives) if isinstance(alternatives, list) else [],
        "scope": str(suggestion.get("scope", "workspace")),
        "subject": str(suggestion.get("subject", "record grouped changes")),
        "body_points": list(body_points) if isinstance(body_points, list) else [],
    }


def build_scoped_commit_suggestion(group_batches: list[Batch]) -> dict[str, object]:
    if not group_batches:
        return build_final_commit_suggestion([])

    if len(group_batches) == 1:
        suggestion = clone_commit_suggestion(group_batches[0].suggested_commit)
        suggestion["body_points"].append(
            "Collapse temporary checkpoint commits for this scope only."
        )
        return suggestion

    suggestion = clone_commit_suggestion(build_final_commit_suggestion(group_batches))
    suggestion["body_points"].append(
        "Keep this scope separate from other scope-level consolidation groups."
    )
    return suggestion


def build_scoped_consolidation_groups(batches: list[Batch]) -> list[dict[str, object]]:
    grouped: dict[str, list[Batch]] = defaultdict(list)
    ordered_keys: list[str] = []
    for batch in batches:
        group_key = sanitize_scope_token(batch.scope if batch.scope else batch.key)
        if group_key not in grouped:
            ordered_keys.append(group_key)
        grouped[group_key].append(batch)

    groups: list[dict[str, object]] = []
    for group_key in ordered_keys:
        group_batches = grouped[group_key]
        labels = [batch.label for batch in group_batches]
        label = labels[0] if all(item == labels[0] for item in labels) else ", ".join(labels)
        groups.append(
            {
                "key": group_key,
                "label": label,
                "batch_keys": [batch.key for batch in group_batches],
                "kinds": list(dict.fromkeys(batch.kind for batch in group_batches)),
                "files": sorted({file for batch in group_batches for file in batch.files}),
                "final_commit": build_scoped_commit_suggestion(group_batches),
            }
        )
    return groups


def build_granularity_plans(
    batches: list[Batch],
) -> tuple[dict[str, dict[str, object]], dict[str, object]]:
    final_commit = build_final_commit_suggestion(batches)
    scoped_groups = build_scoped_consolidation_groups(batches)
    final_steps = []
    scoped_steps = []
    if batches:
        final_steps = [
            "git reset --soft <base_commit>",
            "git commit -m \"<final conventional commit>\"",
        ]
        scoped_steps = [
            "git reset --soft <base_commit>",
            "git reset HEAD -- .",
            "git add <group files>",
            "git commit -m \"<group conventional commit>\"",
            "Repeat git add + git commit for each scoped consolidation group in order.",
        ]

    granularity_plans = {
        "final": {
            "description": "Collapse every completed batch checkpoint into one final commit.",
            "commit_count": 1 if batches else 0,
            "execution_steps": final_steps,
            "final_commits": [clone_commit_suggestion(final_commit)] if batches else [],
            "consolidation_groups": [],
        },
        "scoped": {
            "description": "Collapse completed checkpoint commits into one final commit per scope-level group.",
            "commit_count": len(scoped_groups),
            "execution_steps": scoped_steps,
            "final_commits": [clone_commit_suggestion(group["final_commit"]) for group in scoped_groups],
            "consolidation_groups": scoped_groups,
        },
        "checkpoint": {
            "description": "Keep each completed batch commit as its own checkpoint without an extra squash step.",
            "commit_count": len(batches),
            "execution_steps": [],
            "final_commits": [clone_commit_suggestion(batch.suggested_commit) for batch in batches],
            "consolidation_groups": [],
        },
    }
    return granularity_plans, clone_commit_suggestion(final_commit)


def build_post_commit_consolidation_plan(batches: list[Batch]) -> dict[str, object]:
    granularity_plans, final_commit = build_granularity_plans(batches)
    default_granularity = "final"
    if not batches:
        return {
            "enabled_by_default": False,
            "strategy": "checkpoint-then-final-squash",
            "trigger": "No planned batches remain, so no final squash is required.",
            "default_granularity": default_granularity,
            "selected_granularity": default_granularity,
            "available_granularities": ["final", "scoped", "checkpoint"],
            "required_completed_batch_count": 0,
            "checkpoint": {
                "capture_command": "git rev-parse HEAD",
                "branch_command": "git branch --show-current",
                "note": "Capture the pre-split checkpoint before the first temporary batch commit.",
            },
            "verification_commands": [],
            "execution_steps": [],
            "abort_conditions": [],
            "fallback": "No consolidation step is needed when there are no temporary batch commits.",
            "final_commit": final_commit,
            "granularity_plans": granularity_plans,
        }

    return {
        "enabled_by_default": True,
        "strategy": "checkpoint-then-final-squash",
        "trigger": "Run automatically after every planned batch commits cleanly and no dirty files remain.",
        "default_granularity": default_granularity,
        "selected_granularity": default_granularity,
        "available_granularities": ["final", "scoped", "checkpoint"],
        "required_completed_batch_count": len(batches),
        "checkpoint": {
            "capture_command": "git rev-parse HEAD",
            "branch_command": "git branch --show-current",
            "note": "Record the pre-split checkpoint before the first temporary batch commit.",
        },
        "verification_commands": [
            "git status --short",
            "git rev-list --count <base_commit>..HEAD",
            "git merge-base <base_commit> HEAD",
        ],
        "execution_steps": [
            "git reset --soft <base_commit>",
            "git commit -m \"<final conventional commit>\"",
        ],
        "abort_conditions": [
            "Stop if git status --short is not empty before the squash step.",
            "Stop if git rev-list --count <base_commit>..HEAD does not match the completed batch count.",
            "Stop if git merge-base <base_commit> HEAD is not <base_commit>.",
            "Stop if any batch is still blocked or intentionally left unverified.",
        ],
        "fallback": "If any consolidation safety check fails, stop and keep the checkpoint commits instead of forcing a squash.",
        "final_commit": final_commit,
        "granularity_plans": granularity_plans,
    }


def plan_batches(
    changes: list[FileChange], gate_commands: list[GateCommand]
) -> tuple[list[Batch], list[str]]:
    if not changes:
        return [], []

    file_info: dict[str, dict[str, object]] = {}
    code_scopes: set[str] = set()
    partial_files = [item.path for item in changes if item.is_partial]

    for item in changes:
        category = detect_category(item.path)
        scope, label = derive_scope(item.path)
        file_info[item.path] = {
            "change": item,
            "category": category,
            "scope": scope,
            "label": label,
        }
        if category == "code":
            code_scopes.add(scope)

    groups: dict[str, list[str]] = defaultdict(list)
    group_labels: dict[str, str] = {}
    global_cautions: list[str] = []

    for path, info in file_info.items():
        category = str(info["category"])
        scope = str(info["scope"])
        label = str(info["label"])

        if category in {"docs", "test"} and scope in code_scopes:
            key = scope
        elif category == "config" and scope in code_scopes and scope != "root":
            key = scope
        elif category == "config" and len(code_scopes) == 1:
            key = next(iter(code_scopes))
        elif category == "config" and len(code_scopes) > 1:
            key = "shared-config"
            label = "shared config"
        else:
            key = scope if category == "code" else f"{category}:{scope}"

        groups[key].append(path)
        group_labels[key] = label

    if partial_files:
        global_cautions.append(
            "Some files are partially staged; review hunks before trusting the batch plan."
        )

    if "shared-config" in groups:
        global_cautions.append(
            "Root config or lockfile changes touch multiple feature scopes; verify whether they belong in one batch or must stay shared."
        )

    batches: list[Batch] = []
    for key, paths in groups.items():
        categories = [str(file_info[path]["category"]) for path in paths]
        kind = batch_kind_for_categories(categories)
        label = group_labels.get(key, key)
        if key == "shared-config":
            kind = "config"
        scope = key if ":" not in key else key.split(":", 1)[1]
        reasons = [f"Files cluster around `{label}`."]
        if any(cat == "test" for cat in categories) and kind == "feature":
            reasons.append("Matching tests were kept with the same feature scope.")
        if any(cat == "docs" for cat in categories) and kind == "feature":
            reasons.append("Matching docs were kept with the same feature scope.")
        if key == "shared-config":
            reasons.append("Shared root config stayed separate because multiple feature scopes are dirty.")

        cautions: list[str] = []
        if any(file_info[path]["change"].is_rename for path in paths):
            cautions.append("This batch includes a rename or move; confirm the old and new paths stay together.")
        if any(file_info[path]["change"].is_partial for path in paths):
            cautions.append("One or more files are partially staged; use hunk staging carefully.")
        if key == "shared-config":
            cautions.append("Shared config can hide coupling between otherwise separate features.")

        batches.append(
            Batch(
                key=key,
                label=label,
                scope=scope,
                kind=kind,
                files=sorted(paths),
                reasons=reasons,
                cautions=cautions,
                suggested_commit=build_commit_suggestion(kind=kind, label=label, scope=scope),
                quality_gate_plan=build_quality_gate_plan(kind=kind, commands=gate_commands),
            )
        )

    priority = {"feature": 10, "mixed": 20, "config": 40, "test": 50, "docs": 60}
    batches.sort(key=lambda item: (priority.get(item.kind, 99), item.label, item.key))
    return batches, global_cautions


def summarize_git_state(root: Path, changes: list[FileChange]) -> dict[str, object]:
    branch = run_git(root, "branch", "--show-current")
    counter = Counter()
    for item in changes:
        if item.index_status not in {" ", "?"}:
            counter["staged"] += 1
        if item.worktree_status not in {" ", "?"}:
            counter["unstaged"] += 1
        if item.index_status == "?" and item.worktree_status == "?":
            counter["untracked"] += 1
        if item.is_partial:
            counter["partial"] += 1
    return {
        "is_git_repo": True,
        "branch": branch.stdout.strip() if branch.returncode == 0 else "",
        "change_count": len(changes),
        "staged_count": counter["staged"],
        "unstaged_count": counter["unstaged"],
        "untracked_count": counter["untracked"],
        "partial_count": counter["partial"],
    }


def render_text(payload: dict[str, object]) -> str:
    status = str(payload["status"])
    lines = [f"Status: {status}", f"Project root: {payload['project_root']}"]
    if status != "ok":
        for caution in payload.get("global_cautions", []):
            lines.append(f"- {caution}")
        return "\n".join(lines)

    git_state = payload["git_state"]
    lines.append(
        "Changes: "
        f"{git_state['change_count']} total, "
        f"{git_state['staged_count']} staged, "
        f"{git_state['unstaged_count']} unstaged, "
        f"{git_state['untracked_count']} untracked"
    )
    lines.append("Recommended order:")
    for batch in payload["batches"]:
        lines.append(
            f"- {batch['label']} [{batch['kind']}] -> "
            f"{batch['suggested_commit']['type']}({batch['suggested_commit']['scope']})"
        )
        narrow = batch["quality_gate_plan"]["narrow_commands"]
        if narrow:
            lines.append(f"  First checks: {', '.join(narrow)}")
    consolidation = payload.get("post_commit_consolidation")
    if consolidation:
        lines.append("Post-commit consolidation:")
        lines.append(
            f"- Strategy: {consolidation['strategy']} "
            f"(default={'on' if consolidation['enabled_by_default'] else 'off'})"
        )
        lines.append(
            f"- Default granularity: {consolidation['default_granularity']}"
        )
        if consolidation["execution_steps"]:
            lines.append(f"- Final steps: {', '.join(consolidation['execution_steps'])}")
        scoped_plan = consolidation["granularity_plans"].get("scoped", {})
        if scoped_plan.get("commit_count"):
            lines.append(f"- Scoped option: {scoped_plan['commit_count']} grouped commit(s)")
    if payload["global_cautions"]:
        lines.append("Global cautions:")
        for caution in payload["global_cautions"]:
            lines.append(f"- {caution}")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = Path(args.project_root).resolve()
    payload: dict[str, object]

    if not root.exists():
        print(f"Project root does not exist: {root}", file=sys.stderr)
        return 2

    if not is_git_repository(root):
        payload = {
            "status": "blocked",
            "project_root": str(root),
            "git_state": {"is_git_repo": False},
            "batches": [],
            "recommended_order": [],
            "global_cautions": [
                "Current directory is not inside a git worktree; do not invent commit batches here."
            ],
        }
    else:
        status_result = run_git(root, "status", "--short")
        if status_result.returncode != 0:
            print(status_result.stderr.strip() or "git status failed", file=sys.stderr)
            return 2
        changes = parse_status_lines(status_result.stdout)
        gate_commands = detect_quality_gate_commands(root)
        batches, global_cautions = plan_batches(changes, gate_commands=gate_commands)
        payload = {
            "status": "ok",
            "project_root": str(root),
            "git_state": summarize_git_state(root, changes),
            "quality_gate_commands": [asdict(item) for item in gate_commands],
            "batches": [asdict(batch) for batch in batches],
            "recommended_order": [batch.key for batch in batches],
            "post_commit_consolidation": build_post_commit_consolidation_plan(batches),
            "global_cautions": global_cautions,
        }

    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

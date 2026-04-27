#!/usr/bin/env python3
"""Analyze a repository and scaffold a reusable project-specific skill package."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import tomllib


IGNORED_DIR_NAMES = {
    ".git",
    ".hg",
    ".idea",
    ".next",
    ".nuxt",
    ".pytest_cache",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".uv-cache",
    ".codex-uv-cache",
    ".uv-cache-codex",
    ".uv-cache-local",
    ".uv-python",
    ".venv",
    "__pycache__",
    "artifacts",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "out",
    "target",
    "tmp",
    "venv",
}
IGNORED_FILE_SUFFIXES = {
    ".class",
    ".dll",
    ".dylib",
    ".exe",
    ".gif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".min.css",
    ".min.js",
    ".pdf",
    ".png",
    ".pyc",
    ".pyo",
    ".so",
    ".svg",
    ".webp",
    ".zip",
}
DOC_NAMES = {
    "agents.md",
    "architecture.md",
    "claude.md",
    "contributing.md",
    "readme.md",
}
MANIFEST_NAMES = {
    "Cargo.toml",
    "Makefile",
    "bun.lock",
    "bun.lockb",
    "go.mod",
    "package-lock.json",
    "package.json",
    "pnpm-lock.yaml",
    "poetry.lock",
    "pyproject.toml",
    "requirements.txt",
    "uv.lock",
    "yarn.lock",
}
ENTRY_PREFIXES = ("app", "cli", "index", "main", "manage", "server")
SOURCE_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".mjs",
    ".py",
    ".rb",
    ".rs",
    ".swift",
    ".ts",
    ".tsx",
}
LANGUAGE_BY_SUFFIX = {
    ".c": "C",
    ".cc": "C++",
    ".cpp": "C++",
    ".cs": "C#",
    ".go": "Go",
    ".java": "Java",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".py": "Python",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".swift": "Swift",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
}
COMMAND_PRIORITY = ("dev", "start", "build", "test", "lint", "typecheck", "check")


def normalize_hyphen_name(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    if not normalized:
        raise ValueError("Skill name must contain at least one letter or digit.")
    return normalized


def title_case_skill_name(skill_name: str) -> str:
    return " ".join(part.capitalize() for part in skill_name.split("-") if part)


def yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze a repository and scaffold a project-specific skill package.",
    )
    parser.add_argument("--project-root", required=True, help="Repository root to analyze.")
    parser.add_argument("--skill-name", required=True, help="Name for the generated skill.")
    parser.add_argument("--output-dir", required=True, help="Directory that will receive the new skill.")
    parser.add_argument(
        "--include",
        action="append",
        default=[],
        help="Relative path prefix to include. Repeat to include multiple prefixes.",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Relative path prefix to exclude. Repeat to exclude multiple prefixes.",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=500,
        help="Cap the number of matching files scanned.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing generated skill directory with the same name.",
    )
    return parser.parse_args(argv)


def normalize_prefixes(values: list[str]) -> list[str]:
    prefixes: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.replace("\\", "/").strip().strip("/")
        if normalized and normalized not in seen:
            prefixes.append(normalized)
            seen.add(normalized)
    return prefixes


def path_matches_prefix(relative_path: str, prefix: str) -> bool:
    return relative_path == prefix or relative_path.startswith(f"{prefix}/")


def should_include_path(relative_path: str, includes: list[str], excludes: list[str]) -> bool:
    if includes and not any(path_matches_prefix(relative_path, prefix) for prefix in includes):
        return False
    if any(path_matches_prefix(relative_path, prefix) for prefix in excludes):
        return False
    return True


def should_skip_file(path: Path) -> bool:
    suffixes = path.suffixes
    if suffixes:
        compound_suffix = "".join(suffixes[-2:]) if len(suffixes) >= 2 else suffixes[-1]
        if compound_suffix in IGNORED_FILE_SUFFIXES or path.suffix.lower() in IGNORED_FILE_SUFFIXES:
            return True
    return False


def is_doc(path: Path) -> bool:
    lower = path.name.lower()
    if lower in DOC_NAMES or lower.startswith("readme"):
        return True
    return path.suffix.lower() in {".md", ".rst"} and "docs" in {part.lower() for part in path.parts}


def is_manifest(path: Path) -> bool:
    return path.name in MANIFEST_NAMES


def detect_language(path: Path) -> str:
    return LANGUAGE_BY_SUFFIX.get(path.suffix.lower(), "unknown")


def infer_roles(path: Path) -> list[str]:
    roles: set[str] = set()
    lower_parts = [part.lower() for part in path.parts]
    stem = path.stem.lower()
    suffix = path.suffix.lower()

    if is_doc(path):
        roles.add("docs")
    if is_manifest(path):
        roles.add("manifest")
        roles.add("config")
    if suffix in {".json", ".toml", ".yaml", ".yml", ".ini", ".cfg"}:
        roles.add("config")
    if stem.startswith(ENTRY_PREFIXES) and suffix in SOURCE_EXTENSIONS:
        roles.add("entry")
    if any(token in stem for token in ("test", "spec")) or any(
        token in lower_parts for token in ("test", "tests", "__tests__")
    ):
        roles.add("test")
    if any(part in {"api", "apis", "handlers", "routes", "controllers"} for part in lower_parts):
        roles.add("api")
    if suffix in {".jsx", ".tsx"} or any(
        part in {"components", "pages", "views", "screens", "app"} for part in lower_parts
    ):
        roles.add("ui")
    if suffix in SOURCE_EXTENSIONS and not roles.intersection({"entry", "test", "api", "ui"}):
        roles.add("library")
    return sorted(roles)


def walk_repository(
    root: Path,
    includes: list[str],
    excludes: list[str],
    max_files: int,
) -> tuple[list[Path], list[dict[str, str]]]:
    matches: list[Path] = []
    limits: list[dict[str, str]] = []
    ignored_names_lower = {entry.lower() for entry in IGNORED_DIR_NAMES}

    for current_root, dir_names, file_names in os.walk(root):
        current_path = Path(current_root)
        relative_root = current_path.relative_to(root).as_posix() if current_path != root else ""
        filtered_dirs: list[str] = []
        for name in sorted(dir_names):
            relative_path = f"{relative_root}/{name}".strip("/")
            if name in IGNORED_DIR_NAMES or name.lower() in ignored_names_lower or name.startswith("_tmp"):
                continue
            if any(path_matches_prefix(relative_path, prefix) for prefix in excludes):
                continue
            filtered_dirs.append(name)
        dir_names[:] = filtered_dirs

        for file_name in sorted(file_names):
            file_path = current_path / file_name
            if should_skip_file(file_path):
                continue
            relative_path = file_path.relative_to(root).as_posix()
            if not should_include_path(relative_path, includes, excludes):
                continue
            matches.append(file_path)
            if len(matches) >= max_files:
                limits.append(
                    {
                        "kind": "max-files",
                        "detail": f"Stopped after indexing {max_files} matching files.",
                    }
                )
                return matches, limits
    return matches, limits


def sorted_by_depth(paths: list[Path], root: Path) -> list[Path]:
    return sorted(paths, key=lambda path: (len(path.relative_to(root).parts), str(path)))


def project_name_from_scanned_files(root: Path, files: list[Path]) -> str:
    for package_json in sorted_by_depth([path for path in files if path.name == "package.json"], root):
        try:
            data = json.loads(package_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and isinstance(data.get("name"), str) and data["name"].strip():
            return data["name"].strip()

    for pyproject in sorted_by_depth([path for path in files if path.name == "pyproject.toml"], root):
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            continue
        if isinstance(data, dict):
            project = data.get("project")
            if isinstance(project, dict) and isinstance(project.get("name"), str):
                name = project["name"].strip()
                if name:
                    return name

    for cargo in sorted_by_depth([path for path in files if path.name == "Cargo.toml"], root):
        try:
            data = tomllib.loads(cargo.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            continue
        if isinstance(data, dict):
            package = data.get("package")
            if isinstance(package, dict) and isinstance(package.get("name"), str):
                name = package["name"].strip()
                if name:
                    return name

    for go_mod in sorted_by_depth([path for path in files if path.name == "go.mod"], root):
        try:
            for line in go_mod.read_text(encoding="utf-8").splitlines():
                if line.startswith("module "):
                    module_name = line.split(" ", 1)[1].strip()
                    if module_name:
                        return module_name.split("/")[-1]
        except OSError:
            continue

    return root.name


def detect_package_runner(manifest_dir: Path, scan_root: Path) -> str:
    current = manifest_dir
    while True:
        if (current / "pnpm-lock.yaml").exists():
            return "pnpm"
        if (current / "yarn.lock").exists():
            return "yarn"
        if (current / "bun.lock").exists() or (current / "bun.lockb").exists():
            return "bun run"
        if current == scan_root:
            break
        if current.parent == current:
            break
        current = current.parent
    return "npm run"


def collect_package_json_commands(root: Path, files: list[Path]) -> list[dict[str, str]]:
    commands: list[dict[str, str]] = []
    for package_json in sorted_by_depth([path for path in files if path.name == "package.json"], root):
        try:
            data = json.loads(package_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        scripts = data.get("scripts", {})
        if not isinstance(scripts, dict):
            continue
        runner = detect_package_runner(package_json.parent, root)
        relative_manifest = package_json.relative_to(root).as_posix()
        ordered = list(COMMAND_PRIORITY) + sorted(name for name in scripts if name not in COMMAND_PRIORITY)
        for name in ordered:
            if name not in scripts:
                continue
            commands.append(
                {
                    "command": f"{runner} {name}",
                    "source": relative_manifest,
                    "reason": f'Found the "{name}" script in {relative_manifest}.',
                }
            )
    return commands


def collect_pyproject_commands(root: Path, files: list[Path]) -> list[dict[str, str]]:
    commands: list[dict[str, str]] = []
    for pyproject in sorted_by_depth([path for path in files if path.name == "pyproject.toml"], root):
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            continue
        tool_table = data.get("tool", {})
        if not isinstance(tool_table, dict):
            continue
        relative_manifest = pyproject.relative_to(root).as_posix()
        if "pytest" in tool_table:
            commands.append(
                {
                    "command": "python -m pytest",
                    "source": relative_manifest,
                    "reason": f"Detected pytest configuration in {relative_manifest}.",
                }
            )
        if "ruff" in tool_table:
            commands.append(
                {
                    "command": "python -m ruff check .",
                    "source": relative_manifest,
                    "reason": f"Detected Ruff configuration in {relative_manifest}.",
                }
            )
        if "mypy" in tool_table:
            commands.append(
                {
                    "command": "python -m mypy .",
                    "source": relative_manifest,
                    "reason": f"Detected mypy configuration in {relative_manifest}.",
                }
            )
    return commands


def collect_make_commands(root: Path, files: list[Path]) -> list[dict[str, str]]:
    commands: list[dict[str, str]] = []
    for makefile in sorted_by_depth([path for path in files if path.name == "Makefile"], root):
        try:
            text = makefile.read_text(encoding="utf-8")
        except OSError:
            continue
        relative_manifest = makefile.relative_to(root).as_posix()
        for name in COMMAND_PRIORITY:
            if re.search(rf"^{re.escape(name)}\s*:", text, re.MULTILINE):
                commands.append(
                    {
                        "command": f"make {name}",
                        "source": relative_manifest,
                        "reason": f'Found the "{name}" target in {relative_manifest}.',
                    }
                )
    return commands


def collect_cargo_commands(root: Path, files: list[Path]) -> list[dict[str, str]]:
    commands: list[dict[str, str]] = []
    for cargo in sorted_by_depth([path for path in files if path.name == "Cargo.toml"], root):
        relative_manifest = cargo.relative_to(root).as_posix()
        commands.extend(
            [
                {
                    "command": "cargo build",
                    "source": relative_manifest,
                    "reason": f"{relative_manifest} suggests a Rust build surface.",
                },
                {
                    "command": "cargo test",
                    "source": relative_manifest,
                    "reason": f"{relative_manifest} suggests Rust tests are available.",
                },
            ]
        )
    return commands


def collect_commands(root: Path, files: list[Path]) -> list[dict[str, str]]:
    commands: list[dict[str, str]] = []
    seen: set[str] = set()
    for collector in (
        collect_package_json_commands,
        collect_pyproject_commands,
        collect_make_commands,
        collect_cargo_commands,
    ):
        for command in collector(root, files):
            if command["command"] in seen:
                continue
            seen.add(command["command"])
            commands.append(command)
    return commands[:10]


def summarize_directories(records: list[dict[str, object]], depth: int = 2) -> list[dict[str, object]]:
    directory_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for record in records:
        path = Path(str(record["path"]))
        key = "/".join(path.parts[:depth]) if path.parts else "."
        directory_counts[key]["__files__"] += 1
        language = str(record["language"])
        if language != "unknown":
            directory_counts[key][language] += 1

    items: list[dict[str, object]] = []
    for directory, counts in directory_counts.items():
        file_count = counts.pop("__files__", 0)
        languages = [
            {"language": language, "count": count}
            for language, count in counts.most_common(3)
        ]
        items.append(
            {
                "path": directory,
                "file_count": file_count,
                "languages": languages,
            }
        )
    items.sort(key=lambda item: (-int(item["file_count"]), str(item["path"])))
    return items[:12]


def determine_entry_reason(relative_path: str) -> str:
    stem = Path(relative_path).stem.lower()
    if stem.startswith("main"):
        return "Matched a conventional main bootstrap filename."
    if stem.startswith("server"):
        return "Matched a conventional server bootstrap filename."
    if stem.startswith("app"):
        return "Matched a conventional app bootstrap filename."
    if stem.startswith("index"):
        return "Matched a conventional index bootstrap filename."
    return "Matched a common bootstrap filename pattern."


def build_entry_candidates(records: list[dict[str, object]]) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    for record in records:
        roles = set(str(role) for role in record["roles"])
        if "entry" not in roles:
            continue
        candidates.append(
            {
                "path": str(record["path"]),
                "reason": determine_entry_reason(str(record["path"])),
            }
        )
    candidates.sort(key=lambda item: (item["path"].count("/"), item["path"]))
    return candidates[:8]


def score_record(record: dict[str, object]) -> tuple[int, str]:
    path = str(record["path"])
    roles = set(str(role) for role in record["roles"])
    score = 0
    reasons: list[str] = []

    if path.lower().startswith(("readme", "agents.md", "claude.md")):
        score += 100
        reasons.append("Repository orientation file.")
    if "manifest" in roles:
        score += 90
        reasons.append("Manifest reveals scripts or dependencies.")
    if "entry" in roles:
        score += 80
        reasons.append("Likely bootstrap file.")
    if "api" in roles or "ui" in roles:
        score += 45
        reasons.append("Touches a major application surface.")
    if "test" in roles:
        score += 20
        reasons.append("Tests reveal expected behavior.")
    if not reasons:
        reasons.append("Representative file from the scan.")
    return score, " ".join(reasons)


def build_reading_order(records: list[dict[str, object]]) -> list[dict[str, str]]:
    scored: list[tuple[int, str, str]] = []
    for record in records:
        score, reason = score_record(record)
        if score <= 0:
            continue
        scored.append((score, str(record["path"]), reason))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [{"path": path, "reason": reason} for score, path, reason in scored[:10]]


def analyze_repository(
    root: Path,
    includes: list[str],
    excludes: list[str],
    max_files: int,
) -> dict[str, object]:
    files, limits = walk_repository(root, includes=includes, excludes=excludes, max_files=max_files)
    languages = Counter()
    docs: list[str] = []
    manifests: list[str] = []
    records: list[dict[str, object]] = []

    for path in files:
        relative_path = path.relative_to(root).as_posix()
        language = detect_language(path)
        if language != "unknown":
            languages[language] += 1
        if is_doc(path):
            docs.append(relative_path)
        if is_manifest(path):
            manifests.append(relative_path)
        records.append(
            {
                "path": relative_path,
                "language": language,
                "roles": infer_roles(path),
            }
        )

    role_counts = Counter()
    for record in records:
        role_counts.update(str(role) for role in record["roles"])

    return {
        "source_repo": str(root),
        "project_name": project_name_from_scanned_files(root, files),
        "summary": {
            "total_files": len(records),
            "languages": [
                {"language": language, "count": count}
                for language, count in languages.most_common()
            ],
            "docs": sorted(set(docs)),
            "manifests": sorted(set(manifests)),
        },
        "directories": summarize_directories(records),
        "commands": collect_commands(root, files),
        "entry_candidates": build_entry_candidates(records),
        "reading_order": build_reading_order(records),
        "top_roles": [
            {"role": role, "count": count}
            for role, count in role_counts.most_common(6)
        ],
        "limits": limits,
        "scan": {
            "includes": includes,
            "excludes": excludes,
            "max_files": max_files,
        },
    }


def format_language_summary(summary: dict[str, object]) -> str:
    entries = summary.get("languages", [])
    if not entries:
        return "No clear language signal"
    return ", ".join(f'{entry["language"]} ({entry["count"]})' for entry in entries)


def render_project_map(analysis: dict[str, object]) -> str:
    summary = analysis["summary"]
    lines = [
        "# Project Map",
        "",
        "## Repository Overview",
        f'- Source repo: `{analysis["source_repo"]}`',
        f'- Project name: `{analysis["project_name"]}`',
        f'- Indexed files: {summary["total_files"]}',
        f'- Languages: {format_language_summary(summary)}',
        f'- Docs: {", ".join(f"`{path}`" for path in summary["docs"]) or "None"}',
        f'- Manifests: {", ".join(f"`{path}`" for path in summary["manifests"]) or "None"}',
        "",
        "## Command Hints",
    ]
    if analysis["commands"]:
        for command in analysis["commands"]:
            lines.append(f'- `{command["command"]}`: {command["reason"]}')
    else:
        lines.append("- No strong command hints were extracted from repository manifests.")

    lines.extend(
        [
            "",
            "## Important Directories",
        ]
    )
    if analysis["directories"]:
        for directory in analysis["directories"]:
            languages = ", ".join(
                f'{entry["language"]} ({entry["count"]})' for entry in directory["languages"]
            )
            lines.append(
                f'- `{directory["path"]}`: {directory["file_count"]} files'
                + (f"; {languages}" if languages else "")
            )
    else:
        lines.append("- No directory summary was produced.")

    lines.extend(
        [
            "",
            "## Likely Entrypoints",
        ]
    )
    if analysis["entry_candidates"]:
        for entry in analysis["entry_candidates"]:
            lines.append(f'- `{entry["path"]}`: {entry["reason"]}')
    else:
        lines.append("- No strong entrypoint candidates were detected.")

    lines.extend(
        [
            "",
            "## Suggested Reading Order",
        ]
    )
    if analysis["reading_order"]:
        for entry in analysis["reading_order"]:
            lines.append(f'- `{entry["path"]}`: {entry["reason"]}')
    else:
        lines.append("- No reading order was generated.")

    lines.extend(
        [
            "",
            "## Scan Limits",
        ]
    )
    if analysis["limits"]:
        for limit in analysis["limits"]:
            lines.append(f'- {limit["detail"]}')
    else:
        lines.append("- No scan limits were triggered.")

    return "\n".join(lines) + "\n"


def render_working_rules(analysis: dict[str, object], generated_skill_name: str) -> str:
    role_summary = ", ".join(
        f'{entry["role"]} ({entry["count"]})' for entry in analysis["top_roles"]
    ) or "No strong role signal"
    includes = analysis["scan"]["includes"] or ["repository root"]
    excludes = analysis["scan"]["excludes"] or ["default skip set only"]
    lines = [
        "# Working Rules",
        "",
        "## Trigger Patterns",
        f"- Use `${generated_skill_name}` when future sessions need quick repository orientation, command hints, reading order, or local guardrails for `{analysis['project_name']}`.",
        "- Invoke it before broad repository wandering, especially when the user asks where to start reading or how the project is structured.",
        "",
        "## Observed Facts",
        f"- Source repository: `{analysis['source_repo']}`",
        f"- Scan include scope: {', '.join(f'`{entry}`' for entry in includes)}",
        f"- Scan exclude scope: {', '.join(f'`{entry}`' for entry in excludes)}",
        f"- Dominant file roles: {role_summary}",
        "",
        "## Heuristic Sections",
        "- Treat command hints as likely commands, not executed proof.",
        "- Treat entrypoint and reading-order sections as scan heuristics that should be confirmed with direct file reads.",
        "",
        "## Guardrails",
        "- Start from docs and manifests before proposing broad changes.",
        "- Narrow to one subtree if the user question is package-scoped or feature-scoped.",
        "- Skip cache, vendor, temp, and generated folders unless the task explicitly targets them.",
        "- Refresh the generated package if the repository structure or command surface changes materially.",
        "",
        "## Refresh Guidance",
        f"- Re-run `$project-skill-builder` against `{analysis['source_repo']}` and replace this generated package when the repository drifts.",
        "- Compare the new `project-analysis.json` against the old one before keeping large wording changes.",
    ]
    return "\n".join(lines) + "\n"

def build_generated_skill_description(project_name: str) -> str:
    return (
        f"Use when working in the {project_name} repository and Codex needs repository-specific "
        "orientation, command hints, reading order, entrypoint discovery, and local guardrails "
        "before planning or making edits."
    )


def render_generated_skill_md(
    generated_skill_name: str,
    display_name: str,
    analysis: dict[str, object],
) -> str:
    description = build_generated_skill_description(str(analysis["project_name"]))
    command_hint = analysis["commands"][0]["command"] if analysis["commands"] else "run the most repo-specific command you verify locally"
    docs_reference = " and ".join(
        f"`{path}`" for path in analysis["summary"]["docs"][:2]
    ) or "`references/project-map.md`"
    return (
        f"---\n"
        f"name: {generated_skill_name}\n"
        f"description: {description}\n"
        f"---\n\n"
        f"# {display_name}\n\n"
        "## Overview\n\n"
        f"Use this generated skill when you need to work inside `{analysis['project_name']}` without rediscovering the same repository context from scratch.\n\n"
        "Start from the generated references, then confirm the smallest set of real files and commands needed for the current task.\n\n"
        "## Workflow\n\n"
        "1. Read `CLAUDE.md` to understand how this generated package is organized.\n"
        "2. Read `references/project-map.md` before opening many source files.\n"
        f"3. Start with repository orientation files such as {docs_reference} when they exist.\n"
        "4. Use `references/working-rules.md` to keep observed facts separate from heuristics.\n"
        f"5. Treat command hints such as `{command_hint}` as unverified until you actually run them.\n"
        "6. Narrow to the smallest relevant subtree once you know which package, app, or service matters.\n"
        "7. Refresh this generated skill if the repository structure or command surface has drifted.\n\n"
        "## Guardrails\n\n"
        "- Do not treat the generated reading order as proof of ownership.\n"
        "- Do not claim commands work unless you executed them in the current session.\n"
        "- Do not infer repository-wide conventions from skipped cache, vendor, temp, or generated folders.\n"
        "- Do not expand one package-scoped question into a full-repo redesign.\n\n"
        "## References\n\n"
        "- Read `CLAUDE.md` for module map and read order.\n"
        "- Read `references/project-map.md` for the repository snapshot used to generate this skill.\n"
        "- Read `references/working-rules.md` for trigger patterns, guardrails, and refresh guidance.\n"
    )


def render_generated_claude_md(
    generated_skill_name: str,
    display_name: str,
    analysis: dict[str, object],
) -> str:
    return (
        "# CLAUDE.md\n\n"
        f"Breadcrumbs: [Repository Root](../CLAUDE.md) / {generated_skill_name} / CLAUDE.md\n\n"
        "## Purpose\n\n"
        f"`{generated_skill_name}` is a generated repository-specific skill for `{analysis['project_name']}`. Use it as the fast orientation surface before reading deeper project files.\n\n"
        "## Module Map\n\n"
        "```mermaid\n"
        "flowchart TD\n"
        f'  root["{generated_skill_name}/"] --> skill["SKILL.md<br/>Trigger rules and workflow"]\n'
        '  root --> claude["CLAUDE.md<br/>Module map and read order"]\n'
        '  root --> meta["agents/openai.yaml<br/>Display metadata"]\n'
        '  root --> refs["references/<*.md><br/>Project map and working rules"]\n'
        '  root --> artifacts["artifacts/project-analysis.json<br/>Machine-readable scan evidence"]\n'
        "```\n\n"
        "## Entry Points\n\n"
        "Read files in this order:\n\n"
        "1. `SKILL.md`\n"
        "2. `references/project-map.md`\n"
        "3. `references/working-rules.md`\n"
        "4. `artifacts/project-analysis.json` when you need raw scan evidence\n\n"
        "## Output Contract\n\n"
        "This generated package preserves two kinds of information:\n\n"
        "- observed scan output in `references/project-map.md` and `artifacts/project-analysis.json`\n"
        "- reusable guidance in `SKILL.md` and `references/working-rules.md`\n\n"
        "## Important Constraints\n\n"
        "- Command hints are not execution proof.\n"
        "- Reading order and entrypoints remain heuristics until confirmed.\n"
        "- Refresh the package when the repository structure changes materially.\n"
    )


def render_generated_openai_yaml(generated_skill_name: str, display_name: str) -> str:
    short_description = "Repository-specific workflow guide"
    default_prompt = (
        f"Use ${generated_skill_name} to work in this repository by starting from the generated "
        "project map, command hints, and local guardrails."
    )
    return (
        "interface:\n"
        f"  display_name: {yaml_quote(display_name)}\n"
        f"  short_description: {yaml_quote(short_description)}\n"
        f"  default_prompt: {yaml_quote(default_prompt)}\n"
    )


def scaffold_generated_skill(
    output_dir: Path,
    generated_skill_name: str,
    analysis: dict[str, object],
    force: bool,
) -> tuple[Path, Path]:
    skill_dir = output_dir / generated_skill_name
    if skill_dir.exists():
        if not force:
            raise FileExistsError(
                f"Generated skill directory already exists: {skill_dir}. Re-run with --force to replace it."
            )
        shutil.rmtree(skill_dir)

    display_name = title_case_skill_name(generated_skill_name)
    references_dir = skill_dir / "references"
    agents_dir = skill_dir / "agents"
    artifacts_dir = skill_dir / "artifacts"
    references_dir.mkdir(parents=True, exist_ok=False)
    agents_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    (skill_dir / "SKILL.md").write_text(
        render_generated_skill_md(generated_skill_name, display_name, analysis),
        encoding="utf-8",
    )
    (skill_dir / "CLAUDE.md").write_text(
        render_generated_claude_md(generated_skill_name, display_name, analysis),
        encoding="utf-8",
    )
    (agents_dir / "openai.yaml").write_text(
        render_generated_openai_yaml(generated_skill_name, display_name),
        encoding="utf-8",
    )
    (references_dir / "project-map.md").write_text(
        render_project_map(analysis),
        encoding="utf-8",
    )
    (references_dir / "working-rules.md").write_text(
        render_working_rules(analysis, generated_skill_name),
        encoding="utf-8",
    )
    analysis_json = artifacts_dir / "project-analysis.json"
    analysis_json.write_text(json.dumps(analysis, indent=2, ensure_ascii=True), encoding="utf-8")
    return skill_dir, analysis_json


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.project_root).resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Project root is not a directory: {root}")

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_skill_name = normalize_hyphen_name(args.skill_name)
    includes = normalize_prefixes(args.include)
    excludes = normalize_prefixes(args.exclude)
    analysis = analyze_repository(
        root=root,
        includes=includes,
        excludes=excludes,
        max_files=max(1, args.max_files),
    )
    skill_dir, analysis_json = scaffold_generated_skill(
        output_dir=output_dir,
        generated_skill_name=generated_skill_name,
        analysis=analysis,
        force=args.force,
    )
    print(f"SKILL_DIR={skill_dir}")
    print(f"ANALYSIS_JSON={analysis_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

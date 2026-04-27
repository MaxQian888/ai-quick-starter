#!/usr/bin/env python3
"""Build a lightweight Markdown and JSON index for an unfamiliar repository."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
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
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "out",
    "target",
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
    ".min.js",
    ".min.css",
    ".pdf",
    ".png",
    ".pyc",
    ".pyo",
    ".so",
    ".svg",
    ".webp",
    ".zip",
}
MANIFEST_NAMES = {
    "Cargo.toml",
    "Gemfile",
    "Makefile",
    "Pipfile",
    "build.gradle",
    "build.gradle.kts",
    "composer.json",
    "go.mod",
    "package.json",
    "pom.xml",
    "pyproject.toml",
    "requirements.txt",
}
DOC_NAMES = {
    "architecture.md",
    "contributing.md",
    "readme.md",
}
INTERNAL_INDEX_PARENT_HINTS = {
    "__tests__",
    "components",
    "fixtures",
    "hooks",
    "lib",
    "mocks",
    "services",
    "tests",
    "utils",
}
ENTRY_PREFIXES = ("app", "cli", "index", "main", "manage", "server")
CONFIG_SUFFIXES = (".json", ".toml", ".yaml", ".yml", ".ini", ".cfg")
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
ENTRY_EXTENSIONS = SOURCE_EXTENSIONS | {".html"}
LANGUAGE_BY_SUFFIX = {
    ".c": "C",
    ".cc": "C++",
    ".cpp": "C++",
    ".cs": "C#",
    ".css": "CSS",
    ".go": "Go",
    ".html": "HTML",
    ".java": "Java",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".json": "JSON",
    ".md": "Markdown",
    ".mjs": "JavaScript",
    ".py": "Python",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".scss": "SCSS",
    ".sh": "Shell",
    ".sql": "SQL",
    ".swift": "Swift",
    ".toml": "TOML",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".xml": "XML",
    ".yaml": "YAML",
    ".yml": "YAML",
}
IMPORT_PATTERNS = {
    "Python": [
        re.compile(r"^\s*from\s+([A-Za-z0-9_\.]+)\s+import\b", re.MULTILINE),
        re.compile(r"^\s*import\s+([A-Za-z0-9_\.]+)", re.MULTILINE),
    ],
    "JavaScript": [
        re.compile(r"""import\s+.*?from\s+['"]([^'"]+)['"]"""),
        re.compile(r"""require\(['"]([^'"]+)['"]\)"""),
    ],
    "TypeScript": [
        re.compile(r"""import\s+.*?from\s+['"]([^'"]+)['"]"""),
        re.compile(r"""require\(['"]([^'"]+)['"]\)"""),
    ],
    "Go": [
        re.compile(r'"([^"\n]+)"'),
    ],
}
SYMBOL_PATTERNS = {
    "Python": [
        re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE),
        re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)\s*[\(:]", re.MULTILINE),
    ],
    "JavaScript": [
        re.compile(r"^\s*export\s+function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE),
        re.compile(r"^\s*function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE),
    ],
    "TypeScript": [
        re.compile(r"^\s*export\s+function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE),
        re.compile(r"^\s*function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE),
    ],
}
COMMAND_PRIORITY = ("dev", "start", "build", "test", "lint", "typecheck", "check")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan a repository and emit a lightweight Markdown and JSON index."
    )
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    parser.add_argument("--markdown-out", default="", help="Explicit output path for Markdown.")
    parser.add_argument("--json-out", default="", help="Explicit output path for JSON.")
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
    parser.add_argument("--max-files", type=int, default=400, help="Cap matching files scanned.")
    parser.add_argument(
        "--focus",
        default="",
        help="Optional keyword to boost matching files in reading order.",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=2,
        help="Directory summary depth.",
    )
    return parser.parse_args(argv)


def normalize_prefixes(values: list[str]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        cleaned = value.replace("\\", "/").strip().strip("/")
        if cleaned:
            normalized.append(cleaned)
    return normalized


def resolve_output_path(raw_path: str, suffix: str) -> Path:
    if raw_path:
        output_path = Path(raw_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path

    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="codebase-index-")
    handle.close()
    return Path(handle.name).resolve()


def path_matches_prefix(relative_path: str, prefix: str) -> bool:
    return relative_path == prefix or relative_path.startswith(f"{prefix}/")


def should_include_path(relative_path: str, includes: list[str], excludes: list[str]) -> bool:
    if includes and not any(path_matches_prefix(relative_path, prefix) for prefix in includes):
        return False
    if any(path_matches_prefix(relative_path, prefix) for prefix in excludes):
        return False
    return True


def should_skip_directory(relative_path: str, name: str, excludes: list[str]) -> bool:
    if name in IGNORED_DIR_NAMES:
        return True
    if relative_path and any(path_matches_prefix(relative_path, prefix) for prefix in excludes):
        return True
    return False


def should_skip_file(path: Path) -> bool:
    suffixes = path.suffixes
    if suffixes:
        suffix = "".join(suffixes[-2:]) if len(suffixes) >= 2 else suffixes[-1]
        if suffix in IGNORED_FILE_SUFFIXES or path.suffix in IGNORED_FILE_SUFFIXES:
            return True
    return False


def walk_repository(
    root: Path,
    includes: list[str],
    excludes: list[str],
    max_files: int,
) -> tuple[list[Path], list[dict[str, str]]]:
    matching_files: list[Path] = []
    limits: list[dict[str, str]] = []

    for current_root, dir_names, file_names in os.walk(root):
        current_path = Path(current_root)
        relative_root = current_path.relative_to(root).as_posix() if current_path != root else ""
        dir_names[:] = [
            name
            for name in sorted(dir_names)
            if not should_skip_directory(
                f"{relative_root}/{name}".strip("/"),
                name,
                excludes,
            )
        ]

        for file_name in sorted(file_names):
            file_path = current_path / file_name
            if should_skip_file(file_path):
                continue

            relative_path = file_path.relative_to(root).as_posix()
            if not should_include_path(relative_path, includes, excludes):
                continue

            matching_files.append(file_path)
            if len(matching_files) >= max_files:
                limits.append(
                    {
                        "kind": "max-files",
                        "detail": f"Stopped after indexing {max_files} matching files.",
                    }
                )
                return matching_files, limits

    return matching_files, limits


def detect_language(path: Path) -> str:
    if path.name == "Dockerfile":
        return "Docker"
    return LANGUAGE_BY_SUFFIX.get(path.suffix.lower(), "unknown")


def is_manifest(path: Path) -> bool:
    return path.name in MANIFEST_NAMES


def is_doc(path: Path) -> bool:
    lower_name = path.name.lower()
    if lower_name in DOC_NAMES or lower_name.startswith("readme"):
        return True
    return path.suffix.lower() in {".md", ".rst"} and "docs" in {part.lower() for part in path.parts}


def infer_roles(relative_path: str, path: Path) -> list[str]:
    roles: set[str] = set()
    lower_name = path.stem.lower()
    lower_parts = [part.lower() for part in path.parts]
    internal_index = lower_name == "index" and any(part in INTERNAL_INDEX_PARENT_HINTS for part in lower_parts[:-1])

    if is_doc(path):
        roles.add("docs")
    if is_manifest(path):
        roles.add("config")
        roles.add("build")
    if path.suffix.lower() in CONFIG_SUFFIXES or lower_name.endswith("config"):
        roles.add("config")
    if any(token in lower_name for token in ("test", "spec")) or any(
        token in lower_parts for token in ("test", "tests", "__tests__")
    ):
        roles.add("test")
    if lower_name.startswith(ENTRY_PREFIXES) and path.suffix.lower() in ENTRY_EXTENSIONS and not internal_index:
        roles.add("entry")
    if any(part in {"api", "apis", "routes", "controllers", "handlers"} for part in lower_parts):
        roles.add("api")
    if path.suffix.lower() in {".jsx", ".tsx"} or any(
        part in {"components", "pages", "views", "screens"} for part in lower_parts
    ):
        roles.add("ui")
    if path.suffix.lower() in SOURCE_EXTENSIONS and not roles.intersection({"entry", "test", "ui", "api"}):
        roles.add("library")
    if lower_name in {"schema", "models"} or path.suffix.lower() in {".sql", ".graphql"}:
        roles.add("schema")

    return sorted(roles)


def read_text_excerpt(path: Path) -> str:
    if path.suffix.lower() not in SOURCE_EXTENSIONS | {".md", ".rst", ".json", ".toml", ".yaml", ".yml"}:
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:24000]
    except OSError:
        return ""


def extract_matches(text: str, patterns: list[re.Pattern[str]]) -> list[str]:
    matches: list[str] = []
    for pattern in patterns:
        matches.extend(pattern.findall(text))
    deduped: list[str] = []
    seen: set[str] = set()
    for match in matches:
        normalized = match.strip()
        if normalized and normalized not in seen:
            deduped.append(normalized)
            seen.add(normalized)
    return deduped[:12]


def extract_imports(language: str, text: str) -> list[str]:
    patterns = IMPORT_PATTERNS.get(language, [])
    return extract_matches(text, patterns)


def extract_symbols(language: str, text: str) -> list[str]:
    patterns = SYMBOL_PATTERNS.get(language, [])
    return extract_matches(text, patterns)


def determine_entry_reason(relative_path: str) -> str:
    path = Path(relative_path)
    stem = path.stem.lower()
    if stem.startswith("main"):
        return "Matched a conventional main entry filename."
    if stem.startswith("server"):
        return "Matched a conventional server bootstrap filename."
    if stem.startswith("app"):
        return "Matched a conventional application bootstrap filename."
    if stem.startswith("index"):
        return "Matched a conventional index bootstrap filename."
    return "Matched a common bootstrap filename pattern."


def determine_file_reason(relative_path: str, roles: list[str], imports: list[str]) -> str:
    if "entry" in roles:
        return determine_entry_reason(relative_path)
    if relative_path.lower().startswith("readme"):
        return "Repository readme often explains setup and architecture."
    if "config" in roles and Path(relative_path).name in MANIFEST_NAMES:
        return "Manifest likely defines dependencies, scripts, or build settings."
    if imports:
        return "Imports other modules and is likely part of a feature path."
    if "docs" in roles:
        return "Documentation file that may explain project intent."
    if "test" in roles:
        return "Tests often reveal expected behavior and important seams."
    return "Useful supporting file discovered during the repository scan."


def determine_importance(relative_path: str, roles: list[str]) -> str:
    if "entry" in roles or relative_path.lower().startswith("readme"):
        return "high"
    if "config" in roles or "api" in roles or "ui" in roles:
        return "medium"
    return "low"


def collect_package_json_commands(root: Path) -> list[dict[str, str]]:
    package_path = root / "package.json"
    if not package_path.exists():
        return []

    try:
        package_data = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    scripts = package_data.get("scripts", {})
    if not isinstance(scripts, dict):
        return []

    if (root / "pnpm-lock.yaml").exists():
        package_manager = "pnpm"
    elif (root / "yarn.lock").exists():
        package_manager = "yarn"
    elif (root / "bun.lock").exists() or (root / "bun.lockb").exists():
        package_manager = "bun"
    else:
        package_manager = "npm"

    ordered_names = list(COMMAND_PRIORITY) + sorted(
        name for name in scripts if name not in COMMAND_PRIORITY
    )
    commands: list[dict[str, str]] = []
    for script_name in ordered_names:
        if script_name not in scripts:
            continue
        if package_manager == "pnpm":
            command = f"pnpm {script_name}"
        elif package_manager == "yarn":
            command = f"yarn {script_name}"
        elif package_manager == "bun":
            command = f"bun run {script_name}"
        else:
            command = f"npm run {script_name}"
        commands.append(
            {
                "command": command,
                "source": "package.json",
                "reason": f'Found the "{script_name}" script in package.json.',
            }
        )
    return commands


def collect_pyproject_commands(root: Path) -> list[dict[str, str]]:
    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.exists():
        return []

    try:
        payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return []

    commands: list[dict[str, str]] = []
    tool_table = payload.get("tool", {})
    if isinstance(tool_table, dict):
        if "pytest" in tool_table:
            commands.append(
                {
                    "command": "python -m pytest",
                    "source": "pyproject.toml",
                    "reason": "Detected pytest configuration in pyproject.toml.",
                }
            )
        if "ruff" in tool_table:
            commands.append(
                {
                    "command": "python -m ruff check .",
                    "source": "pyproject.toml",
                    "reason": "Detected Ruff configuration in pyproject.toml.",
                }
            )
        if "mypy" in tool_table:
            commands.append(
                {
                    "command": "python -m mypy .",
                    "source": "pyproject.toml",
                    "reason": "Detected mypy configuration in pyproject.toml.",
                }
            )
    return commands


def collect_make_commands(root: Path) -> list[dict[str, str]]:
    makefile_path = root / "Makefile"
    if not makefile_path.exists():
        return []

    try:
        text = makefile_path.read_text(encoding="utf-8")
    except OSError:
        return []

    commands: list[dict[str, str]] = []
    for target in COMMAND_PRIORITY:
        pattern = re.compile(rf"^{re.escape(target)}\s*:", re.MULTILINE)
        if pattern.search(text):
            commands.append(
                {
                    "command": f"make {target}",
                    "source": "Makefile",
                    "reason": f'Found the "{target}" target in Makefile.',
                }
            )
    return commands


def collect_commands(root: Path) -> list[dict[str, str]]:
    commands = collect_package_json_commands(root)
    commands.extend(
        command
        for command in collect_pyproject_commands(root)
        if command["command"] not in {record["command"] for record in commands}
    )
    commands.extend(
        command
        for command in collect_make_commands(root)
        if command["command"] not in {record["command"] for record in commands}
    )
    return commands[:10]


def build_directory_summary(
    records: list[dict[str, object]],
    depth: int,
) -> list[dict[str, object]]:
    directory_counts: dict[str, Counter[str]] = defaultdict(Counter)

    for record in records:
        path = Path(str(record["path"]))
        if not path.parts:
            key = "."
        else:
            key = "/".join(path.parts[:depth])
        language = str(record["language"])
        directory_counts[key]["__files__"] += 1
        if language != "unknown":
            directory_counts[key][language] += 1

    directories: list[dict[str, object]] = []
    for directory, counts in directory_counts.items():
        file_count = counts.pop("__files__", 0)
        languages = [
            {"language": language, "count": count}
            for language, count in counts.most_common(3)
        ]
        directories.append(
            {
                "path": directory,
                "file_count": file_count,
                "languages": languages,
            }
        )

    directories.sort(key=lambda item: (-int(item["file_count"]), str(item["path"])))
    return directories[:12]


def score_record(record: dict[str, object], focus: str) -> tuple[int, str]:
    path = str(record["path"])
    roles = set(str(role) for role in record["roles"])
    score = 0
    reasons: list[str] = []

    if path.lower().startswith("readme"):
        score += 100
        reasons.append("Read the repository overview first.")
    if "config" in roles and Path(path).name in MANIFEST_NAMES:
        score += 90
        reasons.append("Manifest reveals dependencies and scripts.")
    if "entry" in roles:
        score += 80
        reasons.append("Likely bootstrap or entrypoint.")
    if "api" in roles or "ui" in roles:
        score += 45
        reasons.append("Touches a major application surface.")
    if "test" in roles:
        score += 25
        reasons.append("Tests reveal expected behavior.")

    if focus and focus in path.lower():
        score += 30
        reasons.append(f'Matches focus keyword "{focus}".')

    if not reasons:
        reasons.append("Representative file from the scan.")

    return score, " ".join(reasons)


def build_entry_candidates(records: list[dict[str, object]]) -> list[dict[str, str]]:
    priority_by_stem = {
        "main": 0,
        "server": 1,
        "app": 2,
        "index": 3,
        "cli": 4,
        "manage": 5,
    }
    entries: list[dict[str, str]] = []
    for record in records:
        roles = set(str(role) for role in record["roles"])
        if "entry" not in roles:
            continue
        entries.append(
            {
                "path": str(record["path"]),
                "reason": determine_entry_reason(str(record["path"])),
            }
        )
    entries.sort(
        key=lambda item: (
            priority_by_stem.get(Path(item["path"]).stem.lower(), 99),
            item["path"].count("/"),
            item["path"],
        )
    )
    return entries[:8]


def build_reading_order(records: list[dict[str, object]], focus: str) -> list[dict[str, str]]:
    scored: list[tuple[int, str, str]] = []
    for record in records:
        score, reason = score_record(record, focus)
        if score <= 0:
            continue
        scored.append((score, str(record["path"]), reason))

    scored.sort(key=lambda item: (-item[0], item[1]))
    return [
        {"path": path, "reason": reason}
        for _, path, reason in scored[:8]
    ]


def scan_repository(
    root: Path,
    includes: list[str],
    excludes: list[str],
    max_files: int,
    focus: str,
    depth: int,
) -> dict[str, object]:
    file_paths, limits = walk_repository(root=root, includes=includes, excludes=excludes, max_files=max_files)
    docs: list[str] = []
    manifests: list[str] = []
    languages = Counter()
    records: list[dict[str, object]] = []

    for file_path in file_paths:
        relative_path = file_path.relative_to(root).as_posix()
        language = detect_language(file_path)
        if language != "unknown":
            languages[language] += 1

        roles = infer_roles(relative_path, file_path)
        text = read_text_excerpt(file_path)
        imports = extract_imports(language, text)
        symbols = extract_symbols(language, text)
        reason = determine_file_reason(relative_path, roles, imports)

        if is_doc(file_path):
            docs.append(relative_path)
        if is_manifest(file_path):
            manifests.append(relative_path)

        records.append(
            {
                "path": relative_path,
                "extension": file_path.suffix.lower(),
                "language": language,
                "roles": roles,
                "imports": imports,
                "symbols": symbols,
                "importance": determine_importance(relative_path, roles),
                "reason": reason,
            }
        )

    records.sort(key=lambda item: str(item["path"]))
    docs = sorted(set(docs))
    manifests = sorted(set(manifests))
    commands = collect_commands(root)
    directories = build_directory_summary(records, depth=depth)
    entry_candidates = build_entry_candidates(records)
    reading_order = build_reading_order(records, focus=focus)

    return {
        "repo_root": str(root),
        "summary": {
            "total_files": len(records),
            "languages": [
                {"language": language, "count": count}
                for language, count in languages.most_common()
            ],
            "docs": docs,
            "manifests": manifests,
        },
        "directories": directories,
        "files": records,
        "commands": commands,
        "entry_candidates": entry_candidates,
        "reading_order": reading_order,
        "limits": limits,
    }


def format_language_summary(summary: dict[str, object]) -> str:
    language_parts = []
    for entry in summary["languages"]:
        language_parts.append(f'{entry["language"]} ({entry["count"]})')
    return ", ".join(language_parts) if language_parts else "No clear language signal"


def render_markdown(index: dict[str, object]) -> str:
    summary = index["summary"]
    lines = [
        "# Codebase Index",
        "",
        "## Repository Overview",
        f'- Root: `{index["repo_root"]}`',
        f'- Indexed files: {summary["total_files"]}',
        f'- Languages: {format_language_summary(summary)}',
        f'- Docs: {", ".join(f"`{path}`" for path in summary["docs"]) or "None"}',
        f'- Manifests: {", ".join(f"`{path}`" for path in summary["manifests"]) or "None"}',
        "",
    ]

    if index["commands"]:
        lines.append("### Command Hints")
        for command in index["commands"]:
            lines.append(
                f'- `{command["command"]}`: {command["reason"]}'
            )
        lines.append("")

    lines.extend(
        [
            "## Structure Summary",
        ]
    )
    for directory in index["directories"]:
        languages = ", ".join(
            f'{entry["language"]} ({entry["count"]})' for entry in directory["languages"]
        )
        lines.append(
            f'- `{directory["path"]}`: {directory["file_count"]} files'
            + (f"; {languages}" if languages else "")
        )
    if not index["directories"]:
        lines.append("- No directories matched the scan.")
    lines.append("")

    lines.append("## Likely Entrypoints and Key Files")
    for entry in index["entry_candidates"]:
        lines.append(f'- `{entry["path"]}`: {entry["reason"]}')
    if not index["entry_candidates"]:
        lines.append("- No strong entrypoint candidates were detected.")
    lines.append("")

    lines.append("## Module and File Roles")
    high_value_files = [record for record in index["files"] if record["importance"] != "low"][:10]
    for record in high_value_files:
        roles = ", ".join(record["roles"]) or "unclassified"
        lines.append(f'- `{record["path"]}`: {roles}; {record["reason"]}')
    if not high_value_files:
        lines.append("- No high-value files were identified.")
    lines.append("")

    lines.append("## Dependency Clues")
    dependency_rows = [record for record in index["files"] if record["imports"]][:8]
    for record in dependency_rows:
        preview = ", ".join(record["imports"][:5])
        lines.append(f'- `{record["path"]}` imports `{preview}`')
    if not dependency_rows:
        lines.append("- No lightweight import clues were extracted.")
    lines.append("")

    lines.append("## Suggested Reading Order")
    for entry in index["reading_order"]:
        lines.append(f'- `{entry["path"]}`: {entry["reason"]}')
    if not index["reading_order"]:
        lines.append("- No reading order was generated.")
    lines.append("")

    lines.append("## Risks and Blind Spots")
    lines.append("- Results are heuristic and should be confirmed with direct file reads before risky edits.")
    lines.append("- Import extraction is shallow and may miss framework-specific wiring or generated code.")
    if index["limits"]:
        for limit in index["limits"]:
            lines.append(f'- Limit: {limit["detail"]}')
    else:
        lines.append("- No scan limits were triggered.")
    lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if not root.exists():
        raise SystemExit(f"Repository root does not exist: {root}")

    includes = normalize_prefixes(args.include)
    excludes = normalize_prefixes(args.exclude)
    markdown_path = resolve_output_path(args.markdown_out, ".md")
    json_path = resolve_output_path(args.json_out, ".json")

    payload = scan_repository(
        root=root,
        includes=includes,
        excludes=excludes,
        max_files=args.max_files,
        focus=args.focus.strip().lower(),
        depth=max(1, args.depth),
    )

    markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")

    print(f"MARKDOWN_OUT={markdown_path}")
    print(f"JSON_OUT={json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

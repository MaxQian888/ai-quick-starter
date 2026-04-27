#!/usr/bin/env python3
"""Build an evidence-backed architecture and design report for a repository."""

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
    ".uv-cache",
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
DOC_NAMES = {
    "AGENTS.md",
    "CLAUDE.md",
    "README.md",
    "architecture.md",
    "contributing.md",
    "design.md",
}
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
ROOT_CONTEXT_DOCS = {"agents.md", "claude.md"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze a repository and emit architecture and design reports.",
    )
    parser.add_argument("--root", required=True, help="Repository root to analyze.")
    parser.add_argument("--markdown-out", default="", help="Explicit path for Markdown output.")
    parser.add_argument("--json-out", default="", help="Explicit path for JSON output.")
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
        "--focus",
        default="",
        help="Optional keyword or phrase that should bias architecture findings.",
    )
    parser.add_argument("--max-files", type=int, default=500, help="Cap matching files scanned.")
    parser.add_argument("--depth", type=int, default=2, help="Directory summary depth.")
    return parser.parse_args(argv)


def normalize_prefixes(values: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = value.replace("\\", "/").strip().strip("/")
        if cleaned and cleaned not in seen:
            normalized.append(cleaned)
            seen.add(cleaned)
    return normalized


def resolve_output_path(raw_path: str, suffix: str) -> Path:
    if raw_path:
        output_path = Path(raw_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path

    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="project-architecture-")
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
        compound_suffix = "".join(suffixes[-2:]) if len(suffixes) >= 2 else suffixes[-1]
        if compound_suffix in IGNORED_FILE_SUFFIXES or path.suffix.lower() in IGNORED_FILE_SUFFIXES:
            return True
    return False


def walk_repository(
    root: Path,
    includes: list[str],
    excludes: list[str],
    max_files: int,
) -> tuple[list[Path], list[dict[str, str]]]:
    matches: list[Path] = []
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
            matches.append(file_path)
            if len(matches) >= max_files:
                limits.append(
                    {
                        "kind": "max-files",
                        "detail": f"Scan stopped after {max_files} matching files.",
                    }
                )
                return matches, limits
    return matches, limits


def detect_language(path: Path) -> str:
    return LANGUAGE_BY_SUFFIX.get(path.suffix.lower(), "unknown")


def is_doc(path: Path) -> bool:
    lower_name = path.name.lower()
    if path.name in DOC_NAMES or lower_name.startswith("readme"):
        return True
    return path.suffix.lower() in {".md", ".rst"} and "docs" in {part.lower() for part in path.parts}


def is_manifest(path: Path) -> bool:
    return path.name in MANIFEST_NAMES


def read_text_excerpt(path: Path, limit: int = 16000) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")[:limit]
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="utf-8-sig", errors="ignore")[:limit]
        except OSError:
            return ""
    except OSError:
        return ""


def infer_roles(relative_path: str, file_path: Path) -> list[str]:
    roles: set[str] = set()
    lower_parts = [part.lower() for part in file_path.parts]
    stem = file_path.stem.lower()

    if is_doc(file_path):
        roles.add("docs")
    if is_manifest(file_path):
        roles.add("manifest")
        roles.add("config")
    if file_path.suffix.lower() in {".json", ".toml", ".yaml", ".yml", ".ini", ".cfg"}:
        roles.add("config")
    if stem.startswith(("app", "main", "server", "index", "manage")) and file_path.suffix.lower() in SOURCE_EXTENSIONS:
        roles.add("entry")
    if any(part in {"route", "routes", "router", "routers", "api", "apis"} for part in lower_parts):
        roles.add("api")
    if any(part in {"component", "components", "pages", "screens", "views", "app"} for part in lower_parts):
        roles.add("ui")
    if any(part in {"service", "services"} for part in lower_parts):
        roles.add("service")
    if any(part in {"repository", "repositories", "repo", "repos", "db", "database"} for part in lower_parts):
        roles.add("data")
    if any(part in {"model", "models", "entity", "entities", "schema", "schemas"} for part in lower_parts):
        roles.add("domain")
    if any(token in stem for token in ("test", "spec")) or any(
        token in lower_parts for token in ("tests", "test", "__tests__")
    ):
        roles.add("test")
    if file_path.suffix.lower() in SOURCE_EXTENSIONS and not roles.intersection({"api", "ui", "service", "data", "domain", "entry", "test"}):
        roles.add("library")
    if any(part.lower() in {"script", "scripts", "bin"} for part in file_path.parts):
        roles.add("automation")
    if relative_path.count("/") == 0:
        roles.add("root")
    return sorted(roles)


def extract_symbols(language: str, text: str) -> list[str]:
    patterns: list[re.Pattern[str]] = []
    if language == "Python":
        patterns = [
            re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE),
            re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)\s*[\(:]", re.MULTILINE),
        ]
    elif language in {"JavaScript", "TypeScript"}:
        patterns = [
            re.compile(r"^\s*export\s+function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE),
            re.compile(r"^\s*function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE),
            re.compile(r"^\s*export\s+default\s+function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE),
            re.compile(r"^\s*export\s+class\s+([A-Za-z_][A-Za-z0-9_]*)\s*", re.MULTILINE),
        ]

    symbols: list[str] = []
    for pattern in patterns:
        for match in pattern.findall(text):
            if match not in symbols:
                symbols.append(match)
    return symbols[:20]


def extract_imports(language: str, text: str) -> list[str]:
    patterns: list[re.Pattern[str]] = []
    if language == "Python":
        patterns = [
            re.compile(r"^\s*from\s+([A-Za-z0-9_\.]+)\s+import\b", re.MULTILINE),
            re.compile(r"^\s*import\s+([A-Za-z0-9_\.]+)", re.MULTILINE),
        ]
    elif language in {"JavaScript", "TypeScript"}:
        patterns = [
            re.compile(r"""import\s+.*?from\s+['"]([^'"]+)['"]"""),
            re.compile(r"""require\(['"]([^'"]+)['"]\)"""),
        ]

    imports: list[str] = []
    for pattern in patterns:
        for match in pattern.findall(text):
            module_name = match.strip()
            if module_name and module_name not in imports:
                imports.append(module_name)
    return imports[:40]


def determine_file_reason(relative_path: str, roles: list[str], focus_terms: list[str]) -> str:
    lower_path = relative_path.lower()
    if any(term in lower_path for term in focus_terms):
        return "Path matches the requested focus terms."
    if "entry" in roles:
        return "Likely bootstrap or entrypoint surface."
    if "manifest" in roles:
        return "Manifest reveals commands or dependency surface."
    if "docs" in roles:
        return "Documentation may describe architecture intent."
    if "service" in roles or "data" in roles:
        return "Touches an implementation boundary that often matters in architecture reviews."
    return "General implementation file retained for architecture summary."


def relative_parent_bucket(relative_path: str) -> str:
    parent = Path(relative_path).parent.as_posix()
    return parent if parent else "."


def resolve_js_import(current_path: str, import_value: str, all_paths: set[str]) -> str | None:
    if not import_value.startswith("."):
        return None

    current_parent = Path(current_path).parent
    target_base = (current_parent / import_value).as_posix()
    candidates = [
        target_base,
        f"{target_base}.js",
        f"{target_base}.jsx",
        f"{target_base}.mjs",
        f"{target_base}.ts",
        f"{target_base}.tsx",
        f"{target_base}/index.js",
        f"{target_base}/index.ts",
        f"{target_base}/index.tsx",
    ]
    for candidate in candidates:
        normalized = Path(candidate).as_posix()
        if normalized in all_paths:
            return normalized
    return None


def resolve_python_import(import_value: str, all_paths: set[str]) -> str | None:
    if import_value.startswith("."):
        return None

    module_suffix = import_value.replace(".", "/")
    candidates = [
        f"{module_suffix}.py",
        f"{module_suffix}/__init__.py",
    ]
    for candidate in candidates:
        for path in all_paths:
            if path.endswith(candidate):
                return path
    return None


def resolve_import_target(language: str, current_path: str, import_value: str, all_paths: set[str]) -> str | None:
    if language in {"JavaScript", "TypeScript"}:
        return resolve_js_import(current_path, import_value, all_paths)
    if language == "Python":
        return resolve_python_import(import_value, all_paths)
    return None


def collect_commands(file_paths: list[Path]) -> list[dict[str, str]]:
    commands: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for path in file_paths:
        if path.name == "package.json":
            try:
                payload = json.loads(read_text_excerpt(path, limit=50000) or "{}")
            except json.JSONDecodeError:
                continue
            scripts = payload.get("scripts", {})
            if not isinstance(scripts, dict):
                continue
            for key, value in scripts.items():
                if not isinstance(value, str):
                    continue
                marker = (f"npm run {key}", path.as_posix())
                if marker in seen:
                    continue
                seen.add(marker)
                commands.append(
                    {
                        "command": marker[0],
                        "source": path.as_posix(),
                        "reason": f"`package.json` exposes a `{key}` script.",
                    }
                )
        elif path.name == "pyproject.toml":
            try:
                payload = tomllib.loads(read_text_excerpt(path, limit=50000))
            except tomllib.TOMLDecodeError:
                continue
            tool = payload.get("tool", {})
            if isinstance(tool, dict) and "pytest" in tool:
                marker = ("python -m pytest", path.as_posix())
                if marker not in seen:
                    seen.add(marker)
                    commands.append(
                        {
                            "command": marker[0],
                            "source": path.as_posix(),
                            "reason": "`pyproject.toml` configures pytest.",
                        }
                    )
            if isinstance(tool, dict) and "ruff" in tool:
                marker = ("python -m ruff check .", path.as_posix())
                if marker not in seen:
                    seen.add(marker)
                    commands.append(
                        {
                            "command": marker[0],
                            "source": path.as_posix(),
                            "reason": "`pyproject.toml` configures Ruff.",
                        }
                    )
        elif path.name == "Makefile":
            content = read_text_excerpt(path, limit=30000)
            for target in re.findall(r"^([A-Za-z0-9_-]+):", content, re.MULTILINE):
                if target in COMMAND_PRIORITY:
                    marker = (f"make {target}", path.as_posix())
                    if marker not in seen:
                        seen.add(marker)
                        commands.append(
                            {
                                "command": marker[0],
                                "source": path.as_posix(),
                                "reason": "Makefile exposes a matching workflow target.",
                            }
                        )
        elif path.name == "Cargo.toml":
            for command in ("cargo build", "cargo test"):
                marker = (command, path.as_posix())
                if marker not in seen:
                    seen.add(marker)
                    commands.append(
                        {
                            "command": command,
                            "source": path.as_posix(),
                            "reason": "Cargo project detected.",
                        }
                    )
        elif path.name == "go.mod":
            for command in ("go test ./...", "go build ./..."):
                marker = (command, path.as_posix())
                if marker not in seen:
                    seen.add(marker)
                    commands.append(
                        {
                            "command": command,
                            "source": path.as_posix(),
                            "reason": "Go module detected.",
                        }
                    )

    def sort_key(entry: dict[str, str]) -> tuple[int, str]:
        command = entry["command"]
        for index, keyword in enumerate(COMMAND_PRIORITY):
            if keyword in command:
                return index, command
        return len(COMMAND_PRIORITY), command

    return sorted(commands, key=sort_key)


def build_entry_candidates(records: list[dict[str, object]], focus_terms: list[str]) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    for record in records:
        roles = set(str(role) for role in record["roles"])
        path = str(record["path"])
        score = 0
        reasons: list[str] = []
        if "entry" in roles:
            score += 90
            reasons.append("Filename and location suggest a bootstrap surface.")
        if "manifest" in roles:
            score += 30
            reasons.append("Manifest exposes startup or build commands.")
        if any(term in path.lower() for term in focus_terms):
            score += 20
            reasons.append("Path matches the requested focus terms.")
        if "api" in roles or "ui" in roles:
            score += 10
            reasons.append("Touches a major application surface.")
        if score <= 0:
            continue
        candidates.append(
            {
                "path": path,
                "reason": " ".join(reasons),
                "confidence": "high" if score >= 90 else "medium",
                "score": score,
            }
        )
    candidates.sort(key=lambda item: (-int(item["score"]), str(item["path"])))
    return candidates[:8]


def build_directory_summary(records: list[dict[str, object]], depth: int) -> list[dict[str, object]]:
    grouped_roles: dict[str, Counter[str]] = defaultdict(Counter)
    file_counts: Counter[str] = Counter()

    for record in records:
        path = Path(str(record["path"]))
        parts = path.parts[:-1]
        bucket = "." if not parts else "/".join(parts[:depth])
        file_counts[bucket] += 1
        for role in record["roles"]:
            grouped_roles[bucket][str(role)] += 1

    summary: list[dict[str, object]] = []
    for bucket, count in file_counts.items():
        summary.append(
            {
                "path": bucket,
                "file_count": count,
                "dominant_roles": [role for role, _ in grouped_roles[bucket].most_common(3)],
            }
        )
    summary.sort(key=lambda item: (-int(item["file_count"]), str(item["path"])))
    return summary[:10]


def build_boundary_handoffs(records: list[dict[str, object]]) -> list[dict[str, object]]:
    handoffs: dict[tuple[str, str], dict[str, object]] = {}
    for record in records:
        source_path = str(record["path"])
        source_dir = relative_parent_bucket(source_path)
        for target_path in record["resolved_imports"]:
            target_dir = relative_parent_bucket(str(target_path))
            if source_dir == target_dir:
                continue
            key = (source_dir, target_dir)
            if key not in handoffs:
                handoffs[key] = {
                    "from": source_dir,
                    "to": target_dir,
                    "count": 0,
                    "evidence": [],
                    "confidence": "medium",
                    "reason": "Observed static import edges crossing directory boundaries.",
                }
            handoffs[key]["count"] += 1
            if len(handoffs[key]["evidence"]) < 3:
                handoffs[key]["evidence"].append(
                    {
                        "source": source_path,
                        "target": str(target_path),
                    }
                )
    results = list(handoffs.values())
    results.sort(key=lambda item: (-int(item["count"]), str(item["from"]), str(item["to"])))
    return results[:12]


def detect_design_patterns(
    records: list[dict[str, object]],
    docs: list[str],
    manifests: list[str],
    boundaries: list[dict[str, object]],
) -> list[dict[str, object]]:
    directory_set = {relative_parent_bucket(str(record["path"])) for record in records}
    patterns: list[dict[str, object]] = []

    route_like = {item for item in directory_set if re.search(r"(^|/)(routes?|controllers?|api)(/|$)", item)}
    service_like = {item for item in directory_set if re.search(r"(^|/)(services?)(/|$)", item)}
    data_like = {item for item in directory_set if re.search(r"(^|/)(repositories?|repo|db|database|models?|entities?)(/|$)", item)}
    ui_like = {item for item in directory_set if re.search(r"(^|/)(components?|pages?|screens?|views?|app)(/|$)", item)}

    boundary_pairs = {(entry["from"], entry["to"]) for entry in boundaries}
    if route_like and service_like and (
        data_like or any(source in route_like and target in service_like for source, target in boundary_pairs)
    ):
        patterns.append(
            {
                "name": "layered-application-surface",
                "summary": "Repository shows distinct routing, service, and domain or data seams.",
                "evidence": sorted(route_like | service_like | data_like)[:6],
                "confidence": "high" if data_like else "medium",
            }
        )

    if ui_like and service_like:
        patterns.append(
            {
                "name": "component-and-service-split",
                "summary": "UI-facing directories are separated from service logic.",
                "evidence": sorted(ui_like | service_like)[:6],
                "confidence": "medium",
            }
        )

    if any(Path(path).name.lower() in {"agents.md", "claude.md", "architecture.md"} for path in docs):
        patterns.append(
            {
                "name": "documentation-driven-context",
                "summary": "Repository already contains architecture or agent-facing context docs.",
                "evidence": docs[:4],
                "confidence": "high",
            }
        )

    if len({relative_parent_bucket(path) for path in manifests if "/" in path}) > 1:
        patterns.append(
            {
                "name": "multi-package-or-workspace-surface",
                "summary": "Manifest placement suggests multiple packages or app slices.",
                "evidence": manifests[:6],
                "confidence": "medium",
            }
        )

    return patterns


def build_drift_risks(
    records: list[dict[str, object]],
    docs: list[str],
    manifests: list[str],
    boundaries: list[dict[str, object]],
) -> list[dict[str, object]]:
    risks: list[dict[str, object]] = []
    root_docs = {Path(path).name.lower() for path in docs if "/" not in path}
    ecosystems: set[str] = set()
    test_count = sum(1 for record in records if "test" in record["roles"])

    for manifest in manifests:
        name = Path(manifest).name
        if name in {"package.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb", "package-lock.json"}:
            ecosystems.add("node")
        elif name in {"pyproject.toml", "requirements.txt", "uv.lock", "poetry.lock"}:
            ecosystems.add("python")
        elif name == "Cargo.toml":
            ecosystems.add("rust")
        elif name == "go.mod":
            ecosystems.add("go")

    if not ROOT_CONTEXT_DOCS.intersection(root_docs):
        risks.append(
            {
                "kind": "missing-root-context-docs",
                "summary": "Root AGENTS.md or CLAUDE.md is missing, so architecture intent may be harder to recover consistently.",
                "evidence": docs[:3],
                "confidence": "high",
            }
        )

    if "readme.md" not in root_docs:
        risks.append(
            {
                "kind": "missing-root-readme",
                "summary": "Repository lacks a root README, so first-pass architecture context is likely fragmented.",
                "evidence": docs[:3],
                "confidence": "medium",
            }
        )

    if test_count == 0:
        risks.append(
            {
                "kind": "thin-test-surface",
                "summary": "No test files were observed in the scanned slice.",
                "evidence": [],
                "confidence": "medium",
            }
        )

    if len(ecosystems) > 1:
        risks.append(
            {
                "kind": "mixed-runtime-command-surface",
                "summary": "Multiple ecosystems were detected, increasing coordination and drift risk across toolchains.",
                "evidence": manifests[:6],
                "confidence": "medium",
            }
        )

    if len(boundaries) >= 6 and not docs:
        risks.append(
            {
                "kind": "undocumented-cross-module-coupling",
                "summary": "Cross-directory handoffs are dense while architecture docs were not detected in the scanned slice.",
                "evidence": boundaries[:3],
                "confidence": "medium",
            }
        )

    return risks


def recommend_linked_skills(
    focus: str,
    commands: list[dict[str, str]],
    records: list[dict[str, object]],
    drift_risks: list[dict[str, object]],
) -> list[dict[str, str]]:
    recommendations: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(skill: str, reason: str, when_to_use: str) -> None:
        if skill in seen:
            return
        seen.add(skill)
        recommendations.append(
            {
                "skill": skill,
                "reason": reason,
                "when_to_use": when_to_use,
            }
        )

    add(
        "codebase-indexing-assistant",
        "Use it when this architecture pass needs a broader repository index or a more explicit reading order.",
        "Before widening from architecture review into whole-repo navigation.",
    )

    if focus.strip():
        add(
            "feature-call-chain-mapper",
            "A focus term was provided, so feature-level tracing is the next precise step after the architecture snapshot.",
            "When the next question becomes how a specific feature flows.",
        )

    if commands:
        add(
            "build-project-fixer",
            "Manifest or task-runner commands were detected and may need runtime verification before trusting architecture assumptions.",
            "When command hints need to be verified or runtime gates must be reproduced.",
        )

    risk_kinds = {risk["kind"] for risk in drift_risks}
    if {"missing-root-context-docs", "missing-root-readme"} & risk_kinds:
        add(
            "project-ai-context-initializer",
            "Root context or architecture docs look thin, so a repo-facing AGENTS.md or CLAUDE.md pass would reduce future rediscovery cost.",
            "When the repository needs durable orientation docs and Mermaid maps.",
        )

    if len(records) >= 12 or any("manifest" in record["roles"] for record in records):
        add(
            "project-skill-builder",
            "This repository has enough stable local signals that a repo-specific skill could preserve the findings for later sessions.",
            "After this analysis if the project will be revisited repeatedly.",
        )

    return recommendations[:5]


def build_suggested_next_reads(
    docs: list[str],
    manifests: list[str],
    entry_candidates: list[dict[str, object]],
    boundaries: list[dict[str, object]],
) -> list[dict[str, str]]:
    reads: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(path: str, reason: str) -> None:
        if path in seen:
            return
        seen.add(path)
        reads.append({"path": path, "reason": reason})

    for path in docs[:3]:
        add(path, "Documentation can confirm or challenge the inferred architecture intent.")
    for path in manifests[:3]:
        add(path, "Manifest reveals commands, dependencies, and package boundaries.")
    for candidate in entry_candidates[:3]:
        add(str(candidate["path"]), "Likely entry surface for deeper architectural inspection.")
    for boundary in boundaries[:2]:
        for evidence in boundary["evidence"]:
            add(str(evidence["source"]), "Source file participates in a cross-directory handoff.")
            add(str(evidence["target"]), "Target file participates in a cross-directory handoff.")
    return reads[:8]


def scan_repository(
    root: Path,
    includes: list[str],
    excludes: list[str],
    max_files: int,
    focus: str,
    depth: int,
) -> dict[str, object]:
    file_paths, limits = walk_repository(root, includes, excludes, max_files=max_files)
    all_paths = {path.relative_to(root).as_posix() for path in file_paths}
    focus_terms = [term for term in re.split(r"[^a-z0-9]+", focus.lower()) if term]

    docs: list[str] = []
    manifests: list[str] = []
    languages: Counter[str] = Counter()
    records: list[dict[str, object]] = []

    for file_path in file_paths:
        relative_path = file_path.relative_to(root).as_posix()
        language = detect_language(file_path)
        if language != "unknown":
            languages[language] += 1
        text = read_text_excerpt(file_path)
        roles = infer_roles(relative_path, file_path)
        imports = extract_imports(language, text)
        symbols = extract_symbols(language, text)
        if is_doc(file_path):
            docs.append(relative_path)
        if is_manifest(file_path):
            manifests.append(relative_path)
        records.append(
            {
                "path": relative_path,
                "language": language,
                "roles": roles,
                "imports": imports,
                "symbols": symbols,
                "reason": determine_file_reason(relative_path, roles, focus_terms),
                "resolved_imports": [],
            }
        )

    for record in records:
        resolved: list[str] = []
        for import_value in record["imports"]:
            target = resolve_import_target(str(record["language"]), str(record["path"]), str(import_value), all_paths)
            if target and target not in resolved:
                resolved.append(target)
        record["resolved_imports"] = resolved

    docs = sorted(set(docs))
    manifests = sorted(set(manifests))
    records.sort(key=lambda item: str(item["path"]))

    commands = collect_commands(file_paths)
    entry_candidates = build_entry_candidates(records, focus_terms)
    boundaries = build_boundary_handoffs(records)
    design_patterns = detect_design_patterns(records, docs, manifests, boundaries)
    drift_risks = build_drift_risks(records, docs, manifests, boundaries)
    linked_skills = recommend_linked_skills(focus, commands, records, drift_risks)
    suggested_next_reads = build_suggested_next_reads(docs, manifests, entry_candidates, boundaries)

    return {
        "repo_root": str(root),
        "request": {
            "focus": focus,
            "includes": includes,
            "excludes": excludes,
            "max_files": max_files,
            "depth": depth,
        },
        "summary": {
            "total_files": len(records),
            "languages": [
                {"language": language, "count": count}
                for language, count in languages.most_common()
            ],
            "docs": docs,
            "manifests": manifests,
            "commands": commands,
        },
        "files": records,
        "architecture": {
            "entry_candidates": entry_candidates,
            "top_directories": build_directory_summary(records, depth=max(1, depth)),
            "boundaries": boundaries,
            "design_patterns": design_patterns,
            "drift_risks": drift_risks,
        },
        "linked_skills": linked_skills,
        "suggested_next_reads": suggested_next_reads,
        "limits": limits,
    }


def render_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    architecture = payload["architecture"]
    language_summary = ", ".join(
        f"{item['language']} ({item['count']})" for item in summary["languages"]
    ) or "none"
    docs_summary = ", ".join(f"`{path}`" for path in summary["docs"][:5]) or "none"
    manifests_summary = ", ".join(f"`{path}`" for path in summary["manifests"][:5]) or "none"
    lines = [
        "# Project Architecture Design Report",
        "",
        "## Request",
        "",
        f"- Repository root: `{payload['repo_root']}`",
        f"- Focus: `{payload['request']['focus'] or 'none'}`",
        f"- Includes: {', '.join(payload['request']['includes']) or 'all matching paths'}",
        f"- Excludes: {', '.join(payload['request']['excludes']) or 'default ignore rules'}",
        "",
        "## Repository Snapshot",
        "",
        f"- Total scanned files: {summary['total_files']}",
        f"- Languages: {language_summary}",
        f"- Docs: {docs_summary}",
        f"- Manifests: {manifests_summary}",
        "",
        "## Architecture Shape",
        "",
    ]

    if architecture["entry_candidates"]:
        lines.append("### Candidate Entrypoints")
        lines.append("")
        for entry in architecture["entry_candidates"]:
            lines.append(f"- `{entry['path']}`: {entry['reason']}")
        lines.append("")

    if architecture["top_directories"]:
        lines.append("### Top Directories")
        lines.append("")
        for entry in architecture["top_directories"]:
            roles = ", ".join(entry["dominant_roles"]) or "no dominant roles"
            lines.append(f"- `{entry['path']}`: {entry['file_count']} files, dominant roles: {roles}")
        lines.append("")

    if architecture["boundaries"]:
        lines.append("### Cross-Directory Handoffs")
        lines.append("")
        for entry in architecture["boundaries"]:
            lines.append(f"- `{entry['from']}` -> `{entry['to']}`: {entry['count']} observed handoff(s).")
        lines.append("")

    lines.extend(["## Design Signals", ""])
    if architecture["design_patterns"]:
        for entry in architecture["design_patterns"]:
            evidence = ", ".join(f"`{item}`" for item in entry["evidence"]) or "implicit repository shape"
            lines.append(f"- `{entry['name']}` ({entry['confidence']}): {entry['summary']} Evidence: {evidence}.")
    else:
        lines.append("- No strong design pattern exceeded the heuristic threshold.")
    lines.append("")

    lines.extend(["## Drift Risks", ""])
    if architecture["drift_risks"]:
        for entry in architecture["drift_risks"]:
            evidence = entry["evidence"]
            suffix = f" Evidence: {json.dumps(evidence, ensure_ascii=False)}" if evidence else ""
            lines.append(f"- `{entry['kind']}` ({entry['confidence']}): {entry['summary']}{suffix}")
    else:
        lines.append("- No major drift risk exceeded the current heuristic threshold.")
    lines.append("")

    lines.extend(["## Linked Skills", ""])
    for entry in payload["linked_skills"]:
        lines.append(f"- `${entry['skill']}`: {entry['reason']} Next use: {entry['when_to_use']}")
    lines.append("")

    lines.extend(["## Suggested Next Reads", ""])
    for entry in payload["suggested_next_reads"]:
        lines.append(f"- `{entry['path']}`: {entry['reason']}")
    lines.append("")

    lines.extend(["## Limits", ""])
    if payload["limits"]:
        for entry in payload["limits"]:
            lines.append(f"- `{entry['kind']}`: {entry['detail']}")
    else:
        lines.append("- No explicit scan limits were hit.")
    lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Repository root is not a directory: {root}")

    payload = scan_repository(
        root=root,
        includes=normalize_prefixes(args.include),
        excludes=normalize_prefixes(args.exclude),
        max_files=max(1, args.max_files),
        focus=args.focus.strip(),
        depth=max(1, args.depth),
    )

    markdown_path = resolve_output_path(args.markdown_out, ".md")
    json_path = resolve_output_path(args.json_out, ".json")
    markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"MARKDOWN_OUT={markdown_path}")
    print(f"JSON_OUT={json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

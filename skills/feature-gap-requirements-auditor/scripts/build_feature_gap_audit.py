#!/usr/bin/env python3
"""Build a documentation-vs-implementation feature gap audit for a target folder or component."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import tempfile
from pathlib import Path


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
DOC_EXTENSIONS = {".md", ".mdx", ".rst", ".txt"}
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
    ".vue",
}
TEXT_EXTENSIONS = DOC_EXTENSIONS | SOURCE_EXTENSIONS | {".json", ".yaml", ".yml", ".toml"}
CONTEXT_DOC_NAMES = ("AGENTS.md", "CLAUDE.md", "README.md", "Readme.md", "readme.md")
REQUIREMENT_SECTION_HINTS = (
    "acceptance",
    "behavior",
    "capabilities",
    "feature",
    "functional",
    "requirements",
    "user flow",
    "user story",
)
NON_REQUIREMENT_SECTION_HINTS = (
    "command",
    "how to",
    "implementation plan",
    "installation",
    "navigation",
    "output schema",
    "reading order",
    "reference",
    "resources",
    "skip rules",
    "workflow",
)
BEHAVIOR_HINTS = (
    "allow",
    "display",
    "edit",
    "enable",
    "error",
    "export",
    "filter",
    "import",
    "list",
    "load",
    "loading",
    "manage",
    "preview",
    "refresh",
    "remove",
    "render",
    "retry",
    "save",
    "search",
    "select",
    "show",
    "sort",
    "submit",
    "support",
    "toggle",
    "update",
    "upload",
    "validate",
)
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "then",
    "to",
    "use",
    "user",
    "users",
    "when",
    "with",
}
IDENTIFIER_PATTERNS = (
    re.compile(r"\bexport\s+(?:async\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)"),
    re.compile(r"\bexport\s+const\s+([A-Za-z_][A-Za-z0-9_]*)"),
    re.compile(r"\bexport\s+class\s+([A-Za-z_][A-Za-z0-9_]*)"),
    re.compile(r"\bfunction\s+([A-Za-z_][A-Za-z0-9_]*)"),
    re.compile(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)"),
    re.compile(r"\binterface\s+([A-Za-z_][A-Za-z0-9_]*)"),
    re.compile(r"\btype\s+([A-Za-z_][A-Za-z0-9_]*)"),
)
BULLET_PATTERN = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+(.*)$")
CHECKBOX_PATTERN = re.compile(r"^\s*[-*+]\s+\[(?: |x|X)\]\s+(.*)$")
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$")
SENTENCE_SIGNAL_PATTERN = re.compile(
    r"\b(must|should|required|needs to|need to|allow|support|show|display|validate|upload|export)\b",
    re.IGNORECASE,
)
OUT_OF_SCOPE_SECTION_HINTS = ("out of scope", "non-goals", "non goals", "not in scope")
GUARDRAIL_SECTION_HINTS = ("constraints", "guardrails", "rules", "safety")
GUARDRAIL_TEXT_HINTS = (
    "avoid ",
    "do not ",
    "don't ",
    "must not ",
    "never ",
    "without approval",
)
META_SECTION_HINTS = (
    "interface metadata",
    "planned skill metadata",
    "responsibilities by file",
    "validation",
)
META_TEXT_PREFIXES = (
    "default_prompt:",
    "description:",
    "display_name:",
    "icon_large:",
    "icon_small:",
    "short_description:",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan documentation and implementation context for likely missing or partial features."
    )
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    parser.add_argument("--target", required=True, help="Target directory or file to audit.")
    parser.add_argument(
        "--doc",
        action="append",
        default=[],
        help="Explicit documentation path, relative to the repository root. Repeat as needed.",
    )
    parser.add_argument("--markdown-out", default="", help="Explicit output path for Markdown.")
    parser.add_argument("--json-out", default="", help="Explicit output path for JSON.")
    parser.add_argument("--max-files", type=int, default=120, help="Cap scanned implementation files.")
    parser.add_argument("--max-docs", type=int, default=20, help="Cap discovered documentation files.")
    parser.add_argument(
        "--include-contract-requirements",
        action="store_true",
        help="Include skill/package contract metadata and validation requirements in feature gaps.",
    )
    return parser.parse_args(argv)


def resolve_output_path(raw_path: str, suffix: str) -> Path:
    if raw_path:
        output_path = Path(raw_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path

    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="feature-gap-audit-")
    handle.close()
    return Path(handle.name).resolve()


def resolve_repo_path(root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def relative_to_root(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def should_skip_directory(name: str) -> bool:
    return name in IGNORED_DIR_NAMES


def should_skip_file(path: Path) -> bool:
    suffixes = path.suffixes
    if suffixes:
        suffix = "".join(suffixes[-2:]) if len(suffixes) >= 2 else suffixes[-1]
        if suffix in IGNORED_FILE_SUFFIXES or path.suffix.lower() in IGNORED_FILE_SUFFIXES:
            return True
    return path.suffix.lower() not in TEXT_EXTENSIONS


def split_camel_case(value: str) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    value = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", value)
    return value


def tokenize(text: str) -> list[str]:
    normalized = split_camel_case(text)
    normalized = normalized.replace("/", " ").replace("\\", " ").replace("_", " ").replace("-", " ")
    parts = re.findall(r"[A-Za-z][A-Za-z0-9]+", normalized.lower())
    tokens = [part for part in parts if len(part) >= 3 and part not in STOPWORDS]
    return tokens


def classify_file_kind(path: Path) -> str:
    name = path.name.lower()
    suffix = path.suffix.lower()
    if suffix in DOC_EXTENSIONS:
        return "doc"
    if ".test." in name or ".spec." in name or "__tests__" in path.as_posix():
        return "test"
    if suffix in {".css", ".scss", ".sass", ".less"}:
        return "style"
    if suffix in {".json", ".yaml", ".yml", ".toml"}:
        return "config"
    return "source"


def collect_target_files(
    root: Path,
    target_path: Path,
    max_files: int,
) -> tuple[list[Path], list[dict[str, str]], Path, str]:
    limits: list[dict[str, str]] = []
    if target_path.is_file():
        scan_root = target_path.parent
        target_mode = "file-context"
    else:
        scan_root = target_path
        target_mode = "directory"

    matching_files: list[Path] = []
    for current_root, dir_names, file_names in os.walk(scan_root):
        dir_names[:] = [name for name in sorted(dir_names) if not should_skip_directory(name)]
        for file_name in sorted(file_names):
            file_path = Path(current_root) / file_name
            if should_skip_file(file_path):
                continue
            matching_files.append(file_path)
            if len(matching_files) >= max_files:
                limits.append(
                    {
                        "kind": "max-files",
                        "detail": f"Stopped after scanning {max_files} matching implementation files.",
                    }
                )
                return matching_files, limits, scan_root, target_mode

    return matching_files, limits, scan_root, target_mode


def collect_context_docs(
    root: Path,
    target_path: Path,
    scan_root: Path,
    explicit_docs: list[str],
    max_docs: int,
) -> tuple[list[Path], list[dict[str, str]]]:
    docs: list[Path] = []
    seen: set[Path] = set()
    limits: list[dict[str, str]] = []

    def add_doc(path: Path) -> None:
        resolved = path.resolve()
        if not resolved.exists() or not resolved.is_file():
            return
        if resolved.suffix.lower() not in DOC_EXTENSIONS:
            return
        if resolved in seen:
            return
        docs.append(resolved)
        seen.add(resolved)

    for raw_doc in explicit_docs:
        add_doc(resolve_repo_path(root, raw_doc))

    current = target_path if target_path.is_dir() else target_path.parent
    while True:
        for name in CONTEXT_DOC_NAMES:
            add_doc(current / name)
        if current == root:
            break
        if root not in current.parents:
            break
        current = current.parent

    if scan_root.exists():
        for child in sorted(scan_root.iterdir(), key=lambda item: item.name.lower()):
            if child.is_file() and child.suffix.lower() in DOC_EXTENSIONS:
                add_doc(child)

    if len(docs) > max_docs:
        limits.append(
            {
                "kind": "max-docs",
                "detail": f"Trimmed discovered documentation files from {len(docs)} to {max_docs}.",
            }
        )
        docs = docs[:max_docs]

    return docs, limits


def build_discovered_doc_entries(
    doc_paths: list[Path],
    root: Path,
    target_path: Path,
    scan_root: Path,
    explicit_docs: list[str],
) -> list[dict[str, object]]:
    explicit_doc_paths = {
        resolve_repo_path(root, raw_doc).resolve()
        for raw_doc in explicit_docs
    }
    entries: list[dict[str, object]] = []
    for path in doc_paths:
        resolved = path.resolve()
        name = resolved.name
        role = "context"
        extract_requirements = False

        if resolved in explicit_doc_paths:
            role = "explicit"
            extract_requirements = True
        elif name == "README.md" and resolved.parent == scan_root:
            role = "local-readme"
            extract_requirements = True
        elif name == "SKILL.md" and (
            resolved.parent == scan_root or target_path == resolved.parent
        ):
            role = "local-skill"
            extract_requirements = True
        elif resolved.parent == scan_root and name not in {"AGENTS.md", "CLAUDE.md"}:
            role = "local-doc"
            extract_requirements = True
        elif resolved.parent == scan_root:
            role = "local-context"
        else:
            role = "ancestor-context"

        entries.append(
            {
                "path": relative_to_root(resolved, root),
                "kind": "explicit" if resolved in explicit_doc_paths else "context",
                "role": role,
                "extract_requirements": extract_requirements,
                "_resolved_path": resolved,
            }
        )
    return entries


def extract_identifiers(text: str) -> set[str]:
    identifiers: set[str] = set()
    for pattern in IDENTIFIER_PATTERNS:
        identifiers.update(pattern.findall(text))
    return identifiers


def build_surface_records(files: list[Path], root: Path) -> tuple[list[dict[str, object]], dict[str, set[str]], dict[str, object]]:
    records: list[dict[str, object]] = []
    source_tokens: set[str] = set()
    test_tokens: set[str] = set()
    doc_tokens: set[str] = set()
    status_counts = {"source": 0, "test": 0, "doc": 0, "config": 0, "style": 0}

    for file_path in files:
        kind = classify_file_kind(file_path)
        status_counts[kind] += 1
        text = safe_read_text(file_path) if file_path.suffix.lower() in TEXT_EXTENSIONS else ""
        record_tokens = set(tokenize(relative_to_root(file_path, root)))
        for identifier in extract_identifiers(text):
            record_tokens.update(tokenize(identifier))
        record_tokens.update(tokenize(text[:50000]))
        record = {
            "path": relative_to_root(file_path, root),
            "kind": kind,
            "tokens": sorted(record_tokens),
            "identifiers": sorted(extract_identifiers(text)),
        }
        records.append(record)
        if kind == "source":
            source_tokens.update(record_tokens)
        elif kind == "test":
            test_tokens.update(record_tokens)
        elif kind == "doc":
            doc_tokens.update(record_tokens)

    summary = {
        "file_count": len(records),
        "kind_counts": status_counts,
    }
    token_index = {
        "source": source_tokens,
        "test": test_tokens,
        "doc": doc_tokens,
    }
    return records, token_index, summary


def clean_markdown_text(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    return " ".join(text.strip().split())


def looks_like_container_line(text: str) -> bool:
    lowered = text.lower().strip()
    if lowered.endswith(":"):
        return True
    if lowered.endswith("include") or lowered.endswith("includes"):
        return True
    if lowered.endswith("support") or lowered.endswith("supports"):
        return True
    if lowered.endswith("define") or lowered.endswith("defines"):
        return True
    if lowered.endswith("such as"):
        return True
    return False


def looks_like_manifest_list_item(text: str) -> bool:
    lowered = text.lower().strip(" .,:;")
    if not lowered:
        return True
    if re.search(r"[\*/]", lowered) and "." in lowered:
        return True
    if re.fullmatch(r"[a-z0-9_.-]+\.[a-z0-9_.-]+", lowered):
        return True
    tokens = lowered.split()
    if len(tokens) <= 3 and all("." in token or token.endswith("lock") for token in tokens):
        return True
    return False


def should_keep_requirement(text: str, section_path: str) -> bool:
    lowered = text.lower()
    section_lower = section_path.lower()
    if len(lowered) < 12:
        return False
    if looks_like_container_line(text):
        return False
    if looks_like_manifest_list_item(text):
        return False
    if lowered.startswith("read ") or lowered.startswith("run ") or lowered.startswith("open "):
        return False
    if lowered.startswith("see ") or lowered.startswith("use "):
        return False
    if any(hint in section_lower for hint in NON_REQUIREMENT_SECTION_HINTS) and not SENTENCE_SIGNAL_PATTERN.search(lowered):
        return False
    if any(hint in section_lower for hint in OUT_OF_SCOPE_SECTION_HINTS):
        return False
    if any(hint in section_lower for hint in GUARDRAIL_SECTION_HINTS):
        return True
    if any(lowered.startswith(hint) for hint in GUARDRAIL_TEXT_HINTS):
        return True
    if any(hint in section_lower for hint in REQUIREMENT_SECTION_HINTS):
        return True
    if SENTENCE_SIGNAL_PATTERN.search(lowered):
        return True
    return any(hint in lowered for hint in BEHAVIOR_HINTS)


def infer_priority(text: str, section_path: str) -> str:
    lowered = text.lower()
    section_lower = section_path.lower()
    if "must" in lowered or "required" in lowered or "critical" in lowered:
        return "high"
    if "acceptance" in section_lower or "requirements" in section_lower:
        return "high"
    if "should" in lowered:
        return "medium"
    return "medium"


def classify_requirement_category(
    text: str,
    section_path: str,
    include_contract_requirements: bool,
) -> str:
    lowered = text.lower()
    section_lower = section_path.lower()
    if any(hint in section_lower for hint in OUT_OF_SCOPE_SECTION_HINTS):
        return "out-of-scope"
    if any(hint in section_lower for hint in GUARDRAIL_SECTION_HINTS):
        return "guardrail"
    if any(lowered.startswith(hint) for hint in GUARDRAIL_TEXT_HINTS):
        return "guardrail"
    if not include_contract_requirements:
        if any(hint in section_lower for hint in META_SECTION_HINTS):
            return "meta"
        if any(lowered.startswith(prefix) for prefix in META_TEXT_PREFIXES):
            return "meta"
    return "capability"


def extract_doc_requirements(
    doc_entries: list[dict[str, object]],
    root: Path,
    include_contract_requirements: bool,
) -> list[dict[str, object]]:
    requirements: list[dict[str, object]] = []
    seen_keys: set[tuple[str, str]] = set()

    for doc_entry in doc_entries:
        if not bool(doc_entry["extract_requirements"]):
            continue
        doc_path = Path(doc_entry["_resolved_path"])
        lines = safe_read_text(doc_path).splitlines()
        heading_stack: dict[int, str] = {}

        def section_path() -> str:
            return " > ".join(heading_stack[level] for level in sorted(heading_stack))

        for raw_line in lines:
            heading_match = HEADING_PATTERN.match(raw_line)
            if heading_match:
                level = len(heading_match.group(1))
                heading_stack = {key: value for key, value in heading_stack.items() if key < level}
                heading_stack[level] = clean_markdown_text(heading_match.group(2))
                continue

            bullet_match = CHECKBOX_PATTERN.match(raw_line) or BULLET_PATTERN.match(raw_line)
            candidate_text = ""
            if bullet_match:
                candidate_text = clean_markdown_text(bullet_match.group(1))
            else:
                stripped = clean_markdown_text(raw_line)
                if SENTENCE_SIGNAL_PATTERN.search(stripped):
                    candidate_text = stripped

            if not candidate_text:
                continue
            current_section = section_path()
            if not should_keep_requirement(candidate_text, current_section):
                continue

            keywords = sorted(set(tokenize(candidate_text)))
            category = classify_requirement_category(
                candidate_text,
                current_section,
                include_contract_requirements,
            )
            if category in {"out-of-scope", "meta"}:
                continue
            requirement = {
                "id": f"req-{len(requirements) + 1}",
                "path": relative_to_root(doc_path, root),
                "section": current_section,
                "text": candidate_text,
                "keywords": keywords,
                "priority": infer_priority(candidate_text, current_section),
                "category": category,
                "source_role": doc_entry["role"],
            }
            dedupe_key = (requirement["path"], requirement["text"].lower())
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            requirements.append(requirement)

    return requirements


def build_related_files(
    requirement_keywords: set[str],
    surface_records: list[dict[str, object]],
) -> list[dict[str, object]]:
    related: list[dict[str, object]] = []
    for record in surface_records:
        if record["kind"] not in {"source", "test"}:
            continue
        record_tokens = set(record["tokens"])
        overlap = sorted(requirement_keywords & record_tokens)
        if not overlap:
            continue
        related.append(
            {
                "path": record["path"],
                "kind": record["kind"],
                "matched_keywords": overlap,
                "overlap_count": len(overlap),
            }
        )
    related.sort(key=lambda item: (-int(item["overlap_count"]), item["path"]))
    return related[:5]


def assess_gap_status(
    requirement: dict[str, object],
    token_index: dict[str, set[str]],
    surface_records: list[dict[str, object]],
) -> dict[str, object]:
    keywords = set(requirement["keywords"])
    source_matches = sorted(keywords & token_index["source"])
    test_matches = sorted(keywords & token_index["test"])
    related_files = build_related_files(keywords, surface_records)

    if len(keywords) < 2:
        status = "uncertain"
    elif not source_matches and not test_matches:
        status = "missing"
    else:
        source_ratio = len(source_matches) / max(len(keywords), 1)
        source_threshold = max(2, math.ceil(len(keywords) * 0.6))
        if len(source_matches) >= source_threshold and source_ratio >= 0.6:
            status = "covered"
        else:
            status = "partial"

    return {
        "requirement_id": requirement["id"],
        "requirement_text": requirement["text"],
        "path": requirement["path"],
        "section": requirement["section"],
        "category": requirement["category"],
        "priority": requirement["priority"],
        "status": status,
        "keywords": sorted(keywords),
        "matched_source_keywords": source_matches,
        "matched_test_keywords": test_matches,
        "related_files": related_files,
    }


def build_detailed_requirements(
    candidates: list[dict[str, object]],
    target_summary: dict[str, object],
) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    target_has_tests = int(target_summary["kind_counts"]["test"]) > 0
    for candidate in candidates:
        if candidate["status"] not in {"missing", "partial"}:
            continue

        title = candidate["requirement_text"].rstrip(".")
        acceptance_criteria = [
            f"Implement the documented capability: {title}.",
            "Expose the behavior through the audited target without breaking existing exports, routes, or consumers.",
        ]
        if any(keyword in candidate["keywords"] for keyword in {"loading", "error", "empty", "retry", "validate"}):
            acceptance_criteria.append("Cover success and relevant transitional or failure states that the requirement implies.")
        if target_has_tests:
            acceptance_criteria.append("Update or add targeted tests so the documented behavior is exercised from the owning surface.")
        else:
            acceptance_criteria.append("Add targeted verification for the owning surface so the documented behavior is not left implicit.")

        open_questions: list[str] = []
        if not candidate["related_files"]:
            open_questions.append("Which file or route should own this capability inside the audited target?")
        if candidate["status"] == "partial":
            open_questions.append("What part of the documented behavior is already present, and what is still missing?")

        items.append(
            {
                "title": title,
                "status": candidate["status"],
                "priority": candidate["priority"],
                "rationale": (
                    "Documented behavior has no convincing implementation signal in the audited target."
                    if candidate["status"] == "missing"
                    else "The audited target contains some related signals, but the documented behavior looks incomplete."
                ),
                "evidence": {
                    "doc_path": candidate["path"],
                    "section": candidate["section"],
                    "matched_source_keywords": candidate["matched_source_keywords"],
                    "matched_test_keywords": candidate["matched_test_keywords"],
                },
                "related_files": [item["path"] for item in candidate["related_files"]],
                "acceptance_criteria": acceptance_criteria,
                "open_questions": open_questions,
            }
        )
    return items


def build_blind_spots(doc_paths: list[Path], requirements: list[dict[str, object]]) -> list[str]:
    blind_spots = [
        "Static matching cannot prove runtime behavior, conditional rendering paths, or backend integrations.",
        "Keyword overlap can miss renamed implementations and can overcount generic identifiers such as loading or error.",
        "Treat partial and uncertain items as triage leads, not final product truth, until the owning files are read directly.",
    ]
    if not doc_paths:
        blind_spots.insert(0, "No documentation was discovered, so the audit cannot derive trustworthy product requirements.")
    elif not requirements:
        blind_spots.insert(0, "Documentation was found, but no requirement-like statements were extracted with enough confidence.")
    return blind_spots


def build_suggested_next_reads(
    doc_paths: list[Path],
    gap_candidates: list[dict[str, object]],
    root: Path,
) -> list[str]:
    suggestions: list[str] = []
    for doc_path in doc_paths[:3]:
        suggestions.append(relative_to_root(doc_path, root))
    for candidate in gap_candidates:
        for related in candidate["related_files"]:
            if related["path"] not in suggestions:
                suggestions.append(related["path"])
            if len(suggestions) >= 8:
                return suggestions
    return suggestions[:8]


def render_markdown(payload: dict[str, object]) -> str:
    lines: list[str] = []
    request = payload["request"]

    lines.append("# Feature Gap Audit")
    lines.append("")
    lines.append("## Request")
    lines.append(f"- Root: `{request['root']}`")
    lines.append(f"- Target: `{request['target']}`")
    lines.append(f"- Target mode: `{request['target_mode']}`")
    lines.append("")

    lines.append("## Documentation Signals")
    if payload["discovered_docs"]:
        for entry in payload["discovered_docs"]:
            lines.append(f"- `{entry['path']}`")
    else:
        lines.append("- No documentation files discovered.")
    if payload["doc_requirements"]:
        lines.append("")
        lines.append("Extracted requirements:")
        for requirement in payload["doc_requirements"][:12]:
            lines.append(f"- `{requirement['path']}`: {requirement['text']}")
    lines.append("")

    lines.append("## Target Surface")
    target_summary = payload["target_summary"]
    lines.append(f"- Files scanned: {target_summary['file_count']}")
    for kind, count in target_summary["kind_counts"].items():
        lines.append(f"- {kind}: {count}")
    lines.append("")

    lines.append("## Gap Candidates")
    if payload["feature_gap_candidates"]:
        for candidate in payload["feature_gap_candidates"]:
            lines.append(
                f"- `{candidate['status']}` `{candidate['priority']}` `{candidate['path']}`: {candidate['requirement_text']}"
            )
    else:
        lines.append("- No documentation-derived gap candidates.")
    lines.append("")

    lines.append("## Guardrail Findings")
    if payload["guardrail_findings"]:
        for candidate in payload["guardrail_findings"]:
            lines.append(
                f"- `{candidate['status']}` `{candidate['priority']}` `{candidate['path']}`: {candidate['requirement_text']}"
            )
    else:
        lines.append("- No guardrail findings.")
    lines.append("")

    lines.append("## Detailed Requirements")
    if payload["detailed_requirements"]:
        for item in payload["detailed_requirements"]:
            lines.append(f"- `{item['priority']}` `{item['status']}`: {item['title']}")
            for criterion in item["acceptance_criteria"]:
                lines.append(f"  - {criterion}")
    else:
        lines.append("- No missing or partial requirements were produced.")
    lines.append("")

    lines.append("## Blind Spots")
    for item in payload["blind_spots"]:
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## Suggested Next Reads")
    if payload["suggested_next_reads"]:
        for item in payload["suggested_next_reads"]:
            lines.append(f"- `{item}`")
    else:
        lines.append("- No suggested next reads.")

    return "\n".join(lines) + "\n"


def inspect_repository(
    root: Path,
    target_path: Path,
    explicit_docs: list[str],
    max_files: int,
    max_docs: int,
    include_contract_requirements: bool,
) -> dict[str, object]:
    target_files, file_limits, scan_root, target_mode = collect_target_files(root, target_path, max_files)
    doc_paths, doc_limits = collect_context_docs(root, target_path, scan_root, explicit_docs, max_docs)
    doc_entries = build_discovered_doc_entries(doc_paths, root, target_path, scan_root, explicit_docs)
    surface_records, token_index, target_summary = build_surface_records(target_files, root)
    doc_requirements = extract_doc_requirements(doc_entries, root, include_contract_requirements)
    capability_requirements = [item for item in doc_requirements if item["category"] == "capability"]
    guardrail_requirements = [item for item in doc_requirements if item["category"] == "guardrail"]
    gap_candidates = [
        assess_gap_status(requirement, token_index, surface_records)
        for requirement in capability_requirements
    ]
    guardrail_findings = [
        assess_gap_status(requirement, token_index, surface_records)
        for requirement in guardrail_requirements
    ]
    detailed_requirements = build_detailed_requirements(gap_candidates, target_summary)

    payload = {
        "request": {
            "root": root.as_posix(),
            "target": relative_to_root(target_path, root),
            "target_mode": target_mode,
            "explicit_docs": explicit_docs,
            "include_contract_requirements": include_contract_requirements,
        },
        "discovered_docs": [
            {
                "path": entry["path"],
                "kind": entry["kind"],
                "role": entry["role"],
                "extract_requirements": entry["extract_requirements"],
            }
            for entry in doc_entries
        ],
        "doc_requirements": doc_requirements,
        "target_summary": target_summary,
        "target_files": [
            {
                "path": record["path"],
                "kind": record["kind"],
                "identifiers": record["identifiers"],
            }
            for record in surface_records
        ],
        "feature_gap_candidates": gap_candidates,
        "guardrail_findings": guardrail_findings,
        "detailed_requirements": detailed_requirements,
        "blind_spots": build_blind_spots(doc_paths, doc_requirements),
        "suggested_next_reads": build_suggested_next_reads(doc_paths, gap_candidates, root),
        "limits": file_limits + doc_limits,
    }
    return payload


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    target_path = resolve_repo_path(root, args.target)
    if not root.exists():
        raise SystemExit(f"Repository root not found: {root}")
    if not target_path.exists():
        raise SystemExit(f"Target path not found: {target_path}")

    payload = inspect_repository(
        root=root,
        target_path=target_path,
        explicit_docs=args.doc,
        max_files=args.max_files,
        max_docs=args.max_docs,
        include_contract_requirements=args.include_contract_requirements,
    )
    markdown_path = resolve_output_path(args.markdown_out, ".md")
    json_path = resolve_output_path(args.json_out, ".json")
    markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"MARKDOWN_OUT={markdown_path}")
    print(f"JSON_OUT={json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

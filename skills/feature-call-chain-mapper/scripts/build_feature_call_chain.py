#!/usr/bin/env python3
"""Build a lightweight feature call-chain report for a repository."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
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
ENTRY_PREFIXES = ("app", "cli", "handler", "index", "main", "route", "router", "server")
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
    ".swift": "Swift",
    ".toml": "TOML",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".xml": "XML",
    ".yaml": "YAML",
    ".yml": "YAML",
}
GENERIC_BLIND_SPOTS = [
    "Dynamic dispatch, reflection, and runtime dependency injection can hide edges that static text scanning cannot prove.",
    "Framework registration, decorators, and config-driven wiring may connect modules without an explicit direct call in source text.",
    "Cross-process, remote-service, and generated-code transitions are usually only partially visible to this heuristic tracer.",
]
SYMBOL_PATTERNS: dict[str, list[tuple[str, re.Pattern[str]]]] = {
    "Python": [
        ("function", re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE)),
        ("class", re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)\b", re.MULTILINE)),
    ],
    "JavaScript": [
        (
            "function",
            re.compile(
                r"^\s*export\s+(?:async\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
                re.MULTILINE,
            ),
        ),
        (
            "function",
            re.compile(r"^\s*(?:async\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE),
        ),
        (
            "function",
            re.compile(
                r"^\s*(?:export\s+)?const\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:async\s*)?\(",
                re.MULTILINE,
            ),
        ),
        ("class", re.compile(r"^\s*(?:export\s+)?class\s+([A-Za-z_][A-Za-z0-9_]*)\b", re.MULTILINE)),
    ],
    "TypeScript": [
        (
            "function",
            re.compile(
                r"^\s*export\s+(?:async\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
                re.MULTILINE,
            ),
        ),
        (
            "function",
            re.compile(r"^\s*(?:async\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE),
        ),
        (
            "function",
            re.compile(
                r"^\s*(?:export\s+)?const\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:async\s*)?\(",
                re.MULTILINE,
            ),
        ),
        ("class", re.compile(r"^\s*(?:export\s+)?class\s+([A-Za-z_][A-Za-z0-9_]*)\b", re.MULTILINE)),
    ],
    "Go": [("function", re.compile(r"^\s*func\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE))],
    "Rust": [
        ("function", re.compile(r"^\s*(?:pub\s+)?fn\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE)),
        ("class", re.compile(r"^\s*(?:pub\s+)?struct\s+([A-Za-z_][A-Za-z0-9_]*)\b", re.MULTILINE)),
    ],
    "Java": [
        ("class", re.compile(r"^\s*(?:public\s+)?class\s+([A-Za-z_][A-Za-z0-9_]*)\b", re.MULTILINE)),
        (
            "function",
            re.compile(
                r"^\s*(?:public|private|protected)\s+(?:static\s+)?[A-Za-z0-9_<>,\[\]]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
                re.MULTILINE,
            ),
        ),
    ],
    "C#": [
        ("class", re.compile(r"^\s*(?:public\s+)?class\s+([A-Za-z_][A-Za-z0-9_]*)\b", re.MULTILINE)),
        (
            "function",
            re.compile(
                r"^\s*(?:public|private|protected|internal)\s+(?:static\s+)?[A-Za-z0-9_<>,\[\]\?]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
                re.MULTILINE,
            ),
        ),
    ],
}


@dataclass
class ImportRecord:
    module: str
    names: list[str]
    raw: str
    target_path: str | None = None


@dataclass
class SymbolRecord:
    id: str
    symbol: str
    kind: str
    file: str
    line: int
    language: str
    role: str
    evidence: str
    confidence: str
    notes: str
    body: str
    score: int


@dataclass
class FileRecord:
    path: str
    language: str
    extension: str
    text: str
    imports: list[ImportRecord]
    symbols: list[SymbolRecord]
    feature_hits: list[str]
    entry_reason: str | None
    score: int


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Trace likely feature call chains and emit structured Markdown and JSON reports."
    )
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    parser.add_argument("--feature", default="", help="Feature keyword or phrase to trace.")
    parser.add_argument("--entry-file", default="", help="Explicit repository-relative file to anchor the trace.")
    parser.add_argument("--entry-symbol", default="", help="Explicit symbol to anchor the trace.")
    parser.add_argument("--markdown-out", default="", help="Explicit output path for Markdown.")
    parser.add_argument("--json-out", default="", help="Explicit output path for JSON.")
    parser.add_argument("--include", action="append", default=[], help="Relative path prefix to include.")
    parser.add_argument("--exclude", action="append", default=[], help="Relative path prefix to exclude.")
    parser.add_argument("--max-files", type=int, default=250, help="Cap matching files scanned.")
    parser.add_argument("--max-depth", type=int, default=4, help="Cap graph expansion depth.")
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

    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="feature-call-chain-")
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
    return path.suffix.lower() not in SOURCE_EXTENSIONS


def detect_language(path: Path) -> str:
    return LANGUAGE_BY_SUFFIX.get(path.suffix.lower(), "unknown")


def tokenize_feature_terms(feature: str) -> list[str]:
    tokens = [token.lower() for token in re.findall(r"[A-Za-z0-9_]+", feature)]
    return [token for token in tokens if token]


def is_binary_text(text: str) -> bool:
    return "\x00" in text


def safe_read_text(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="ignore")
    return "" if is_binary_text(text) else text


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
            if not should_skip_directory(f"{relative_root}/{name}".strip("/"), name, excludes)
        ]

        for file_name in sorted(file_names):
            path = current_path / file_name
            relative_path = path.relative_to(root).as_posix()
            if should_skip_file(path):
                continue
            if not should_include_path(relative_path, includes, excludes):
                continue
            matching_files.append(path)
            if len(matching_files) >= max_files:
                limits.append(
                    {
                        "kind": "max-files",
                        "detail": f"Stopped after scanning {max_files} matching source files.",
                    }
                )
                return matching_files, limits
    return matching_files, limits


def entry_reason_for_path(relative_path: str, feature_terms: list[str], explicit_entry_file: str) -> str | None:
    path_lower = relative_path.lower()
    stem_lower = Path(relative_path).stem.lower()
    if explicit_entry_file and relative_path == explicit_entry_file:
        return "Explicit entry file anchor requested by the user."
    if any(stem_lower.startswith(prefix) for prefix in ENTRY_PREFIXES):
        return "Matched a conventional entry or handler filename."
    if "/routes/" in f"/{path_lower}/" or "/controllers/" in f"/{path_lower}/":
        return "Path suggests a route or controller surface."
    if feature_terms and any(term in path_lower for term in feature_terms):
        return "File path matches the requested feature terms."
    return None


def feature_hits_for_path(relative_path: str, text: str, feature_terms: list[str]) -> list[str]:
    haystacks = [relative_path.lower(), text.lower()]
    hits: list[str] = []
    for term in feature_terms:
        if any(term in haystack for haystack in haystacks):
            hits.append(term)
    return hits


def extract_js_import_names(clause: str) -> list[str]:
    names: list[str] = []
    cleaned = clause.strip()
    if cleaned.startswith("{") and cleaned.endswith("}"):
        inner = cleaned[1:-1]
        for item in inner.split(","):
            name = item.strip().split(" as ")[0].strip()
            if name:
                names.append(name)
        return names

    if "," in cleaned:
        first, remainder = cleaned.split(",", 1)
        if first.strip():
            names.append(first.strip())
        if "{" in remainder and "}" in remainder:
            names.extend(extract_js_import_names(remainder[remainder.index("{") : remainder.index("}") + 1]))
        return names

    if cleaned and not cleaned.startswith("*"):
        names.append(cleaned)
    return names


def parse_imports(language: str, text: str) -> list[ImportRecord]:
    imports: list[ImportRecord] = []
    if language == "Python":
        for match in re.finditer(r"^\s*from\s+([A-Za-z0-9_\.]+)\s+import\s+([^\n#]+)", text, re.MULTILINE):
            names = [part.strip() for part in match.group(2).split(",") if part.strip() and part.strip() != "*"]
            imports.append(ImportRecord(module=match.group(1), names=names, raw=match.group(0).strip()))
        for match in re.finditer(r"^\s*import\s+([A-Za-z0-9_\.]+)", text, re.MULTILINE):
            module = match.group(1)
            imports.append(ImportRecord(module=module, names=[module.split(".")[-1]], raw=match.group(0).strip()))
        return imports

    if language in {"JavaScript", "TypeScript"}:
        for match in re.finditer(r"import\s+(.+?)\s+from\s+['\"]([^'\"]+)['\"]", text):
            clause = match.group(1).strip()
            module = match.group(2)
            imports.append(
                ImportRecord(module=module, names=extract_js_import_names(clause), raw=match.group(0).strip())
            )
        for match in re.finditer(r"require\(['\"]([^'\"]+)['\"]\)", text):
            imports.append(ImportRecord(module=match.group(1), names=[], raw=match.group(0).strip()))
        return imports

    if language == "Go":
        for block in re.findall(r"import\s*\((.*?)\)", text, re.DOTALL):
            for module in re.findall(r'\"([^\"\\n]+)\"', block):
                imports.append(ImportRecord(module=module, names=[module.split("/")[-1]], raw=module))
        return imports

    if language == "Rust":
        for match in re.finditer(r"^\s*use\s+([^;]+);", text, re.MULTILINE):
            module = match.group(1).strip()
            imports.append(ImportRecord(module=module, names=[module.split("::")[-1]], raw=match.group(0).strip()))
        return imports

    if language == "Java":
        for match in re.finditer(r"^\s*import\s+([^;]+);", text, re.MULTILINE):
            module = match.group(1).strip()
            imports.append(ImportRecord(module=module, names=[module.split(".")[-1]], raw=match.group(0).strip()))
        return imports

    if language == "C#":
        for match in re.finditer(r"^\s*using\s+([^;]+);", text, re.MULTILINE):
            module = match.group(1).strip()
            imports.append(ImportRecord(module=module, names=[module.split(".")[-1]], raw=match.group(0).strip()))
        return imports

    return imports


def resolve_import_target(root: Path, current_file: str, language: str, module: str) -> str | None:
    current_path = root / current_file
    if language == "Python":
        module_path = module.replace(".", "/")
        candidates = [
            current_path.parent / f"{module_path}.py",
            root / f"{module_path}.py",
            current_path.parent / module_path / "__init__.py",
            root / module_path / "__init__.py",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate.relative_to(root).as_posix()
        return None

    if language in {"JavaScript", "TypeScript"}:
        if not module.startswith("."):
            return None
        module_path = (current_path.parent / module).resolve()
        candidates = [
            module_path,
            module_path.with_suffix(".ts"),
            module_path.with_suffix(".tsx"),
            module_path.with_suffix(".js"),
            module_path.with_suffix(".jsx"),
            module_path / "index.ts",
            module_path / "index.tsx",
            module_path / "index.js",
            module_path / "index.jsx",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate.relative_to(root).as_posix()
        return None
    return None


def extract_symbols(
    language: str,
    relative_path: str,
    text: str,
    feature_terms: list[str],
    entry_reason: str | None,
    explicit_entry_symbol: str,
) -> list[SymbolRecord]:
    patterns = SYMBOL_PATTERNS.get(language, [])
    found: list[tuple[int, str, str]] = []
    seen: set[tuple[int, str]] = set()

    for kind, pattern in patterns:
        for match in pattern.finditer(text):
            name = match.group(1)
            key = (match.start(), name)
            if key in seen:
                continue
            seen.add(key)
            found.append((match.start(), kind, name))

    found.sort(key=lambda item: item[0])
    symbols: list[SymbolRecord] = []
    for index, (start, kind, name) in enumerate(found, start=1):
        end = found[index][0] if index < len(found) else len(text)
        body = text[start:end]
        line = text.count("\n", 0, start) + 1
        score = 0
        evidence = "observed"
        confidence = "medium"
        role = "implementation"
        notes: list[str] = []
        lowered_name = name.lower()
        if explicit_entry_symbol and name == explicit_entry_symbol:
            score += 6
            role = "entry"
            confidence = "high"
            notes.append("Matched the explicit entry symbol anchor.")
        if entry_reason and index == 1:
            score += 4
            role = "entry"
            confidence = "high"
            notes.append("Declared in a promoted entrypoint file.")
        if feature_terms and any(term in lowered_name for term in feature_terms):
            score += 5
            confidence = "high"
            notes.append("Symbol name matches the requested feature terms.")
        if any(keyword in lowered_name for keyword in ("route", "handler", "controller")) and role != "entry":
            role = "entry"
            notes.append("Symbol name suggests a request entry surface.")
        if not notes:
            notes.append("Symbol was observed directly in source text during heuristic tracing.")
        symbols.append(
            SymbolRecord(
                id=f"node-{len(symbols) + 1}",
                symbol=name,
                kind=kind,
                file=relative_path,
                line=line,
                language=language,
                role=role,
                evidence=evidence,
                confidence=confidence,
                notes=" ".join(notes),
                body=body,
                score=score,
            )
        )
    return symbols


def call_pattern(symbol_name: str) -> re.Pattern[str]:
    return re.compile(rf"\b{re.escape(symbol_name)}\s*\(")


def collect_file_records(root: Path, args: argparse.Namespace) -> tuple[list[FileRecord], list[dict[str, str]]]:
    includes = normalize_prefixes(args.include)
    excludes = normalize_prefixes(args.exclude)
    feature_terms = tokenize_feature_terms(args.feature)
    explicit_entry_file = args.entry_file.replace("\\", "/").strip()
    explicit_entry_symbol = args.entry_symbol.strip()

    paths, limits = walk_repository(root, includes, excludes, args.max_files)
    records: list[FileRecord] = []
    for path in paths:
        relative_path = path.relative_to(root).as_posix()
        text = safe_read_text(path)
        language = detect_language(path)
        imports = parse_imports(language, text)
        for import_record in imports:
            import_record.target_path = resolve_import_target(root, relative_path, language, import_record.module)
        feature_hits = feature_hits_for_path(relative_path, text, feature_terms)
        entry_reason = entry_reason_for_path(relative_path, feature_terms, explicit_entry_file)
        score = 0
        if entry_reason:
            score += 4
        score += len(feature_hits) * 3
        if explicit_entry_file and relative_path == explicit_entry_file:
            score += 8
        symbols = extract_symbols(
            language=language,
            relative_path=relative_path,
            text=text,
            feature_terms=feature_terms,
            entry_reason=entry_reason,
            explicit_entry_symbol=explicit_entry_symbol,
        )
        score += sum(1 for symbol in symbols if symbol.score > 0)
        records.append(
            FileRecord(
                path=relative_path,
                language=language,
                extension=path.suffix.lower(),
                text=text,
                imports=imports,
                symbols=symbols,
                feature_hits=feature_hits,
                entry_reason=entry_reason,
                score=score,
            )
        )
    return records, limits


def add_edge(
    edges: list[dict[str, object]],
    seen: set[tuple[str, str, str]],
    *,
    from_node: SymbolRecord,
    to_node: SymbolRecord,
    relation: str,
    evidence: str,
    confidence: str,
    reason: str,
) -> None:
    key = (from_node.id, to_node.id, relation)
    if key in seen:
        return
    seen.add(key)
    edges.append(
        {
            "from": from_node.id,
            "to": to_node.id,
            "relation": relation,
            "evidence": evidence,
            "confidence": confidence,
            "reason": reason,
        }
    )


def edges_for_symbol(edges: list[dict[str, object]], symbol_id: str) -> list[dict[str, object]]:
    return [edge for edge in edges if edge["from"] == symbol_id]


def build_edges(
    file_records: list[FileRecord],
    symbol_lookup: dict[tuple[str, str], SymbolRecord],
) -> list[dict[str, object]]:
    edges: list[dict[str, object]] = []
    seen: set[tuple[str, str, str]] = set()
    for record in file_records:
        local_symbols = {symbol.symbol: symbol for symbol in record.symbols}
        import_targets: dict[str, SymbolRecord] = {}
        for import_record in record.imports:
            if import_record.target_path:
                for imported_name in import_record.names:
                    target = symbol_lookup.get((import_record.target_path, imported_name))
                    if target:
                        import_targets[imported_name] = target

        for symbol in record.symbols:
            for candidate_name, target in local_symbols.items():
                if candidate_name == symbol.symbol:
                    continue
                if call_pattern(candidate_name).search(symbol.body):
                    add_edge(
                        edges,
                        seen,
                        from_node=symbol,
                        to_node=target,
                        relation="calls",
                        evidence="observed",
                        confidence="high",
                        reason="Direct same-file symbol call was observed in the source text.",
                    )
            for imported_name, target in import_targets.items():
                if call_pattern(imported_name).search(symbol.body):
                    add_edge(
                        edges,
                        seen,
                        from_node=symbol,
                        to_node=target,
                        relation="calls",
                        evidence="observed",
                        confidence="high",
                        reason="Observed a direct call to an imported symbol.",
                    )
            if not edges_for_symbol(edges, symbol.id):
                for import_record in record.imports:
                    if import_record.target_path and import_record.names:
                        first_name = import_record.names[0]
                        target = symbol_lookup.get((import_record.target_path, first_name))
                        if target:
                            add_edge(
                                edges,
                                seen,
                                from_node=symbol,
                                to_node=target,
                                relation="references",
                                evidence="inferred",
                                confidence="medium",
                                reason="Imported symbol was not called directly, but the module handoff is likely relevant.",
                            )
                            break
    return edges


def select_relevant_nodes(
    file_records: list[FileRecord],
    edges: list[dict[str, object]],
    feature_terms: list[str],
    explicit_entry_file: str,
    explicit_entry_symbol: str,
    max_depth: int,
) -> list[str]:
    adjacency: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        adjacency[str(edge["from"])].add(str(edge["to"]))
        adjacency[str(edge["to"])].add(str(edge["from"]))

    seeds: set[str] = set()
    for record in file_records:
        file_is_seed = bool(record.entry_reason) or bool(record.feature_hits)
        if explicit_entry_file and record.path == explicit_entry_file:
            file_is_seed = True
        for symbol in record.symbols:
            lowered_symbol = symbol.symbol.lower()
            if explicit_entry_symbol and symbol.symbol == explicit_entry_symbol:
                seeds.add(symbol.id)
                continue
            if file_is_seed:
                seeds.add(symbol.id)
                continue
            if feature_terms and any(term in lowered_symbol for term in feature_terms):
                seeds.add(symbol.id)

    if not seeds:
        for record in sorted(file_records, key=lambda item: item.score, reverse=True)[:2]:
            for symbol in record.symbols[:1]:
                seeds.add(symbol.id)

    visited = set(seeds)
    frontier = set(seeds)
    for _ in range(max_depth):
        next_frontier: set[str] = set()
        for node_id in frontier:
            next_frontier.update(adjacency.get(node_id, set()))
        next_frontier -= visited
        if not next_frontier:
            break
        visited |= next_frontier
        frontier = next_frontier
    return sorted(visited)


def build_fallback_nodes(file_records: list[FileRecord]) -> list[SymbolRecord]:
    fallback: list[SymbolRecord] = []
    for record in sorted(file_records, key=lambda item: item.score, reverse=True):
        if record.symbols:
            fallback.append(record.symbols[0])
        if len(fallback) >= 2:
            break
    return fallback


def downgrade_nodes_to_low_confidence(nodes: list[SymbolRecord], reason: str) -> None:
    for node in nodes:
        node.confidence = "low"
        node.notes = f"{node.notes} {reason}".strip()


def build_candidate_entrypoints(file_records: list[FileRecord], explicit_entry_file: str) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    for record in sorted(file_records, key=lambda item: item.score, reverse=True):
        reason = record.entry_reason
        if not reason and record.score < 2:
            continue
        if explicit_entry_file and record.path == explicit_entry_file:
            reason = "Explicit entry file anchor requested by the user."
        if not reason:
            reason = "High feature relevance made this file a candidate entrypoint."
        candidates.append(
            {
                "path": record.path,
                "language": record.language,
                "reason": reason,
                "confidence": "high" if record.entry_reason or record.path == explicit_entry_file else "medium",
            }
        )
    return candidates[:5]


def build_evidence_files(
    file_records: list[FileRecord],
    candidate_entrypoints: list[dict[str, object]],
    nodes: list[SymbolRecord],
) -> list[dict[str, object]]:
    node_files = {node.file for node in nodes}
    entry_paths = {entry["path"] for entry in candidate_entrypoints}
    evidence: list[dict[str, object]] = []
    for record in sorted(file_records, key=lambda item: item.score, reverse=True):
        if record.path not in node_files and record.path not in entry_paths and not record.feature_hits:
            continue
        confidence = "high" if record.path in entry_paths or record.feature_hits else "medium"
        evidence.append(
            {
                "path": record.path,
                "language": record.language,
                "matched_terms": record.feature_hits,
                "symbol_count": len(record.symbols),
                "confidence": confidence,
                "reason": record.entry_reason or "File contains symbols or matches that contribute to the feature trace.",
            }
        )
    return evidence[:8]


def build_cross_module_handoffs(
    edges: list[dict[str, object]],
    nodes_by_id: dict[str, SymbolRecord],
) -> list[dict[str, object]]:
    handoffs: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for edge in edges:
        from_node = nodes_by_id.get(str(edge["from"]))
        to_node = nodes_by_id.get(str(edge["to"]))
        if not from_node or not to_node or from_node.file == to_node.file:
            continue
        key = (from_node.file, to_node.file)
        if key in seen:
            continue
        seen.add(key)
        handoffs.append(
            {
                "from_file": from_node.file,
                "from_symbol": from_node.symbol,
                "to_file": to_node.file,
                "to_symbol": to_node.symbol,
                "relation": edge["relation"],
                "confidence": edge["confidence"],
                "reason": edge["reason"],
            }
        )
    return handoffs


def build_blind_spots(
    edges: list[dict[str, object]],
    file_records: list[FileRecord],
    args: argparse.Namespace,
) -> list[str]:
    blind_spots = list(GENERIC_BLIND_SPOTS)
    if not edges:
        blind_spots.append("No direct edges were observed, so the reported chain relies heavily on file and symbol heuristics.")
    if not any(record.entry_reason for record in file_records):
        blind_spots.append("No conventional entrypoint names were found, so entry promotion fell back to feature relevance.")
    if args.feature and len(tokenize_feature_terms(args.feature)) > 1:
        blind_spots.append("Multi-word feature requests can match multiple unrelated modules when the repository vocabulary is broad.")
    return blind_spots


def build_suggested_next_reads(
    candidate_entrypoints: list[dict[str, object]],
    evidence_files: list[dict[str, object]],
    cross_module_handoffs: list[dict[str, object]],
) -> list[dict[str, str]]:
    suggestions: list[dict[str, str]] = []
    seen: set[str] = set()
    for entry in candidate_entrypoints:
        path = str(entry["path"])
        if path in seen:
            continue
        seen.add(path)
        suggestions.append({"path": path, "reason": "Start here because it is the strongest candidate entrypoint."})
    for handoff in cross_module_handoffs:
        path = str(handoff["to_file"])
        if path in seen:
            continue
        seen.add(path)
        suggestions.append({"path": path, "reason": "Cross-module handoff suggests this file carries the feature deeper."})
    for record in evidence_files:
        path = str(record["path"])
        if path in seen:
            continue
        seen.add(path)
        suggestions.append({"path": path, "reason": "Evidence file contains relevant symbols or feature matches."})
    return suggestions[:8]


def build_report(root: Path, args: argparse.Namespace) -> dict[str, object]:
    feature_terms = tokenize_feature_terms(args.feature)
    explicit_entry_file = args.entry_file.replace("\\", "/").strip()
    explicit_entry_symbol = args.entry_symbol.strip()
    file_records, limits = collect_file_records(root, args)
    languages = Counter(record.language for record in file_records)

    symbol_lookup: dict[tuple[str, str], SymbolRecord] = {}
    nodes_by_id: dict[str, SymbolRecord] = {}
    next_id = 1
    for record in file_records:
        for symbol in record.symbols:
            symbol.id = f"node-{next_id}"
            next_id += 1
            symbol_lookup[(record.path, symbol.symbol)] = symbol
            nodes_by_id[symbol.id] = symbol

    edges = build_edges(file_records, symbol_lookup)
    selected_node_ids = select_relevant_nodes(
        file_records, edges, feature_terms, explicit_entry_file, explicit_entry_symbol, args.max_depth
    )
    nodes = [nodes_by_id[node_id] for node_id in selected_node_ids if node_id in nodes_by_id]
    if not nodes:
        nodes = build_fallback_nodes(file_records)

    selected_node_ids = {node.id for node in nodes}
    selected_edges = [edge for edge in edges if edge["from"] in selected_node_ids and edge["to"] in selected_node_ids]
    if not selected_edges and not any(record.feature_hits for record in file_records):
        downgrade_nodes_to_low_confidence(
            nodes,
            "Confidence was lowered because the feature request did not match direct symbols or observed call edges.",
        )
    candidate_entrypoints = build_candidate_entrypoints(file_records, explicit_entry_file)
    evidence_files = build_evidence_files(file_records, candidate_entrypoints, nodes)
    cross_module_handoffs = build_cross_module_handoffs(selected_edges, nodes_by_id)
    blind_spots = build_blind_spots(selected_edges, file_records, args)
    suggested_next_reads = build_suggested_next_reads(candidate_entrypoints, evidence_files, cross_module_handoffs)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(root),
        "request": {
            "feature": args.feature,
            "entry_file": explicit_entry_file,
            "entry_symbol": explicit_entry_symbol,
        },
        "scope": {
            "includes": normalize_prefixes(args.include),
            "excludes": normalize_prefixes(args.exclude),
            "max_files": args.max_files,
            "max_depth": args.max_depth,
            "scanned_files": len(file_records),
            "languages": [{"language": language, "count": count} for language, count in sorted(languages.items())],
        },
        "candidate_entrypoints": candidate_entrypoints,
        "evidence_files": evidence_files,
        "symbols": [
            {
                "symbol": node.symbol,
                "kind": node.kind,
                "file": node.file,
                "line": node.line,
                "language": node.language,
                "role": node.role,
                "confidence": node.confidence,
            }
            for node in nodes
        ],
        "nodes": [
            {
                "id": node.id,
                "kind": node.kind,
                "symbol": node.symbol,
                "file": node.file,
                "line": node.line,
                "language": node.language,
                "role": node.role,
                "evidence": node.evidence,
                "confidence": node.confidence,
                "notes": node.notes,
            }
            for node in nodes
        ],
        "edges": selected_edges,
        "cross_module_handoffs": cross_module_handoffs,
        "blind_spots": blind_spots,
        "suggested_next_reads": suggested_next_reads,
        "limits": limits,
    }


def render_markdown(payload: dict[str, object]) -> str:
    request = payload["request"]
    scope = payload["scope"]
    lines = [
        "# Feature Call Chain Report",
        "",
        "## Request",
        f"- Feature: `{request['feature'] or '(not provided)'}`",
        f"- Entry file: `{request['entry_file'] or '(not provided)'}`",
        f"- Entry symbol: `{request['entry_symbol'] or '(not provided)'}`",
        "",
        "## Scope",
        f"- Repository root: `{payload['repo_root']}`",
        f"- Scanned files: {scope['scanned_files']}",
        f"- Includes: `{', '.join(scope['includes']) if scope['includes'] else '(none)'}`",
        f"- Excludes: `{', '.join(scope['excludes']) if scope['excludes'] else '(none)'}`",
        "",
        "## Candidate Entrypoints",
    ]

    entrypoints = payload["candidate_entrypoints"]
    if entrypoints:
        for entry in entrypoints:
            lines.append(f"- `{entry['path']}` [{entry['confidence']}] - {entry['reason']}")
    else:
        lines.append("- No strong entrypoint candidates were identified.")

    lines.extend(["", "## Evidence Files"])
    evidence_files = payload["evidence_files"]
    if evidence_files:
        for record in evidence_files:
            matched_terms = ", ".join(record["matched_terms"]) if record["matched_terms"] else "none"
            lines.append(
                f"- `{record['path']}` [{record['confidence']}] - matched terms: {matched_terms}; {record['reason']}"
            )
    else:
        lines.append("- No evidence files were promoted.")

    lines.extend(["", "## Symbols"])
    symbols = payload["symbols"]
    if symbols:
        for symbol in symbols:
            lines.append(
                f"- `{symbol['symbol']}` in `{symbol['file']}`:{symbol['line']} [{symbol['confidence']}] - role: {symbol['role']}"
            )
    else:
        lines.append("- No symbols were extracted.")

    lines.extend(["", "## Call Chain"])
    edges = payload["edges"]
    nodes_by_id = {node["id"]: node for node in payload["nodes"]}
    if edges:
        for edge in edges:
            from_node = nodes_by_id.get(edge["from"], {"symbol": edge["from"]})
            to_node = nodes_by_id.get(edge["to"], {"symbol": edge["to"]})
            lines.append(
                f"- `{from_node['symbol']}` -> `{to_node['symbol']}` [{edge['relation']}, {edge['confidence']}, {edge['evidence']}] - {edge['reason']}"
            )
    else:
        lines.append("- No direct edges were observed; rely on evidence files and blind spots.")

    lines.extend(["", "## Cross-Module Handoffs"])
    handoffs = payload["cross_module_handoffs"]
    if handoffs:
        for handoff in handoffs:
            lines.append(
                f"- `{handoff['from_symbol']}` in `{handoff['from_file']}` -> `{handoff['to_symbol']}` in `{handoff['to_file']}` [{handoff['confidence']}] - {handoff['reason']}"
            )
    else:
        lines.append("- No cross-module handoffs were promoted.")

    lines.extend(["", "## Blind Spots"])
    for item in payload["blind_spots"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Suggested Next Reads"])
    next_reads = payload["suggested_next_reads"]
    if next_reads:
        for item in next_reads:
            lines.append(f"- `{item['path']}` - {item['reason']}")
    else:
        lines.append("- No next-read suggestions were produced.")

    if payload["limits"]:
        lines.extend(["", "## Limits"])
        for item in payload["limits"]:
            lines.append(f"- `{item['kind']}` - {item['detail']}")

    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    markdown_path = resolve_output_path(args.markdown_out, suffix=".md")
    json_path = resolve_output_path(args.json_out, suffix=".json")
    payload = build_report(root, args)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    print(f"MARKDOWN_OUT={markdown_path}")
    print(f"JSON_OUT={json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

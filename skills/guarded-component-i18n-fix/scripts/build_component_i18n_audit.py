#!/usr/bin/env python3
"""Build a guarded i18n audit for a component directory."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from collections import defaultdict
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
SCAN_EXTENSIONS = {".js", ".jsx", ".mjs", ".ts", ".tsx", ".vue", ".py", ".json"}
COMPONENT_EXTENSIONS = {".js", ".jsx", ".mjs", ".ts", ".tsx", ".vue"}
TEXT_ATTRIBUTE_NAMES = ("title", "placeholder", "label", "alt", "aria-label", "helperText")
GENERIC_TRANSLATION_PATTERNS = (
    r"\buseTranslation\s*\(",
    r"\buseTranslations\s*\(",
    r"\buseIntl\s*\(",
    r"\buseI18n\s*\(",
    r"\$t\s*\(",
    r"\bt\s*\(\s*['\"]",
    r"\bgettext\s*\(",
    r"\b_\s*\(\s*['\"]",
    r"FormattedMessage",
)
GENERIC_BLIND_SPOTS = [
    "Static scanning cannot prove runtime namespace registration, lazy locale loading, or framework-only message wiring.",
    "Generated UI text, computed message keys, and strings assembled from multiple expressions may be missed or under-classified.",
    "The safe fix plan is intentionally conservative and should not be treated as permission to introduce a second i18n framework.",
]

SYSTEM_DEFINITIONS = {
    "next-intl": {
        "kind": "hook-based",
        "packages": ("next-intl",),
        "import_patterns": (r"from\s+['\"]next-intl['\"]",),
        "usage_patterns": (
            r"\buseTranslations\s*\(",
            r"\bgetTranslations\s*\(",
            r"NextIntlClientProvider",
        ),
        "path_patterns": (r"(^|/)i18n/request\.(ts|tsx|js|jsx)$",),
        "forbid": ("react-i18next", "react-intl", "vue-i18n"),
    },
    "react-i18next": {
        "kind": "hook-based",
        "packages": ("react-i18next", "i18next"),
        "import_patterns": (r"from\s+['\"]react-i18next['\"]",),
        "usage_patterns": (
            r"\buseTranslation\s*\(",
            r"<Trans\b",
            r"\bi18n\.t\s*\(",
        ),
        "path_patterns": (r"(^|/)i18n\.(ts|tsx|js|jsx)$", r"(^|/)locales?/"),
        "forbid": ("next-intl", "react-intl", "vue-i18n"),
    },
    "react-intl": {
        "kind": "hook-based",
        "packages": ("react-intl",),
        "import_patterns": (r"from\s+['\"]react-intl['\"]",),
        "usage_patterns": (
            r"\buseIntl\s*\(",
            r"FormattedMessage",
            r"\bformatMessage\s*\(",
        ),
        "path_patterns": (),
        "forbid": ("next-intl", "react-i18next", "vue-i18n"),
    },
    "vue-i18n": {
        "kind": "hook-based",
        "packages": ("vue-i18n",),
        "import_patterns": (r"from\s+['\"]vue-i18n['\"]",),
        "usage_patterns": (
            r"\buseI18n\s*\(",
            r"\$t\s*\(",
        ),
        "path_patterns": (),
        "forbid": ("next-intl", "react-i18next", "react-intl"),
    },
    "gettext": {
        "kind": "function-based",
        "packages": (),
        "import_patterns": (r"\bfrom\s+gettext\s+import\b", r"\bimport\s+gettext\b"),
        "usage_patterns": (
            r"\bgettext\s*\(",
            r"\b_\s*\(\s*['\"]",
        ),
        "path_patterns": (r"\.po$", r"\.mo$"),
        "forbid": ("next-intl", "react-i18next", "react-intl", "vue-i18n"),
    },
}
CUSTOM_SYSTEM_HINTS = {
    "kind": "custom",
    "import_patterns": (
        r"from\s+['\"][^'\"]*(?:i18n|intl|locale|messages)[^'\"]*['\"]",
        r"from\s+['\"][^'\"]*useI18n[^'\"]*['\"]",
    ),
    "usage_patterns": (
        r"\buseI18n\s*\(",
        r"\buseLocale\s*\(",
        r"\buseTranslations\s*\(",
    ),
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan a component directory, detect the existing i18n system, and emit a guarded audit."
    )
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    parser.add_argument("--target", required=True, help="Repository-relative component directory or file.")
    parser.add_argument("--markdown-out", default="", help="Explicit output path for Markdown.")
    parser.add_argument("--json-out", default="", help="Explicit output path for JSON.")
    parser.add_argument("--max-files", type=int, default=250, help="Cap matching files scanned.")
    return parser.parse_args(argv)


def resolve_output_path(raw_path: str, suffix: str) -> Path:
    if raw_path:
        output_path = Path(raw_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path

    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="component-i18n-audit-")
    handle.close()
    return Path(handle.name).resolve()


def should_skip_directory(name: str) -> bool:
    return name in IGNORED_DIR_NAMES


def should_skip_file(path: Path) -> bool:
    suffixes = path.suffixes
    if suffixes:
        suffix = "".join(suffixes[-2:]) if len(suffixes) >= 2 else suffixes[-1]
        if suffix in IGNORED_FILE_SUFFIXES or path.suffix in IGNORED_FILE_SUFFIXES:
            return True
    return path.suffix.lower() not in SCAN_EXTENSIONS


def safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def walk_files(root: Path, max_files: int) -> tuple[list[Path], list[dict[str, str]]]:
    matching_files: list[Path] = []
    limits: list[dict[str, str]] = []

    for current_root, dir_names, file_names in os.walk(root):
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
                        "detail": f"Stopped after scanning {max_files} matching files.",
                    }
                )
                return matching_files, limits

    return matching_files, limits


def load_package_names(root: Path) -> set[str]:
    package_names: set[str] = set()
    manifest_path = root / "package.json"
    if not manifest_path.exists():
        return package_names
    try:
        payload = json.loads(safe_read_text(manifest_path))
    except json.JSONDecodeError:
        return package_names

    for section in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        entries = payload.get(section, {})
        if isinstance(entries, dict):
            package_names.update(entries.keys())
    return package_names


def score_systems(root: Path, files: list[Path], package_names: set[str]) -> dict[str, dict[str, object]]:
    scores: dict[str, dict[str, object]] = {}
    for name, definition in SYSTEM_DEFINITIONS.items():
        scores[name] = {
            "name": name,
            "kind": definition["kind"],
            "score": 0,
            "evidence": [],
        }

    custom_score = {
        "name": "custom",
        "kind": "custom",
        "score": 0,
        "evidence": [],
    }

    for system_name, definition in SYSTEM_DEFINITIONS.items():
        record = scores[system_name]
        for package_name in definition["packages"]:
            if package_name in package_names:
                record["score"] += 4
                record["evidence"].append(f"package:{package_name}")

    for file_path in files:
        relative_path = file_path.relative_to(root).as_posix()
        text = safe_read_text(file_path)

        for system_name, definition in SYSTEM_DEFINITIONS.items():
            record = scores[system_name]
            if any(re.search(pattern, relative_path) for pattern in definition["path_patterns"]):
                record["score"] += 2
                record["evidence"].append(f"path:{relative_path}")

            for pattern in definition["import_patterns"]:
                if re.search(pattern, text):
                    record["score"] += 3
                    record["evidence"].append(f"import:{relative_path}")
                    break

            for pattern in definition["usage_patterns"]:
                if re.search(pattern, text):
                    record["score"] += 2
                    record["evidence"].append(f"usage:{relative_path}")
                    break

        if any(re.search(pattern, text) for pattern in CUSTOM_SYSTEM_HINTS["import_patterns"]):
            custom_score["score"] += 2
            custom_score["evidence"].append(f"import:{relative_path}")
        if any(re.search(pattern, text) for pattern in CUSTOM_SYSTEM_HINTS["usage_patterns"]):
            custom_score["score"] += 2
            custom_score["evidence"].append(f"usage:{relative_path}")

    if custom_score["score"] > 0:
        scores["custom"] = custom_score

    return scores


def select_system(scores: dict[str, dict[str, object]]) -> tuple[dict[str, object], list[dict[str, object]]]:
    candidates = sorted(
        (
            {
                "name": record["name"],
                "kind": record["kind"],
                "score": record["score"],
                "evidence": sorted(set(record["evidence"]))[:8],
            }
            for record in scores.values()
            if int(record["score"]) > 0
        ),
        key=lambda item: (-int(item["score"]), item["name"]),
    )

    if not candidates:
        return (
            {
                "name": "unknown",
                "kind": "unknown",
                "score": 0,
                "confidence": "low",
                "notes": "No strong i18n framework signal was detected.",
                "evidence": [],
            },
            [],
        )

    selected = dict(candidates[0])
    second = candidates[1] if len(candidates) > 1 else None

    if second and int(selected["score"]) - int(second["score"]) <= 1:
        selected["confidence"] = "low"
        selected["notes"] = (
            f"Detection is ambiguous between {selected['name']} and {second['name']}. "
            "Don't introduce or normalize i18n code until the intended stack is confirmed."
        )
    elif int(selected["score"]) >= 7:
        selected["confidence"] = "high"
        selected["notes"] = f"Strong repository-wide evidence points to {selected['name']}."
    else:
        selected["confidence"] = "medium"
        selected["notes"] = f"Some repository evidence points to {selected['name']}."

    return selected, candidates


def collect_target_files(root: Path, target: Path) -> list[Path]:
    if target.is_file():
        return [target] if target.suffix.lower() in COMPONENT_EXTENSIONS else []

    component_files: list[Path] = []
    for current_root, dir_names, file_names in os.walk(target):
        dir_names[:] = [name for name in sorted(dir_names) if not should_skip_directory(name)]
        for file_name in sorted(file_names):
            file_path = Path(current_root) / file_name
            if file_path.suffix.lower() in COMPONENT_EXTENSIONS:
                component_files.append(file_path)
    return component_files


def find_candidate_strings(text: str) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped:
            continue

        for attribute_name in TEXT_ATTRIBUTE_NAMES:
            pattern = re.compile(rf"{re.escape(attribute_name)}\s*=\s*['\"]([^'\"]*[A-Za-z][^'\"]*)['\"]")
            for match in pattern.finditer(raw_line):
                value = match.group(1).strip()
                if len(value) >= 3:
                    findings.append(
                        {
                            "line": line_number,
                            "kind": f"attribute:{attribute_name}",
                            "text": value,
                            "snippet": stripped,
                        }
                    )

        for pattern_name, pattern in (
            ("jsx-text", re.compile(r">\s*([A-Za-z][^<{]{2,})\s*<")),
            ("post-expression-text", re.compile(r"}\s*([A-Za-z][^<]{2,})\s*<")),
            ("template-text", re.compile(r">\s*([\u4e00-\u9fffA-Za-z][^<{]{1,})\s*<")),
        ):
            for match in pattern.finditer(raw_line):
                value = match.group(1).strip()
                if value and not value.startswith(("http", "/")):
                    findings.append(
                        {
                            "line": line_number,
                            "kind": pattern_name,
                            "text": value,
                            "snippet": stripped,
                        }
                    )

    deduped: list[dict[str, object]] = []
    seen: set[tuple[int, str]] = set()
    for item in findings:
        key = (int(item["line"]), str(item["text"]))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def file_uses_translation(text: str) -> bool:
    return any(re.search(pattern, text) for pattern in GENERIC_TRANSLATION_PATTERNS)


def build_component_findings(
    root: Path,
    target_files: list[Path],
    selected_system: dict[str, object],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    component_findings: list[dict[str, object]] = []
    safe_fix_plan: list[dict[str, object]] = []
    blocked = selected_system["confidence"] == "low"

    for file_path in target_files:
        relative_path = file_path.relative_to(root).as_posix()
        text = safe_read_text(file_path)
        candidate_strings = find_candidate_strings(text)
        uses_translation = file_uses_translation(text)

        if blocked:
            status = "blocked"
            notes = selected_system["notes"]
            operation = "blocked-until-system-confirmed"
        elif candidate_strings and uses_translation:
            status = "mixed-patterns"
            notes = "File mixes existing translation usage with raw user-facing text."
            operation = "normalize-existing-pattern"
        elif candidate_strings:
            status = "needs-localization"
            notes = "File contains user-facing text without visible translation usage."
            operation = "reuse-existing-i18n-hook"
        elif uses_translation:
            status = "already-localized"
            notes = "File already appears to use translation APIs, and no raw text was detected."
            operation = "none"
        else:
            status = "no-user-facing-text-detected"
            notes = "No obvious user-facing text was detected."
            operation = "none"

        component_findings.append(
            {
                "path": relative_path,
                "status": status,
                "uses_translation": uses_translation,
                "candidate_strings": candidate_strings[:8],
                "notes": notes,
            }
        )

        if operation != "none":
            safe_fix_plan.append(
                {
                    "path": relative_path,
                    "operation": operation,
                    "confidence": selected_system["confidence"],
                    "rationale": notes,
                }
            )

    return component_findings, safe_fix_plan


def build_forbidden_actions(selected_system: dict[str, object], candidates: list[dict[str, object]]) -> list[str]:
    if selected_system["name"] == "unknown":
        return [
            "Do not introduce a new i18n framework until the repository's intended translation stack is confirmed.",
            "Do not bulk-rewrite components based only on hardcoded-string matches.",
        ]

    if selected_system["confidence"] == "low":
        names = ", ".join(candidate["name"] for candidate in candidates[:2])
        return [
            f"Do not introduce or normalize to a framework before resolving the ambiguous signals: {names}.",
            "Do not convert the target directory with a new i18n bootstrap, provider, or locale loader yet.",
        ]

    forbidden = []
    definition = SYSTEM_DEFINITIONS.get(selected_system["name"])
    if definition:
        for framework_name in definition["forbid"]:
            forbidden.append(
                f"Do not introduce {framework_name} in this target directory when {selected_system['name']} is already the detected project stack."
            )
    forbidden.append("Do not create duplicate locale files or a parallel message-loading path without evidence that the project already uses it.")
    return forbidden


def build_report(
    root: Path,
    target_argument: str,
    selected_system: dict[str, object],
    candidates: list[dict[str, object]],
    component_findings: list[dict[str, object]],
    safe_fix_plan: list[dict[str, object]],
    forbidden_actions: list[str],
    limits: list[dict[str, str]],
) -> dict[str, object]:
    status_counts: dict[str, int] = defaultdict(int)
    for finding in component_findings:
        status_counts[str(finding["status"])] += 1

    return {
        "root": str(root),
        "target": target_argument,
        "selected_system": selected_system,
        "detected_systems": candidates,
        "summary": {
            "component_count": len(component_findings),
            "status_counts": dict(sorted(status_counts.items())),
        },
        "component_findings": component_findings,
        "safe_fix_plan": safe_fix_plan,
        "forbidden_actions": forbidden_actions,
        "limits": limits,
        "blind_spots": GENERIC_BLIND_SPOTS,
        "suggested_next_reads": [
            "Inspect one existing localized component in the same repository before editing any target file.",
            "Read the repository locale-loading entrypoint and confirm the expected namespace or message file layout.",
        ],
    }


def render_markdown(report: dict[str, object]) -> str:
    lines: list[str] = []
    lines.append("# Component I18n Audit")
    lines.append("")
    lines.append("## Request")
    lines.append(f"- root: `{report['root']}`")
    lines.append(f"- target: `{report['target']}`")
    lines.append("")
    lines.append("## Detected I18n System")
    selected = report["selected_system"]
    lines.append(f"- selected: `{selected['name']}`")
    lines.append(f"- confidence: `{selected['confidence']}`")
    lines.append(f"- notes: {selected['notes']}")
    if selected["evidence"]:
        lines.append("- evidence:")
        for evidence in selected["evidence"]:
            lines.append(f"  - `{evidence}`")
    lines.append("")
    lines.append("## Component Findings")
    for finding in report["component_findings"]:
        lines.append(f"- `{finding['path']}` -> `{finding['status']}`")
        lines.append(f"  notes: {finding['notes']}")
        if finding["candidate_strings"]:
            preview = ", ".join(f"`{item['text']}`" for item in finding["candidate_strings"][:3])
            lines.append(f"  strings: {preview}")
    if not report["component_findings"]:
        lines.append("- No component files were found under the requested target.")
    lines.append("")
    lines.append("## Safe Fix Plan")
    for step in report["safe_fix_plan"]:
        lines.append(f"- `{step['path']}` -> `{step['operation']}` ({step['confidence']})")
        lines.append(f"  reason: {step['rationale']}")
    if not report["safe_fix_plan"]:
        lines.append("- No code edits are recommended from this audit alone.")
    lines.append("")
    lines.append("## Forbidden Actions")
    for action in report["forbidden_actions"]:
        lines.append(f"- {action}")
    lines.append("")
    lines.append("## Blind Spots")
    for item in report["blind_spots"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Suggested Next Reads")
    for item in report["suggested_next_reads"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if not root.exists():
        print(f"[ERROR] root does not exist: {root}")
        return 1

    target = (root / args.target).resolve()
    if not target.exists():
        print(f"[ERROR] target does not exist: {args.target}")
        return 1

    files, limits = walk_files(root, args.max_files)
    package_names = load_package_names(root)
    scores = score_systems(root, files, package_names)
    selected_system, candidates = select_system(scores)
    target_files = collect_target_files(root, target)
    component_findings, safe_fix_plan = build_component_findings(root, target_files, selected_system)
    forbidden_actions = build_forbidden_actions(selected_system, candidates)

    report = build_report(
        root=root,
        target_argument=args.target,
        selected_system=selected_system,
        candidates=candidates,
        component_findings=component_findings,
        safe_fix_plan=safe_fix_plan,
        forbidden_actions=forbidden_actions,
        limits=limits,
    )

    markdown_out = resolve_output_path(args.markdown_out, ".md")
    json_out = resolve_output_path(args.json_out, ".json")
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    json_out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"MARKDOWN_OUT={markdown_out}")
    print(f"JSON_OUT={json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

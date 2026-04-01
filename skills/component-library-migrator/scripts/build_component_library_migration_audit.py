#!/usr/bin/env python3
"""Build a conservative component-library migration audit for a React target path."""

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
    "tmp",
    "venv",
}
COMPONENT_EXTENSIONS = {".js", ".jsx", ".mjs", ".ts", ".tsx"}
SUPPORTED_NATIVE_COMPONENTS = {
    "button": "Button",
    "input": "Input",
    "textarea": "Textarea",
    "select": "Select",
}
HIGH_RISK_PATTERNS = (
    (re.compile(r'role\s*=\s*["\']dialog["\']'), "File contains a custom dialog surface."),
    (re.compile(r'aria-modal\s*=\s*["\']true["\']'), "File manages modal semantics directly."),
    (re.compile(r"\bonClose\b"), "File wires close handlers that could change overlay behavior."),
)

BUILTIN_LIBRARY_ALIASES = {
    "shadcn/ui": {"shadcn", "shadcn/ui", "shadcn-ui"},
    "mui": {"mui", "@mui/material", "material-ui", "mui/material"},
    "ant-design": {"ant-design", "antd", "ant design"},
    "chakra-ui": {"chakra", "chakra-ui", "@chakra-ui/react", "chakra ui"},
    "heroui": {"heroui", "hero ui", "hero-ui", "@heroui/react"},
}
BUILTIN_LIBRARY_DISPLAY_NAMES = {
    "shadcn/ui": "shadcn/ui",
    "mui": "MUI",
    "ant-design": "Ant Design",
    "chakra-ui": "Chakra UI",
    "heroui": "HeroUI",
}
KNOWN_UI_PACKAGES = {
    "@mui/material": "mui",
    "antd": "ant-design",
    "@chakra-ui/react": "chakra-ui",
    "@heroui/react": "heroui",
    "nextui-org/react": "heroui",
    "shadcn-ui": "shadcn/ui",
    "radix-ui": "shadcn/ui",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan a component directory and emit a conservative component-library migration audit."
    )
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    parser.add_argument("--target", required=True, help="Repository-relative component directory or file.")
    parser.add_argument("--library", required=True, help="Requested target component library.")
    parser.add_argument("--markdown-out", default="", help="Explicit output path for Markdown.")
    parser.add_argument("--json-out", default="", help="Explicit output path for JSON.")
    parser.add_argument("--max-files", type=int, default=250, help="Cap matching files scanned.")
    return parser.parse_args(argv)


def resolve_output_path(raw_path: str, suffix: str) -> Path:
    if raw_path:
        output_path = Path(raw_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path

    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="component-library-migrator-")
    handle.close()
    return Path(handle.name).resolve()


def should_skip_directory(name: str) -> bool:
    return name in IGNORED_DIR_NAMES


def safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def normalize_target_library(raw_name: str) -> dict[str, object]:
    normalized = re.sub(r"[\s_]+", "-", raw_name.strip().lower())
    for canonical_name, aliases in BUILTIN_LIBRARY_ALIASES.items():
        if normalized in {alias.lower() for alias in aliases}:
            return {
                "requested_name": raw_name,
                "canonical_name": canonical_name,
                "display_name": BUILTIN_LIBRARY_DISPLAY_NAMES[canonical_name],
                "is_builtin": True,
                "notes": f"{BUILTIN_LIBRARY_DISPLAY_NAMES[canonical_name]} is supported for conservative automatic edits.",
            }

    fallback_name = normalized.strip("-") or "unknown-library"
    return {
        "requested_name": raw_name,
        "canonical_name": fallback_name,
        "display_name": raw_name.strip() or fallback_name,
        "is_builtin": False,
        "notes": "Unsupported libraries stay in audit-only mode and do not produce automatic edits in version one.",
    }


def load_package_names(root: Path) -> set[str]:
    manifest_path = root / "package.json"
    if not manifest_path.exists():
        return set()

    try:
        payload = json.loads(safe_read_text(manifest_path))
    except json.JSONDecodeError:
        return set()

    package_names: set[str] = set()
    for section in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        entries = payload.get(section, {})
        if isinstance(entries, dict):
            package_names.update(entries.keys())
    return package_names


def detect_current_ui_libraries(package_names: set[str]) -> list[str]:
    detected = sorted({canonical for package_name, canonical in KNOWN_UI_PACKAGES.items() if package_name in package_names})
    return detected


def collect_target_files(root: Path, target: Path, max_files: int) -> tuple[list[Path], list[dict[str, str]]]:
    if target.is_file():
        if target.suffix.lower() in COMPONENT_EXTENSIONS:
            return [target], []
        return [], [{"kind": "non-component-target", "detail": f"Target file is not a supported component file: {target.name}"}]

    component_files: list[Path] = []
    limits: list[dict[str, str]] = []
    for current_root, dir_names, file_names in os.walk(target):
        dir_names[:] = [name for name in sorted(dir_names) if not should_skip_directory(name)]
        for file_name in sorted(file_names):
            file_path = Path(current_root) / file_name
            if file_path.suffix.lower() not in COMPONENT_EXTENSIONS:
                continue
            component_files.append(file_path)
            if len(component_files) >= max_files:
                limits.append({"kind": "max-files", "detail": f"Stopped after scanning {max_files} component files."})
                return component_files, limits
    return component_files, limits


def detect_native_components(text: str) -> list[str]:
    found: list[str] = []
    for native_name in SUPPORTED_NATIVE_COMPONENTS:
        if re.search(rf"<{native_name}\b", text):
            found.append(native_name)
    return found


def detect_custom_wrapper_usage(text: str) -> list[str]:
    imported_names: list[str] = []
    import_pattern = re.compile(
        r"import\s+(?:{(?P<braced>[^}]+)}|(?P<default>[A-Z][A-Za-z0-9_]*))\s+from\s+['\"](?P<source>\.{1,2}/[^'\"]+)['\"]"
    )
    for match in import_pattern.finditer(text):
        raw_names: list[str] = []
        if match.group("default"):
            raw_names.append(match.group("default"))
        if match.group("braced"):
            raw_names.extend(
                item.strip().split(" as ")[-1].strip()
                for item in match.group("braced").split(",")
                if item.strip()
            )
        for name in raw_names:
            if name and name[:1].isupper():
                imported_names.append(name)

    used_wrappers = [name for name in imported_names if re.search(rf"<{re.escape(name)}\b", text)]
    return sorted(set(used_wrappers))


def detect_high_risk_patterns(text: str) -> list[str]:
    reasons = [reason for pattern, reason in HIGH_RISK_PATTERNS if pattern.search(text)]
    if re.search(r"\bchildren\b", text) and re.search(r"\bopen\b", text) and re.search(r"\bonClose\b", text):
        reasons.append("File appears to define a stateful composite overlay component.")
    return sorted(set(reasons))


def build_component_findings(
    root: Path,
    target_files: list[Path],
    target_library: dict[str, object],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[str]]:
    component_findings: list[dict[str, object]] = []
    candidate_mappings: list[dict[str, object]] = []
    safe_fix_plan: list[dict[str, object]] = []
    blocked_reasons: list[str] = []
    audit_only_mode = not bool(target_library["is_builtin"])

    for file_path in target_files:
        relative_path = file_path.relative_to(root).as_posix()
        text = safe_read_text(file_path)
        custom_wrappers = detect_custom_wrapper_usage(text)
        high_risk_reasons = detect_high_risk_patterns(text)
        native_components = detect_native_components(text)

        status = "no-candidate"
        notes = "No low-risk migration candidates were detected."
        file_candidate_mappings: list[dict[str, object]] = []

        if high_risk_reasons:
            status = "blocked"
            notes = "; ".join(high_risk_reasons)
            blocked_reasons.extend(high_risk_reasons)
        elif custom_wrappers:
            status = "blocked"
            notes = f"File relies on local wrapper components: {', '.join(custom_wrappers)}."
            blocked_reasons.append(notes)
        elif native_components:
            for native_name in native_components:
                mapping = {
                    "path": relative_path,
                    "source_component": native_name,
                    "target_component": SUPPORTED_NATIVE_COMPONENTS[native_name],
                    "confidence": "medium" if audit_only_mode else "high",
                    "rationale": f"Native `<{native_name}>` usage is a low-ambiguity migration candidate.",
                }
                file_candidate_mappings.append(mapping)

            if audit_only_mode:
                status = "audit-only"
                notes = "Candidate replacements were found, but the requested library is not built in."
            else:
                status = "safe-candidate"
                notes = "File contains low-ambiguity native elements that match built-in migration rules."
                for mapping in file_candidate_mappings:
                    safe_fix_plan.append(
                        {
                            "path": relative_path,
                            "operation": "replace-import-and-jsx",
                            "target_component": mapping["target_component"],
                            "confidence": mapping["confidence"],
                            "rationale": mapping["rationale"],
                        }
                    )

            candidate_mappings.extend(file_candidate_mappings)

        component_findings.append(
            {
                "path": relative_path,
                "status": status,
                "native_components": native_components,
                "custom_wrappers": custom_wrappers,
                "notes": notes,
            }
        )

    return component_findings, candidate_mappings, safe_fix_plan, sorted(set(blocked_reasons))


def build_forbidden_actions(target_library: dict[str, object], mode: str) -> list[str]:
    actions = [
        "Do not broaden edits beyond the target path unless the audit proves a required shared wrapper or import seam.",
        "Do not auto-migrate complex overlays, data grids, editors, or other high-risk composite widgets in version one.",
        "Do not claim migration success from the static audit alone.",
    ]
    if mode == "audit-only":
        actions.insert(
            0,
            f"Do not generate direct migration edits for unsupported target library `{target_library['canonical_name']}`.",
        )
    else:
        actions.insert(
            0,
            f"Do not mix multiple migration styles when targeting built-in library `{target_library['canonical_name']}`.",
        )
    return actions


def build_report(
    root: Path,
    target_argument: str,
    target_library: dict[str, object],
    current_ui_libraries: list[str],
    component_findings: list[dict[str, object]],
    candidate_mappings: list[dict[str, object]],
    safe_fix_plan: list[dict[str, object]],
    blocked_reasons: list[str],
    limits: list[dict[str, str]],
) -> dict[str, object]:
    mode = "auto-edit" if target_library["is_builtin"] else "audit-only"
    status_counts: dict[str, int] = defaultdict(int)
    for finding in component_findings:
        status_counts[str(finding["status"])] += 1

    return {
        "root": str(root),
        "target": target_argument,
        "mode": mode,
        "target_library": target_library,
        "detected_ui_libraries": current_ui_libraries,
        "summary": {
            "component_count": len(component_findings),
            "status_counts": dict(sorted(status_counts.items())),
        },
        "component_findings": component_findings,
        "candidate_mappings": candidate_mappings,
        "safe_fix_plan": safe_fix_plan if mode == "auto-edit" else [],
        "blocked_reasons": blocked_reasons,
        "forbidden_actions": build_forbidden_actions(target_library, mode),
        "limits": limits,
        "blind_spots": [
            "Static scanning cannot prove runtime parity, visual parity, or component-library theming compatibility.",
            "Local wrapper components and shared abstractions may hide migration requirements outside the requested target path.",
        ],
        "suggested_next_reads": [
            "Inspect an existing component that already uses the requested target library inside the same repository, if one exists.",
            "Review the nearest form, overlay, or styling utility used by the target files before applying edits.",
        ],
    }


def render_markdown(report: dict[str, object]) -> str:
    lines: list[str] = []
    lines.append("# Component Library Migration Audit")
    lines.append("")
    lines.append("## Request")
    lines.append(f"- root: `{report['root']}`")
    lines.append(f"- target: `{report['target']}`")
    lines.append(f"- mode: `{report['mode']}`")
    lines.append("")
    lines.append("## Target Library")
    target_library = report["target_library"]
    lines.append(f"- requested: `{target_library['requested_name']}`")
    lines.append(f"- canonical: `{target_library['canonical_name']}`")
    lines.append(f"- built-in: `{target_library['is_builtin']}`")
    lines.append(f"- notes: {target_library['notes']}")
    if report["detected_ui_libraries"]:
        current = ", ".join(f"`{name}`" for name in report["detected_ui_libraries"])
        lines.append(f"- detected current libraries: {current}")
    lines.append("")
    lines.append("## Component Findings")
    if report["component_findings"]:
        for finding in report["component_findings"]:
            lines.append(f"- `{finding['path']}` -> `{finding['status']}`")
            lines.append(f"  notes: {finding['notes']}")
    else:
        lines.append("- No component files were found under the requested target.")
    lines.append("")
    lines.append("## Candidate Mappings")
    if report["candidate_mappings"]:
        for mapping in report["candidate_mappings"]:
            lines.append(
                f"- `{mapping['path']}`: `<{mapping['source_component']}>` -> `{mapping['target_component']}` ({mapping['confidence']})"
            )
            lines.append(f"  reason: {mapping['rationale']}")
    else:
        lines.append("- No low-risk candidate mappings were found.")
    lines.append("")
    lines.append("## Safe Fix Plan")
    if report["safe_fix_plan"]:
        for step in report["safe_fix_plan"]:
            lines.append(
                f"- `{step['path']}` -> `{step['operation']}` using `{step['target_component']}` ({step['confidence']})"
            )
            lines.append(f"  reason: {step['rationale']}")
    else:
        lines.append("- No automatic edits are recommended from this audit.")
    lines.append("")
    lines.append("## Forbidden Actions")
    for action in report["forbidden_actions"]:
        lines.append(f"- {action}")
    lines.append("")
    lines.append("## Blocked Reasons")
    if report["blocked_reasons"]:
        for reason in report["blocked_reasons"]:
            lines.append(f"- {reason}")
    else:
        lines.append("- No blocked files were detected.")
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

    target_library = normalize_target_library(args.library)
    package_names = load_package_names(root)
    current_ui_libraries = detect_current_ui_libraries(package_names)
    target_files, limits = collect_target_files(root, target, args.max_files)
    component_findings, candidate_mappings, safe_fix_plan, blocked_reasons = build_component_findings(
        root=root,
        target_files=target_files,
        target_library=target_library,
    )
    report = build_report(
        root=root,
        target_argument=args.target,
        target_library=target_library,
        current_ui_libraries=current_ui_libraries,
        component_findings=component_findings,
        candidate_mappings=candidate_mappings,
        safe_fix_plan=safe_fix_plan,
        blocked_reasons=blocked_reasons,
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

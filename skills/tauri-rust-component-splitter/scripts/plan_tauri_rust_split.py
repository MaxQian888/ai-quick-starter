#!/usr/bin/env python3
"""Plan a conservative split for large Tauri Rust modules."""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


GENERIC_MODULE_NAMES = {"common", "helpers", "manager", "misc", "shared", "utils"}
PLATFORM_TOKENS = {"window", "shell", "tray", "clipboard", "os", "process", "native", "dialog"}
SERVICE_TOKENS = {"send", "sync", "fetch", "load", "save", "refresh", "install", "resolve"}
MODEL_SUFFIXES = ("Payload", "Request", "Response", "Model", "Config", "Settings", "Record")


@dataclass
class Symbol:
    name: str
    kind: str
    bucket: str
    file_path: Path
    line: int
    confidence: str
    rationale: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect a src-tauri Rust target and plan a conservative split.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--target", required=True, help="Target Rust file or directory inside src-tauri.")
    parser.add_argument("--markdown-out", default="", help="Optional Markdown output path.")
    parser.add_argument("--json-out", default="", help="Optional JSON output path.")
    parser.add_argument("--scaffold", action="store_true", help="Create placeholder files for the proposed layout.")
    return parser.parse_args()


def resolve_output_path(raw_path: str, suffix: str) -> Path:
    if raw_path:
        output_path = Path(raw_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="tauri-rust-split-")
    handle.close()
    return Path(handle.name).resolve()


def to_snake_case(value: str) -> str:
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    text = re.sub(r"[^A-Za-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text.lower() or "module"


def is_snake_case(value: str) -> bool:
    return bool(re.fullmatch(r"[a-z][a-z0-9_]*", value))


def is_pascal_case(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Z][A-Za-z0-9]*", value))


def relative_posix(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def resolve_paths(root_raw: str, target_raw: str) -> tuple[Path, Path]:
    root = Path(root_raw).resolve()
    target = Path(target_raw)
    if not target.is_absolute():
        target = (root / target).resolve()
    else:
        target = target.resolve()
    return root, target


def ensure_src_tauri_target(root: Path, target: Path) -> Path:
    if not target.exists():
        raise ValueError(f"Target does not exist: {target}")
    try:
        relative = target.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Target must be inside repository root: {target}") from exc

    parts = relative.parts
    if "src-tauri" not in parts:
        raise ValueError(f"Target must be inside src-tauri: {relative.as_posix()}")

    src_tauri_index = parts.index("src-tauri")
    tauri_root = root.joinpath(*parts[: src_tauri_index + 1])
    return tauri_root


def iter_rust_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target] if target.suffix == ".rs" else []
    return sorted(path for path in target.rglob("*.rs") if path.is_file())


def classify_type(name: str, source: str) -> tuple[str, str, str]:
    lowered = name.lower()
    if name.endswith("State"):
        return "state", "high", "State type or shared mutable state signal."
    if name.endswith("Service") or name.endswith("Manager"):
        return "services", "high", "Service-style type name."
    if "Mutex<" in source or "RwLock<" in source:
        return "state", "medium", "Shared mutable state signal inside the type body."
    if any(token in lowered for token in PLATFORM_TOKENS) or name.endswith("Platform"):
        return "platform", "medium", "Platform-facing type name."
    if name.endswith("Error"):
        return "errors", "high", "Error type name."
    if name.endswith(MODEL_SUFFIXES):
        return "models", "medium", "Data model naming signal."
    return "keep", "low", "No strong Tauri split signal."


def classify_function(name: str, is_command: bool) -> tuple[str, str, str]:
    lowered = name.lower()
    if is_command:
        return "commands", "high", "Annotated with #[tauri::command]."
    if any(token in lowered for token in PLATFORM_TOKENS):
        return "platform", "medium", "Platform-oriented function name."
    if any(token in lowered for token in SERVICE_TOKENS):
        return "services", "medium", "Service-like function name."
    return "keep", "low", "No strong split signal for standalone function."


def build_naming_findings(file_path: Path, source: str, root: Path) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    stem = file_path.stem
    if stem in GENERIC_MODULE_NAMES:
        findings.append(
            {
                "rule": "generic-module-name",
                "severity": "medium",
                "subject": relative_posix(file_path, root),
                "current_name": stem,
                "suggested_name": "",
                "rationale": "Generic module names hide responsibility and make future splits harder.",
            }
        )

    for match in re.finditer(r"\b(?:pub\s+)?struct\s+([A-Za-z_][A-Za-z0-9_]*)", source):
        name = match.group(1)
        if not is_pascal_case(name):
            findings.append(
                {
                    "rule": "type-should-be-pascal-case",
                    "severity": "medium",
                    "subject": relative_posix(file_path, root),
                    "current_name": name,
                    "suggested_name": "".join(part.capitalize() for part in re.split(r"[_\W]+", name) if part),
                    "rationale": "Rust struct names should use PascalCase.",
                }
            )

    for match in re.finditer(r"\b(?:pub\s+)?(?:async\s+)?fn\s+([A-Za-z_][A-Za-z0-9_]*)", source):
        name = match.group(1)
        if not is_snake_case(name):
            findings.append(
                {
                    "rule": "function-should-be-snake-case",
                    "severity": "medium",
                    "subject": relative_posix(file_path, root),
                    "current_name": name,
                    "suggested_name": to_snake_case(name),
                    "rationale": "Rust function names should use snake_case.",
                }
            )

    return findings


def collect_block(lines: list[str], start_index: int) -> str:
    block_lines: list[str] = []
    depth = 0
    saw_brace = False
    for line in lines[start_index:]:
        block_lines.append(line)
        depth += line.count("{")
        depth -= line.count("}")
        if "{" in line:
            saw_brace = True
        if saw_brace and depth <= 0:
            break
        if not saw_brace and line.strip().endswith(";"):
            break
    return "\n".join(block_lines)


def extract_symbols(file_path: Path) -> list[Symbol]:
    source = file_path.read_text(encoding="utf-8")
    lines = source.splitlines()
    symbols: list[Symbol] = []
    brace_depth = 0
    pending_command = False

    for index, line in enumerate(lines):
        stripped = line.strip()

        if "#[tauri::command]" in stripped:
            pending_command = True

        if brace_depth == 0:
            struct_match = re.match(r"(?:pub\s+)?struct\s+([A-Za-z_][A-Za-z0-9_]*)", stripped)
            if struct_match:
                name = struct_match.group(1)
                block = collect_block(lines, index)
                bucket, confidence, rationale = classify_type(name, block)
                if bucket != "keep":
                    symbols.append(Symbol(name, "struct", bucket, file_path, index + 1, confidence, rationale))

            function_match = re.match(r"(?:pub\s+)?(?:async\s+)?fn\s+([A-Za-z_][A-Za-z0-9_]*)", stripped)
            if function_match:
                name = function_match.group(1)
                bucket, confidence, rationale = classify_function(name, pending_command)
                if bucket != "keep":
                    symbols.append(Symbol(name, "function", bucket, file_path, index + 1, confidence, rationale))
                pending_command = False
            elif stripped and not stripped.startswith("#[") and pending_command:
                pending_command = False

        brace_depth += line.count("{")
        brace_depth -= line.count("}")

    return symbols


def destination_for_symbol(symbol: Symbol, tauri_src_root: Path, target: Path) -> Path:
    target_stem = target.stem if target.is_file() else target.name
    target_stem = to_snake_case(target_stem)
    if symbol.bucket == "commands":
        file_name = f"{target_stem}_commands.rs"
        return tauri_src_root / "src" / "commands" / file_name
    if symbol.bucket == "state":
        return tauri_src_root / "src" / "state" / f"{to_snake_case(symbol.name)}.rs"
    if symbol.bucket == "services":
        return tauri_src_root / "src" / "services" / f"{to_snake_case(symbol.name)}.rs"
    if symbol.bucket == "platform":
        return tauri_src_root / "src" / "platform" / f"{to_snake_case(symbol.name)}.rs"
    if symbol.bucket == "models":
        return tauri_src_root / "src" / "models" / f"{to_snake_case(symbol.name)}.rs"
    if symbol.bucket == "errors":
        return tauri_src_root / "src" / "errors.rs"
    return symbol.file_path


def build_project_context(root: Path, target: Path, tauri_root: Path) -> dict[str, object]:
    rust_files = list((tauri_root / "src").glob("*.rs")) if (tauri_root / "src").exists() else []
    return {
        "tauri_root": relative_posix(tauri_root, root),
        "target_kind": "file" if target.is_file() else "directory",
        "target_relative_path": relative_posix(target, root),
        "nearby_root_files": sorted(path.name for path in rust_files),
    }


def build_payload(root: Path, target: Path, tauri_root: Path) -> dict[str, object]:
    rust_files = iter_rust_files(target)
    if not rust_files:
        raise ValueError(f"No Rust files found under target: {relative_posix(target, root)}")

    naming_findings: list[dict[str, object]] = []
    symbols: list[Symbol] = []
    for file_path in rust_files:
        source = file_path.read_text(encoding="utf-8")
        naming_findings.extend(build_naming_findings(file_path, source, root))
        symbols.extend(extract_symbols(file_path))

    grouped: dict[str, dict[str, object]] = {}
    symbol_plan: list[dict[str, object]] = []
    for symbol in symbols:
        destination = destination_for_symbol(symbol, tauri_root, target)
        destination_key = relative_posix(destination, root)
        group = grouped.setdefault(
            destination_key,
            {
                "path": destination_key,
                "responsibility": symbol.bucket,
                "confidence": symbol.confidence,
                "symbols": [],
                "rationale": symbol.rationale,
            },
        )
        group["symbols"].append({"name": symbol.name, "kind": symbol.kind, "line": symbol.line})
        if symbol.confidence == "high":
            group["confidence"] = "high"
        symbol_plan.append(
            {
                "name": symbol.name,
                "kind": symbol.kind,
                "bucket": symbol.bucket,
                "source_path": relative_posix(symbol.file_path, root),
                "line": symbol.line,
                "destination_path": destination_key,
                "confidence": symbol.confidence,
                "rationale": symbol.rationale,
            }
        )

    proposed_files = [grouped[key] for key in sorted(grouped)]
    migration_phases = [
        {
            "name": "extract-commands",
            "steps": ["Move Tauri command functions first and keep their signatures stable."],
        },
        {
            "name": "extract-state-and-services",
            "steps": ["Move shared state and service types after command entry points are isolated."],
        },
        {
            "name": "wire-module-exports",
            "steps": ["Add or update module declarations in a later explicit refactor pass."],
        },
    ]
    scaffold_plan = [{"path": item["path"], "responsibility": item["responsibility"]} for item in proposed_files]

    return {
        "root": str(root),
        "target": relative_posix(target, root),
        "project_context": build_project_context(root, target, tauri_root),
        "summary": {
            "file_count": len(rust_files),
            "symbol_count": len(symbol_plan),
            "proposed_file_count": len(proposed_files),
            "naming_issue_count": len(naming_findings),
        },
        "naming_findings": naming_findings,
        "proposed_files": proposed_files,
        "symbol_plan": symbol_plan,
        "migration_phases": migration_phases,
        "scaffold_plan": scaffold_plan,
        "forbidden_actions": [
            "Do not move implementation automatically from this plan alone.",
            "Do not replace a mixed-responsibility file with generic common or utils buckets.",
            "Do not claim the Rust refactor is complete until a later code-moving pass is verified.",
        ],
        "verification_suggestions": [
            "Review the plan before moving any Rust implementation.",
            "Run cargo fmt, cargo check, and targeted tests after a later migration pass.",
            "Keep Tauri command signatures stable while extracting supporting logic.",
        ],
        "scaffold_created": [],
        "scaffold_skipped": [],
    }


def render_markdown(payload: dict[str, object]) -> str:
    context = payload["project_context"]
    lines = [
        "# Tauri Rust Split Plan",
        "",
        "## Request",
        f"- target: `{payload['target']}`",
        "",
        "## Project Context",
        f"- tauri_root: `{context['tauri_root']}`",
        f"- target_kind: `{context['target_kind']}`",
        f"- nearby_root_files: `{json.dumps(context['nearby_root_files'])}`",
        "",
        "## Naming Findings",
    ]

    if payload["naming_findings"]:
        for item in payload["naming_findings"]:
            lines.append(
                f"- `{item['current_name']}` -> `{item['rule']}` ({item['severity']}): {item['rationale']}"
            )
    else:
        lines.append("- No naming problems detected in the scanned Rust files.")

    lines.extend(["", "## Proposed File Layout"])
    if payload["proposed_files"]:
        for item in payload["proposed_files"]:
            symbol_names = ", ".join(symbol["name"] for symbol in item["symbols"])
            lines.append(
                f"- `{item['path']}` ({item['responsibility']}, {item['confidence']}): {symbol_names or 'placeholder'}"
            )
    else:
        lines.append("- No confident split targets were detected.")

    lines.extend(["", "## Migration Phases"])
    for phase in payload["migration_phases"]:
        lines.append(f"- `{phase['name']}`")
        for step in phase["steps"]:
            lines.append(f"  - {step}")

    lines.extend(["", "## Forbidden Actions"])
    for item in payload["forbidden_actions"]:
        lines.append(f"- {item}")

    return "\n".join(lines) + "\n"


def ensure_mod_decl(mod_file: Path, module_name: str) -> bool:
    declaration = f"pub mod {module_name};"
    if mod_file.exists():
        content = mod_file.read_text(encoding="utf-8")
        if declaration in content:
            return False
        if content and not content.endswith("\n"):
            content += "\n"
        mod_file.write_text(content + declaration + "\n", encoding="utf-8")
        return True

    mod_file.parent.mkdir(parents=True, exist_ok=True)
    mod_file.write_text(declaration + "\n", encoding="utf-8")
    return True


def create_scaffold(payload: dict[str, object], root: Path) -> None:
    created: list[str] = []
    skipped: list[str] = []

    for item in payload["proposed_files"]:
        destination = root / item["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            skipped.append(item["path"])
        else:
            symbol_lines = [f"// - {symbol['kind']}: {symbol['name']}" for symbol in item["symbols"]]
            body = [
                "// Placeholder generated by plan_tauri_rust_split.py",
                f"// Responsibility: {item['responsibility']}",
                "// Planned symbols:",
                *symbol_lines,
                "",
                "// TODO: Move implementation here in a later explicit refactor pass.",
                "",
            ]
            destination.write_text("\n".join(body), encoding="utf-8")
            created.append(item["path"])

        parent = destination.parent
        if parent.name in {"commands", "services", "state", "platform", "models"}:
            mod_file = parent / "mod.rs"
            changed = ensure_mod_decl(mod_file, destination.stem)
            mod_relative = relative_posix(mod_file, root)
            if changed and mod_relative not in created:
                created.append(mod_relative)

    payload["scaffold_created"] = sorted(created)
    payload["scaffold_skipped"] = sorted(skipped)


def main() -> int:
    args = parse_args()
    try:
        root, target = resolve_paths(args.root, args.target)
        tauri_root = ensure_src_tauri_target(root, target)
        payload = build_payload(root, target, tauri_root)
        if args.scaffold:
            create_scaffold(payload, root)

        markdown_out = resolve_output_path(args.markdown_out, ".md")
        json_out = resolve_output_path(args.json_out, ".json")
        markdown_out.write_text(render_markdown(payload), encoding="utf-8")
        json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        print(f"MARKDOWN_OUT={markdown_out}")
        print(f"JSON_OUT={json_out}")
        return 0
    except Exception as exc:  # pragma: no cover - CLI guardrail
        print(f"Error: {exc}", file=__import__("sys").stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

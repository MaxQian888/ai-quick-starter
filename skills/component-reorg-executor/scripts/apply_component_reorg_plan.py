#!/usr/bin/env python3
"""Apply an approved component reorganization plan."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
from pathlib import Path


TEXT_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
IMPORT_PATTERN = re.compile(
    r"(?P<prefix>\b(?:import|export)\b[\s\S]*?\bfrom\s*|import\s*\()\s*(?P<quote>['\"])(?P<spec>\.[^'\"]*)(?P=quote)",
    re.MULTILINE,
)
MODULE_SUFFIXES = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply an approved component reorganization plan.")
    parser.add_argument("--plan", required=True, help="Path to planner JSON output.")
    parser.add_argument("--markdown-out", default="", help="Optional Markdown output path.")
    parser.add_argument("--json-out", default="", help="Optional JSON output path.")
    return parser.parse_args()


def resolve_output_path(raw_path: str, suffix: str) -> Path:
    if raw_path:
        output_path = Path(raw_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="component-reorg-exec-")
    handle.close()
    return Path(handle.name).resolve()


def read_plan(plan_path: Path) -> dict[str, object]:
    return json.loads(plan_path.read_text(encoding="utf-8"))


def validate_plan(payload: dict[str, object]) -> tuple[Path, Path, list[dict[str, object]], list[dict[str, object]]]:
    root = Path(str(payload["root"])).resolve()
    target = ensure_within_root(root, root / str(payload["target_directory"]), "Target directory")
    move_plan_raw = payload.get("move_plan", [])
    if not isinstance(move_plan_raw, list):
        raise ValueError("move_plan must be a list")
    moves: list[dict[str, object]] = []
    skipped: list[dict[str, object]] = []
    for entry in move_plan_raw:
        if not isinstance(entry, dict):
            continue
        action = str(entry.get("action", ""))
        if action == "move":
            moves.append(entry)
        else:
            skipped.append(entry)
    return root, target, moves, skipped


def normalize_relative(root: Path, raw_path: str) -> str:
    return (root / raw_path).resolve().relative_to(root.resolve()).as_posix()


def ensure_within_root(root: Path, candidate: Path, label: str) -> Path:
    resolved_root = root.resolve()
    resolved_candidate = candidate.resolve()
    try:
        resolved_candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"{label} must stay within the repository root: {resolved_candidate}") from exc
    return resolved_candidate


def move_files(root: Path, moves: list[dict[str, object]]) -> list[dict[str, object]]:
    applied: list[dict[str, object]] = []
    for entry in moves:
        source_rel = str(entry["path"])
        destination_rel = str(entry["destination_path"])
        source_path = ensure_within_root(root, root / source_rel, "Planned move source")
        destination_path = ensure_within_root(root, root / destination_rel, "Planned move destination")
        if not source_path.exists():
            raise FileNotFoundError(f"Planned move source does not exist: {source_rel}")
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_path), str(destination_path))
        applied.append(
            {
                "source_path": source_rel,
                "destination_path": destination_rel,
                "proposed_subfolder": str(entry.get("proposed_subfolder", "")),
            }
        )
    return applied


def collect_text_files(target: Path) -> list[Path]:
    if not target.exists():
        return []
    files: list[Path] = []
    for path in sorted(target.rglob("*")):
        if path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS:
            files.append(path)
    return files


def build_module_candidates(base_dir: Path, specifier: str) -> list[Path]:
    raw = (base_dir / specifier).resolve()
    candidates = [raw]
    for suffix in MODULE_SUFFIXES:
        candidates.append(Path(str(raw) + suffix))
    for suffix in MODULE_SUFFIXES:
        candidates.append(raw / f"index{suffix}")
    deduped: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        deduped.append(candidate)
    return deduped


def format_relative_specifier(from_dir: Path, target_path: Path, original_specifier: str) -> str:
    relative = Path(__import__("os").path.relpath(target_path, from_dir))
    relative_text = relative.as_posix()
    if not relative_text.startswith("."):
        relative_text = f"./{relative_text}"

    if any(original_specifier.endswith(suffix) for suffix in MODULE_SUFFIXES):
        return relative_text

    for suffix in MODULE_SUFFIXES:
        if relative_text.endswith(suffix):
            relative_text = relative_text[: -len(suffix)]
            break

    if relative_text.endswith("/index"):
        relative_text = relative_text[: -len("/index")]
    return relative_text


def rewrite_file(file_path: Path, move_map: dict[Path, Path], anchor_dir: Path | None = None) -> bool:
    original_text = file_path.read_text(encoding="utf-8")
    changed = False
    source_dir = anchor_dir or file_path.parent

    def replace(match: re.Match[str]) -> str:
        nonlocal changed
        specifier = match.group("spec")
        destination = None
        for candidate in build_module_candidates(source_dir, specifier):
            moved_destination = move_map.get(candidate)
            if moved_destination is not None:
                destination = moved_destination
                break
            if candidate.exists():
                destination = candidate
                break
        if destination is None:
            return match.group(0)
        new_specifier = format_relative_specifier(file_path.parent, destination, specifier)
        if new_specifier == specifier:
            return match.group(0)
        changed = True
        return f"{match.group('prefix')}{match.group('quote')}{new_specifier}{match.group('quote')}"

    updated_text = IMPORT_PATTERN.sub(replace, original_text)
    if changed:
        file_path.write_text(updated_text, encoding="utf-8")
    return changed


def rewrite_local_imports(root: Path, target: Path, applied_moves: list[dict[str, object]]) -> list[str]:
    move_map = {
        (root / entry["source_path"]).resolve(): (root / entry["destination_path"]).resolve()
        for entry in applied_moves
    }
    anchor_map = {
        (root / entry["destination_path"]).resolve(): (root / entry["source_path"]).resolve().parent
        for entry in applied_moves
    }
    rewritten: list[str] = []
    for file_path in collect_text_files(target):
        if rewrite_file(file_path, move_map, anchor_map.get(file_path.resolve())):
            rewritten.append(file_path.resolve().relative_to(root.resolve()).as_posix())
    return sorted(rewritten)


def build_payload(
    plan_path: Path,
    root: Path,
    target: Path,
    applied_moves: list[dict[str, object]],
    rewritten_files: list[str],
    skipped_entries: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "plan_path": str(plan_path.resolve()),
        "root": str(root),
        "target_directory": target.resolve().relative_to(root.resolve()).as_posix(),
        "summary": {
            "moved": len(applied_moves),
            "rewritten_files": len(rewritten_files),
            "skipped_entries": len(skipped_entries),
        },
        "applied_moves": applied_moves,
        "rewritten_files": rewritten_files,
        "skipped_entries": skipped_entries,
    }


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Component Reorg Execution Report",
        "",
        "## Request",
        f"- plan: `{payload['plan_path']}`",
        f"- root: `{payload['root']}`",
        f"- target: `{payload['target_directory']}`",
        "",
        "## Applied Moves",
    ]
    if payload["applied_moves"]:
        for entry in payload["applied_moves"]:
            lines.append(f"- `{entry['source_path']}` -> `{entry['destination_path']}`")
    else:
        lines.append("- No move entries were applied.")

    lines.extend(["", "## Rewritten Files"])
    if payload["rewritten_files"]:
        for item in payload["rewritten_files"]:
            lines.append(f"- `{item}`")
    else:
        lines.append("- No local import or barrel rewrites were required.")

    lines.extend(["", "## Skipped Entries"])
    if payload["skipped_entries"]:
        for entry in payload["skipped_entries"]:
            lines.append(f"- `{entry.get('path', '')}` -> `{entry.get('action', 'unknown')}`")
    else:
        lines.append("- None.")

    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    plan_path = Path(args.plan).resolve()
    if not plan_path.exists():
        print(f"[ERROR] plan does not exist: {plan_path}")
        return 1

    try:
        payload = read_plan(plan_path)
        root, target, moves, skipped = validate_plan(payload)
        applied_moves = move_files(root, moves)
        rewritten_files = rewrite_local_imports(root, target, applied_moves)
        report = build_payload(plan_path, root, target, applied_moves, rewritten_files, skipped)
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 1

    markdown_out = resolve_output_path(args.markdown_out, ".md")
    json_out = resolve_output_path(args.json_out, ".json")
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    json_out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"MARKDOWN_OUT={markdown_out}")
    print(f"JSON_OUT={json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

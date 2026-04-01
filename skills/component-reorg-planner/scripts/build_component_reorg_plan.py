#!/usr/bin/env python3
"""Audit a component directory and emit a conservative reorganization plan."""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from collections import defaultdict
from pathlib import Path

from detect_component_context import analyze_context


IGNORED_DIR_NAMES = {
    ".git",
    ".idea",
    ".next",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
}
COMPONENT_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx"}
STYLE_EXTENSIONS = {".css", ".scss", ".sass", ".less"}
GROUP_RULES = {
    "forms": {"form", "field", "input", "select", "checkbox", "radio", "switch", "picker", "editor"},
    "data-display": {"table", "grid", "datatable", "list", "row", "column"},
    "overlays": {"dialog", "modal", "drawer", "sheet", "popover", "tooltip"},
    "navigation": {"tabs", "tab", "nav", "menu", "breadcrumb", "pagination", "stepper"},
    "filters": {"filter", "filters", "search", "query", "sort", "facet"},
    "feedback": {"alert", "toast", "error", "empty", "loading", "skeleton", "success"},
    "analytics": {"chart", "graph", "metric", "stats", "sparkline"},
}
GROUP_RATIONALES = {
    "forms": "Matched form-related naming signals.",
    "data-display": "Matched data display naming signals.",
    "overlays": "Matched modal or dialog naming signals.",
    "navigation": "Matched navigation naming signals.",
    "filters": "Matched search or filtering naming signals.",
    "feedback": "Matched feedback-state naming signals.",
    "analytics": "Matched analytics naming signals.",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit a component directory and emit a function-based reorganization plan."
    )
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--target", required=True, help="Target component directory or file.")
    parser.add_argument("--markdown-out", default="", help="Optional Markdown output path.")
    parser.add_argument("--json-out", default="", help="Optional JSON output path.")
    return parser.parse_args()


def resolve_output_path(raw_path: str, suffix: str) -> Path:
    if raw_path:
        output_path = Path(raw_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="component-reorg-plan-")
    handle.close()
    return Path(handle.name).resolve()


def should_skip_dir(path: Path) -> bool:
    return path.name in IGNORED_DIR_NAMES


def iter_target_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    files: list[Path] = []
    for current_root, dir_names, file_names in __import__("os").walk(target):
        dir_names[:] = [name for name in sorted(dir_names) if name not in IGNORED_DIR_NAMES]
        for file_name in sorted(file_names):
            files.append(Path(current_root) / file_name)
    return files


def tokenize_name(file_path: Path) -> list[str]:
    stem = file_path.stem
    if stem.endswith(".test") or stem.endswith(".spec") or stem.endswith(".stories"):
        stem = stem.rsplit(".", 1)[0]
    words = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", stem)
    words = re.sub(r"[^A-Za-z0-9]+", " ", words)
    return [token.lower() for token in words.split() if token]


def classify_file_kind(file_path: Path) -> str:
    name = file_path.name.lower()
    stem = file_path.stem
    if ".test." in name or ".spec." in name:
        return "test"
    if ".stories." in name:
        return "story"
    if file_path.suffix.lower() in STYLE_EXTENSIONS or ".module." in name:
        return "style"
    if stem == "index":
        return "barrel"
    if stem.startswith("use") and len(stem) > 3 and stem[3:4].isupper():
        return "hook"
    if stem.endswith(".types") or stem.endswith("Types") or name in {"types.ts", "types.tsx"}:
        return "types"
    if file_path.suffix.lower() in COMPONENT_EXTENSIONS and stem[:1].isupper():
        return "component"
    return "other"


def classify_group(file_path: Path) -> tuple[str | None, int, list[str]]:
    tokens = tokenize_name(file_path)
    best_group: str | None = None
    best_matches: list[str] = []
    for group_name, keywords in GROUP_RULES.items():
        matches = sorted({token for token in tokens if token in keywords})
        if len(matches) > len(best_matches):
            best_group = group_name
            best_matches = matches
    if best_group is None or not best_matches:
        return None, 0, []
    return best_group, len(best_matches), best_matches


def build_move_entry(root: Path, target: Path, file_path: Path, kind: str) -> dict[str, object]:
    relative = file_path.resolve().relative_to(root.resolve()).as_posix()
    target_dir = target if target.is_dir() else target.parent
    if kind != "component":
        return {
            "path": relative,
            "file_kind": kind,
            "action": "keep-put",
            "proposed_subfolder": "",
            "destination_path": relative,
            "confidence": "high",
            "rationale": "Support files stay in the existing layer until a later execution pass is approved.",
        }

    group_name, score, matches = classify_group(file_path)
    if group_name is None:
        return {
            "path": relative,
            "file_kind": kind,
            "action": "keep-put",
            "proposed_subfolder": "",
            "destination_path": relative,
            "confidence": "low",
            "rationale": "Low-confidence functional fit. Keep the component in place instead of forcing a generic grouping.",
        }

    destination = target_dir / group_name / file_path.name
    confidence = "high" if score >= 2 else "medium"
    return {
        "path": relative,
        "file_kind": kind,
        "action": "move",
        "proposed_subfolder": group_name,
        "destination_path": destination.resolve().relative_to(root.resolve()).as_posix(),
        "confidence": confidence,
        "rationale": f"{GROUP_RATIONALES[group_name]} Matched tokens: {', '.join(matches)}.",
    }


def build_component_clusters(move_plan: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for entry in move_plan:
        if entry["action"] == "move":
            grouped[str(entry["proposed_subfolder"])].append(entry)

    clusters: list[dict[str, object]] = []
    for group_name in sorted(grouped):
        entries = grouped[group_name]
        clusters.append(
            {
                "name": group_name,
                "rationale": GROUP_RATIONALES[group_name],
                "files": [entry["path"] for entry in entries],
                "confidence": "high" if all(entry["confidence"] == "high" for entry in entries) else "medium",
            }
        )
    return clusters


def build_summary(move_plan: list[dict[str, object]]) -> dict[str, int]:
    move_candidates = sum(1 for entry in move_plan if entry["action"] == "move")
    keep_put = sum(1 for entry in move_plan if entry["action"] == "keep-put")
    return {
        "file_count": len(move_plan),
        "move_candidates": move_candidates,
        "keep_put": keep_put,
    }


def build_forbidden_moves(summary: dict[str, int], context: dict[str, object]) -> list[str]:
    forbidden = [
        "Do not move files from this plan directly; approve and execute the move graph in a separate implementation pass.",
        "Do not move hooks, barrel files, or support-only files into functional subfolders unless the repository already co-locates them there.",
        "Do not rewrite import paths or delete compatibility seams until the planned destination map is approved.",
    ]
    if int(summary["move_candidates"]) == 0:
        forbidden.append("Do not force a low-confidence reshuffle just to create subfolders.")
    if context["structure_mode"] == "mixed":
        forbidden.append("Do not convert a mixed repository layout into a new global structure from one local component directory.")
    return forbidden


def build_risk_register(move_plan: list[dict[str, object]]) -> list[dict[str, str]]:
    risks = [
        {
            "severity": "medium",
            "title": "Import churn",
            "detail": "Any approved component moves will require a follow-up pass to update relative imports and barrel exports.",
        }
    ]
    if any(entry["file_kind"] == "barrel" for entry in move_plan):
        risks.append(
            {
                "severity": "medium",
                "title": "Barrel coupling",
                "detail": "An index barrel exists in the target directory and may hide downstream consumers of the current flat layout.",
            }
        )
    if any(entry["confidence"] == "low" for entry in move_plan if entry["file_kind"] == "component"):
        risks.append(
            {
                "severity": "low",
                "title": "Weak naming signals",
                "detail": "Some components do not expose enough functional naming hints to justify automated regrouping.",
            }
        )
    return risks


def build_verification_suggestions(context: dict[str, object]) -> list[str]:
    suggestions = [
        "Review the move plan with the owning engineer before any file movement.",
        "When executing approved moves, update relative imports and barrel exports in the same patch.",
        "Re-run the narrowest component tests or lint command covering the target directory after execution.",
    ]
    if context["framework"] == "nextjs":
        suggestions.append("If the target sits under App Router, verify route-level rendering after any approved reorganization.")
    return suggestions


def render_markdown(payload: dict[str, object]) -> str:
    context = payload["project_context"]
    lines = [
        "# Component Reorg Plan",
        "",
        "## Request",
        f"- root: `{payload['root']}`",
        f"- target: `{payload['target_directory']}`",
        "",
        "## Project Context",
        f"- framework: `{context['framework']}`",
        f"- router: `{context['router']}`",
        f"- structure mode: `{context['structure_mode']}`",
        f"- recommended support paths: `{json.dumps(context['recommended_paths'], ensure_ascii=True)}`",
        "",
        "## Proposed Functional Subfolders",
    ]
    if payload["proposed_subfolders"]:
        for cluster in payload["proposed_subfolders"]:
            lines.append(f"- `{cluster['name']}` ({cluster['confidence']}): {cluster['rationale']}")
    else:
        lines.append("- No confident functional subfolders were detected.")

    lines.extend(["", "## Move Plan"])
    for entry in payload["move_plan"]:
        lines.append(
            f"- `{entry['path']}` -> `{entry['action']}`"
            + (f" into `{entry['proposed_subfolder']}`" if entry["proposed_subfolder"] else "")
        )
        lines.append(f"  rationale: {entry['rationale']}")

    lines.extend(["", "## Forbidden Moves"])
    for item in payload["forbidden_moves"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Verification Suggestions"])
    for item in payload["verification_suggestions"]:
        lines.append(f"- {item}")

    return "\n".join(lines) + "\n"


def build_payload(root: Path, target: Path) -> dict[str, object]:
    context = analyze_context(root, target)
    files = iter_target_files(target)
    move_plan = [build_move_entry(root, target, file_path, classify_file_kind(file_path)) for file_path in files]
    proposed_subfolders = build_component_clusters(move_plan)
    summary = build_summary(move_plan)

    return {
        "root": str(root),
        "target_directory": target.resolve().relative_to(root.resolve()).as_posix(),
        "project_context": context,
        "summary": summary,
        "proposed_subfolders": proposed_subfolders,
        "move_plan": move_plan,
        "blocked_or_keep_put": [entry for entry in move_plan if entry["action"] != "move"],
        "risk_register": build_risk_register(move_plan),
        "forbidden_moves": build_forbidden_moves(summary, context),
        "verification_suggestions": build_verification_suggestions(context),
    }


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    target = (root / args.target).resolve() if not Path(args.target).is_absolute() else Path(args.target).resolve()
    if not root.exists():
        print(f"[ERROR] root does not exist: {root}")
        return 1
    if not target.exists():
        print(f"[ERROR] target does not exist: {target}")
        return 1

    payload = build_payload(root, target)
    markdown_out = resolve_output_path(args.markdown_out, ".md")
    json_out = resolve_output_path(args.json_out, ".json")
    markdown_out.write_text(render_markdown(payload), encoding="utf-8")
    json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"MARKDOWN_OUT={markdown_out}")
    print(f"JSON_OUT={json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

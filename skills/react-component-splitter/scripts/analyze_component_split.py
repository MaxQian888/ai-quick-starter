#!/usr/bin/env python3
"""Analyze a React component file and suggest split candidates."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


COMPONENT_DECLARATION_PATTERNS = [
    re.compile(r"export\s+default\s+function\s+([A-Z][A-Za-z0-9_]*)\s*\("),
    re.compile(r"export\s+function\s+([A-Z][A-Za-z0-9_]*)\s*\("),
    re.compile(r"const\s+([A-Z][A-Za-z0-9_]*)\s*[:=]\s*(?:\(|\w)"),
]

JSX_TAG_PATTERN = re.compile(r"<([A-Za-z][A-Za-z0-9]*)\b")
HOOK_CALL_PATTERN = re.compile(r"\b(use[A-Z][A-Za-z0-9_]*)\s*\(")
INLINE_HANDLER_PATTERN = re.compile(r"on[A-Z][A-Za-z0-9_]*\s*=\s*\{[^}]*=>")
EVENT_HANDLER_BINDING_PATTERN = re.compile(r"on[A-Z][A-Za-z0-9_]*\s*=\s*\{")
FETCH_PATTERN = re.compile(r"\b(fetch|axios|useQuery|useMutation|graphql|request)\b")
TYPE_PATTERN = re.compile(r"^\s*(type|interface)\s+[A-Za-z0-9_]+", re.MULTILINE)

HELPER_FUNCTION_PATTERN = re.compile(
    r"\b(?:function|const)\s+([a-z][A-Za-z0-9_]*)\s*(?:=|\()"
)
HELPER_NAME_HINTS = (
    "format",
    "build",
    "parse",
    "map",
    "sort",
    "validate",
    "normalize",
    "derive",
    "compute",
    "filter",
)

COMMON_SUFFIXES = (
    "Page",
    "Screen",
    "View",
    "Container",
    "Panel",
    "Section",
    "Modal",
    "Dialog",
    "Card",
)


@dataclass
class Candidate:
    id: str
    kind: str
    priority: str
    reason: str
    suggested_file: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "kind": self.kind,
            "priority": self.priority,
            "reason": self.reason,
            "suggested_file": self.suggested_file,
        }


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def detect_component_name(content: str, fallback: str) -> str:
    for pattern in COMPONENT_DECLARATION_PATTERNS:
        match = pattern.search(content)
        if match:
            return match.group(1)
    return fallback


def strip_component_suffix(component_name: str) -> str:
    for suffix in COMMON_SUFFIXES:
        if component_name.endswith(suffix) and len(component_name) > len(suffix):
            return component_name[: -len(suffix)]
    return component_name


def guess_feature_name(component_name: str) -> str:
    base = strip_component_suffix(component_name)
    return base or component_name


def count_jsx_lines(content: str) -> int:
    lines = content.splitlines()
    return sum(1 for line in lines if "<" in line and ">" in line)


def count_non_empty_lines(content: str) -> int:
    return sum(1 for line in content.splitlines() if line.strip())


def count_local_helper_functions(content: str) -> int:
    names = HELPER_FUNCTION_PATTERN.findall(content)
    return sum(1 for name in names if any(name.startswith(hint) for hint in HELPER_NAME_HINTS))


def split_path(path: str) -> Path:
    return Path(path) if path else Path(".")


def resolve_recommended_dirs(layout: dict | None) -> dict[str, str]:
    default_dirs = {
        "components": "src/components",
        "hooks": "src/hooks",
        "utils": "src/utils",
        "types": "src/types",
    }
    if not layout:
        return default_dirs
    recommendations = layout.get("recommendations")
    if not isinstance(recommendations, dict):
        return default_dirs
    merged = dict(default_dirs)
    for key in merged:
        value = recommendations.get(key)
        if isinstance(value, str) and value.strip():
            merged[key] = value
    return merged


def parse_layout(layout_path: str | None) -> dict | None:
    if not layout_path:
        return None
    path = Path(layout_path)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def rank_risk(lines_non_empty: int, total_hooks: int, inline_handlers: int) -> str:
    if lines_non_empty >= 350 or total_hooks >= 10 or inline_handlers >= 10:
        return "high"
    if lines_non_empty >= 220 or total_hooks >= 6 or inline_handlers >= 5:
        return "medium"
    return "low"


def build_candidates(
    feature_name: str,
    metrics: dict[str, int],
    recommended_dirs: dict[str, str],
) -> list[Candidate]:
    candidates: list[Candidate] = []
    candidate_idx = 1

    jsx_pressure = metrics["jsx_lines"] >= 120 or metrics["jsx_tag_total"] >= 80
    if jsx_pressure:
        candidates.append(
            Candidate(
                id=f"C{candidate_idx}",
                kind="presentational-extract",
                priority="high",
                reason="Large JSX surface indicates UI composition should be split from orchestration.",
                suggested_file=str(split_path(recommended_dirs["components"]) / f"{feature_name}View.tsx"),
            )
        )
        candidate_idx += 1

    state_pressure = metrics["state_hooks"] >= 3 or metrics["effect_hooks"] >= 2
    if state_pressure:
        candidates.append(
            Candidate(
                id=f"C{candidate_idx}",
                kind="controller-hook-extract",
                priority="high",
                reason="State/effect density is high; move behavior orchestration into a dedicated hook.",
                suggested_file=str(split_path(recommended_dirs["hooks"]) / f"use{feature_name}Controller.ts"),
            )
        )
        candidate_idx += 1

    if metrics["data_calls"] >= 1:
        candidates.append(
            Candidate(
                id=f"C{candidate_idx}",
                kind="data-access-hook-extract",
                priority="medium",
                reason="Data fetching or mutations detected; isolate IO from presentational UI.",
                suggested_file=str(split_path(recommended_dirs["hooks"]) / f"use{feature_name}Data.ts"),
            )
        )
        candidate_idx += 1

    if metrics["helper_functions"] >= 2:
        candidates.append(
            Candidate(
                id=f"C{candidate_idx}",
                kind="utility-extract",
                priority="medium",
                reason="Multiple pure helper-like functions found; centralize domain transforms.",
                suggested_file=str(split_path(recommended_dirs["utils"]) / f"{feature_name.lower()}.utils.ts"),
            )
        )
        candidate_idx += 1

    if metrics["type_declarations"] >= 2:
        candidates.append(
            Candidate(
                id=f"C{candidate_idx}",
                kind="types-extract",
                priority="low",
                reason="Several local type/interface declarations suggest a shared type module.",
                suggested_file=str(split_path(recommended_dirs["types"]) / f"{feature_name.lower()}.types.ts"),
            )
        )
        candidate_idx += 1

    if metrics["inline_handlers"] >= 4:
        candidates.append(
            Candidate(
                id=f"C{candidate_idx}",
                kind="handler-stabilization",
                priority="medium",
                reason="Many inline JSX handlers detected; consider moving callbacks to named functions or hook.",
                suggested_file=str(split_path(recommended_dirs["hooks"]) / f"use{feature_name}Handlers.ts"),
            )
        )

    return candidates


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze a React component file and suggest split candidates."
    )
    parser.add_argument("--file", required=True, help="Path to target .tsx/.jsx component file")
    parser.add_argument(
        "--layout-json",
        default=None,
        help="Optional path to JSON output from detect_react_layout.py",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    file_path = Path(args.file).resolve()
    if not file_path.exists():
        raise SystemExit(f"File not found: {file_path}")

    content = read_text(file_path)
    component_name = detect_component_name(content, file_path.stem)
    feature_name = guess_feature_name(component_name)
    layout = parse_layout(args.layout_json)
    recommended_dirs = resolve_recommended_dirs(layout)

    hooks = HOOK_CALL_PATTERN.findall(content)
    jsx_tags = JSX_TAG_PATTERN.findall(content)
    inline_handlers = len(INLINE_HANDLER_PATTERN.findall(content))
    event_bindings = len(EVENT_HANDLER_BINDING_PATTERN.findall(content))

    metrics = {
        "lines_non_empty": count_non_empty_lines(content),
        "jsx_lines": count_jsx_lines(content),
        "jsx_tag_total": len(jsx_tags),
        "custom_component_tags": sum(1 for tag in jsx_tags if tag[:1].isupper()),
        "dom_tag_total": sum(1 for tag in jsx_tags if tag[:1].islower()),
        "hook_calls_total": len(hooks),
        "state_hooks": sum(1 for hook in hooks if hook in ("useState", "useReducer")),
        "effect_hooks": sum(1 for hook in hooks if hook == "useEffect"),
        "memo_hooks": sum(1 for hook in hooks if hook in ("useMemo", "useCallback")),
        "data_calls": len(FETCH_PATTERN.findall(content)),
        "inline_handlers": inline_handlers,
        "event_bindings_total": event_bindings,
        "helper_functions": count_local_helper_functions(content),
        "type_declarations": len(TYPE_PATTERN.findall(content)),
    }

    risk_level = rank_risk(
        lines_non_empty=metrics["lines_non_empty"],
        total_hooks=metrics["hook_calls_total"],
        inline_handlers=metrics["inline_handlers"],
    )

    candidates = build_candidates(feature_name, metrics, recommended_dirs)
    result = {
        "file": str(file_path),
        "component_name": component_name,
        "feature_name": feature_name,
        "risk_level": risk_level,
        "metrics": metrics,
        "recommended_dirs": recommended_dirs,
        "candidates": [candidate.to_dict() for candidate in candidates],
    }

    if args.pretty:
        print(json.dumps(result, indent=2, ensure_ascii=True))
    else:
        print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

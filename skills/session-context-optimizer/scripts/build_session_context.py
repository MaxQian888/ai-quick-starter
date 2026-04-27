from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


DEFAULT_SKIP_PREFIXES = (
    "_tmp",
    "tmp",
    "node_modules",
    ".uv-cache",
    ".uv-python",
    "__pycache__",
)

STRUCTURE_WEIGHTS = {
    "has_skill_md": 1,
    "has_openai_yaml": 2,
    "has_references_dir": 2,
    "has_scripts_dir": 3,
    "has_tests_dir": 3,
}

TASK_STOPWORDS = {
    "a",
    "an",
    "and",
    "build",
    "for",
    "from",
    "help",
    "improve",
    "in",
    "into",
    "of",
    "on",
    "or",
    "the",
    "this",
    "to",
    "use",
    "with",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scan a repository for candidate skill modules.")
    parser.add_argument("--root", required=True, help="Repository root to inspect.")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--task", default=None, help="Optional current-task string used for lightweight relevance scoring.")
    parser.add_argument("--include", action="append", default=[], help="Prefix filter for candidate paths.")
    parser.add_argument("--exclude", action="append", default=[], help="Prefix filter for skipped candidate paths.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of candidates to report.")
    return parser


def should_skip_directory(name: str) -> bool:
    return any(name == prefix or name.startswith(f"{prefix}-") or name.startswith(f"{prefix}_") for prefix in DEFAULT_SKIP_PREFIXES)


def matches_filters(path: str, includes: list[str], excludes: list[str]) -> bool:
    if includes and not any(path.startswith(pattern) for pattern in includes):
        return False
    if excludes and any(path.startswith(pattern) for pattern in excludes):
        return False
    return True


def tokenize(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 1 and token not in TASK_STOPWORDS
    }


def read_frontmatter_fields(skill_md_path: Path) -> dict[str, str]:
    if not skill_md_path.is_file():
        return {}
    text = skill_md_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip("\"'")
    return fields


def collect_filename_terms(path: Path) -> set[str]:
    terms: set[str] = set()
    for directory_name in ("references", "scripts", "tests"):
        directory = path / directory_name
        if not directory.is_dir():
            continue
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                terms.update(tokenize(file_path.stem))
                terms.update(tokenize(file_path.name))
    return terms


def describe_recommendation(structure_score: int, matched_terms: list[str], ranking_mode: str) -> str:
    if structure_score >= 9:
        structure_phrase = "strong structure score"
    elif structure_score >= 5:
        structure_phrase = "solid structure score"
    else:
        structure_phrase = "basic structure score"

    if ranking_mode == "structure-plus-task":
        if matched_terms:
            return f"{structure_phrase}; task matched {', '.join(matched_terms[:4])}."
        return f"{structure_phrase}; no direct task terms matched."
    return f"{structure_phrase}."


def collect_candidate(path: Path, task_terms: set[str], ranking_mode: str) -> dict[str, object]:
    signals = {
        "has_skill_md": (path / "SKILL.md").is_file(),
        "has_openai_yaml": (path / "agents" / "openai.yaml").is_file(),
        "has_references_dir": (path / "references").is_dir(),
        "has_scripts_dir": (path / "scripts").is_dir(),
        "has_tests_dir": (path / "tests").is_dir(),
    }
    frontmatter = read_frontmatter_fields(path / "SKILL.md")
    path_terms = tokenize(path.name)
    name_terms = tokenize(frontmatter.get("name", ""))
    description_terms = tokenize(frontmatter.get("description", ""))
    filename_terms = collect_filename_terms(path)
    structure_score = sum(weight for key, weight in STRUCTURE_WEIGHTS.items() if signals[key])

    matched_terms: list[str] = []
    task_score = 0
    if task_terms:
        for term in sorted(task_terms):
            term_score = 0
            if term in path_terms or term in name_terms:
                term_score += 3
            if term in description_terms:
                term_score += 3
            if term in filename_terms:
                term_score += 1
            if term_score:
                matched_terms.append(term)
                task_score += term_score

    return {
        "path": path.name,
        "signal_count": sum(1 for value in signals.values() if value),
        "structure_score": structure_score,
        "task_score": task_score,
        "final_score": structure_score + task_score,
        "matched_terms": matched_terms,
        "why_recommended": describe_recommendation(structure_score, matched_terms, ranking_mode),
        "signals": signals,
    }


def scan_repository(
    root: Path,
    task: str | None = None,
    includes: list[str] | None = None,
    excludes: list[str] | None = None,
    limit: int | None = None,
) -> dict[str, object]:
    includes = includes or []
    excludes = excludes or []
    task_terms = tokenize(task or "")
    ranking_mode = "structure-plus-task" if task_terms else "structure-only"
    candidates: list[dict[str, object]] = []
    skipped: list[dict[str, str]] = []

    for entry in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        if not entry.is_dir():
            continue
        if should_skip_directory(entry.name):
            skipped.append({"path": entry.name, "reason": "default-skip"})
            continue

        candidate = collect_candidate(entry, task_terms, ranking_mode)
        if not candidate["signals"]["has_skill_md"]:
            continue
        if not matches_filters(entry.name, includes, excludes):
            skipped.append({"path": entry.name, "reason": "filtered"})
            continue
        candidates.append(candidate)

    candidates.sort(key=lambda item: (-item["final_score"], -item["structure_score"], item["path"].lower()))

    if limit is not None:
        candidates = candidates[: max(limit, 0)]

    return {
        "root": str(root),
        "task": task,
        "ranking_mode": ranking_mode,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "skipped": skipped,
    }


def render_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Session Context Candidates",
        "",
        f"- Root: `{summary['root']}`",
        f"- Ranking mode: {summary['ranking_mode']}",
        f"- Candidate count: {summary['candidate_count']}",
        "",
        "## Candidates",
    ]

    candidates = summary["candidates"]
    if candidates:
        for candidate in candidates:
            lines.append(
                f"- `{candidate['path']}` - final `{candidate['final_score']}`, structure `{candidate['structure_score']}`, task `{candidate['task_score']}`"
            )
            if candidate["matched_terms"]:
                lines.append(f"  - matched: `{', '.join(candidate['matched_terms'])}`")
            lines.append(f"  - why: {candidate['why_recommended']}")
    else:
        lines.append("- None")

    lines.extend(["", "## Skipped Paths"])
    skipped = summary["skipped"]
    if skipped:
        for item in skipped:
            lines.append(f"- `{item['path']}` ({item['reason']})")
    else:
        lines.append("- None")

    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    summary = scan_repository(
        Path(args.root),
        task=args.task,
        includes=args.include,
        excludes=args.exclude,
        limit=args.limit,
    )
    if args.format == "markdown":
        print(render_markdown(summary), end="")
    else:
        print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

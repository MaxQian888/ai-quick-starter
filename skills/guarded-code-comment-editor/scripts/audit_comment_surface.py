from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path


LANGUAGE_BY_SUFFIX = {
    ".ts": "typescript",
    ".tsx": "tsx",
    ".js": "javascript",
    ".jsx": "jsx",
    ".py": "python",
    ".sh": "shell",
    ".ps1": "powershell",
}

SUSPICIOUS_PATTERNS = [
    re.compile(r"^this (function|method|component|script)\b", re.IGNORECASE),
    re.compile(r"^initialize (the|a|an)\b", re.IGNORECASE),
    re.compile(r"^handle (the|this)\b", re.IGNORECASE),
    re.compile(r"^set (the|a|an)\b", re.IGNORECASE),
    re.compile(r"^return (the|a|an)\b", re.IGNORECASE),
    re.compile(r"^check (if|whether)\b", re.IGNORECASE),
    re.compile(r"^create (the|a|an)\b", re.IGNORECASE),
    re.compile(r"^update (the|a|an)\b", re.IGNORECASE),
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit local code-comment style before editing.")
    parser.add_argument("--root", required=True, help="Repository root for relative paths.")
    parser.add_argument("--target", required=True, help="Target file or directory to audit.")
    parser.add_argument("--json", dest="as_json", action="store_true", help="Emit JSON output.")
    parser.add_argument(
        "--max-files",
        type=int,
        default=200,
        help="Maximum supported files to inspect when the target is a directory.",
    )
    return parser.parse_args(argv)


def classify_language(path: Path) -> str | None:
    return LANGUAGE_BY_SUFFIX.get(path.suffix.lower())


def iter_supported_files(target: Path, max_files: int) -> list[Path]:
    if target.is_file():
        return [target] if classify_language(target) else []

    files: list[Path] = []
    for path in sorted(target.rglob("*")):
        if not path.is_file():
            continue
        if classify_language(path) is None:
            continue
        files.append(path)
        if len(files) >= max(1, max_files):
            break
    return files


def safe_relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def extract_line_comments(text: str, language: str) -> list[dict[str, object]]:
    comments: list[dict[str, object]] = []
    marker = "#"
    if language in {"typescript", "tsx", "javascript", "jsx"}:
        marker = "//"

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if marker == "//":
            if not stripped.startswith("//"):
                continue
            comment_text = stripped[2:].strip()
        else:
            if not stripped.startswith("#"):
                continue
            comment_text = stripped[1:].strip()
        if not comment_text:
            continue
        comments.append({"line": line_number, "text": comment_text, "kind": "inline"})
    return comments


def extract_python_docstrings(text: str) -> list[dict[str, object]]:
    docstrings: list[dict[str, object]] = []
    pattern = re.compile(r'("""|\'\'\')([\s\S]*?)\1', re.MULTILINE)
    for match in pattern.finditer(text):
        start_line = text.count("\n", 0, match.start()) + 1
        body = match.group(2).strip()
        if not body:
            continue
        docstrings.append({"line": start_line, "text": body, "kind": "docstring"})
    return docstrings


def is_suspicious_comment(text: str) -> bool:
    normalized = " ".join(text.strip().split())
    if len(normalized) < 6:
        return False
    return any(pattern.search(normalized) for pattern in SUSPICIOUS_PATTERNS)


def classify_density(comment_units: int, line_count: int) -> str:
    if line_count <= 0:
        return "sparse"
    ratio = (comment_units / line_count) * 100
    if ratio < 8:
        return "sparse"
    if ratio < 20:
        return "moderate"
    return "dense"


def build_needs_review(suspicious_comments: list[dict[str, object]], density: str) -> list[str]:
    flags: list[str] = []
    if suspicious_comments:
        flags.append("rewrite-generic-comment")
    if density == "dense":
        flags.append("avoid-over-commenting")
    return flags


def classify_status(suspicious_comments: list[dict[str, object]], comment_units: int) -> str:
    if suspicious_comments:
        return "needs-rewrite"
    if comment_units == 0:
        return "sparse-surface"
    return "stable"


def analyze_file(path: Path, root: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    language = classify_language(path)
    if language is None:
        raise ValueError(f"Unsupported file type: {path}")

    inline_comments = extract_line_comments(text, language)
    docstrings = extract_python_docstrings(text) if language == "python" else []
    suspicious_comments = [
        {"line": entry["line"], "text": entry["text"], "kind": entry["kind"]}
        for entry in [*inline_comments, *docstrings]
        if entry["kind"] == "inline" and is_suspicious_comment(str(entry["text"]))
    ]
    informative_units = max(0, len(inline_comments) + len(docstrings) - len(suspicious_comments))
    total_lines = len(text.splitlines()) or 1
    density = classify_density(len(inline_comments) + len(docstrings), total_lines)
    exemplar_score = (informative_units * 4) + (len(docstrings) * 3) - (len(suspicious_comments) * 6)

    return {
        "path": safe_relative(path, root),
        "language": language,
        "line_count": total_lines,
        "comment_lines": len(inline_comments),
        "docstring_blocks": len(docstrings),
        "density": density,
        "density_per_100_lines": round(((len(inline_comments) + len(docstrings)) / total_lines) * 100, 2),
        "suspicious_comments": suspicious_comments,
        "needs_review": build_needs_review(suspicious_comments, density),
        "status": classify_status(suspicious_comments, len(inline_comments) + len(docstrings)),
        "exemplar_score": exemplar_score,
    }


def build_selected_style(file_findings: list[dict[str, object]]) -> dict[str, object]:
    language_counts = Counter(item["language"] for item in file_findings)
    if not language_counts:
        return {
            "primary_language": None,
            "confidence": "low",
            "comment_density": "sparse",
            "docstring_style": "inline-only",
            "evidence": [],
        }

    primary_language = sorted(language_counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
    total_files = len(file_findings)
    dominant_count = language_counts[primary_language]
    density_counts = Counter(item["density"] for item in file_findings)
    comment_density = sorted(density_counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
    python_docstrings = sum(item["docstring_blocks"] for item in file_findings if item["language"] == "python")

    if python_docstrings >= max(2, dominant_count):
        docstring_style = "docstring-heavy"
    elif python_docstrings > 0:
        docstring_style = "mixed"
    else:
        docstring_style = "inline-only"

    if total_files == 1 or dominant_count >= 2:
        confidence = "high"
    elif dominant_count == total_files:
        confidence = "medium"
    else:
        confidence = "low"

    evidence = [
        f"languages:{dict(language_counts)}",
        f"density:{comment_density}",
    ]
    if docstring_style != "inline-only":
        evidence.append(f"docstrings:{python_docstrings}")

    return {
        "primary_language": primary_language,
        "confidence": confidence,
        "comment_density": comment_density,
        "docstring_style": docstring_style,
        "evidence": evidence,
    }


def build_style_exemplars(file_findings: list[dict[str, object]], primary_language: str | None) -> list[dict[str, object]]:
    exemplars: list[dict[str, object]] = []
    for item in file_findings:
        if primary_language and item["language"] != primary_language:
            continue
        if item["exemplar_score"] <= 0:
            continue
        exemplars.append(
            {
                "path": item["path"],
                "language": item["language"],
                "score": item["exemplar_score"],
                "reason": "same-language exemplar with fewer suspicious comments",
            }
        )
    exemplars.sort(key=lambda item: (-int(item["score"]), item["path"]))
    return exemplars


def build_safe_edit_hints(selected_style: dict[str, object], summary: dict[str, object]) -> list[str]:
    hints = [
        "Sample the nearest same-language files before editing the target comments.",
        "Explain intent, edge cases, or hazards instead of narrating each line.",
    ]
    if summary["suspicious_comment_count"] > 0:
        hints.append("Rewrite generic template comments before adding any new comments.")
    if selected_style["comment_density"] == "sparse":
        hints.append("Keep edits minimal because the local area uses sparse comments.")
    return hints


def build_forbidden_actions(selected_style: dict[str, object]) -> list[str]:
    forbidden = [
        "Do not restate obvious syntax or trivial assignments in comments.",
        "Do not change executable code while performing comment-only cleanup.",
    ]
    if selected_style["comment_density"] == "sparse":
        forbidden.append("Do not backfill comments onto every function or statement in sparse-comment code.")
    return forbidden


def analyze_target(root: Path, target: Path, max_files: int = 200) -> dict[str, object]:
    files = iter_supported_files(target, max_files=max_files)
    file_findings = [analyze_file(path, root) for path in files]
    language_counts = Counter(item["language"] for item in file_findings)
    suspicious_comment_count = sum(len(item["suspicious_comments"]) for item in file_findings)
    total_docstrings = sum(int(item["docstring_blocks"]) for item in file_findings)

    selected_style = build_selected_style(file_findings)
    style_exemplars = build_style_exemplars(file_findings, selected_style["primary_language"])
    summary = {
        "file_count": len(file_findings),
        "languages": dict(language_counts),
        "comment_density": selected_style["comment_density"],
        "docstring_blocks": total_docstrings,
        "suspicious_comment_count": suspicious_comment_count,
    }

    return {
        "root": str(root),
        "target": str(target),
        "selected_style": selected_style,
        "summary": summary,
        "style_exemplars": style_exemplars,
        "file_findings": file_findings,
        "safe_edit_hints": build_safe_edit_hints(selected_style, summary),
        "forbidden_actions": build_forbidden_actions(selected_style),
    }


def render_text_report(payload: dict[str, object]) -> str:
    selected = payload["selected_style"]
    summary = payload["summary"]
    lines = [
        "## Request",
        f"Target: {payload['target']}",
        "",
        "## Selected Style",
        f"Primary language: {selected['primary_language'] or 'unknown'}",
        f"Confidence: {selected['confidence']}",
        f"Comment density: {selected['comment_density']}",
        f"Docstring style: {selected['docstring_style']}",
        "",
        "## Summary",
        f"Files audited: {summary['file_count']}",
        f"Languages: {summary['languages']}",
        f"Suspicious comments: {summary['suspicious_comment_count']}",
    ]

    exemplars = payload["style_exemplars"]
    if exemplars:
        lines.extend(["", "## Style Exemplars"])
        for item in exemplars:
            lines.append(f"- {item['path']} ({item['language']}, score={item['score']})")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    target = Path(args.target).resolve()
    if not root.exists():
        print(f"Root path does not exist: {root}", file=sys.stderr)
        return 1
    if not target.exists():
        print(f"Target path does not exist: {target}", file=sys.stderr)
        return 1

    payload = analyze_target(root=root, target=target, max_files=args.max_files)
    if args.as_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(render_text_report(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

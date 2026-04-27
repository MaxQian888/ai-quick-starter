#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path


SUPPORTED_EXTENSIONS = {
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
    ".py",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".cs",
}
SKIP_DIR_NAMES = {
    ".git",
    ".next",
    ".nuxt",
    ".turbo",
    ".uv-cache",
    ".uv-python",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "vendor",
}
LEVEL_ORDER = ("trace", "debug", "info", "warn", "error", "fatal")
FRAMEWORK_PATTERNS = {
    "console": (
        re.compile(r"\bconsole\.(?:debug|info|warn|error|log|trace)\s*\("),
    ),
    "pino": (
        re.compile(r"\bfrom\s+['\"]pino['\"]"),
        re.compile(r"\brequire\(\s*['\"]pino['\"]\s*\)"),
        re.compile(r"\bpino\s*\("),
    ),
    "winston": (
        re.compile(r"\bfrom\s+['\"]winston['\"]"),
        re.compile(r"\brequire\(\s*['\"]winston['\"]\s*\)"),
        re.compile(r"\bcreateLogger\s*\("),
        re.compile(r"\bwinston\."),
    ),
    "debug-js": (
        re.compile(r"\bfrom\s+['\"]debug['\"]"),
        re.compile(r"\brequire\(\s*['\"]debug['\"]\s*\)"),
    ),
    "custom-wrapper": (
        re.compile(r"from\s+['\"][^'\"]*logger[^'\"]*['\"]"),
        re.compile(r"import\s+.*\blogger\b.*from\s+['\"][^'\"]+['\"]"),
        re.compile(r"require\(\s*['\"][^'\"]*logger[^'\"]*['\"]\s*\)"),
    ),
    "python-logging": (
        re.compile(r"\bimport\s+logging\b"),
        re.compile(r"\bfrom\s+logging\s+import\b"),
        re.compile(r"\blogging\.getLogger\s*\("),
    ),
    "structlog": (
        re.compile(r"\bimport\s+structlog\b"),
        re.compile(r"\bfrom\s+structlog\s+import\b"),
        re.compile(r"\bstructlog\.get_logger\s*\("),
    ),
    "loguru": (
        re.compile(r"\bfrom\s+loguru\s+import\s+logger\b"),
        re.compile(r"\bimport\s+loguru\b"),
    ),
    "go-log": (
        re.compile(r"\blog\.(?:Print|Printf|Println|Fatal|Fatalf|Fatalln|Panic|Panicf|Panicln)\s*\("),
    ),
    "go-slog": (
        re.compile(r"\bslog\.(?:Debug|Info|Warn|Error)\s*\("),
        re.compile(r'"log/slog"'),
    ),
    "zap": (
        re.compile(r"\bzap\."),
        re.compile(r'"go\.uber\.org/zap"'),
    ),
    "zerolog": (
        re.compile(r"\bzerolog\b"),
        re.compile(r'"github\.com/rs/zerolog"'),
    ),
    "rust-tracing": (
        re.compile(r"\btracing::(?:trace|debug|info|warn|error)!\s*\("),
        re.compile(r"\buse\s+tracing::"),
    ),
    "rust-log": (
        re.compile(r"\b(?:trace|debug|info|warn|error)!\s*\("),
    ),
    "slf4j": (
        re.compile(r"\bLoggerFactory\.getLogger\s*\("),
        re.compile(r"\borg\.slf4j\."),
    ),
    "microsoft-extensions-logging": (
        re.compile(r"\bILogger<"),
        re.compile(r"\busing\s+Microsoft\.Extensions\.Logging\b"),
    ),
    "serilog": (
        re.compile(r"\bSerilog\b"),
        re.compile(r"\bLog\.(?:Debug|Information|Warning|Error|Fatal)\s*\("),
    ),
}
LEVEL_PATTERNS = {
    "trace": (
        re.compile(r"\bconsole\.trace\s*\("),
        re.compile(r"\b(?:logger|log|LOGGER|_logger)\.trace\s*\("),
        re.compile(r"\b(?:logger|log|LOGGER|_logger)\.Trace\s*\("),
        re.compile(r"\btrace!\s*\("),
        re.compile(r"\bLogTrace\s*\("),
    ),
    "debug": (
        re.compile(r"\bconsole\.debug\s*\("),
        re.compile(r"\b(?:logger|log|LOGGER|_logger)\.debug\s*\("),
        re.compile(r"\b(?:logger|log|LOGGER|_logger)\.Debug\s*\("),
        re.compile(r"\bslog\.Debug\s*\("),
        re.compile(r"\bdebug!\s*\("),
        re.compile(r"\bLogDebug\s*\("),
    ),
    "info": (
        re.compile(r"\bconsole\.info\s*\("),
        re.compile(r"\b(?:logger|log|LOGGER|_logger)\.info\s*\("),
        re.compile(r"\b(?:logger|log|LOGGER|_logger)\.Info\s*\("),
        re.compile(r"\bslog\.Info\s*\("),
        re.compile(r"\binfo!\s*\("),
        re.compile(r"\bLogInformation\s*\("),
        re.compile(r"\bLog\.Information\s*\("),
    ),
    "warn": (
        re.compile(r"\bconsole\.warn\s*\("),
        re.compile(r"\b(?:logger|log|LOGGER|_logger)\.warn\s*\("),
        re.compile(r"\b(?:logger|log|LOGGER|_logger)\.Warn\s*\("),
        re.compile(r"\b(?:logger|log|LOGGER|_logger)\.warning\s*\("),
        re.compile(r"\b(?:logger|log|LOGGER|_logger)\.Warning\s*\("),
        re.compile(r"\bslog\.Warn\s*\("),
        re.compile(r"\bwarn!\s*\("),
        re.compile(r"\bLogWarning\s*\("),
        re.compile(r"\bLog\.Warning\s*\("),
    ),
    "error": (
        re.compile(r"\bconsole\.error\s*\("),
        re.compile(r"\b(?:logger|log|LOGGER|_logger)\.error\s*\("),
        re.compile(r"\b(?:logger|log|LOGGER|_logger)\.Error\s*\("),
        re.compile(r"\b(?:logger|log|LOGGER|_logger)\.exception\s*\("),
        re.compile(r"\b(?:logger|log|LOGGER|_logger)\.Exception\s*\("),
        re.compile(r"\bslog\.Error\s*\("),
        re.compile(r"\berror!\s*\("),
        re.compile(r"\bLogError\s*\("),
        re.compile(r"\bLog\.Error\s*\("),
    ),
    "fatal": (
        re.compile(r"\b(?:logger|log|LOGGER|_logger)\.fatal\s*\("),
        re.compile(r"\b(?:logger|log|LOGGER|_logger)\.Fatal\s*\("),
        re.compile(r"\b(?:logger|log|LOGGER|_logger)\.critical\s*\("),
        re.compile(r"\b(?:logger|log|LOGGER|_logger)\.Critical\s*\("),
        re.compile(r"\bcritical!\s*\("),
        re.compile(r"\bfatal!\s*\("),
        re.compile(r"\bLogCritical\s*\("),
        re.compile(r"\bLog\.Fatal\s*\("),
    ),
}


@dataclass
class FileAudit:
    path: str
    status: str
    lines: int
    frameworks: list[str]
    dominant_framework: str | None
    level_counts: dict[str, int]
    call_count: int
    density_per_100_lines: float
    needs_review: list[str]
    notes: list[str]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit logging frameworks, levels, and density in a target directory.",
    )
    parser.add_argument("--root", default=".", help="Repository root or context root.")
    parser.add_argument("--target", required=True, help="Directory or file to audit.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args(argv)


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIR_NAMES for part in path.parts)


def iter_supported_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target] if target.suffix.lower() in SUPPORTED_EXTENSIONS else []

    files: list[Path] = []
    for path in target.rglob("*"):
        if not path.is_file():
            continue
        if should_skip(path.relative_to(target)):
            continue
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        files.append(path)
    return sorted(files)


def count_pattern_matches(text: str, patterns: tuple[re.Pattern[str], ...]) -> int:
    return sum(len(pattern.findall(text)) for pattern in patterns)


def detect_frameworks(text: str) -> Counter[str]:
    scores: Counter[str] = Counter()
    for name, patterns in FRAMEWORK_PATTERNS.items():
        count = count_pattern_matches(text, patterns)
        if count:
            scores[name] = count
    if "rust-tracing" in scores and "rust-log" in scores:
        scores["rust-log"] = max(0, scores["rust-log"] - scores["rust-tracing"])
        if scores["rust-log"] == 0:
            del scores["rust-log"]
    return scores


def count_levels(text: str) -> dict[str, int]:
    level_counts: dict[str, int] = {}
    for level in LEVEL_ORDER:
        level_counts[level] = count_pattern_matches(text, LEVEL_PATTERNS[level])
    return level_counts


def dominant_name(counter: Counter[str]) -> str | None:
    if not counter:
        return None
    return counter.most_common(1)[0][0]


def compute_review_flags(
    frameworks: list[str],
    level_counts: dict[str, int],
    call_count: int,
    density_per_100_lines: float,
) -> list[str]:
    flags: list[str] = []
    if len(frameworks) > 1:
        flags.append("mixed-frameworks")
    if call_count == 0:
        flags.append("no-log-calls")
    if call_count >= 8 and density_per_100_lines >= 8:
        flags.append("high-density")
    if call_count >= 6 and level_counts["info"] / max(call_count, 1) >= 0.65:
        flags.append("info-heavy")
    if call_count >= 6 and level_counts["debug"] / max(call_count, 1) >= 0.5:
        flags.append("debug-heavy")
    if call_count > 0 and not frameworks:
        flags.append("unclassified-logging")
    return flags


def classify_file_status(
    frameworks: list[str],
    call_count: int,
    needs_review: list[str],
) -> str:
    if call_count == 0:
        return "no-logs"
    if "mixed-frameworks" in needs_review:
        return "mixed-patterns"
    if "high-density" in needs_review:
        return "needs-density-review"
    if frameworks:
        return "aligned"
    return "needs-manual-read"


def build_file_notes(status: str, needs_review: list[str]) -> list[str]:
    notes: list[str] = []
    if status == "no-logs":
        notes.append("No recognizable logging calls were found in this file.")
    if status == "mixed-patterns":
        notes.append("More than one logging framework or wrapper appears in this file.")
    if status == "needs-density-review":
        notes.append("This file already has dense logging and should be trimmed before adding more.")
    if "unclassified-logging" in needs_review:
        notes.append("Logging calls exist but the framework was not confidently classified.")
    return notes


def analyze_file(path: Path, root: Path) -> FileAudit:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = len(text.splitlines()) or 1
    frameworks = detect_frameworks(text)
    level_counts = count_levels(text)
    call_count = sum(level_counts.values())
    density_per_100_lines = round((call_count / lines) * 100, 2)
    framework_names = sorted(frameworks.keys())
    needs_review = compute_review_flags(
        frameworks=framework_names,
        level_counts=level_counts,
        call_count=call_count,
        density_per_100_lines=density_per_100_lines,
    )
    status = classify_file_status(
        frameworks=framework_names,
        call_count=call_count,
        needs_review=needs_review,
    )
    return FileAudit(
        path=str(path.relative_to(root)),
        status=status,
        lines=lines,
        frameworks=framework_names,
        dominant_framework=dominant_name(frameworks),
        level_counts=level_counts,
        call_count=call_count,
        density_per_100_lines=density_per_100_lines,
        needs_review=needs_review,
        notes=build_file_notes(status=status, needs_review=needs_review),
    )


def summarize_detected_systems(file_audits: list[FileAudit]) -> list[dict[str, object]]:
    score_totals: Counter[str] = Counter()
    file_totals: Counter[str] = Counter()
    for audit in file_audits:
        for framework in audit.frameworks:
            score_totals[framework] += 1
        if audit.dominant_framework:
            file_totals[audit.dominant_framework] += 1

    detected: list[dict[str, object]] = []
    for name, score in score_totals.most_common():
        examples = [audit.path for audit in file_audits if name in audit.frameworks][:3]
        detected.append(
            {
                "name": name,
                "score": score,
                "file_count": file_totals.get(name, 0),
                "evidence": examples,
            }
        )
    return detected


def compute_confidence(
    dominant_framework: str | None,
    detected_systems: list[dict[str, object]],
) -> str:
    if not dominant_framework or not detected_systems:
        return "low"

    total_score = sum(item["score"] for item in detected_systems)
    top_score = detected_systems[0]["score"]
    dominance_ratio = top_score / max(total_score, 1)
    top_file_count = detected_systems[0]["file_count"]

    if dominance_ratio >= 0.7 and top_file_count >= 2:
        return "high"
    if dominance_ratio >= 0.5 and top_file_count >= 1:
        return "medium"
    return "low"


def build_selected_system(
    dominant_framework: str | None,
    detected_systems: list[dict[str, object]],
) -> dict[str, object]:
    confidence = compute_confidence(dominant_framework, detected_systems)
    if not dominant_framework:
        return {
            "name": None,
            "score": 0,
            "confidence": confidence,
            "notes": [
                "No logging framework was confidently detected in the target scope.",
            ],
            "evidence": [],
        }

    top = detected_systems[0]
    notes = [f"Preserve {dominant_framework} in this target unless adjacent files prove otherwise."]
    if confidence == "low":
        notes.append("Inspect shared logger entrypoints before editing because the local signal is weak.")
    return {
        "name": dominant_framework,
        "score": top["score"],
        "confidence": confidence,
        "notes": notes,
        "evidence": top["evidence"],
    }


def build_safe_fix_plan(
    file_audits: list[FileAudit],
    dominant_framework: str | None,
    confidence: str,
) -> list[dict[str, str]]:
    plan: list[dict[str, str]] = []
    for audit in file_audits:
        if audit.status == "aligned" and dominant_framework and audit.dominant_framework == dominant_framework:
            plan.append(
                {
                    "path": audit.path,
                    "operation": "edit-existing-logs",
                    "confidence": confidence,
                    "rationale": f"This file already uses the dominant local framework '{dominant_framework}'.",
                }
            )
            continue
        if audit.status == "no-logs" and dominant_framework and confidence == "high":
            plan.append(
                {
                    "path": audit.path,
                    "operation": "add-minimal-logs-with-dominant-pattern",
                    "confidence": "medium",
                    "rationale": f"No logs were detected here, but neighboring files strongly suggest using '{dominant_framework}'.",
                }
            )
    return plan


def build_forbidden_actions(
    file_audits: list[FileAudit],
    dominant_framework: str | None,
    confidence: str,
) -> list[str]:
    actions = [
        "Do not introduce a new logging framework or wrapper in the target directory.",
        "Do not log secrets, tokens, cookies, passwords, or full personal data payloads.",
    ]
    if not dominant_framework or confidence == "low":
        actions.append("Do not add new logs until the shared logger entrypoint or adjacent files are inspected manually.")
    if any(audit.status == "mixed-patterns" for audit in file_audits):
        actions.append("Do not normalize every mixed file at once; fix one local pattern cluster at a time.")
    if any("high-density" in audit.needs_review for audit in file_audits):
        actions.append("Do not add more info/debug logs to high-density files before removing duplicates.")
    return actions


def build_blind_spots(
    file_audits: list[FileAudit],
    confidence: str,
) -> list[str]:
    blind_spots = [
        "Static scanning cannot prove runtime hot paths, log sampling, or wrapper configuration.",
    ]
    if not file_audits:
        blind_spots.append("No supported source files were found in the target path.")
    if confidence == "low":
        blind_spots.append("Framework confidence is low, so the audit may be missing a shared logger abstraction outside the target.")
    if any(audit.status == "no-logs" for audit in file_audits):
        blind_spots.append("Files with no logs may still inherit logging behavior indirectly through shared utilities.")
    if any(audit.status == "needs-manual-read" for audit in file_audits):
        blind_spots.append("Some logging calls were not classified and need manual review before editing.")
    return blind_spots


def build_suggested_next_reads(
    file_audits: list[FileAudit],
    dominant_framework: str | None,
) -> list[str]:
    preferred = [
        audit.path
        for audit in file_audits
        if audit.dominant_framework == dominant_framework and audit.status == "aligned"
    ]
    fallback = [audit.path for audit in file_audits if audit.status != "no-logs"]
    picks = preferred or fallback
    return picks[:3]


def build_recommendations(
    selected_system: dict[str, object],
    file_audits: list[FileAudit],
) -> list[str]:
    recommendations: list[str] = []
    if selected_system["name"]:
        recommendations.append(
            f"Preserve '{selected_system['name']}' as the default logging pattern for this target unless adjacent files prove otherwise."
        )
    if any(audit.status == "mixed-patterns" for audit in file_audits):
        recommendations.append(
            "The target mixes multiple logging frameworks or wrappers; converge toward the dominant local pattern instead of introducing another one."
        )
    noisy_files = [audit.path for audit in file_audits if "high-density" in audit.needs_review]
    if noisy_files:
        recommendations.append(
            f"Review high-density files before adding new logs: {', '.join(noisy_files[:3])}."
        )
    if any("info-heavy" in audit.needs_review for audit in file_audits):
        recommendations.append(
            "Prefer collapsing repeated info logs into fewer lifecycle summaries where the same identifier and outcome repeat."
        )
    if not file_audits:
        recommendations.append(
            "No supported source files were found in the target path. Confirm the directory or expand the audit scope before editing logs."
        )
    return recommendations


def analyze_target(root: Path, target: Path) -> dict[str, object]:
    files = iter_supported_files(target)
    file_audits = [analyze_file(path, root) for path in files]
    level_totals: Counter[str] = Counter()
    for audit in file_audits:
        level_totals.update(audit.level_counts)

    detected_systems = summarize_detected_systems(file_audits)
    dominant_framework = detected_systems[0]["name"] if detected_systems else None
    selected_system = build_selected_system(dominant_framework, detected_systems)
    confidence = selected_system["confidence"]

    payload = {
        "root": str(root),
        "target": str(target),
        "selected_system": selected_system,
        "detected_systems": detected_systems,
        "summary": {
            "file_count": len(file_audits),
            "status_counts": dict(Counter(audit.status for audit in file_audits)),
            "level_totals": {level: level_totals.get(level, 0) for level in LEVEL_ORDER},
        },
        "file_findings": [asdict(audit) for audit in file_audits],
        "files": [asdict(audit) for audit in file_audits],
        "safe_fix_plan": build_safe_fix_plan(
            file_audits=file_audits,
            dominant_framework=dominant_framework,
            confidence=confidence,
        ),
        "forbidden_actions": build_forbidden_actions(
            file_audits=file_audits,
            dominant_framework=dominant_framework,
            confidence=confidence,
        ),
        "blind_spots": build_blind_spots(
            file_audits=file_audits,
            confidence=confidence,
        ),
        "suggested_next_reads": build_suggested_next_reads(
            file_audits=file_audits,
            dominant_framework=dominant_framework,
        ),
        "recommendations": build_recommendations(
            selected_system=selected_system,
            file_audits=file_audits,
        ),
    }
    return payload


def render_text_report(payload: dict[str, object]) -> str:
    selected = payload["selected_system"]
    summary = payload["summary"]
    file_findings = payload["file_findings"]
    lines = [
        "## Request",
        f"Target: {payload['target']}",
        "",
        "## Detected Logging System",
        f"Name: {selected['name'] or 'unknown'}",
        f"Confidence: {selected['confidence']}",
        f"Evidence: {selected['evidence']}",
        "",
        "## File Findings",
        f"Files audited: {summary['file_count']}",
        f"Status counts: {summary['status_counts']}",
        f"Level totals: {summary['level_totals']}",
    ]
    for file_payload in file_findings[:10]:
        flags = ", ".join(file_payload["needs_review"]) if file_payload["needs_review"] else "ok"
        lines.append(
            f"- {file_payload['path']}: status={file_payload['status']}, "
            f"framework={file_payload['dominant_framework'] or 'unknown'}, "
            f"calls={file_payload['call_count']}, density={file_payload['density_per_100_lines']}, review={flags}"
        )
    lines.extend(["", "## Safe Fix Plan"])
    if payload["safe_fix_plan"]:
        for step in payload["safe_fix_plan"]:
            lines.append(
                f"- {step['path']}: {step['operation']} ({step['confidence']}) - {step['rationale']}"
            )
    else:
        lines.append("- No file is safe to edit automatically from the static audit alone.")
    lines.extend(["", "## Forbidden Actions"])
    for item in payload["forbidden_actions"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Blind Spots"])
    for item in payload["blind_spots"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Suggested Next Reads"])
    for path in payload["suggested_next_reads"]:
        lines.append(f"- {path}")
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

    payload = analyze_target(root=root, target=target)
    if args.as_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(render_text_report(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Audit one skill folder for safety and security risks."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from collections import Counter
from pathlib import Path


IGNORED_DIR_NAMES = {
    ".git",
    ".hg",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".svn",
    ".tmp-tests",
    ".tox",
    ".venv",
    "__pycache__",
    "artifacts",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "out",
    "target",
    "tmp",
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
    ".min.css",
    ".min.js",
    ".pdf",
    ".png",
    ".pyc",
    ".pyo",
    ".so",
    ".svg",
    ".webp",
    ".zip",
}
TEXT_EXTENSIONS = {
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1}
SEVERITY_WEIGHTS = {"critical": 40, "high": 25, "medium": 15, "low": 8}
BLIND_SPOTS = [
    "Static scanning cannot prove whether helper scripts become dangerous only after environment-variable expansion or runtime input interpolation.",
    "The audit does not execute untrusted helper scripts, so behavior hidden behind control flow or downloaded payloads may remain undiscovered.",
    "A clean result only means no supported static rule fired in this pass; it does not prove the skill is safe for production or unattended execution.",
]

SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"(?P<name>(?:[A-Z0-9_]*?(?:API[_-]?KEY|TOKEN|SECRET|PASSWORD|PASSWD|ACCESS[_-]?KEY)[A-Z0-9_]*|(?:api[_-]?key|token|secret|password|passwd|access[_-]?key)))\s*[:=]\s*[\"'](?P<value>[^\"'\n]{6,})[\"']",
    re.IGNORECASE,
)
SECRET_INLINE_PATTERNS = (
    re.compile(r"\bsk-(?:live|proj|svc|test)-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
)
DANGEROUS_COMMAND_PATTERNS = (
    re.compile(r"\brm\s+-rf\s+/"),
    re.compile(r"\bRemove-Item\b[^\n]*(?:-Recurse[^\n]*-Force|-Force[^\n]*-Recurse)", re.IGNORECASE),
    re.compile(r"\bdel\b[^\n]*/f[^\n]*/s[^\n]*/q", re.IGNORECASE),
    re.compile(r"\bgit\s+reset\s+--hard\b"),
    re.compile(r"\bgit\s+checkout\s+--\b"),
    re.compile(r"\bcurl\b[^\n|]+\|\s*(?:bash|sh)\b", re.IGNORECASE),
    re.compile(r"\bInvoke-Expression\b", re.IGNORECASE),
    re.compile(r"\biex\b", re.IGNORECASE),
)
NETWORK_OR_PRODUCTION_PATTERNS = (
    re.compile(r"\bkubectl\s+apply\b"),
    re.compile(r"\bterraform\s+apply\b"),
    re.compile(r"\bgit\s+push\b"),
    re.compile(r"\baws\s+s3\s+rm\b"),
    re.compile(r"\bssh\s+[^\s]+\b"),
    re.compile(r"\bscp\s+[^\s]+\b"),
)
WRITE_VERB_PATTERN = re.compile(r"\b(write|save|copy|move|create|export)\b", re.IGNORECASE)
ABSOLUTE_PATH_PATTERN = re.compile(
    r"(?P<path>(?:[A-Za-z]:[\\/][^\s`\"']+)|(?:~[\\/][^\s`\"']+)|(?:/(?:etc|home|root|usr|var)/[^\s`\"']+))"
)
NODE_TEST_PATTERNS = ("*.test.mjs", "test_*.mjs")
PESTER_TEST_PATTERN = "*.Tests.ps1"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit one skill folder for safety risks.")
    parser.add_argument("--skill-path", required=True, help="Path to the target skill directory.")
    parser.add_argument("--json-out", default="", help="Optional explicit JSON output path.")
    parser.add_argument("--markdown-out", default="", help="Optional explicit Markdown output path.")
    parser.add_argument("--max-files", type=int, default=250, help="Cap matching files scanned.")
    return parser.parse_args(argv)


def resolve_output_path(raw_path: str, suffix: str) -> Path:
    if raw_path:
        output_path = Path(raw_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path

    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="skill-safety-audit-")
    handle.close()
    return Path(handle.name).resolve()


def safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def should_skip_file(path: Path) -> bool:
    suffixes = path.suffixes
    if suffixes:
        compound = "".join(suffixes[-2:]) if len(suffixes) >= 2 else suffixes[-1]
        if compound in IGNORED_FILE_SUFFIXES or path.suffix.lower() in IGNORED_FILE_SUFFIXES:
            return True
    if path.name == "SKILL.md":
        return False
    if path.name == "openai.yaml":
        return False
    return path.suffix.lower() not in TEXT_EXTENSIONS


def walk_files(skill_path: Path, max_files: int) -> tuple[list[Path], list[dict[str, str]]]:
    matches: list[Path] = []
    limits: list[dict[str, str]] = []

    for current_root, dir_names, file_names in os.walk(skill_path):
        dir_names[:] = [name for name in sorted(dir_names) if name not in IGNORED_DIR_NAMES and not name.startswith("_tmp")]
        for file_name in sorted(file_names):
            file_path = Path(current_root) / file_name
            if should_skip_file(file_path):
                continue
            matches.append(file_path)
            if len(matches) >= max_files:
                limits.append({"kind": "max-files", "detail": f"Stopped after scanning {max_files} text files."})
                return matches, limits
    return matches, limits


def split_frontmatter(content: str) -> tuple[str, str]:
    match = re.match(r"^---\n(.*?)\n---\n?(.*)$", content, re.DOTALL)
    if not match:
        return "", content
    return match.group(1), match.group(2)


def parse_frontmatter(frontmatter_text: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for line in frontmatter_text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        parsed[key.strip()] = value.strip().strip("\"'")
    return parsed


def is_placeholder_secret(value: str) -> bool:
    lowered = value.strip().lower()
    return (
        lowered.startswith("<") and lowered.endswith(">")
        or "your_" in lowered
        or "your-" in lowered
        or "your " in lowered
        or "example" in lowered
        or "changeme" in lowered
        or lowered in {"replace-me", "replace_me", "test", "fake", "dummy", "sample"}
    )


def redact_secret(value: str) -> str:
    if len(value) <= 8:
        return value[:2] + "***"
    return f"{value[:6]}...{value[-4:]}"


def make_finding(
    *,
    category: str,
    severity: str,
    path: str,
    evidence: str,
    rationale: str,
    suggested_fix: str,
) -> dict[str, str]:
    return {
        "category": category,
        "severity": severity,
        "path": path,
        "evidence": evidence,
        "rationale": rationale,
        "suggested_fix": suggested_fix,
    }


def detect_hardcoded_secrets(relative_path: str, text: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for match in SECRET_ASSIGNMENT_PATTERN.finditer(text):
        value = match.group("value").strip()
        if is_placeholder_secret(value):
            continue
        findings.append(
            make_finding(
                category="hardcoded-secret",
                severity="high",
                path=relative_path,
                evidence=f"{match.group('name')}={redact_secret(value)}",
                rationale="The skill appears to embed a credential-like value instead of using a placeholder or environment-only guidance.",
                suggested_fix="Replace the real value with a placeholder and instruct the user to supply it through environment variables or secrets management.",
            )
        )
    for pattern in SECRET_INLINE_PATTERNS:
        for match in pattern.finditer(text):
            token = match.group(0)
            findings.append(
                make_finding(
                    category="hardcoded-secret",
                    severity="high",
                    path=relative_path,
                    evidence=redact_secret(token),
                    rationale="The skill contains a token-like literal that looks reusable outside a local fixture.",
                    suggested_fix="Remove the real token and replace it with a clearly fake placeholder value.",
                )
            )
    return dedupe_findings(findings)


def detect_dangerous_commands(relative_path: str, text: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for pattern in DANGEROUS_COMMAND_PATTERNS:
        for match in pattern.finditer(text):
            findings.append(
                make_finding(
                    category="dangerous-command",
                    severity="high",
                    path=relative_path,
                    evidence=match.group(0).strip(),
                    rationale="The skill contains a destructive or shell-eval pattern that should not be recommended without an explicit guarded workflow.",
                    suggested_fix="Replace the direct command with a preview-first guarded workflow, or document stricter confirmation and path-validation steps.",
                )
            )
    return dedupe_findings(findings)


def detect_network_or_production_actions(relative_path: str, text: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for pattern in NETWORK_OR_PRODUCTION_PATTERNS:
        for match in pattern.finditer(text):
            findings.append(
                make_finding(
                    category="unguarded-network-or-production-action",
                    severity="medium",
                    path=relative_path,
                    evidence=match.group(0).strip(),
                    rationale="The skill appears to recommend a network or production-facing action without a visible dry-run, confirmation, or environment guard.",
                    suggested_fix="Add explicit scope checks, dry-run guidance, and confirmation rules before production or network actions.",
                )
            )
    return dedupe_findings(findings)


def path_is_within_root(candidate: Path, root: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def normalize_candidate_path(raw_path: str) -> Path | None:
    cleaned = raw_path.strip().strip("`\"'")
    if cleaned.startswith("~/") or cleaned.startswith("~\\"):
        return Path.home() / cleaned[2:]
    if re.match(r"^[A-Za-z]:[\\/]", cleaned):
        return Path(cleaned.replace("/", "\\"))
    if cleaned.startswith("/"):
        return Path(cleaned)
    return None


def detect_outside_workspace_writes(relative_path: str, text: str, skill_path: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    workspace_root = skill_path.parent.resolve()
    for raw_line in text.splitlines():
        if not WRITE_VERB_PATTERN.search(raw_line):
            continue
        for match in ABSOLUTE_PATH_PATTERN.finditer(raw_line):
            candidate = normalize_candidate_path(match.group("path"))
            if candidate is None or path_is_within_root(candidate, workspace_root):
                continue
            findings.append(
                make_finding(
                    category="outside-workspace-write",
                    severity="high",
                    path=relative_path,
                    evidence=str(match.group("path")),
                    rationale="The skill instructs writes to an absolute path outside the current workspace boundary.",
                    suggested_fix="Constrain writes to a repository-relative path or require an explicit human-confirmed destination outside the workspace.",
                )
            )
    return dedupe_findings(findings)


def detect_trigger_risk(skill_path: Path) -> list[dict[str, str]]:
    skill_md_path = skill_path / "SKILL.md"
    if not skill_md_path.exists():
        return []
    frontmatter_text, _ = split_frontmatter(safe_read_text(skill_md_path))
    frontmatter = parse_frontmatter(frontmatter_text)
    description = frontmatter.get("description", "").strip()
    if not description:
        return []

    generic_markers = (
        "any code",
        "any repository",
        "any task",
        "all coding",
        "anything",
        "everything",
        "general purpose",
    )
    if any(marker in description.lower() for marker in generic_markers):
        return [
            make_finding(
                category="trigger-too-broad",
                severity="medium",
                path="SKILL.md",
                evidence=description,
                rationale="The trigger wording is broad enough that the skill could activate outside its intended risk boundary.",
                suggested_fix="Narrow the description to one concrete task shape, artifact type, or risk context.",
            )
        ]
    return []


def count_script_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for item in path.rglob("*") if item.is_file() and item.name != "README.md")


def has_supported_runtime_verification(tests_dir: Path) -> bool:
    if not tests_dir.exists():
        return False
    if (tests_dir / "runtime-verification.json").exists():
        return True
    if list(tests_dir.rglob("test_*.py")):
        return True
    for pattern in NODE_TEST_PATTERNS:
        if list(tests_dir.rglob(pattern)):
            return True
    if list(tests_dir.rglob(PESTER_TEST_PATTERN)):
        return True
    return False


def detect_missing_runtime_verification(skill_path: Path) -> list[dict[str, str]]:
    scripts_dir = skill_path / "scripts"
    if count_script_files(scripts_dir) == 0:
        return []
    tests_dir = skill_path / "tests"
    if has_supported_runtime_verification(tests_dir):
        return []
    return [
        make_finding(
            category="missing-runtime-verification",
            severity="medium",
            path="scripts/",
            evidence="script-backed skill has no supported tests or runtime-verification.json contract",
            rationale="A script-backed skill without a runnable verification surface is harder to trust and easier to ship with hidden unsafe behavior.",
            suggested_fix="Add `tests/` coverage or an explicit `tests/runtime-verification.json` command for the helper scripts.",
        )
    ]


def dedupe_findings(findings: list[dict[str, str]]) -> list[dict[str, str]]:
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for finding in findings:
        key = (finding["category"], finding["path"], finding["evidence"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(finding)
    return sorted(deduped, key=lambda item: (-SEVERITY_ORDER[item["severity"]], item["path"], item["category"], item["evidence"]))


def scan_files(skill_path: Path, files: list[Path]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for file_path in files:
        relative_path = file_path.relative_to(skill_path).as_posix()
        text = safe_read_text(file_path)
        findings.extend(detect_hardcoded_secrets(relative_path, text))
        findings.extend(detect_dangerous_commands(relative_path, text))
        findings.extend(detect_network_or_production_actions(relative_path, text))
        findings.extend(detect_outside_workspace_writes(relative_path, text, skill_path))
    findings.extend(detect_trigger_risk(skill_path))
    findings.extend(detect_missing_runtime_verification(skill_path))
    return dedupe_findings(findings)


def build_safe_fix_plan(findings: list[dict[str, str]]) -> list[dict[str, str]]:
    operations = {
        "hardcoded-secret": "replace-real-secret-with-placeholder",
        "dangerous-command": "replace-dangerous-command-with-guarded-workflow",
        "outside-workspace-write": "constrain-writes-to-workspace",
        "unguarded-network-or-production-action": "add-dry-run-and-confirmation-guards",
        "trigger-too-broad": "narrow-trigger-description",
        "missing-runtime-verification": "add-runtime-verification",
    }
    steps: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for finding in findings:
        operation = operations.get(finding["category"])
        if not operation:
            continue
        key = (finding["path"], operation)
        if key in seen:
            continue
        seen.add(key)
        steps.append(
            {
                "path": finding["path"],
                "operation": operation,
                "severity": finding["severity"],
                "rationale": finding["suggested_fix"],
            }
        )
    return steps


def build_blocked_actions(findings: list[dict[str, str]]) -> list[str]:
    categories = {finding["category"] for finding in findings}
    blocked: list[str] = []
    if "dangerous-command" in categories:
        blocked.append("Do not execute the skill's destructive or shell-eval commands until they are replaced with preview-first guarded steps.")
    if "hardcoded-secret" in categories:
        blocked.append("Do not publish, share, or reuse the skill while credential-like values remain embedded in its files.")
    if "outside-workspace-write" in categories:
        blocked.append("Do not follow the skill's absolute write instructions outside the current workspace until the destination is narrowed or confirmed by a human.")
    if "unguarded-network-or-production-action" in categories:
        blocked.append("Do not run production or network-facing commands from the skill without explicit dry-run and confirmation guardrails.")
    if "trigger-too-broad" in categories:
        blocked.append("Do not install the skill for automatic discovery until the trigger description is narrowed to the intended scope.")
    return blocked


def compute_risk_score(findings: list[dict[str, str]]) -> int:
    return min(100, sum(SEVERITY_WEIGHTS[finding["severity"]] for finding in findings))


def determine_status(findings: list[dict[str, str]]) -> str:
    if not findings:
        return "clean"
    if any(finding["severity"] in {"critical", "high"} for finding in findings):
        return "high-risk"
    return "review-needed"


def build_summary(findings: list[dict[str, str]], files: list[Path]) -> dict[str, object]:
    severity_counts = Counter(finding["severity"] for finding in findings)
    category_counts = Counter(finding["category"] for finding in findings)
    return {
        "scanned_file_count": len(files),
        "finding_count": len(findings),
        "severity_counts": dict(sorted(severity_counts.items())),
        "category_counts": dict(sorted(category_counts.items())),
    }


def build_report(skill_path: Path, files: list[Path], findings: list[dict[str, str]], limits: list[dict[str, str]]) -> dict[str, object]:
    skill_name = skill_path.name
    risk_score = compute_risk_score(findings)
    return {
        "skill_name": skill_name,
        "skill_path": str(skill_path),
        "overall_status": determine_status(findings),
        "risk_score": risk_score,
        "summary": build_summary(findings, files),
        "findings": findings,
        "safe_fix_plan": build_safe_fix_plan(findings),
        "blocked_actions": build_blocked_actions(findings),
        "blind_spots": BLIND_SPOTS,
        "limits": limits,
    }


def render_markdown(report: dict[str, object]) -> str:
    lines: list[str] = []
    lines.append("# Skill Safety Audit")
    lines.append("")
    lines.append("## Request")
    lines.append(f"- skill_path: `{report['skill_path']}`")
    lines.append("")
    lines.append("## Overall Status")
    lines.append(f"- status: `{report['overall_status']}`")
    lines.append(f"- risk_score: `{report['risk_score']}`")
    lines.append(f"- scanned_files: `{report['summary']['scanned_file_count']}`")
    lines.append(f"- findings: `{report['summary']['finding_count']}`")
    lines.append("")
    lines.append("## Findings")
    if report["findings"]:
        for finding in report["findings"]:
            lines.append(f"- `{finding['path']}` -> `{finding['category']}` / `{finding['severity']}`")
            lines.append(f"  evidence: `{finding['evidence']}`")
            lines.append(f"  rationale: {finding['rationale']}")
    else:
        lines.append("- No supported risk patterns were detected in this pass.")
    lines.append("")
    lines.append("## Safe Fix Plan")
    if report["safe_fix_plan"]:
        for step in report["safe_fix_plan"]:
            lines.append(f"- `{step['path']}` -> `{step['operation']}` ({step['severity']})")
            lines.append(f"  rationale: {step['rationale']}")
    else:
        lines.append("- No immediate fix plan is required from this audit pass.")
    lines.append("")
    lines.append("## Blocked Actions")
    if report["blocked_actions"]:
        for action in report["blocked_actions"]:
            lines.append(f"- {action}")
    else:
        lines.append("- None.")
    lines.append("")
    lines.append("## Blind Spots")
    for item in report["blind_spots"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    skill_path = Path(args.skill_path).resolve()
    if not skill_path.exists() or not skill_path.is_dir():
        print(f"[ERROR] skill path is not a directory: {skill_path}")
        return 1
    if not (skill_path / "SKILL.md").exists():
        print(f"[ERROR] SKILL.md not found under: {skill_path}")
        return 1

    files, limits = walk_files(skill_path, max(1, args.max_files))
    findings = scan_files(skill_path, files)
    report = build_report(skill_path, files, findings, limits)

    markdown_out = resolve_output_path(args.markdown_out, ".md")
    json_out = resolve_output_path(args.json_out, ".json")
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    json_out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"MARKDOWN_OUT={markdown_out}")
    print(f"JSON_OUT={json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

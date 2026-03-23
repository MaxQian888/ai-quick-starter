from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath


MARKER = "# Added by gitignore-curator"
RECENT_COMMIT_LIMIT = 10

GENERATED_DIR_RULES = {
    "node_modules": ("node_modules/", "Node dependency directories are generated locally."),
    ".next": (".next/", "Next.js build output is generated."),
    ".nuxt": (".nuxt/", "Nuxt build output is generated."),
    ".svelte-kit": (".svelte-kit/", "SvelteKit build output is generated."),
    ".venv": (".venv/", "Python virtual environments are local-only."),
    "venv": ("venv/", "Python virtual environments are local-only."),
    "__pycache__": ("__pycache__/", "Python bytecode caches are generated."),
    ".pytest_cache": (".pytest_cache/", "pytest caches are generated."),
    ".mypy_cache": (".mypy_cache/", "mypy caches are generated."),
    ".ruff_cache": (".ruff_cache/", "ruff caches are generated."),
    ".tox": (".tox/", "tox environments are generated."),
    ".nox": (".nox/", "nox environments are generated."),
    ".terraform": (".terraform/", "Terraform working directories are generated."),
    ".gradle": (".gradle/", "Gradle caches are generated."),
    "target": ("target/", "Build output is generated."),
    "coverage": ("coverage/", "Coverage reports are generated."),
    "dist": ("dist/", "Build output is generated."),
    "build": ("build/", "Build output is generated."),
    "htmlcov": ("htmlcov/", "Coverage reports are generated."),
}
EDITOR_LOCAL_DIR_RULES = {
    ".idea": (".idea/", "JetBrains project metadata is local-only."),
    ".vs": (".vs/", "Visual Studio metadata is local-only."),
}
ROOT_SIGNAL_RULES = {
    "package.json": [("node_modules/", "Node dependency directories are generated locally.")],
    "Cargo.toml": [("target/", "Rust build output is generated.")],
    "Dockerfile": [(".git/", "Git metadata is not needed in Docker build contexts.", ".dockerignore")],
}
LOCAL_ENV_NAMES = {".env", ".env.local"}
SAFE_LOCAL_ENV_SUFFIX = ".local"
SECONDARY_SHARED_TARGETS = (".dockerignore", ".eslintignore", ".prettierignore", ".ignore")
SECONDARY_SHARED_PATTERNS = {
    "node_modules/",
    ".next/",
    ".nuxt/",
    ".svelte-kit/",
    ".venv/",
    "venv/",
    "__pycache__/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    ".tox/",
    ".nox/",
    ".terraform/",
    ".gradle/",
    "target/",
    "coverage/",
    "dist/",
    "build/",
    "htmlcov/",
}
INSPECTED_IGNORE_FILES = (
    ".gitignore",
    ".git/info/exclude",
    ".dockerignore",
    ".npmignore",
    ".eslintignore",
    ".prettierignore",
    ".ignore",
)


@dataclass(frozen=True)
class CandidateRule:
    pattern: str
    target_file: str
    reason: str
    confidence: str
    evidence: list[str]


@dataclass(frozen=True)
class SkippedRule:
    pattern: str
    reasons: list[str]


@dataclass(frozen=True)
class AppliedRule:
    pattern: str
    target_file: str


@dataclass(frozen=True)
class StatusEntry:
    code: str
    path: str


@dataclass
class RepoSignals:
    detected_stacks: list[str]
    observed_dirs: set[str]
    observed_files: set[str]
    existing_patterns_by_file: dict[str, set[str]]
    inspected_ignore_files: list[str]
    status_entries: list[StatusEntry]
    recent_commit_paths: list[str]
    tracked_paths: set[str]
    optional_targets: set[str]
    docker_context: bool


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect a git repo and suggest safe ignore-file rules."
    )
    parser.add_argument("--project-root", default=".", help="Path inside the target repository.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Append missing suggested rules to the recommended ignore files.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    return parser.parse_args(argv)


def run_git_command(repo_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_path), *args],
        capture_output=True,
        text=True,
    )


def normalize_git_path(path: str) -> str:
    return path.strip().replace("\\", "/")


def find_repo_root(start: Path) -> Path | None:
    probe = start if start.is_dir() else start.parent
    result = run_git_command(probe, "rev-parse", "--show-toplevel")
    if result.returncode == 0:
        return Path(result.stdout.strip()).resolve()
    for candidate in [probe, *probe.parents]:
        if (candidate / ".git").exists():
            return candidate.resolve()
    return None


def detect_stacks(repo_root: Path) -> list[str]:
    stacks: set[str] = set()
    if any(
        (repo_root / name).exists()
        for name in ("package.json", "pnpm-lock.yaml", "package-lock.json", "yarn.lock")
    ):
        stacks.add("node")
    if any(
        (repo_root / name).exists()
        for name in ("pyproject.toml", "requirements.txt", "setup.py", "setup.cfg")
    ):
        stacks.add("python")
    if (repo_root / "Cargo.toml").exists():
        stacks.add("rust")
    if (repo_root / "go.mod").exists():
        stacks.add("go")
    if any((repo_root / name).exists() for name in ("pom.xml", "build.gradle", "build.gradle.kts")):
        stacks.add("java")
    if list(repo_root.glob("*.csproj")) or list(repo_root.glob("*.sln")):
        stacks.add("dotnet")
    if list(repo_root.glob("*.tf")) or (repo_root / ".terraform").exists():
        stacks.add("terraform")
    if (repo_root / "Dockerfile").exists() or (repo_root / ".dockerignore").exists():
        stacks.add("docker")
    return sorted(stacks)


def walk_repo(repo_root: Path) -> tuple[set[str], set[str]]:
    observed_dirs: set[str] = set()
    observed_files: set[str] = set()
    prune_dirs = {
        ".git",
        "node_modules",
        ".next",
        ".nuxt",
        ".svelte-kit",
        ".venv",
        "venv",
        "target",
        "dist",
        "build",
        "coverage",
        "htmlcov",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        ".nox",
    }
    for _, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [name for name in dirnames if name != ".git"]
        for dirname in list(dirnames):
            observed_dirs.add(dirname)
        for filename in filenames:
            observed_files.add(filename)
        dirnames[:] = [name for name in dirnames if name not in prune_dirs]
    return observed_dirs, observed_files


def parse_status_output(stdout: str) -> list[StatusEntry]:
    entries: list[StatusEntry] = []
    for raw_line in stdout.splitlines():
        if not raw_line:
            continue
        code = raw_line[:2]
        path = raw_line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        normalized = normalize_git_path(path)
        if normalized:
            entries.append(StatusEntry(code=code, path=normalized))
    return entries


def collect_status_entries(repo_root: Path) -> list[StatusEntry]:
    result = run_git_command(repo_root, "status", "--short", "--untracked-files=all")
    if result.returncode != 0:
        return []
    return parse_status_output(result.stdout)


def collect_recent_commit_paths(repo_root: Path) -> list[str]:
    result = run_git_command(
        repo_root,
        "log",
        "--name-only",
        "--pretty=format:",
        "-n",
        str(RECENT_COMMIT_LIMIT),
    )
    if result.returncode != 0:
        return []
    seen: set[str] = set()
    paths: list[str] = []
    for line in result.stdout.splitlines():
        normalized = normalize_git_path(line)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        paths.append(normalized)
    return paths


def collect_tracked_paths(repo_root: Path) -> set[str]:
    result = run_git_command(repo_root, "ls-files")
    if result.returncode != 0:
        return set()
    return {normalize_git_path(line) for line in result.stdout.splitlines() if line.strip()}


def list_inspected_ignore_files(repo_root: Path) -> list[str]:
    inspected: list[str] = []
    for relative_path in INSPECTED_IGNORE_FILES:
        absolute_path = repo_root / relative_path
        if relative_path in (".gitignore", ".git/info/exclude") or absolute_path.exists():
            inspected.append(relative_path)
    return inspected


def collect_existing_patterns_by_file(repo_root: Path) -> dict[str, set[str]]:
    patterns_by_file: dict[str, set[str]] = {}
    for relative_path in list_inspected_ignore_files(repo_root):
        absolute_path = repo_root / relative_path
        patterns: set[str] = set()
        if absolute_path.exists():
            for line in absolute_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                patterns.add(stripped)
        patterns_by_file[relative_path] = patterns
    return patterns_by_file


def collect_local_env_rules(repo_root: Path) -> list[tuple[str, str]]:
    rules: list[tuple[str, str]] = []
    for path in sorted(repo_root.glob(".env*")):
        if not path.is_file():
            continue
        name = path.name
        if name.endswith(".example") or name.endswith(".sample"):
            continue
        if name in LOCAL_ENV_NAMES or (name.startswith(".env.") and name.endswith(SAFE_LOCAL_ENV_SUFFIX)):
            rules.append(
                (
                    name,
                    "Local environment files often contain machine-specific or secret values.",
                )
            )
    return rules


def path_matches_pattern(path: str, pattern: str) -> bool:
    normalized_path = normalize_git_path(path)
    pure_path = PurePosixPath(normalized_path)
    if pattern.endswith("/"):
        target = pattern[:-1]
        return target in pure_path.parts
    if pattern == "*.log":
        return pure_path.name.endswith(".log")
    return normalized_path == pattern or pure_path.name == pattern


def matching_paths(paths: set[str] | list[str], pattern: str) -> list[str]:
    matches = sorted({normalize_git_path(path) for path in paths if path_matches_pattern(path, pattern)})
    return matches


def collect_repo_signals(repo_root: Path) -> RepoSignals:
    detected_stacks = detect_stacks(repo_root)
    observed_dirs, observed_files = walk_repo(repo_root)
    inspected_ignore_files = list_inspected_ignore_files(repo_root)
    existing_patterns_by_file = collect_existing_patterns_by_file(repo_root)
    status_entries = collect_status_entries(repo_root)
    recent_commit_paths = collect_recent_commit_paths(repo_root)
    tracked_paths = collect_tracked_paths(repo_root)
    optional_targets = {
        relative_path
        for relative_path in SECONDARY_SHARED_TARGETS
        if relative_path == ".dockerignore"
        or (repo_root / relative_path).exists()
    }
    docker_context = (repo_root / "Dockerfile").exists() or (repo_root / ".dockerignore").exists()
    return RepoSignals(
        detected_stacks=detected_stacks,
        observed_dirs=observed_dirs,
        observed_files=observed_files,
        existing_patterns_by_file=existing_patterns_by_file,
        inspected_ignore_files=inspected_ignore_files,
        status_entries=status_entries,
        recent_commit_paths=recent_commit_paths,
        tracked_paths=tracked_paths,
        optional_targets=optional_targets,
        docker_context=docker_context,
    )


def confidence_from_evidence(evidence: list[str], *, local_only: bool = False) -> str:
    if any(item.startswith("git-status") for item in evidence):
        return "medium" if local_only else "high"
    if any(item.startswith("observed") for item in evidence):
        return "medium"
    return "low"


def secondary_targets_for_pattern(pattern: str, signals: RepoSignals) -> list[str]:
    targets: list[str] = []
    if pattern not in SECONDARY_SHARED_PATTERNS:
        return targets
    for target_file in SECONDARY_SHARED_TARGETS:
        if target_file not in signals.optional_targets:
            continue
        if target_file == ".dockerignore" and not signals.docker_context:
            continue
        targets.append(target_file)
    return targets


def build_candidate_rules(
    repo_root: Path,
    signals: RepoSignals,
) -> tuple[list[CandidateRule], list[SkippedRule]]:
    candidates: list[CandidateRule] = []
    skipped: list[SkippedRule] = []
    seen_candidates: set[tuple[str, str]] = set()
    skipped_patterns: set[str] = set()
    status_paths = [entry.path for entry in signals.status_entries]

    def add_skipped(pattern: str, reason: str) -> None:
        if pattern in skipped_patterns:
            return
        skipped_patterns.add(pattern)
        skipped.append(SkippedRule(pattern=pattern, reasons=[reason]))

    def add_candidate(
        pattern: str,
        reason: str,
        target_file: str,
        evidence: list[str],
        *,
        local_only: bool = False,
    ) -> None:
        key = (pattern, target_file)
        if key in seen_candidates:
            return
        if pattern in signals.existing_patterns_by_file.get(target_file, set()):
            return
        seen_candidates.add(key)
        candidates.append(
            CandidateRule(
                pattern=pattern,
                target_file=target_file,
                reason=reason,
                confidence=confidence_from_evidence(evidence, local_only=local_only),
                evidence=evidence,
            )
        )

    def consider_pattern(
        pattern: str,
        reason: str,
        primary_target: str,
        evidence: list[str],
        *,
        local_only: bool = False,
        allow_secondary_targets: bool = False,
    ) -> None:
        if not evidence:
            return
        if all(item.startswith("recent-commit") for item in evidence):
            return
        tracked_hits = matching_paths(signals.tracked_paths, pattern)
        if tracked_hits:
            sample = ", ".join(tracked_hits[:3])
            add_skipped(pattern, f"tracked paths already match this pattern: {sample}")
            return

        targets = [primary_target]
        if allow_secondary_targets:
            targets.extend(secondary_targets_for_pattern(pattern, signals))
        for target_file in targets:
            target_evidence = list(evidence)
            if target_file == ".dockerignore":
                target_evidence.append("docker-context: Dockerfile or .dockerignore detected")
            add_candidate(
                pattern,
                reason,
                target_file,
                target_evidence,
                local_only=local_only and target_file == ".git/info/exclude",
            )

    for dirname, (pattern, reason) in GENERATED_DIR_RULES.items():
        evidence: list[str] = []
        if dirname in signals.observed_dirs or (repo_root / dirname).exists():
            evidence.append(f"observed-directory: {dirname}")
        status_hits = matching_paths(status_paths, pattern)
        if status_hits:
            evidence.append(f"git-status: {status_hits[0]}")
        recent_hits = matching_paths(signals.recent_commit_paths, pattern)
        if recent_hits:
            evidence.append(f"recent-commit: {recent_hits[0]}")
        consider_pattern(
            pattern,
            reason,
            ".gitignore",
            evidence,
            allow_secondary_targets=True,
        )

    for dirname, (pattern, reason) in EDITOR_LOCAL_DIR_RULES.items():
        evidence: list[str] = []
        if dirname in signals.observed_dirs or (repo_root / dirname).exists():
            evidence.append(f"observed-directory: {dirname}")
        status_hits = matching_paths(status_paths, pattern)
        if status_hits:
            evidence.append(f"git-status: {status_hits[0]}")
        recent_hits = matching_paths(signals.recent_commit_paths, pattern)
        if recent_hits:
            evidence.append(f"recent-commit: {recent_hits[0]}")
        consider_pattern(
            pattern,
            reason,
            ".git/info/exclude",
            evidence,
            local_only=True,
        )

    for pattern, reason in collect_local_env_rules(repo_root):
        evidence = [f"observed-file: {pattern}"]
        status_hits = matching_paths(status_paths, pattern)
        if status_hits:
            evidence.append(f"git-status: {status_hits[0]}")
        recent_hits = matching_paths(signals.recent_commit_paths, pattern)
        if recent_hits:
            evidence.append(f"recent-commit: {recent_hits[0]}")
        consider_pattern(pattern, reason, ".gitignore", evidence)

    log_paths = [path for path in status_paths if path.endswith(".log")]
    if any(name.endswith(".log") for name in signals.observed_files) or log_paths:
        evidence = []
        if log_paths:
            evidence.append(f"git-status: {log_paths[0]}")
        elif any(name.endswith(".log") for name in signals.observed_files):
            evidence.append("observed-file: *.log")
        recent_hits = matching_paths(signals.recent_commit_paths, "*.log")
        if recent_hits:
            evidence.append(f"recent-commit: {recent_hits[0]}")
        consider_pattern(
            "*.log",
            "Log files are generated locally and should usually not be committed.",
            ".gitignore",
            evidence,
        )

    for pattern, file_name, reason in (
        (".DS_Store", ".DS_Store", "macOS Finder metadata is local-only."),
        ("Thumbs.db", "Thumbs.db", "Windows Explorer metadata is local-only."),
    ):
        evidence = []
        if file_name in signals.observed_files:
            evidence.append(f"observed-file: {file_name}")
        status_hits = matching_paths(status_paths, pattern)
        if status_hits:
            evidence.append(f"git-status: {status_hits[0]}")
        recent_hits = matching_paths(signals.recent_commit_paths, pattern)
        if recent_hits:
            evidence.append(f"recent-commit: {recent_hits[0]}")
        consider_pattern(
            pattern,
            reason,
            ".git/info/exclude",
            evidence,
            local_only=True,
        )

    for signal_name, configured_rules in ROOT_SIGNAL_RULES.items():
        if not (repo_root / signal_name).exists():
            continue
        for configured_rule in configured_rules:
            if len(configured_rule) == 3:
                pattern, reason, target_file = configured_rule
            else:
                pattern, reason = configured_rule
                target_file = ".gitignore"
            consider_pattern(
                pattern,
                reason,
                target_file,
                [f"stack-signal: found {signal_name}"],
                allow_secondary_targets=target_file == ".gitignore",
            )

    return sorted(candidates, key=lambda item: (item.target_file, item.pattern)), sorted(
        skipped,
        key=lambda item: item.pattern,
    )


def append_lines(base_text: str, lines: list[str]) -> str:
    text = base_text
    if text and not text.endswith("\n"):
        text += "\n"
    if text and not text.endswith("\n\n"):
        text += "\n"
    text += "\n".join(lines) + "\n"
    return text


def apply_rules(repo_root: Path, candidate_rules: list[CandidateRule]) -> list[AppliedRule]:
    rules_by_target: dict[str, list[str]] = {}
    for item in candidate_rules:
        rules_by_target.setdefault(item.target_file, []).append(item.pattern)

    applied: list[AppliedRule] = []
    for target_file, patterns in rules_by_target.items():
        target_path = repo_root / target_file
        existing: set[str] = set()
        if target_path.exists():
            existing = {
                line.strip()
                for line in target_path.read_text(encoding="utf-8", errors="ignore").splitlines()
                if line.strip()
            }
        missing_patterns = [pattern for pattern in patterns if pattern not in existing]
        if not missing_patterns:
            continue
        current_text = ""
        if target_path.exists():
            current_text = target_path.read_text(encoding="utf-8", errors="ignore")
        lines_to_add = []
        if MARKER not in current_text:
            lines_to_add.append(MARKER)
        lines_to_add.extend(missing_patterns)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(append_lines(current_text, lines_to_add), encoding="utf-8")
        applied.extend(
            AppliedRule(pattern=pattern, target_file=target_file) for pattern in missing_patterns
        )
    return applied


def render_payload(
    repo_root: Path,
    signals: RepoSignals,
    candidate_rules: list[CandidateRule],
    skipped_rules: list[SkippedRule],
    applied_rules: list[AppliedRule],
) -> dict[str, object]:
    return {
        "repo_root": str(repo_root),
        "detected_stacks": signals.detected_stacks,
        "candidate_rules": [asdict(item) for item in candidate_rules],
        "skipped_rules": [asdict(item) for item in skipped_rules],
        "applied_rules": [asdict(item) for item in applied_rules],
        "inspected_ignore_files": signals.inspected_ignore_files,
        "recent_commit_paths_sample": signals.recent_commit_paths[:10],
        "status_entries_sample": [asdict(item) for item in signals.status_entries[:10]],
        "is_git_repo": True,
    }


def emit_text(candidate_rules: list[CandidateRule], skipped_rules: list[SkippedRule], applied_rules: list[AppliedRule]) -> None:
    if not candidate_rules:
        print("No safe ignore-file additions detected.")
    else:
        print("Suggested ignore-file additions:")
        for item in candidate_rules:
            evidence = "; ".join(item.evidence)
            print(
                f"- {item.target_file}: {item.pattern} [{item.confidence}]"
                f" - {item.reason} ({evidence})"
            )

    if skipped_rules:
        print("")
        print("Skipped patterns:")
        for item in skipped_rules:
            print(f"- {item.pattern}: {'; '.join(item.reasons)}")

    if applied_rules:
        print("")
        print("Applied rules:")
        for item in applied_rules:
            print(f"- {item.target_file}: {item.pattern}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    requested_root = Path(args.project_root).resolve()
    repo_root = find_repo_root(requested_root)
    if repo_root is None:
        print("Current path is not inside a git repository.", file=sys.stderr)
        return 1

    signals = collect_repo_signals(repo_root)
    candidate_rules, skipped_rules = build_candidate_rules(repo_root, signals)
    applied_rules: list[AppliedRule] = []

    if args.apply:
        applied_rules = apply_rules(repo_root, candidate_rules)

    payload = render_payload(repo_root, signals, candidate_rules, skipped_rules, applied_rules)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        emit_text(candidate_rules, skipped_rules, applied_rules)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

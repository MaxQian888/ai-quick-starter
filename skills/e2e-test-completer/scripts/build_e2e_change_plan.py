#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


SPEC_EXTS = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
SKIP_DIR_NAMES = {
    ".git",
    ".next",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "out",
}
STOP_TOKENS = {
    "app",
    "apps",
    "component",
    "components",
    "coverage",
    "cypress",
    "cy",
    "e2e",
    "feature",
    "features",
    "hook",
    "hooks",
    "index",
    "lib",
    "libs",
    "page",
    "pages",
    "playwright",
    "screen",
    "screens",
    "spec",
    "src",
    "test",
    "tests",
    "ui",
    "utils",
    "view",
    "views",
}
CONTENT_STOP_TOKENS = STOP_TOKENS | {
    "allow",
    "allows",
    "and",
    "async",
    "await",
    "const",
    "describe",
    "expect",
    "export",
    "from",
    "import",
    "locator",
    "null",
    "page",
    "return",
    "sign",
    "test",
    "then",
}
IMPLEMENTATION_SKIP_TOKENS = (".spec.", ".test.", ".cy.")
PLAYWRIGHT_CONFIGS = (
    "playwright.config.ts",
    "playwright.config.js",
    "playwright.config.mjs",
    "playwright.config.cjs",
)
CYPRESS_CONFIGS = (
    "cypress.config.ts",
    "cypress.config.js",
    "cypress.config.mjs",
    "cypress.config.cjs",
)


@dataclass
class RunnerSurface:
    framework: str
    package_manager: str
    primary_command: str
    config_paths: list[str]
    working_directory: str


@dataclass
class SpecMatch:
    spec: str
    score: int
    reasons: list[str]


@dataclass
class ChangeReport:
    changed_file: str
    matches: list[SpecMatch]


@dataclass
class SpecDocument:
    path: str
    content_tokens: set[str]


@dataclass
class RunnerCandidate:
    framework: str
    package_manager: str
    package_data: dict[str, object]
    config_paths: list[str]
    spec_paths: list[str]
    working_directory: str
    score: int


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discover E2E runner surface, map changes to specs, and build a dry-run verification plan.",
    )
    parser.add_argument("--project-root", default=".")
    parser.add_argument(
        "--mode",
        choices=("discover", "plan", "simulate"),
        default="discover",
    )
    parser.add_argument(
        "--changed-file",
        action="append",
        default=[],
        help="Changed implementation file relative to --project-root. Repeat as needed.",
    )
    parser.add_argument(
        "--changed-file-list",
        help="Optional newline-delimited file containing changed paths.",
    )
    parser.add_argument(
        "--git-base",
        help="Optional git base revision for changed-file detection via git diff --name-only.",
    )
    parser.add_argument(
        "--framework",
        choices=("auto", "playwright", "cypress"),
        default="auto",
    )
    parser.add_argument("--max-matches", type=int, default=5)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args(argv)


def normalize_rel(path: Path) -> str:
    return path.as_posix()


def normalize_dir_text(value: str) -> str:
    return "" if value in {"", "."} else value


def should_skip_path(path: Path) -> bool:
    return any(part.lower() in SKIP_DIR_NAMES for part in path.parts)


def load_package_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def parse_csv_tokens(text: str, stop_tokens: set[str]) -> list[str]:
    tokens: list[str] = []
    for token in re.split(r"[^a-z0-9]+", text.lower()):
        if not token or token in stop_tokens:
            continue
        if len(token) == 1 and not token.isdigit():
            continue
        tokens.append(token)
    return tokens


def tokenize_path(path: str) -> list[str]:
    return parse_csv_tokens(path.replace("\\", "/"), STOP_TOKENS)


def tokenize_content(text: str) -> set[str]:
    return set(parse_csv_tokens(text, CONTENT_STOP_TOKENS))


def discover_package_manager(root: Path, working_directory: str) -> str:
    search_roots: list[Path] = []
    current = root / working_directory if working_directory else root
    current = current.resolve()
    root_resolved = root.resolve()

    while True:
        search_roots.append(current)
        if current == root_resolved:
            break
        if root_resolved not in current.parents:
            break
        current = current.parent

    for candidate_root in search_roots:
        if (candidate_root / "pnpm-lock.yaml").exists():
            return "pnpm"
        if (candidate_root / "package-lock.json").exists():
            return "npm"
        if (candidate_root / "yarn.lock").exists():
            return "yarn"
        if (candidate_root / "bun.lock").exists() or (candidate_root / "bun.lockb").exists():
            return "bun"
    return "npm"


def find_repo_package_dirs(root: Path) -> list[str]:
    package_dirs: set[str] = set()
    for package_json in root.rglob("package.json"):
        if should_skip_path(package_json.relative_to(root)):
            continue
        rel_dir = normalize_rel(package_json.parent.relative_to(root))
        package_dirs.add("" if rel_dir == "." else rel_dir)
    package_dirs.add("")
    return sorted(package_dirs)


def find_config_paths(root: Path, filenames: tuple[str, ...]) -> list[str]:
    paths: list[str] = []
    for filename in filenames:
        for path in root.rglob(filename):
            if should_skip_path(path.relative_to(root)):
                continue
            paths.append(normalize_rel(path.relative_to(root)))
    return sorted(paths)


def is_e2e_spec_path(path: str) -> bool:
    lower = path.lower()
    return (
        lower.startswith("e2e/")
        or "/e2e/" in lower
        or lower.startswith("cypress/e2e/")
        or ".cy." in lower
        or ("playwright" in lower and (".spec." in lower or ".test." in lower))
        or (("e2e" in lower or "tests/e2e" in lower) and (".spec." in lower or ".test." in lower))
    )


def find_all_spec_paths(root: Path) -> list[str]:
    specs: list[str] = []
    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        rel_path = file_path.relative_to(root)
        if should_skip_path(rel_path):
            continue
        if file_path.suffix.lower() not in SPEC_EXTS:
            continue
        rel = normalize_rel(rel_path)
        if is_e2e_spec_path(rel):
            specs.append(rel)
    return sorted(specs)


def is_under_directory(path: str, directory: str) -> bool:
    if not directory:
        return True
    return path == directory or path.startswith(f"{directory}/")


def find_nearest_package_dir(root: Path, working_directory: str, known_dirs: set[str]) -> str:
    if working_directory in known_dirs:
        return working_directory

    current = Path(working_directory)
    while str(current) not in {".", ""}:
        current_text = normalize_rel(current)
        if current_text in known_dirs:
            return current_text
        current = current.parent
    return ""


def detect_framework_from_surface(
    preferred: str,
    package_data: dict[str, object],
    playwright_configs: list[str],
    cypress_configs: list[str],
    spec_paths: list[str],
) -> str:
    if preferred != "auto":
        return preferred

    scripts = package_data.get("scripts", {})
    if not isinstance(scripts, dict):
        scripts = {}

    script_values = " ".join(str(value).lower() for value in scripts.values())
    joined_specs = " ".join(spec_paths).lower()

    if playwright_configs or "playwright" in script_values or "playwright" in joined_specs:
        return "playwright"
    if cypress_configs or "cypress" in script_values or ".cy." in joined_specs:
        return "cypress"
    return "unknown"


def find_script_name(framework: str, package_data: dict[str, object]) -> str:
    scripts = package_data.get("scripts", {})
    if not isinstance(scripts, dict):
        return ""

    for key, value in scripts.items():
        key_text = str(key).lower()
        value_text = str(value).lower()
        if framework == "playwright" and "playwright" in value_text:
            return str(key)
        if framework == "cypress" and "cypress" in value_text:
            return str(key)
        if "e2e" in key_text:
            return str(key)
    return ""


def script_command(package_manager: str, script_name: str, working_directory: str) -> str:
    if package_manager == "pnpm":
        return f"pnpm --dir {working_directory} {script_name}" if working_directory else f"pnpm {script_name}"
    if package_manager == "yarn":
        return f"yarn --cwd {working_directory} {script_name}" if working_directory else f"yarn {script_name}"
    if package_manager == "bun":
        return f"bun --cwd {working_directory} run {script_name}" if working_directory else f"bun run {script_name}"
    return f"npm --prefix {working_directory} run {script_name}" if working_directory else f"npm run {script_name}"


def exec_base_command(package_manager: str, command: str, working_directory: str) -> str:
    if package_manager == "pnpm":
        return (
            f"pnpm --dir {working_directory} exec {command}"
            if working_directory
            else f"pnpm exec {command}"
        )
    if package_manager == "yarn":
        return f"yarn --cwd {working_directory} {command}" if working_directory else f"yarn {command}"
    if package_manager == "bun":
        return f"bun --cwd {working_directory} x {command}" if working_directory else f"bunx {command}"
    return (
        f"npm --prefix {working_directory} exec -- {command}"
        if working_directory
        else f"npx {command}"
    )


def build_primary_command(
    framework: str,
    package_manager: str,
    package_data: dict[str, object],
    working_directory: str,
) -> str:
    script_name = find_script_name(framework, package_data)
    if script_name:
        return script_command(package_manager, script_name, working_directory)
    if framework == "playwright":
        return exec_base_command(package_manager, "playwright test", working_directory)
    if framework == "cypress":
        return exec_base_command(package_manager, "cypress run", working_directory)
    return ""


def collect_spec_documents(root: Path, spec_paths: list[str]) -> list[SpecDocument]:
    documents: list[SpecDocument] = []
    for spec_path in spec_paths:
        file_path = root / Path(spec_path)
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            content = ""
        documents.append(
            SpecDocument(
                path=spec_path,
                content_tokens=tokenize_content(content[:20000]),
            )
        )
    return documents


def discover_runner_candidate(root: Path, preferred_framework: str) -> RunnerCandidate | None:
    package_dirs = find_repo_package_dirs(root)
    package_dir_set = set(package_dirs)
    all_playwright_configs = find_config_paths(root, PLAYWRIGHT_CONFIGS)
    all_cypress_configs = find_config_paths(root, CYPRESS_CONFIGS)
    all_spec_paths = find_all_spec_paths(root)

    candidate_dirs = set(package_dirs)
    candidate_dirs.update(normalize_dir_text(normalize_rel(Path(path).parent)) for path in all_playwright_configs)
    candidate_dirs.update(normalize_dir_text(normalize_rel(Path(path).parent)) for path in all_cypress_configs)

    best: RunnerCandidate | None = None
    for working_directory in sorted(candidate_dirs):
        working_directory = normalize_dir_text(working_directory)

        package_dir = find_nearest_package_dir(root, working_directory, package_dir_set)
        package_json_path = root / package_dir / "package.json" if package_dir else root / "package.json"
        package_data = load_package_json(package_json_path)
        local_playwright_configs = [
            path
            for path in all_playwright_configs
            if normalize_dir_text(normalize_rel(Path(path).parent)) == working_directory
        ]
        local_cypress_configs = [
            path
            for path in all_cypress_configs
            if normalize_dir_text(normalize_rel(Path(path).parent)) == working_directory
        ]
        local_specs = [
            spec for spec in all_spec_paths if is_under_directory(spec, working_directory)
        ]
        framework = detect_framework_from_surface(
            preferred_framework,
            package_data,
            local_playwright_configs,
            local_cypress_configs,
            local_specs,
        )
        if framework == "unknown":
            continue

        package_manager = discover_package_manager(root, working_directory)
        script_name = find_script_name(framework, package_data)
        score = 0
        if script_name:
            score += 6
        if (framework == "playwright" and local_playwright_configs) or (
            framework == "cypress" and local_cypress_configs
        ):
            score += 5
        if local_specs:
            score += min(4, len(local_specs))
        if working_directory:
            score += 1

        candidate = RunnerCandidate(
            framework=framework,
            package_manager=package_manager,
            package_data=package_data,
            config_paths=local_playwright_configs if framework == "playwright" else local_cypress_configs,
            spec_paths=local_specs,
            working_directory=working_directory,
            score=score,
        )
        if best is None or (candidate.score, len(candidate.working_directory)) > (
            best.score,
            len(best.working_directory),
        ):
            best = candidate

    return best


def normalize_input_path(root: Path, value: str) -> str:
    raw = Path(value)
    path = raw if raw.is_absolute() else (root / raw)
    try:
        return normalize_rel(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return normalize_rel(raw)


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        normalized = item.replace("\\", "/")
        if normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def discover_git_status_changes(root: Path) -> list[str]:
    if not (root / ".git").exists():
        return []
    try:
        completed = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return []
    if completed.returncode != 0:
        return []

    changed: list[str] = []
    for line in completed.stdout.splitlines():
        if len(line) < 4:
            continue
        changed.append(line[3:].strip().replace("\\", "/"))
    return dedupe([item for item in changed if item])


def discover_git_diff_changes(root: Path, git_base: str) -> list[str]:
    if not (root / ".git").exists():
        return []
    try:
        completed = subprocess.run(
            ["git", "diff", "--name-only", git_base, "--"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return []
    if completed.returncode != 0:
        return []
    return dedupe([line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()])


def load_changed_files(root: Path, args: argparse.Namespace) -> list[str]:
    changed: list[str] = []
    for item in args.changed_file:
        changed.append(normalize_input_path(root, item))

    if args.changed_file_list:
        lines = Path(args.changed_file_list).read_text(encoding="utf-8").splitlines()
        for line in lines:
            cleaned = line.strip()
            if cleaned:
                changed.append(normalize_input_path(root, cleaned))

    if changed:
        return dedupe(changed)
    if args.git_base:
        return discover_git_diff_changes(root, args.git_base)
    return discover_git_status_changes(root)


def is_implementation_path(path: str) -> bool:
    lower = path.lower()
    if any(token in lower for token in IMPLEMENTATION_SKIP_TOKENS):
        return False
    return Path(path).suffix.lower() in SPEC_EXTS


def score_spec_match(changed_file: str, spec_document: SpecDocument) -> SpecMatch | None:
    changed_tokens = tokenize_path(changed_file)
    spec_path_tokens = tokenize_path(spec_document.path)
    path_overlap = sorted(set(changed_tokens) & set(spec_path_tokens))
    content_overlap = sorted(set(changed_tokens) & spec_document.content_tokens)

    if not path_overlap and not content_overlap:
        changed_stem = Path(changed_file).stem.lower()
        spec_stem = Path(spec_document.path).stem.lower()
        if not changed_stem or changed_stem not in spec_stem:
            return None

    score = len(path_overlap) * 3 + len(content_overlap)
    reasons = [f"token:{token}" for token in path_overlap]
    reasons.extend(f"content:{token}" for token in content_overlap)

    changed_stem = Path(changed_file).stem.lower()
    spec_stem = Path(spec_document.path).stem.lower()
    if changed_stem and changed_stem in spec_stem:
        score += 2
        reasons.append("stem")

    parent_tokens = set(tokenize_path(str(Path(changed_file).parent)))
    spec_parent_tokens = set(tokenize_path(str(Path(spec_document.path).parent)))
    shared_parent = sorted(parent_tokens & spec_parent_tokens)
    if shared_parent:
        score += len(shared_parent)
        reasons.extend(f"dir:{token}" for token in shared_parent)

    return SpecMatch(spec=spec_document.path, score=score, reasons=dedupe(reasons))


def build_change_reports(
    changed_files: list[str],
    spec_documents: list[SpecDocument],
    max_matches: int,
) -> tuple[list[ChangeReport], list[dict[str, str]]]:
    reports: list[ChangeReport] = []
    coverage_gaps: list[dict[str, str]] = []

    for changed_file in changed_files:
        if not is_implementation_path(changed_file):
            continue
        matches = [
            match
            for spec_document in spec_documents
            if (match := score_spec_match(changed_file, spec_document)) is not None
        ]
        matches.sort(key=lambda item: (-item.score, item.spec))
        trimmed = matches[:max_matches]
        reports.append(ChangeReport(changed_file=changed_file, matches=trimmed))
        if not trimmed:
            coverage_gaps.append(
                {
                    "changed_file": changed_file,
                    "reason": "No E2E spec matched the changed path tokens or spec content tokens.",
                }
            )

    return reports, coverage_gaps


def relative_to_working_directory(path: str, working_directory: str) -> str:
    if not working_directory:
        return path
    prefix = f"{working_directory}/"
    if path.startswith(prefix):
        return path[len(prefix) :]
    return path


def build_targeted_command(
    framework: str,
    package_manager: str,
    targeted_specs: list[str],
    working_directory: str,
) -> str:
    if not targeted_specs:
        return ""
    scoped_specs = [relative_to_working_directory(spec, working_directory) for spec in targeted_specs]
    if framework == "playwright":
        return f"{exec_base_command(package_manager, 'playwright test', working_directory)} {' '.join(scoped_specs)}"
    if framework == "cypress":
        return f"{exec_base_command(package_manager, 'cypress run', working_directory)} --spec {','.join(scoped_specs)}"
    return ""


def build_payload(args: argparse.Namespace) -> dict[str, object]:
    root = Path(args.project_root).resolve()
    candidate = discover_runner_candidate(root, args.framework)
    changed_files = load_changed_files(root, args)

    if candidate is None:
        runner = RunnerSurface(
            framework="unknown",
            package_manager=discover_package_manager(root, ""),
            primary_command="",
            config_paths=[],
            working_directory="",
        )
        spec_paths: list[str] = []
        spec_documents: list[SpecDocument] = []
    else:
        runner = RunnerSurface(
            framework=candidate.framework,
            package_manager=candidate.package_manager,
            primary_command=build_primary_command(
                candidate.framework,
                candidate.package_manager,
                candidate.package_data,
                candidate.working_directory,
            ),
            config_paths=candidate.config_paths,
            working_directory=candidate.working_directory,
        )
        spec_paths = candidate.spec_paths
        spec_documents = collect_spec_documents(root, spec_paths)

    change_reports, coverage_gaps = build_change_reports(
        changed_files=changed_files,
        spec_documents=spec_documents,
        max_matches=args.max_matches,
    )
    targeted_specs = dedupe([report.matches[0].spec for report in change_reports if report.matches])
    execution_plan = {
        "targeted_command": build_targeted_command(
            runner.framework,
            runner.package_manager,
            targeted_specs,
            runner.working_directory,
        ),
        "full_command": runner.primary_command,
        "readiness": "ready" if runner.framework != "unknown" and runner.primary_command else "blocked",
        "targeted_specs": targeted_specs,
    }

    overall_status = "discovered"
    if runner.framework == "unknown":
        overall_status = "blocked"
    elif args.mode == "plan":
        overall_status = "gap" if coverage_gaps else "planned"
    elif args.mode == "simulate":
        overall_status = "gap" if coverage_gaps else "simulated"

    return {
        "project_root": str(root),
        "runner": asdict(runner),
        "spec_count": len(spec_paths),
        "spec_paths": spec_paths,
        "changed_files": changed_files,
        "change_reports": [
            {
                "changed_file": report.changed_file,
                "matches": [asdict(match) for match in report.matches],
            }
            for report in change_reports
        ],
        "coverage_gaps": coverage_gaps,
        "execution_plan": execution_plan,
        "overall_status": overall_status,
    }


def print_text(payload: dict[str, object]) -> None:
    runner = payload["runner"]
    if isinstance(runner, dict):
        print(f"framework: {runner['framework']}")
        print(f"package_manager: {runner['package_manager']}")
        print(f"working_directory: {runner['working_directory']}")
        print(f"primary_command: {runner['primary_command']}")
    print(f"spec_count: {payload['spec_count']}")
    if payload["changed_files"]:
        print("changed_files:")
        for path in payload["changed_files"]:
            print(f"  - {path}")
    if payload["coverage_gaps"]:
        print("coverage_gaps:")
        for gap in payload["coverage_gaps"]:
            print(f"  - {gap['changed_file']}: {gap['reason']}")
    execution_plan = payload["execution_plan"]
    if isinstance(execution_plan, dict) and execution_plan.get("targeted_command"):
        print(f"targeted_command: {execution_plan['targeted_command']}")
    print(f"overall_status: {payload['overall_status']}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_payload(args)
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_text(payload)
    return 1 if payload["overall_status"] in {"blocked", "gap"} else 0


if __name__ == "__main__":
    raise SystemExit(main())

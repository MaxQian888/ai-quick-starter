from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


MAX_SCAN_DEPTH = 4
MIXED_CONCERN_DIRS = {
    "components",
    "pages",
    "routes",
    "services",
    "utils",
    "lib",
    "hooks",
    "api",
    "domain",
    "infrastructure",
    "repositories",
}


@dataclass
class RepoSignals:
    project_root: Path
    git_root: Path
    package_jsons: list[Path]
    pyprojects: list[Path]
    workspace_files: list[Path]
    ci_files: list[Path]
    top_level_dirs: list[str]
    src_dirs: list[str]
    manifests: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a staged project-structure migration blueprint.")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--migration-type", default="auto", choices=["auto", "monorepo", "restructure", "split-merge"])
    parser.add_argument("--stack", default="auto", choices=["auto", "js-ts", "python", "mixed"])
    parser.add_argument("--target-shape", default="")
    parser.add_argument("--json-out")
    parser.add_argument("--markdown-out")
    parser.add_argument("--max-depth", type=int, default=MAX_SCAN_DEPTH)
    return parser.parse_args()


def find_git_root(project_root: Path) -> Path:
    current = project_root.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".git").exists():
            return candidate
    return current


def bounded_rglob(project_root: Path, pattern: str, max_depth: int) -> list[Path]:
    matches: list[Path] = []
    for path in project_root.rglob(pattern):
        try:
            relative = path.relative_to(project_root)
        except ValueError:
            continue
        if len(relative.parts) <= max_depth + 1:
            matches.append(path)
    return sorted(matches)


def collect_repo_signals(project_root: Path, max_depth: int) -> RepoSignals:
    git_root = find_git_root(project_root)
    package_jsons = bounded_rglob(project_root, "package.json", max_depth)
    pyprojects = bounded_rglob(project_root, "pyproject.toml", max_depth)
    workspace_files = sorted(
        [
            path
            for name in ("pnpm-workspace.yaml", "turbo.json", "nx.json")
            for path in bounded_rglob(project_root, name, max_depth)
        ]
    )
    ci_files = bounded_rglob(project_root, "*.yml", max_depth) + bounded_rglob(project_root, "*.yaml", max_depth)
    ci_files = sorted(path for path in ci_files if ".github" in path.parts)
    top_level_dirs = sorted(path.name for path in project_root.iterdir() if path.is_dir())
    src_root = project_root / "src"
    src_dirs = sorted(path.name for path in src_root.iterdir() if path.is_dir()) if src_root.exists() else []
    manifests = sorted(str(path.relative_to(project_root)) for path in [*package_jsons, *pyprojects])
    return RepoSignals(
        project_root=project_root.resolve(),
        git_root=git_root.resolve(),
        package_jsons=package_jsons,
        pyprojects=pyprojects,
        workspace_files=workspace_files,
        ci_files=ci_files,
        top_level_dirs=top_level_dirs,
        src_dirs=src_dirs,
        manifests=manifests,
    )


def classify_stack(signals: RepoSignals, stack_override: str) -> tuple[str, list[str]]:
    if stack_override != "auto":
        return stack_override, [f"stack forced by flag: {stack_override}"]
    has_js = bool(signals.package_jsons or signals.workspace_files)
    has_python = bool(signals.pyprojects)
    reasons: list[str] = []
    if has_js:
        reasons.append("detected package.json or workspace configuration")
    if has_python:
        reasons.append("detected pyproject.toml")
    if has_js and has_python:
        return "mixed", reasons
    if has_js:
        return "js-ts", reasons
    if has_python:
        return "python", reasons
    return "unknown", ["no strong language manifest detected"]


def classify_migration(signals: RepoSignals, migration_override: str) -> dict[str, object]:
    evidence: list[str] = []
    ambiguities: list[str] = []
    if migration_override != "auto":
        return {
            "type": migration_override,
            "confidence": 1.0,
            "evidence": [f"migration type forced by flag: {migration_override}"],
            "ambiguities": ambiguities,
        }

    has_workspace = bool(signals.workspace_files)
    has_workspace_packages = any("apps" in path.parts or "packages" in path.parts for path in signals.package_jsons[1:])
    mixed_concerns = len(set(signals.src_dirs) & MIXED_CONCERN_DIRS) >= 3
    app_roots = [name for name in signals.top_level_dirs if name in {"apps", "packages", "services", "projects"}]

    if has_workspace or has_workspace_packages:
        if has_workspace:
            evidence.extend(f"workspace config: {path.name}" for path in signals.workspace_files)
        if has_workspace_packages:
            evidence.append("detected nested package manifests under apps/ or packages/")
        return {
            "type": "monorepo",
            "confidence": 0.9,
            "evidence": evidence,
            "ambiguities": ambiguities,
        }

    if len(app_roots) >= 2 or len(signals.package_jsons) + len(signals.pyprojects) >= 3:
        evidence.append("detected multiple application or package roots without a unified workspace")
        return {
            "type": "split-merge",
            "confidence": 0.72,
            "evidence": evidence,
            "ambiguities": ambiguities,
        }

    if mixed_concerns:
        evidence.extend(f"mixed concern directory under src/: {name}" for name in sorted(set(signals.src_dirs) & MIXED_CONCERN_DIRS))
        return {
            "type": "restructure",
            "confidence": 0.78,
            "evidence": evidence,
            "ambiguities": ambiguities,
        }

    ambiguities.append("repository shape does not strongly indicate monorepo or split-merge migration")
    return {
        "type": "restructure",
        "confidence": 0.56,
        "evidence": ["defaulted to staged restructure because the repository appears to be a single project"],
        "ambiguities": ambiguities,
    }


def build_current_structure(signals: RepoSignals) -> dict[str, object]:
    mixed_dirs = sorted(set(signals.src_dirs) & MIXED_CONCERN_DIRS)
    return {
        "top_level_directories": signals.top_level_dirs,
        "manifests": signals.manifests,
        "workspace_files": [str(path.relative_to(signals.project_root)) for path in signals.workspace_files],
        "ci_files": [str(path.relative_to(signals.project_root)) for path in signals.ci_files],
        "src_directories": signals.src_dirs,
        "mixed_concerns": len(mixed_dirs) >= 3,
        "coupling_hotspots": mixed_dirs[:5],
    }


def build_target_structure(migration_type: str, stack: str, target_shape: str) -> dict[str, object]:
    if migration_type == "monorepo":
        layout = ["apps/<app-name>", "packages/<shared-lib>", "tooling/", "docs/"]
        patterns = ["workspace-root manifests", "shared package boundaries", "root verification matrix"]
    elif migration_type == "split-merge":
        layout = ["apps/<surface-a>", "apps/<surface-b>", "packages/<shared>", "migration-shims/"]
        patterns = ["explicit ownership boundaries", "import redirection shims", "shared runtime contracts"]
    else:
        layout = ["src/<domain-or-layer>", "src/shared/", "tests/", "tooling/"]
        patterns = ["focused domain or layer directories", "entrypoint compatibility shims", "phased import migration"]

    if stack == "python":
        patterns.append("package-level re-export shims")
    if stack in {"js-ts", "mixed"}:
        patterns.append("path alias and workspace-script transition plan")
    if target_shape:
        patterns.append(f"user target shape hint: {target_shape}")

    return {
        "layout": layout,
        "recommended_patterns": patterns,
        "compatibility_strategy": "preserve transitional shims until downstream callers and commands migrate",
    }


def build_batches(migration_type: str, stack: str) -> list[dict[str, object]]:
    batch_two_title = "Move entrypoints and internal imports"
    if migration_type == "monorepo":
        batch_two_title = "Split app and package roots"
    elif migration_type == "split-merge":
        batch_two_title = "Separate independent app surfaces"

    final_verify = "run the repo-native verify or build-test-lint chain"
    if stack == "python":
        final_verify = "run the repo-native verify chain or pytest, ruff, and mypy equivalents"

    return [
        {
            "id": "batch-1",
            "title": "Establish target skeleton and compatibility seams",
            "goal": "Create destination directories, transitional shims, and migration notes before moving behavior.",
            "depends_on": [],
            "primary_paths": ["tooling/", "docs/", "src/", "apps/", "packages/"],
            "verification": ["confirm new skeleton is non-breaking", "run the narrowest smoke or lint command"],
        },
        {
            "id": "batch-2",
            "title": batch_two_title,
            "goal": "Move one structure concern at a time while keeping imports and task-runner entrypoints stable.",
            "depends_on": ["batch-1"],
            "primary_paths": ["src/", "apps/", "packages/", "pyproject.toml", "package.json"],
            "verification": ["run affected-package or affected-module tests", "re-run impacted build or typecheck commands"],
        },
        {
            "id": "batch-3",
            "title": "Clean up legacy paths and finalize verification",
            "goal": "Remove old aliases or shims only after downstream callers migrate and the validation chain is green.",
            "depends_on": ["batch-2"],
            "primary_paths": ["legacy paths", "compatibility shims", "task-runner config"],
            "verification": ["confirm old paths are unused", final_verify],
        },
    ]


def build_verification_plan(stack: str, signals: RepoSignals) -> dict[str, object]:
    minimal = ["re-run the failing or directly impacted command for the current batch"]
    if signals.ci_files:
        minimal.append("cross-check the closest matching CI run step before widening scope")
    adjacent = ["run neighboring module, package, or app checks that share the moved paths"]
    final = ["run the strongest repository-native verify chain that current manifests or CI evidence support"]
    if stack == "python":
        final.append("if no single verify chain exists, run pytest plus lint and typecheck equivalents")
    elif stack in {"js-ts", "mixed"}:
        final.append("include workspace-root build, test, lint, and typecheck if the repo exposes them")
    return {
        "per_batch": minimal,
        "adjacent": adjacent,
        "final": final,
    }


def build_risk_register(migration_type: str, signals: RepoSignals) -> list[dict[str, str]]:
    risks = [
        {
            "severity": "high",
            "title": "Validation drift",
            "detail": "Repository-native verification commands may break if package roots or task-runner entrypoints move before compatibility shims exist.",
        },
        {
            "severity": "medium",
            "title": "Import churn",
            "detail": "Path or package renames can leave stale callers behind unless transitional aliases are preserved.",
        },
    ]
    if migration_type == "monorepo":
        risks.append(
            {
                "severity": "high",
                "title": "Workspace bootstrap mismatch",
                "detail": "Root lockfiles, workspace manifests, and package scripts must agree before hoisted installs or root commands are trustworthy.",
            }
        )
    if not signals.ci_files:
        risks.append(
            {
                "severity": "medium",
                "title": "Weak verification evidence",
                "detail": "No nearby CI workflow was detected, so validation commands may require manual confirmation.",
            }
        )
    return risks


def build_forbidden_moves() -> list[str]:
    return [
        "Do not mix structure migration with unrelated feature work in the same batch.",
        "Do not remove compatibility shims before downstream callers migrate.",
        "Do not widen validation claims beyond the commands actually re-run.",
        "Do not move multiple high-coupling subtrees in one uncontrolled pass.",
    ]


def build_open_questions(stack: str, migration: dict[str, object], signals: RepoSignals) -> list[str]:
    questions: list[str] = []
    if stack == "unknown":
        questions.append("Confirm the primary stack and runtime entrypoints before editing repository structure.")
    if migration["confidence"] < 0.7:
        questions.append("Confirm whether this should stay a staged restructure or become a split or merge migration.")
    if not signals.ci_files:
        questions.append("Confirm the final validation chain because no CI run steps were detected nearby.")
    return questions


def render_markdown(payload: dict[str, object]) -> str:
    project_profile = payload["project_profile"]
    migration = payload["migration_classification"]
    current = payload["current_structure"]
    target = payload["target_structure"]
    batches = payload["migration_batches"]
    verification = payload["verification_plan"]
    risks = payload["risk_register"]
    forbidden = payload["forbidden_moves"]
    open_questions = payload["open_questions"]

    lines = [
        "# Migration Blueprint",
        "",
        "## Project Profile",
        f"- Project root: `{project_profile['project_root']}`",
        f"- Git root: `{project_profile['git_root']}`",
        f"- Stack: `{project_profile['stack']}`",
        f"- Evidence: {', '.join(project_profile['stack_evidence'])}",
        "",
        "## Migration Classification",
        f"- Type: `{migration['type']}`",
        f"- Confidence: `{migration['confidence']}`",
        f"- Evidence: {', '.join(migration['evidence'])}",
    ]
    if migration["ambiguities"]:
        lines.append(f"- Ambiguities: {', '.join(migration['ambiguities'])}")
    lines.extend(
        [
            "",
            "## Current Structure",
            f"- Top-level directories: {', '.join(current['top_level_directories']) or '(none)'}",
            f"- Manifests: {', '.join(current['manifests']) or '(none)'}",
            f"- Mixed concerns: `{current['mixed_concerns']}`",
            f"- Coupling hotspots: {', '.join(current['coupling_hotspots']) or '(none)'}",
            "",
            "## Target Structure",
            f"- Layout: {', '.join(target['layout'])}",
            f"- Recommended patterns: {', '.join(target['recommended_patterns'])}",
            f"- Compatibility strategy: {target['compatibility_strategy']}",
            "",
            "## Migration Batches",
        ]
    )
    for batch in batches:
        lines.extend(
            [
                f"### {batch['id']}: {batch['title']}",
                f"- Goal: {batch['goal']}",
                f"- Depends on: {', '.join(batch['depends_on']) or '(none)'}",
                f"- Primary paths: {', '.join(batch['primary_paths'])}",
                f"- Verification: {', '.join(batch['verification'])}",
                "",
            ]
        )
    lines.extend(
        [
            "## Verification Plan",
            f"- Per batch: {', '.join(verification['per_batch'])}",
            f"- Adjacent: {', '.join(verification['adjacent'])}",
            f"- Final: {', '.join(verification['final'])}",
            "",
            "## Risk Register",
        ]
    )
    for risk in risks:
        lines.append(f"- [{risk['severity']}] {risk['title']}: {risk['detail']}")
    lines.extend(["", "## Forbidden Moves"])
    for item in forbidden:
        lines.append(f"- {item}")
    lines.extend(["", "## Open Questions"])
    if open_questions:
        for item in open_questions:
            lines.append(f"- {item}")
    else:
        lines.append("- None.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    signals = collect_repo_signals(project_root, args.max_depth)
    stack, stack_evidence = classify_stack(signals, args.stack)
    migration = classify_migration(signals, args.migration_type)

    payload = {
        "project_profile": {
            "project_root": str(signals.project_root),
            "git_root": str(signals.git_root),
            "stack": stack,
            "stack_evidence": stack_evidence,
            "workspace_files": [str(path.relative_to(project_root)) for path in signals.workspace_files],
            "ci_files": [str(path.relative_to(project_root)) for path in signals.ci_files],
        },
        "migration_classification": migration,
        "current_structure": build_current_structure(signals),
        "target_structure": build_target_structure(migration["type"], stack, args.target_shape),
        "migration_batches": build_batches(migration["type"], stack),
        "verification_plan": build_verification_plan(stack, signals),
        "risk_register": build_risk_register(migration["type"], signals),
        "forbidden_moves": build_forbidden_moves(),
        "open_questions": build_open_questions(stack, migration, signals),
    }

    json_path = Path(args.json_out) if args.json_out else output_dir / "migration-blueprint.json"
    markdown_path = Path(args.markdown_out) if args.markdown_out else output_dir / "migration-blueprint.md"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(payload), encoding="utf-8")

    print(f"JSON_OUT={json_path}")
    print(f"MARKDOWN_OUT={markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

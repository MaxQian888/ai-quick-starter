#!/usr/bin/env python3
"""Build a guarded project-level i18n support plan."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from pathlib import Path


IGNORED_DIR_NAMES = {
    ".git",
    ".hg",
    ".idea",
    ".next",
    ".nuxt",
    ".pytest_cache",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "out",
    "target",
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
    ".min.js",
    ".min.css",
    ".pdf",
    ".png",
    ".pyc",
    ".pyo",
    ".so",
    ".svg",
    ".webp",
    ".zip",
}
SCAN_EXTENSIONS = {".js", ".jsx", ".mjs", ".ts", ".tsx", ".vue", ".py", ".json", ".toml"}
GENERIC_BLIND_SPOTS = [
    "Static scanning cannot prove runtime locale negotiation, message loading, or end-to-end fallback behavior.",
    "Monorepo package boundaries and custom wrappers may hide the real app owner for i18n bootstrap.",
    "The recommended strategy is intentionally conservative and should not be treated as permission to localize every string in one pass.",
]
SYSTEM_DEFINITIONS = {
    "next-intl": {
        "kind": "hook-based",
        "packages": ("next-intl",),
        "import_patterns": (r"from\s+['\"]next-intl['\"]",),
        "usage_patterns": (
            r"\buseTranslations\s*\(",
            r"\bgetTranslations\s*\(",
            r"NextIntlClientProvider",
        ),
        "path_patterns": (r"(^|/)i18n/request\.(ts|tsx|js|jsx)$", r"(^|/)messages?/"),
        "forbid": ("react-i18next", "react-intl", "vue-i18n"),
    },
    "react-i18next": {
        "kind": "hook-based",
        "packages": ("react-i18next", "i18next"),
        "import_patterns": (r"from\s+['\"]react-i18next['\"]",),
        "usage_patterns": (
            r"\buseTranslation\s*\(",
            r"<Trans\b",
            r"\bi18n\.t\s*\(",
        ),
        "path_patterns": (r"(^|/)i18n\.(ts|tsx|js|jsx)$", r"(^|/)locales?/"),
        "forbid": ("next-intl", "react-intl", "vue-i18n"),
    },
    "react-intl": {
        "kind": "hook-based",
        "packages": ("react-intl",),
        "import_patterns": (r"from\s+['\"]react-intl['\"]",),
        "usage_patterns": (
            r"\buseIntl\s*\(",
            r"FormattedMessage",
            r"\bformatMessage\s*\(",
        ),
        "path_patterns": (),
        "forbid": ("next-intl", "react-i18next", "vue-i18n"),
    },
    "vue-i18n": {
        "kind": "hook-based",
        "packages": ("vue-i18n",),
        "import_patterns": (r"from\s+['\"]vue-i18n['\"]",),
        "usage_patterns": (
            r"\buseI18n\s*\(",
            r"\$t\s*\(",
        ),
        "path_patterns": (),
        "forbid": ("next-intl", "react-i18next", "react-intl"),
    },
    "gettext": {
        "kind": "function-based",
        "packages": (),
        "import_patterns": (r"\bfrom\s+gettext\s+import\b", r"\bimport\s+gettext\b"),
        "usage_patterns": (
            r"\bgettext\s*\(",
            r"\b_\s*\(\s*['\"]",
        ),
        "path_patterns": (r"\.po$", r"\.mo$"),
        "forbid": ("next-intl", "react-i18next", "react-intl", "vue-i18n"),
    },
}
CUSTOM_SYSTEM_HINTS = {
    "kind": "custom",
    "import_patterns": (
        r"from\s+['\"][^'\"]*(?:i18n|intl|locale|messages)[^'\"]*['\"]",
        r"from\s+['\"][^'\"]*useI18n[^'\"]*['\"]",
    ),
    "usage_patterns": (
        r"\buseI18n\s*\(",
        r"\buseLocale\s*\(",
        r"\buseTranslations\s*\(",
    ),
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan a repository, detect the existing i18n stack, and emit a guarded project-level plan."
    )
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    parser.add_argument("--markdown-out", default="", help="Explicit output path for Markdown.")
    parser.add_argument("--json-out", default="", help="Explicit output path for JSON.")
    parser.add_argument("--max-files", type=int, default=400, help="Cap matching files scanned.")
    return parser.parse_args(argv)


def resolve_output_path(raw_path: str, suffix: str) -> Path:
    if raw_path:
        output_path = Path(raw_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path

    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="project-i18n-plan-")
    handle.close()
    return Path(handle.name).resolve()


def should_skip_directory(name: str) -> bool:
    return name in IGNORED_DIR_NAMES


def should_skip_file(path: Path) -> bool:
    suffixes = path.suffixes
    if suffixes:
        suffix = "".join(suffixes[-2:]) if len(suffixes) >= 2 else suffixes[-1]
        if suffix in IGNORED_FILE_SUFFIXES or path.suffix in IGNORED_FILE_SUFFIXES:
            return True
    return path.suffix.lower() not in SCAN_EXTENSIONS


def safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def walk_files(root: Path, max_files: int) -> tuple[list[Path], list[dict[str, str]]]:
    matching_files: list[Path] = []
    limits: list[dict[str, str]] = []

    for current_root, dir_names, file_names in os.walk(root):
        dir_names[:] = [name for name in sorted(dir_names) if not should_skip_directory(name)]
        for file_name in sorted(file_names):
            file_path = Path(current_root) / file_name
            if should_skip_file(file_path):
                continue
            matching_files.append(file_path)
            if len(matching_files) >= max_files:
                limits.append(
                    {
                        "kind": "max-files",
                        "detail": f"Stopped after scanning {max_files} matching files.",
                    }
                )
                return matching_files, limits

    return matching_files, limits


def load_package_json(root: Path) -> dict[str, object]:
    manifest_path = root / "package.json"
    if not manifest_path.exists():
        return {}
    try:
        return json.loads(safe_read_text(manifest_path))
    except json.JSONDecodeError:
        return {}


def load_package_names(package_json: dict[str, object]) -> set[str]:
    package_names: set[str] = set()
    for section in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        entries = package_json.get(section, {})
        if isinstance(entries, dict):
            package_names.update(entries.keys())
    return package_names


def detect_project_profile(root: Path, files: list[Path], package_json: dict[str, object]) -> dict[str, object]:
    package_names = load_package_names(package_json)
    runtimes: list[str] = []
    frameworks: list[str] = []
    app_shapes: list[str] = []
    evidence: list[str] = []

    if package_json:
        runtimes.append("node")
        evidence.append("manifest:package.json")
    if (root / "pyproject.toml").exists() or any(path.suffix == ".py" for path in files):
        runtimes.append("python")
        evidence.append("manifest:python")

    if "next" in package_names:
        frameworks.append("nextjs")
        evidence.append("package:next")
    if "react" in package_names:
        frameworks.append("react")
        evidence.append("package:react")
    if "vue" in package_names:
        frameworks.append("vue")
        evidence.append("package:vue")

    if (root / "app").exists():
        app_shapes.append("next-app-router")
        evidence.append("path:app/")
    if (root / "pages").exists():
        app_shapes.append("next-pages-router")
        evidence.append("path:pages/")
    if "vite" in package_names:
        app_shapes.append("vite-spa")
        evidence.append("package:vite")
    if "react-router" in package_names or "react-router-dom" in package_names:
        app_shapes.append("react-router")
        evidence.append("package:react-router")
    if any(path.suffix == ".vue" for path in files):
        app_shapes.append("vue-sfc")
        evidence.append("files:.vue")
    if any(path.suffix == ".py" for path in files):
        app_shapes.append("python-app")
        evidence.append("files:.py")

    if "workspaces" in package_json:
        app_shapes.append("workspace")
        evidence.append("manifest:workspaces")

    return {
        "runtimes": sorted(set(runtimes)),
        "frameworks": sorted(set(frameworks)),
        "app_shapes": sorted(set(app_shapes)),
        "evidence": sorted(set(evidence)),
    }


def score_systems(root: Path, files: list[Path], package_names: set[str]) -> dict[str, dict[str, object]]:
    scores: dict[str, dict[str, object]] = {}
    for name, definition in SYSTEM_DEFINITIONS.items():
        scores[name] = {
            "name": name,
            "kind": definition["kind"],
            "score": 0,
            "evidence": [],
        }

    custom_score = {
        "name": "custom",
        "kind": "custom",
        "score": 0,
        "evidence": [],
    }

    for system_name, definition in SYSTEM_DEFINITIONS.items():
        record = scores[system_name]
        for package_name in definition["packages"]:
            if package_name in package_names:
                record["score"] += 4
                record["evidence"].append(f"package:{package_name}")

    for file_path in files:
        relative_path = file_path.relative_to(root).as_posix()
        text = safe_read_text(file_path)

        for system_name, definition in SYSTEM_DEFINITIONS.items():
            record = scores[system_name]
            if any(re.search(pattern, relative_path) for pattern in definition["path_patterns"]):
                record["score"] += 2
                record["evidence"].append(f"path:{relative_path}")

            for pattern in definition["import_patterns"]:
                if re.search(pattern, text):
                    record["score"] += 3
                    record["evidence"].append(f"import:{relative_path}")
                    break

            for pattern in definition["usage_patterns"]:
                if re.search(pattern, text):
                    record["score"] += 2
                    record["evidence"].append(f"usage:{relative_path}")
                    break

        if any(re.search(pattern, text) for pattern in CUSTOM_SYSTEM_HINTS["import_patterns"]):
            custom_score["score"] += 2
            custom_score["evidence"].append(f"import:{relative_path}")
        if any(re.search(pattern, text) for pattern in CUSTOM_SYSTEM_HINTS["usage_patterns"]):
            custom_score["score"] += 2
            custom_score["evidence"].append(f"usage:{relative_path}")

    if custom_score["score"] > 0:
        scores["custom"] = custom_score

    return scores


def select_system(scores: dict[str, dict[str, object]]) -> tuple[dict[str, object], list[dict[str, object]]]:
    candidates = sorted(
        (
            {
                "name": record["name"],
                "kind": record["kind"],
                "score": record["score"],
                "evidence": sorted(set(record["evidence"]))[:8],
            }
            for record in scores.values()
            if int(record["score"]) > 0
        ),
        key=lambda item: (-int(item["score"]), item["name"]),
    )

    if not candidates:
        return (
            {
                "name": "unknown",
                "kind": "unknown",
                "score": 0,
                "confidence": "low",
                "notes": "No strong i18n framework signal was detected.",
                "evidence": [],
            },
            [],
        )

    selected = dict(candidates[0])
    second = candidates[1] if len(candidates) > 1 else None

    if second and second["name"] != "custom" and (
        int(second["score"]) >= 6
        or (
            int(second["score"]) >= 4
            and int(selected["score"]) - int(second["score"]) <= 3
        )
    ):
        selected["confidence"] = "low"
        selected["notes"] = (
            f"Detection is ambiguous between {selected['name']} and {second['name']}. "
            "Do not introduce or normalize i18n code until a human confirms the intended stack."
        )
    elif int(selected["score"]) >= 7:
        selected["confidence"] = "high"
        selected["notes"] = f"Strong repository-wide evidence points to {selected['name']}."
    else:
        selected["confidence"] = "medium"
        selected["notes"] = f"Some repository evidence points to {selected['name']}."

    return selected, candidates


def build_strategy_options(profile: dict[str, object], selected_system: dict[str, object]) -> list[dict[str, str]]:
    frameworks = set(profile["frameworks"])
    runtimes = set(profile["runtimes"])
    options: list[dict[str, str]] = []

    if selected_system["name"] != "unknown":
        options.append(
            {
                "system": str(selected_system["name"]),
                "fit": "highest",
                "reason": "Existing repository evidence should outrank greenfield framework selection.",
            }
        )
    if "nextjs" in frameworks:
        options.append(
            {
                "system": "next-intl",
                "fit": "high",
                "reason": "Repository profile indicates Next.js routing and server/client locale coordination.",
            }
        )
    if "react" in frameworks and "nextjs" not in frameworks:
        options.append(
            {
                "system": "react-i18next",
                "fit": "high",
                "reason": "Repository profile indicates a React client surface without Next.js locale wiring.",
            }
        )
    if "vue" in frameworks:
        options.append(
            {
                "system": "vue-i18n",
                "fit": "high",
                "reason": "Repository profile indicates Vue components and standard Vue i18n wiring.",
            }
        )
    if runtimes == {"python"}:
        options.append(
            {
                "system": "gettext",
                "fit": "medium",
                "reason": "Repository profile indicates a Python-only surface where gettext catalogs are the conservative default.",
            }
        )

    seen: set[str] = set()
    deduped: list[dict[str, str]] = []
    for option in options:
        if option["system"] in seen:
            continue
        seen.add(option["system"])
        deduped.append(option)
    return deduped


def recommend_strategy(
    profile: dict[str, object],
    selected_system: dict[str, object],
) -> dict[str, str]:
    frameworks = set(profile["frameworks"])
    runtimes = set(profile["runtimes"])

    if selected_system["confidence"] in {"high", "medium"} and selected_system["name"] != "unknown":
        return {
            "mode": "extend-existing",
            "system": str(selected_system["name"]),
            "confidence": str(selected_system["confidence"]),
            "rationale": f"Reuse the detected {selected_system['name']} stack and avoid creating a parallel localization system.",
        }

    if selected_system["confidence"] == "low" and selected_system["name"] != "unknown":
        return {
            "mode": "blocked",
            "system": str(selected_system["name"]),
            "confidence": "low",
            "rationale": selected_system["notes"],
        }

    if "workspace" in profile["app_shapes"] and len(frameworks) > 1:
        return {
            "mode": "blocked",
            "system": "unknown",
            "confidence": "low",
            "rationale": "Workspace-style repository with multiple app surfaces detected. Identify the owner app before wiring i18n.",
        }

    if len(frameworks) > 1 and "nextjs" not in frameworks:
        return {
            "mode": "blocked",
            "system": "unknown",
            "confidence": "low",
            "rationale": "Multiple frontend frameworks were detected. Scope the target app before choosing an i18n system.",
        }

    if "nextjs" in frameworks:
        return {
            "mode": "introduce-new",
            "system": "next-intl",
            "confidence": "medium",
            "rationale": "No existing stack was detected and the repository profile points to Next.js as the primary surface.",
        }
    if "react" in frameworks:
        return {
            "mode": "introduce-new",
            "system": "react-i18next",
            "confidence": "medium",
            "rationale": "No existing stack was detected and the repository profile points to a React client surface.",
        }
    if "vue" in frameworks:
        return {
            "mode": "introduce-new",
            "system": "vue-i18n",
            "confidence": "medium",
            "rationale": "No existing stack was detected and the repository profile points to Vue.",
        }
    if runtimes == {"python"}:
        return {
            "mode": "introduce-new",
            "system": "gettext",
            "confidence": "medium",
            "rationale": "No existing stack was detected and the repository appears to be Python-only.",
        }

    return {
        "mode": "blocked",
        "system": "unknown",
        "confidence": "low",
        "rationale": "Repository shape is insufficiently clear to choose a safe project-level i18n system automatically.",
    }


def build_adoption_plan(strategy: dict[str, str], profile: dict[str, object]) -> list[dict[str, str]]:
    mode = strategy["mode"]
    system = strategy["system"]
    target_surface = "one representative app flow"
    if "next-app-router" in profile["app_shapes"] or "next-pages-router" in profile["app_shapes"]:
        target_surface = "one representative route or page"
    elif "vue-sfc" in profile["app_shapes"]:
        target_surface = "one representative page or component cluster"

    if mode == "blocked":
        return [
            {
                "step": "1",
                "action": "Confirm the owner app, intended i18n stack, and bootstrap entrypoint with a human.",
                "rationale": strategy["rationale"],
            }
        ]

    bootstrap_action = {
        "next-intl": "Wire request or routing locale bootstrap and add one message source.",
        "react-i18next": "Create the i18n bootstrap module and register one locale namespace.",
        "vue-i18n": "Create the Vue i18n instance and register one locale message bundle.",
        "gettext": "Create or confirm gettext catalog wiring and one locale catalog.",
    }.get(system, "Create the bootstrap and one locale source.")

    return [
        {
            "step": "1",
            "action": "Confirm the target app surface and existing localized seams nearby.",
            "rationale": "Project-level enablement should start with the real owner app, not every package at once.",
        },
        {
            "step": "2",
            "action": bootstrap_action,
            "rationale": f"This establishes the {system} foundation without a broad rewrite.",
        },
        {
            "step": "3",
            "action": f"Localize {target_surface} and reuse the same namespace or key style consistently.",
            "rationale": "A narrow first slice surfaces provider, routing, and fallback issues early.",
        },
        {
            "step": "4",
            "action": "Expand only after runtime and test verification pass for the first slice.",
            "rationale": "Project-wide localization should widen after the bootstrap contract is proven.",
        },
    ]


def build_verification_plan(strategy: dict[str, str]) -> list[dict[str, str]]:
    plan = [
        {
            "phase": "bootstrap",
            "check": "Verify the app boots with the new or reused locale bootstrap and no missing-provider errors.",
        },
        {
            "phase": "messages",
            "check": "Verify one locale loads correctly and unresolved message keys are visible during testing.",
        },
        {
            "phase": "fallback",
            "check": "Verify fallback locale behavior or default language selection works as intended.",
        },
    ]

    if strategy["mode"] != "blocked":
        plan.append(
            {
                "phase": "representative-flow",
                "check": "Verify one representative route, page, or component flow renders translated content end to end.",
            }
        )

    return plan


def build_forbidden_actions(
    profile: dict[str, object],
    selected_system: dict[str, object],
    strategy: dict[str, str],
    candidates: list[dict[str, object]],
) -> list[str]:
    if strategy["mode"] == "blocked":
        if selected_system["confidence"] == "low" and candidates:
            names = ", ".join(candidate["name"] for candidate in candidates[:2])
            return [
                f"Do not introduce or normalize to a framework before resolving the ambiguous signals: {names}.",
                "Do not add a repository-wide locale bootstrap until the owner app is confirmed.",
            ]
        return [
            "Do not pick an i18n framework until the target app surface is identified more precisely.",
            "Do not start a repository-wide string conversion from this report alone.",
        ]

    forbidden = [
        "Do not bulk-localize every file in one pass after adding the bootstrap.",
        "Do not create a second locale tree or message registry parallel to the chosen system.",
    ]

    definition = SYSTEM_DEFINITIONS.get(strategy["system"])
    if definition:
        for framework_name in definition["forbid"]:
            forbidden.append(
                f"Do not introduce {framework_name} when the recommended path is {strategy['system']}."
            )

    if "workspace" in profile["app_shapes"]:
        forbidden.append("Do not assume every workspace package should share the same i18n bootstrap.")

    return forbidden


def build_report(
    root: Path,
    profile: dict[str, object],
    selected_system: dict[str, object],
    candidates: list[dict[str, object]],
    strategy: dict[str, str],
    options: list[dict[str, str]],
    adoption_plan: list[dict[str, str]],
    verification_plan: list[dict[str, str]],
    forbidden_actions: list[str],
    limits: list[dict[str, str]],
) -> dict[str, object]:
    return {
        "root": str(root),
        "project_profile": profile,
        "selected_system": selected_system,
        "detected_systems": candidates,
        "recommended_strategy": strategy,
        "strategy_options": options,
        "adoption_plan": adoption_plan,
        "verification_plan": verification_plan,
        "forbidden_actions": forbidden_actions,
        "limits": limits,
        "blind_spots": GENERIC_BLIND_SPOTS,
        "suggested_next_reads": [
            "Inspect one existing app entrypoint, provider boundary, or route bootstrap before editing many files.",
            "Read the official framework docs only after the local stack and target app are confirmed.",
        ],
    }


def render_markdown(report: dict[str, object]) -> str:
    lines: list[str] = []
    lines.append("# Project I18n Support Plan")
    lines.append("")
    lines.append("## Request")
    lines.append(f"- root: `{report['root']}`")
    lines.append("")
    lines.append("## Project Profile")
    profile = report["project_profile"]
    lines.append(f"- runtimes: {', '.join(f'`{item}`' for item in profile['runtimes']) or '`unknown`'}")
    lines.append(f"- frameworks: {', '.join(f'`{item}`' for item in profile['frameworks']) or '`unknown`'}")
    lines.append(f"- app_shapes: {', '.join(f'`{item}`' for item in profile['app_shapes']) or '`unknown`'}")
    if profile["evidence"]:
        lines.append("- evidence:")
        for evidence in profile["evidence"]:
            lines.append(f"  - `{evidence}`")
    lines.append("")
    lines.append("## Detected I18n System")
    selected = report["selected_system"]
    lines.append(f"- selected: `{selected['name']}`")
    lines.append(f"- confidence: `{selected['confidence']}`")
    lines.append(f"- notes: {selected['notes']}")
    if selected["evidence"]:
        lines.append("- evidence:")
        for evidence in selected["evidence"]:
            lines.append(f"  - `{evidence}`")
    lines.append("")
    lines.append("## Recommended Strategy")
    strategy = report["recommended_strategy"]
    lines.append(f"- mode: `{strategy['mode']}`")
    lines.append(f"- system: `{strategy['system']}`")
    lines.append(f"- confidence: `{strategy['confidence']}`")
    lines.append(f"- rationale: {strategy['rationale']}")
    if report["strategy_options"]:
        lines.append("- options:")
        for option in report["strategy_options"]:
            lines.append(f"  - `{option['system']}` ({option['fit']}): {option['reason']}")
    lines.append("")
    lines.append("## Adoption Plan")
    for step in report["adoption_plan"]:
        lines.append(f"- Step {step['step']}: {step['action']}")
        lines.append(f"  - reason: {step['rationale']}")
    lines.append("")
    lines.append("## Verification Plan")
    for step in report["verification_plan"]:
        lines.append(f"- `{step['phase']}`: {step['check']}")
    lines.append("")
    lines.append("## Forbidden Actions")
    for action in report["forbidden_actions"]:
        lines.append(f"- {action}")
    lines.append("")
    lines.append("## Blind Spots")
    for item in report["blind_spots"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Suggested Next Reads")
    for item in report["suggested_next_reads"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if not root.exists():
        print(f"[ERROR] root does not exist: {root}")
        return 1

    files, limits = walk_files(root, args.max_files)
    package_json = load_package_json(root)
    package_names = load_package_names(package_json)
    profile = detect_project_profile(root, files, package_json)
    scores = score_systems(root, files, package_names)
    selected_system, candidates = select_system(scores)
    strategy = recommend_strategy(profile, selected_system)
    options = build_strategy_options(profile, selected_system)
    adoption_plan = build_adoption_plan(strategy, profile)
    verification_plan = build_verification_plan(strategy)
    forbidden_actions = build_forbidden_actions(profile, selected_system, strategy, candidates)
    report = build_report(
        root=root,
        profile=profile,
        selected_system=selected_system,
        candidates=candidates,
        strategy=strategy,
        options=options,
        adoption_plan=adoption_plan,
        verification_plan=verification_plan,
        forbidden_actions=forbidden_actions,
        limits=limits,
    )

    markdown_out = resolve_output_path(args.markdown_out, ".md")
    json_out = resolve_output_path(args.json_out, ".json")
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    json_out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"MARKDOWN_OUT={markdown_out}")
    print(f"JSON_OUT={json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

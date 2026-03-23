#!/usr/bin/env python3
"""Detect React project layout and recommend split destinations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


FEATURE_DIR_NAMES = ("features", "modules", "domains")
LAYER_DIR_NAMES = ("components", "hooks", "services", "utils", "lib")


def read_package_json(root: Path) -> dict:
    package_path = root / "package.json"
    if not package_path.exists():
        return {}
    try:
        return json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def has_any_path(paths: Iterable[Path]) -> bool:
    return any(path.exists() for path in paths)


def detect_source_root(root: Path) -> Path:
    src = root / "src"
    return src if src.exists() else root


def detect_framework(package_data: dict) -> str:
    deps = {}
    deps.update(package_data.get("dependencies", {}))
    deps.update(package_data.get("devDependencies", {}))
    if "next" in deps:
        return "nextjs"
    if "react" in deps:
        return "react"
    return "unknown"


def detect_router(root: Path, source_root: Path, framework: str) -> str:
    app_candidates = [source_root / "app", root / "app"]
    pages_candidates = [source_root / "pages", root / "pages"]
    has_app = has_any_path(app_candidates)
    has_pages = has_any_path(pages_candidates)

    if framework != "nextjs":
        return "none"
    if has_app and has_pages:
        return "mixed-app-pages"
    if has_app:
        return "app-router"
    if has_pages:
        return "pages-router"
    return "unknown"


def detect_architecture(source_root: Path) -> str:
    feature_hits = [name for name in FEATURE_DIR_NAMES if (source_root / name).exists()]
    layer_hits = [name for name in LAYER_DIR_NAMES if (source_root / name).exists()]
    if feature_hits and layer_hits:
        return "mixed"
    if feature_hits:
        return "feature-first"
    if layer_hits:
        return "layer-first"
    return "unknown"


def find_first(root: Path, patterns: list[str]) -> str | None:
    for pattern in patterns:
        for _ in root.rglob(pattern):
            return pattern
    return None


def has_named_dir(root: Path, name: str) -> bool:
    for entry in root.rglob(name):
        if entry.is_dir():
            return True
    return False


def detect_style(root: Path, source_root: Path, package_data: dict) -> str:
    deps = {}
    deps.update(package_data.get("dependencies", {}))
    deps.update(package_data.get("devDependencies", {}))

    if (root / "tailwind.config.js").exists() or (root / "tailwind.config.ts").exists():
        return "tailwind"
    if "@emotion/react" in deps:
        return "emotion"
    if "styled-components" in deps:
        return "styled-components"
    if find_first(source_root, ["*.module.css", "*.module.scss", "*.module.sass"]):
        return "css-modules"
    if find_first(source_root, ["*.scss", "*.sass"]):
        return "scss"
    if find_first(source_root, ["*.css"]):
        return "css"
    return "unknown"


def detect_test_layout(source_root: Path) -> str:
    has_tests_dir = has_named_dir(source_root, "__tests__")
    has_colocated = find_first(
        source_root,
        ["*.test.tsx", "*.test.ts", "*.spec.tsx", "*.spec.ts", "*.test.jsx", "*.spec.jsx"],
    )
    if has_tests_dir and has_colocated:
        return "mixed"
    if has_colocated:
        return "co-located"
    if has_tests_dir:
        return "__tests__"
    return "unknown"


def nearest_feature_dir(target: Path, source_root: Path) -> str | None:
    current = target.resolve()
    source_resolved = source_root.resolve()
    while current != current.parent:
        if current.parent.name in FEATURE_DIR_NAMES:
            return str(current)
        if current == source_resolved:
            break
        current = current.parent
    return None


def nearest_route_dir(target: Path) -> str | None:
    current = target.resolve()
    while current != current.parent:
        page_file = current / "page.tsx"
        layout_file = current / "layout.tsx"
        page_jsx = current / "page.jsx"
        if page_file.exists() or layout_file.exists() or page_jsx.exists():
            return str(current)
        current = current.parent
    return None


def recommend_paths(
    source_root: Path, architecture: str, router: str, target: Path | None
) -> dict[str, str]:
    if architecture == "feature-first":
        if target:
            feature_dir = nearest_feature_dir(target.parent, source_root)
            if feature_dir:
                feature_path = Path(feature_dir)
                return {
                    "components": str(feature_path / "components"),
                    "hooks": str(feature_path / "hooks"),
                    "utils": str(feature_path / "utils"),
                    "types": str(feature_path / "types"),
                }
        base = source_root / "features"
        return {
            "components": str(base / "<feature>" / "components"),
            "hooks": str(base / "<feature>" / "hooks"),
            "utils": str(base / "<feature>" / "utils"),
            "types": str(base / "<feature>" / "types"),
        }

    if router == "app-router" and target:
        route_dir = nearest_route_dir(target.parent)
        if route_dir:
            route_path = Path(route_dir)
            return {
                "components": str(route_path / "components"),
                "hooks": str(route_path / "hooks"),
                "utils": str(route_path / "utils"),
                "types": str(route_path / "types.ts"),
            }

    return {
        "components": str(source_root / "components"),
        "hooks": str(source_root / "hooks"),
        "utils": str(source_root / "utils"),
        "types": str(source_root / "types"),
    }


def build_evidence(
    framework: str,
    router: str,
    source_root: Path,
    architecture: str,
    style: str,
    test_layout: str,
) -> list[str]:
    evidence = [
        f"framework={framework}",
        f"router={router}",
        f"source_root={source_root}",
        f"architecture={architecture}",
        f"style={style}",
        f"test_layout={test_layout}",
    ]
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect React project structure and recommend split destinations."
    )
    parser.add_argument("--root", default=".", help="Project root path")
    parser.add_argument(
        "--target",
        default=None,
        help="Path to the large component being split (optional, relative to root or absolute)",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    package_data = read_package_json(root)
    source_root = detect_source_root(root)
    framework = detect_framework(package_data)
    router = detect_router(root, source_root, framework)
    architecture = detect_architecture(source_root)
    style = "unknown" if framework == "unknown" else detect_style(root, source_root, package_data)
    test_layout = detect_test_layout(source_root)

    target_path = None
    if args.target:
        candidate = Path(args.target)
        target_path = candidate if candidate.is_absolute() else (root / candidate)
        target_path = target_path.resolve()

    recommendations = recommend_paths(source_root, architecture, router, target_path)
    evidence = build_evidence(framework, router, source_root, architecture, style, test_layout)

    result = {
        "root": str(root),
        "framework": framework,
        "router": router,
        "source_root": str(source_root),
        "architecture": architecture,
        "style": style,
        "test_layout": test_layout,
        "recommendations": recommendations,
        "evidence": evidence,
    }

    if args.pretty:
        print(json.dumps(result, indent=2, ensure_ascii=True))
    else:
        print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

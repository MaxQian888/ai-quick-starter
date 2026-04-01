#!/usr/bin/env python3
"""Detect project context for component reorganization planning."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


FEATURE_DIR_NAMES = ("features", "modules", "domains")
LAYER_DIR_NAMES = ("components", "hooks", "utils", "lib", "services")
ROUTE_MARKER_FILES = (
    "page.tsx",
    "page.jsx",
    "layout.tsx",
    "layout.jsx",
    "route.ts",
    "route.js",
    "loading.tsx",
    "error.tsx",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detect React or Next.js repository structure for component reorganization planning."
    )
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--target", required=True, help="Target component directory or file.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    return parser.parse_args()


def read_package_json(root: Path) -> dict[str, object]:
    package_path = root / "package.json"
    if not package_path.exists():
        return {}
    try:
        return json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def detect_source_root(root: Path) -> Path:
    src = root / "src"
    return src if src.exists() else root


def detect_framework(package_data: dict[str, object]) -> str:
    deps: dict[str, str] = {}
    for section in ("dependencies", "devDependencies", "peerDependencies"):
        section_data = package_data.get(section, {})
        if isinstance(section_data, dict):
            deps.update({str(key): str(value) for key, value in section_data.items()})
    if "next" in deps:
        return "nextjs"
    if "react" in deps:
        return "react"
    return "unknown"


def detect_router(root: Path, source_root: Path, framework: str) -> str:
    if framework != "nextjs":
        return "none"
    has_src_app = (source_root / "app").exists()
    has_root_app = (root / "app").exists()
    has_src_pages = (source_root / "pages").exists()
    has_root_pages = (root / "pages").exists()
    has_app = has_src_app or has_root_app
    has_pages = has_src_pages or has_root_pages
    if has_app and has_pages:
        return "mixed-app-pages"
    if has_app:
        return "app-router"
    if has_pages:
        return "pages-router"
    return "unknown"


def find_nearest_feature_root(target: Path, source_root: Path) -> Path | None:
    source_resolved = source_root.resolve()
    current = target.resolve()
    if current.is_file():
        current = current.parent
    while True:
        parent = current.parent
        if parent.name in FEATURE_DIR_NAMES:
            return current
        if current == source_resolved or current == current.parent:
            return None
        current = parent


def find_nearest_route_root(target: Path, source_root: Path, router: str) -> Path | None:
    if router not in {"app-router", "pages-router", "mixed-app-pages"}:
        return None
    current = target.resolve()
    if current.is_file():
        current = current.parent
    while True:
        if any((current / marker).exists() for marker in ROUTE_MARKER_FILES):
            return current
        if current.name in {"app", "pages"}:
            return None
        if current == source_root.resolve() or current == current.parent:
            return None
        current = current.parent


def detect_structure_mode(
    source_root: Path,
    target: Path,
    feature_root: Path | None,
    route_root: Path | None,
) -> str:
    if feature_root is not None:
        return "feature-first"
    if route_root is not None:
        return "route-first"

    feature_hits = [name for name in FEATURE_DIR_NAMES if (source_root / name).exists()]
    layer_hits = [name for name in LAYER_DIR_NAMES if (source_root / name).exists()]

    if feature_hits and layer_hits:
        return "mixed"
    if feature_hits:
        return "feature-first"
    if layer_hits:
        return "layer-first"
    return "unknown"


def relative_path(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def recommend_paths(
    root: Path,
    source_root: Path,
    target: Path,
    structure_mode: str,
    feature_root: Path | None,
    route_root: Path | None,
) -> dict[str, str]:
    target_dir = target if target.is_dir() else target.parent

    if structure_mode == "feature-first" and feature_root is not None:
        return {
            "components": relative_path(root, target_dir),
            "hooks": relative_path(root, feature_root / "hooks"),
            "utils": relative_path(root, feature_root / "utils"),
            "types": relative_path(root, feature_root / "types"),
            "tests": relative_path(root, feature_root / "components"),
        }

    if structure_mode == "route-first" and route_root is not None:
        return {
            "components": relative_path(root, target_dir),
            "hooks": relative_path(root, route_root / "hooks"),
            "utils": relative_path(root, route_root / "utils"),
            "types": relative_path(root, route_root / "types.ts"),
            "tests": relative_path(root, target_dir),
        }

    if structure_mode in {"layer-first", "mixed"}:
        return {
            "components": relative_path(root, target_dir),
            "hooks": relative_path(root, source_root / "hooks"),
            "utils": relative_path(root, source_root / "utils"),
            "types": relative_path(root, source_root / "types"),
            "tests": relative_path(root, target_dir),
        }

    return {
        "components": relative_path(root, target_dir),
        "hooks": relative_path(root, target_dir),
        "utils": relative_path(root, target_dir),
        "types": relative_path(root, target_dir),
        "tests": relative_path(root, target_dir),
    }


def build_evidence(
    framework: str,
    router: str,
    source_root: Path,
    structure_mode: str,
    recommended_paths: dict[str, str],
) -> list[str]:
    evidence = [
        f"framework={framework}",
        f"router={router}",
        f"source_root={source_root.as_posix()}",
        f"structure_mode={structure_mode}",
    ]
    evidence.extend(f"{key}={value}" for key, value in sorted(recommended_paths.items()))
    return evidence


def analyze_context(root_path: str | Path, target_path: str | Path) -> dict[str, object]:
    root = Path(root_path).resolve()
    target_candidate = Path(target_path)
    target = target_candidate if target_candidate.is_absolute() else (root / target_candidate)
    target = target.resolve()
    if not root.exists():
        raise FileNotFoundError(f"Repository root does not exist: {root}")
    if not target.exists():
        raise FileNotFoundError(f"Target does not exist: {target}")

    package_data = read_package_json(root)
    source_root = detect_source_root(root)
    framework = detect_framework(package_data)
    router = detect_router(root, source_root, framework)
    feature_root = find_nearest_feature_root(target, source_root)
    route_root = find_nearest_route_root(target, source_root, router)
    structure_mode = detect_structure_mode(source_root, target, feature_root, route_root)
    recommended_paths = recommend_paths(root, source_root, target, structure_mode, feature_root, route_root)

    return {
        "root": str(root),
        "target": relative_path(root, target),
        "framework": framework,
        "router": router,
        "source_root": relative_path(root, source_root),
        "feature_root": relative_path(root, feature_root) if feature_root else "",
        "route_root": relative_path(root, route_root) if route_root else "",
        "structure_mode": structure_mode,
        "recommended_paths": recommended_paths,
        "evidence": build_evidence(framework, router, source_root, structure_mode, recommended_paths),
    }


def main() -> int:
    args = parse_args()
    try:
        payload = analyze_context(args.root, args.target)
    except FileNotFoundError as exc:
        print(f"[ERROR] {exc}")
        return 1

    if args.pretty:
        print(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

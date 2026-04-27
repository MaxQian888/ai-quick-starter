from __future__ import annotations

import argparse
import json
from pathlib import Path

STACK_MARKERS = {
    "package.json": "node",
    "pnpm-lock.yaml": "pnpm",
    "bun.lockb": "bun",
    "pyproject.toml": "python",
    "requirements.txt": "python",
    "Cargo.toml": "rust",
    "go.mod": "go",
}

CANDIDATE_ROOTS = ("src", "apps", "packages", "tests", "scripts", "docs")
SKIP_DIR_NAMES = {
    ".git",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".cache",
    ".uv-cache",
    ".uv-cache-codex",
    ".uv-cache-local",
    ".codex-uv-cache",
    ".uv-python",
    "tmp",
}
ALLOWED_HIDDEN_DIRS = {".github", ".husky"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize project context for prompt optimization")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--format", default="json", choices=("json", "markdown"))
    parser.add_argument("--max-depth", type=int, default=2)
    parser.add_argument("--include", action="append", default=[], help="Optional path prefixes to prioritize")
    return parser.parse_args()


def normalize(path_text: str) -> str:
    return path_text.replace("\\", "/").strip("/")


def has_prefix(path: str, prefixes: list[str]) -> bool:
    if not prefixes:
        return True
    for prefix in prefixes:
        if path == prefix or path.startswith(prefix + "/"):
            return True
    return False


def relative_depth_for_filters(path: str, prefixes: list[str]) -> int:
    parts = Path(path).parts
    if not prefixes:
        return len(parts)

    matched_depths: list[int] = []
    for prefix in prefixes:
        prefix_parts = Path(prefix).parts
        if parts[: len(prefix_parts)] == prefix_parts:
            matched_depths.append(len(parts) - len(prefix_parts))
    if matched_depths:
        return min(matched_depths)
    return len(parts)


def detect_validation_clues(root: Path, files: list[str]) -> list[str]:
    clues: list[str] = []

    package_json = root / "package.json"
    if package_json.exists():
        try:
            payload = json.loads(package_json.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        scripts = payload.get("scripts") if isinstance(payload, dict) else None
        if isinstance(scripts, dict):
            for key in sorted(scripts.keys()):
                if isinstance(key, str) and key in {"lint", "test", "build", "typecheck", "check"}:
                    clues.append(f"npm:{key}")

    if "pyproject.toml" in files or (root / "pyproject.toml").exists():
        clues.append("python:pyproject")
    if "Cargo.toml" in files or (root / "Cargo.toml").exists():
        clues.append("rust:cargo")
    if "go.mod" in files or (root / "go.mod").exists():
        clues.append("go:go-mod")

    return sorted(set(clues))


def summarize(root: Path, max_depth: int, include: list[str]) -> dict[str, object]:
    include_prefixes = [normalize(p) for p in include if normalize(p)]

    all_files: list[str] = []
    top_level_dirs: list[str] = []

    for item in root.iterdir():
        if item.is_dir():
            if (
                item.name in SKIP_DIR_NAMES
                or item.name.startswith("_tmp")
                or (item.name.startswith(".") and item.name not in ALLOWED_HIDDEN_DIRS)
            ):
                continue
            top_level_dirs.append(item.name)

    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        parts = file_path.relative_to(root).parts
        if any(
            part in SKIP_DIR_NAMES
            or part.startswith("_tmp")
            or (part.startswith(".") and part not in ALLOWED_HIDDEN_DIRS)
            for part in parts[:-1]
        ):
            continue
        rel = normalize(str(file_path.relative_to(root)))
        if not has_prefix(rel, include_prefixes):
            continue
        depth = relative_depth_for_filters(rel, include_prefixes)
        if depth > max_depth:
            continue
        all_files.append(rel)

    all_files = sorted(set(all_files))

    markers: list[dict[str, str]] = []
    stacks: list[str] = []
    for marker, stack in STACK_MARKERS.items():
        if marker in all_files or (root / marker).exists():
            markers.append({"file": marker, "stack": stack})
            stacks.append(stack)

    candidate_paths = []
    for name in CANDIDATE_ROOTS:
        path = root / name
        if path.exists() and path.is_dir():
            candidate_paths.append(name)

    docs = [p for p in all_files if p.lower().startswith("docs/") or p.lower().startswith("readme")]
    validation = detect_validation_clues(root, all_files)

    summary = {
        "root": str(root),
        "top_level_dirs": sorted(top_level_dirs),
        "stack_markers": markers,
        "stacks": sorted(set(stacks)),
        "candidate_source_roots": candidate_paths,
        "validation_clues": validation,
        "notable_docs": docs[:20],
        "include_filters": include_prefixes,
        "scanned_file_count": len(all_files),
    }
    return summary


def render_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Project Context Summary",
        "",
        f"- Root: `{summary['root']}`",
        f"- Scanned file count: {summary['scanned_file_count']}",
        "",
        "## Stacks",
    ]
    stacks = summary.get("stacks", [])
    if stacks:
        for item in stacks:
            lines.append(f"- {item}")
    else:
        lines.append("- (none detected)")

    lines.append("")
    lines.append("## Candidate Source Roots")
    roots = summary.get("candidate_source_roots", [])
    if roots:
        for item in roots:
            lines.append(f"- {item}")
    else:
        lines.append("- (none)")

    lines.append("")
    lines.append("## Validation Clues")
    clues = summary.get("validation_clues", [])
    if clues:
        for item in clues:
            lines.append(f"- {item}")
    else:
        lines.append("- (none)")

    lines.append("")
    lines.append("## Notable Docs")
    docs = summary.get("notable_docs", [])
    if docs:
        for item in docs:
            lines.append(f"- {item}")
    else:
        lines.append("- (none)")

    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Invalid root path: {root}")

    summary = summarize(root=root, max_depth=max(args.max_depth, 0), include=args.include)

    if args.format == "markdown":
        print(render_markdown(summary), end="")
    else:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

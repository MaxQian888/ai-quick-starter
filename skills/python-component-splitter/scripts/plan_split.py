#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


STYLE_FILE_MAP: Dict[str, Dict[str, str]] = {
    "layered": {
        "api": "api.py",
        "services": "services.py",
        "repositories": "repositories.py",
        "models": "models.py",
        "schemas": "schemas.py",
        "validators": "validators.py",
        "commands": "commands.py",
        "queries": "queries.py",
        "domain": "domain.py",
        "config": "config.py",
        "utilities": "utils.py",
    },
    "hexagonal": {
        "api": "interfaces/api.py",
        "services": "application/services.py",
        "repositories": "infrastructure/repositories.py",
        "models": "domain/entities.py",
        "schemas": "interfaces/schemas.py",
        "validators": "application/validators.py",
        "commands": "application/commands.py",
        "queries": "application/queries.py",
        "domain": "domain/core.py",
        "config": "infrastructure/config.py",
        "utilities": "shared/utils.py",
    },
    "package": {
        "api": "api.py",
        "services": "services.py",
        "repositories": "persistence.py",
        "models": "models.py",
        "schemas": "schemas.py",
        "validators": "validators.py",
        "commands": "operations.py",
        "queries": "queries.py",
        "domain": "core.py",
        "config": "config.py",
        "utilities": "utils.py",
    },
}


@dataclass
class Symbol:
    name: str
    kind: str
    line: int
    bucket: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Analyze a large Python module and generate a structure-aware split plan. "
            "Optionally scaffold target files."
        )
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Repository root used to infer architecture style and render relative paths.",
    )
    parser.add_argument(
        "--target",
        required=True,
        help="Path to the oversized Python module to split.",
    )
    parser.add_argument(
        "--component-name",
        help=(
            "Target package directory name. Default: <target_stem>_parts "
            "(avoids import collisions during staged migration)."
        ),
    )
    parser.add_argument(
        "--style",
        choices=["auto", "layered", "hexagonal", "package"],
        default="auto",
        help="Architecture style to map symbols into files.",
    )
    parser.add_argument(
        "--output-format",
        choices=["markdown", "json"],
        default="markdown",
        help="Render plan as markdown or JSON.",
    )
    parser.add_argument(
        "--output",
        help="Optional output file path. If omitted, print to stdout.",
    )
    parser.add_argument(
        "--scaffold",
        action="store_true",
        help="Create directories and placeholder files according to the plan.",
    )
    return parser.parse_args()


def normalize_name(raw: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", raw).strip("_")
    if not cleaned:
        return "component_parts"
    if cleaned[0].isdigit():
        cleaned = f"component_{cleaned}"
    return cleaned.lower()


def resolve_paths(args: argparse.Namespace) -> Tuple[Path, Path, Path]:
    project_root = Path(args.project_root).resolve()
    target = Path(args.target).resolve()
    if not target.exists():
        raise FileNotFoundError(f"Target module does not exist: {target}")
    if target.suffix != ".py":
        raise ValueError(f"Target must be a .py file: {target}")
    component_name = normalize_name(args.component_name or f"{target.stem}_parts")
    package_dir = target.parent / component_name
    return project_root, target, package_dir


def collect_directory_names(root: Path, max_depth: int = 4) -> List[str]:
    names: List[str] = []
    for path in root.rglob("*"):
        if not path.is_dir():
            continue
        try:
            depth = len(path.relative_to(root).parts)
        except ValueError:
            continue
        if depth <= max_depth:
            names.append(path.name.lower())
    return names


def detect_style(project_root: Path, requested_style: str) -> Tuple[str, str]:
    if requested_style != "auto":
        return requested_style, f"Style forced by --style={requested_style}"

    names = set(collect_directory_names(project_root))
    if {"domain", "application", "infrastructure"}.issubset(names):
        return "hexagonal", "Detected domain/application/infrastructure directories"

    layered_markers = {"api", "services", "repositories", "models", "schemas"}
    score = len(layered_markers.intersection(names))
    if score >= 3:
        return "layered", f"Detected {score} layered markers ({', '.join(sorted(layered_markers.intersection(names)))})"

    return "package", "No strong architecture markers found; defaulting to package style"


def classify_class(name: str) -> str:
    lowered = name.lower()
    if "repository" in lowered or lowered.endswith("dao"):
        return "repositories"
    if "service" in lowered or "manager" in lowered:
        return "services"
    if "controller" in lowered or "handler" in lowered or "view" in lowered:
        return "api"
    if "schema" in lowered or "dto" in lowered or "serializer" in lowered:
        return "schemas"
    if "model" in lowered or "entity" in lowered:
        return "models"
    if "config" in lowered or "setting" in lowered:
        return "config"
    if "validator" in lowered:
        return "validators"
    return "domain"


def classify_function(name: str) -> str:
    lowered = name.lower()
    if lowered.startswith(("get_", "list_", "fetch_", "query_", "load_", "read_")):
        return "queries"
    if lowered.startswith(("create_", "update_", "delete_", "save_", "build_", "write_")):
        return "commands"
    if "validate" in lowered or "parse" in lowered or "normalize" in lowered:
        return "validators"
    if "route" in lowered or "endpoint" in lowered or "handler" in lowered:
        return "api"
    return "services"


def classify_assignment(name: str) -> str:
    lowered = name.lower()
    if name.isupper() or "config" in lowered or "setting" in lowered:
        return "config"
    return "utilities"


def extract_symbols(module_path: Path) -> Tuple[List[str], List[Symbol]]:
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(module_path))
    imports: List[str] = []
    symbols: List[Symbol] = []

    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
            continue
        if isinstance(node, ast.ImportFrom):
            base = node.module or ""
            imports.append(f"{'.' * node.level}{base}")
            continue
        if isinstance(node, ast.ClassDef):
            symbols.append(
                Symbol(
                    name=node.name,
                    kind="class",
                    line=node.lineno,
                    bucket=classify_class(node.name),
                )
            )
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(
                Symbol(
                    name=node.name,
                    kind="function",
                    line=node.lineno,
                    bucket=classify_function(node.name),
                )
            )
            continue
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    symbols.append(
                        Symbol(
                            name=target.id,
                            kind="constant",
                            line=node.lineno,
                            bucket=classify_assignment(target.id),
                        )
                    )
            continue
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            symbols.append(
                Symbol(
                    name=node.target.id,
                    kind="constant",
                    line=node.lineno,
                    bucket=classify_assignment(node.target.id),
                )
            )

    return sorted(set(imports)), symbols


def relative_or_absolute(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def build_plan(
    project_root: Path,
    target: Path,
    package_dir: Path,
    style: str,
    style_reason: str,
    imports: Iterable[str],
    symbols: Iterable[Symbol],
) -> Dict[str, object]:
    file_map = STYLE_FILE_MAP[style]
    file_to_symbols: Dict[str, List[Symbol]] = defaultdict(list)
    for symbol in symbols:
        destination = file_map.get(symbol.bucket, file_map["utilities"])
        file_to_symbols[destination].append(symbol)

    if not file_to_symbols:
        file_to_symbols[file_map["utilities"]] = []

    files = []
    for rel_file, grouped_symbols in sorted(file_to_symbols.items()):
        full_path = package_dir / rel_file
        files.append(
            {
                "path": relative_or_absolute(full_path, project_root),
                "symbols": [
                    {
                        "name": symbol.name,
                        "kind": symbol.kind,
                        "line": symbol.line,
                        "bucket": symbol.bucket,
                    }
                    for symbol in grouped_symbols
                ],
            }
        )

    migration_steps = [
        "Create target package and placeholder files.",
        "Move symbols file-by-file, keeping signatures stable.",
        "Add thin compatibility shim in original module that re-exports public API.",
        "Run unit/integration tests after each moved group to isolate regressions.",
        "Update imports in callers in small batches and remove shim when fully migrated.",
    ]

    return {
        "project_root": relative_or_absolute(project_root, project_root),
        "target_module": relative_or_absolute(target, project_root),
        "target_package": relative_or_absolute(package_dir, project_root),
        "detected_style": style,
        "style_reason": style_reason,
        "import_dependencies": list(imports),
        "files": files,
        "migration_steps": migration_steps,
    }


def render_markdown(plan: Dict[str, object]) -> str:
    lines: List[str] = []
    lines.append("# Python Component Split Plan")
    lines.append("")
    lines.append(f"- Target module: `{plan['target_module']}`")
    lines.append(f"- Target package: `{plan['target_package']}`")
    lines.append(f"- Architecture style: `{plan['detected_style']}`")
    lines.append(f"- Style reason: {plan['style_reason']}")
    lines.append("")
    lines.append("## Proposed File Layout")
    lines.append("")

    for file_item in plan["files"]:
        path = file_item["path"]
        symbols = file_item["symbols"]
        lines.append(f"- `{path}`")
        if symbols:
            for symbol in symbols:
                lines.append(
                    f"  - {symbol['kind']} `{symbol['name']}` (line {symbol['line']}, bucket {symbol['bucket']})"
                )
        else:
            lines.append("  - Placeholder module (no direct symbol assignment)")

    lines.append("")
    lines.append("## Migration Steps")
    lines.append("")
    for index, step in enumerate(plan["migration_steps"], start=1):
        lines.append(f"{index}. {step}")

    imports = plan.get("import_dependencies") or []
    if imports:
        lines.append("")
        lines.append("## Imported Modules Snapshot")
        lines.append("")
        for module in imports:
            lines.append(f"- `{module}`")

    return "\n".join(lines).strip() + "\n"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def create_scaffold(plan: Dict[str, object], project_root: Path) -> List[str]:
    created: List[str] = []
    package_dir = (project_root / plan["target_package"]).resolve()
    package_dir.mkdir(parents=True, exist_ok=True)

    init_path = package_dir / "__init__.py"
    if not init_path.exists():
        write_text(
            init_path,
            '"""Split package generated by plan_split.py."""\n\n__all__ = []\n',
        )
        created.append(relative_or_absolute(init_path, project_root))

    for file_item in plan["files"]:
        target_file = (project_root / file_item["path"]).resolve()
        if target_file.exists():
            continue

        symbol_lines = [f"# - {item['kind']}: {item['name']}" for item in file_item["symbols"]]
        body = [
            '"""Placeholder module generated by plan_split.py."""',
            "",
            "# Planned symbols:",
            *symbol_lines,
            "",
            "# TODO: Move implementation from the original module incrementally.",
            "",
        ]
        write_text(target_file, "\n".join(body))
        created.append(relative_or_absolute(target_file, project_root))

    return created


def main() -> int:
    args = parse_args()
    try:
        project_root, target, package_dir = resolve_paths(args)
        style, style_reason = detect_style(project_root, args.style)
        imports, symbols = extract_symbols(target)
        plan = build_plan(
            project_root=project_root,
            target=target,
            package_dir=package_dir,
            style=style,
            style_reason=style_reason,
            imports=imports,
            symbols=symbols,
        )

        if args.scaffold:
            created = create_scaffold(plan, project_root)
            plan["scaffold_created"] = created

        if args.output_format == "json":
            rendered = json.dumps(plan, indent=2, ensure_ascii=False) + "\n"
        else:
            rendered = render_markdown(plan)
            if args.scaffold and plan.get("scaffold_created"):
                rendered += "\n## Scaffold Created\n\n"
                for item in plan["scaffold_created"]:
                    rendered += f"- `{item}`\n"

        if args.output:
            output_path = Path(args.output).resolve()
            write_text(output_path, rendered)
            print(f"Wrote split plan to {output_path}")
        else:
            print(rendered, end="")

        return 0
    except Exception as exc:  # pragma: no cover - CLI guardrail
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

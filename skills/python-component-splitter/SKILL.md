---
name: python-component-splitter
description: Refactor oversized Python modules into project-aligned, maintainable small components with a staged migration plan. Use when users ask to split a large Python file/class/service, modularize monolithic Python code, enforce layered/hexagonal/package architecture that matches existing repository structure, or reduce coupling while preserving compatibility imports.
---

# Python Component Splitter

Split one oversized module into a staged package layout that fits the existing repository style, then keep imports stable until migration completes.

## Quick Start

1. Generate a split plan from the target module.

```bash
uv run --python 3.11 scripts/plan_split.py --project-root . --target src/orders/order_service.py --output-format markdown
```

2. Scaffold placeholder files from the plan.

```bash
uv run --python 3.11 scripts/plan_split.py --project-root . --target src/orders/order_service.py --scaffold --output reports/order_service_split.md
```

3. Move code concern-by-concern, then keep a compatibility shim in the original module.

## Workflow

1. Detect project conventions before editing.
- Reuse existing root (`src/` or repository root).
- Reuse existing style names (`services`, `repositories`, `domain/application/infrastructure`, etc.).

2. Generate and review split plan.
- Run `scripts/plan_split.py` with `--style auto` first.
- If auto-detection disagrees with local conventions, rerun with `--style layered|hexagonal|package`.
- Validate symbol grouping before creating files.

3. Scaffold destination package.
- Run with `--scaffold` to create placeholder modules.
- Keep generated files near the original module to reduce import churn.

4. Execute incremental migration.
- Move stable data models and schemas first.
- Move repository/data-access code next.
- Move service orchestration and API glue last.
- Run tests after each batch to isolate regressions.

5. Preserve compatibility.
- Keep original module file as thin re-export shim.
- Migrate callers in batches.
- Remove shim only when no old imports remain.

## Rules

- Follow current project naming first; treat script output as a starting point, not a hard rule.
- Keep each new module focused on one concern.
- Avoid cross-layer imports that violate current architecture style.
- Keep public API explicit in `__init__.py` when exposing package-level imports.

## References

- Project-style mapping and defaults: `references/project-structure-mapping.md`
- Refactor execution checklist: `references/refactor-checklist.md`
- Planner/scaffolder script: `scripts/plan_split.py`

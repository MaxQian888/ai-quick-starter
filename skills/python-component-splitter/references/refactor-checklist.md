# Refactor Checklist

Use this checklist before, during, and after splitting a large Python component.

## Before Split

1. Confirm target file scope and ownership with user or repo maintainers.
2. Identify external importers of the target module.
3. Decide architecture style (`layered`, `hexagonal`, `package`) from existing project structure.
4. Generate a split plan and verify symbol grouping is reasonable.

## During Split

1. Scaffold destination package files.
2. Move one concern at a time (models first, then repositories/services, then API glue).
3. Keep function signatures and class names stable unless change is explicitly requested.
4. Add transitional imports in original module to preserve compatibility.
5. Execute targeted tests after each movement batch.

## After Split

1. Run full test suite or the broadest available subset.
2. Run static checks (`ruff`, `mypy`, or project equivalent).
3. Search for stale imports to old module path.
4. Update docs or module comments when architecture changes are visible to contributors.
5. Remove compatibility shim only after import migration is complete.

## Common Failure Modes

- Circular imports introduced by moving utilities to the wrong layer.
- Inversion violation (domain depending on infrastructure in hexagonal style).
- Silent behavior drift from moving module-level state/constants.
- Missing `__init__.py` exports causing runtime import breakage.

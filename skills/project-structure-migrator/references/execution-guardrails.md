# Execution Guardrails

Use this file before editing when the migration feels broader than one focused batch.

## Core Rules

- Detect the current repository truth before proposing any destination structure.
- Keep one primary migration concern per batch.
- Preserve build, test, lint, and typecheck integrity while moving structure.
- Record uncertainty instead of bluffing confidence.

## Forbidden Batch Shapes

- directory relocation plus unrelated feature work
- package split plus dependency modernization plus runtime bugfixes in one pass
- removing legacy paths before downstream callers migrate
- broad search-and-replace import rewrites without a rollback point

## Compatibility Rules

- Keep forwarding files, aliases, or shims when imports or entrypoints change.
- Remove compatibility seams only after verification proves they are unused.
- If root scripts move, keep a temporary compatibility command surface until callers migrate.

## Verification Rules

- Re-run the smallest impacted command first.
- Widen only after the narrow check passes.
- Do not claim the final migration succeeded unless the final repository-native chain actually ran.

## Reporting Rules

- Mark observed facts separately from proposed target layout.
- Call out weak evidence in `open_questions` or `risk_register`.
- State clearly what was verified and what remains unverified.

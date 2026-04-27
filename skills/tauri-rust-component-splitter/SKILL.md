---
name: tauri-rust-component-splitter
description: |
  Use whenever you need to split oversized `src-tauri` Rust modules into smaller maintainable components without breaking current seams. Make sure to use this skill whenever the user says "split Rust", "refactor src-tauri", "Tauri backend too big", "modularize Rust", "extract commands", or "clean up lib.rs" — even for partial extractions or when only one concern (like models or errors) should be pulled out. Also trigger when a single Rust file in `src-tauri/src/` exceeds 400 lines, mixes Tauri commands with business logic, or violates the project's established module boundaries. Covers Tauri v2, Tauri v1, and mixed Rust/TypeScript projects.
---

# Tauri Rust Component Splitter

Inspect a `src-tauri` Rust file or module first. Produce a conservative split plan that isolates Tauri commands, services, state, platform adapters, models, and errors into clearer files, then scaffold placeholders only when the plan is accepted.

## Adaptive Detection

Before splitting, detect the Tauri project context:

1. **Tauri version**: Check `src-tauri/Cargo.toml` for `tauri` dependency version (v1 vs v2).
2. **Module structure**: Look for existing `commands/`, `services/`, `models/`, or `state/` directories.
3. **Command registration**: Note how commands are registered in `lib.rs` or `main.rs`.
4. **State management**: Identify if the app uses `tauri::State`, `Mutex`, `Arc`, or custom state patterns.
5. **Error handling**: Check for custom error types and how they are serialized to the frontend.

Use these signals to match the split plan to existing conventions.

## Quick Start

1. Confirm the repository root and exact Rust target inside `src-tauri`.
2. Run the helper script before drafting a split manually.

```bash
python scripts/plan_tauri_rust_split.py --root . --target src-tauri/src/app.rs
```

3. Read the JSON output first.
4. Review `naming_findings`, `proposed_files`, `symbol_plan`, `migration_phases`, and `forbidden_actions`.
5. If the plan looks right and the user wants placeholders, re-run with `--scaffold`.

```bash
python scripts/plan_tauri_rust_split.py --root . --target src-tauri/src/app.rs --scaffold
```

## Workflow

1. Confirm scope before editing.
   - Stay inside `src-tauri`.
   - Prefer one file or one local module directory per pass.
   - Stop if the target is outside `src-tauri` or contains no Rust files.

2. Build the plan before moving code.
   - Use `scripts/plan_tauri_rust_split.py`.
   - Treat script output as a starting point, not a blind rewrite order.
   - Reuse nearby repository conventions before inventing new folders.

3. Review boundaries and naming.
   - Read [references/tauri-boundaries.md](references/tauri-boundaries.md) when deciding whether a symbol belongs in `commands`, `services`, `state`, `platform`, `models`, or `errors`.
   - Read [references/naming-conventions.md](references/naming-conventions.md) when the report flags generic module names or casing problems.

4. Scaffold only approved destinations.
   - Use `--scaffold` only after the proposed layout is accepted.
   - Placeholder files are migration aids, not proof the refactor is finished.
   - Do not overwrite existing implementation files just to match the plan.

5. Defer implementation movement to a later explicit refactor pass.
   - Keep command signatures stable while extracting supporting logic.
   - Move one concern at a time.
   - Run Rust verification after the later migration, not from the planner pass alone.

## What To Review In The Report

- `project_context`: whether the target is a file or directory and which `src-tauri` root it belongs to.
- `naming_findings`: generic module names, bad type casing, bad function casing, and similar smells.
- `proposed_files`: the suggested destination files, grouped by responsibility.
- `symbol_plan`: each detected symbol, its current file, and suggested destination.
- `migration_phases`: a conservative extraction order.
- `scaffold_plan`: the files that would be created if `--scaffold` is used.
- `forbidden_actions`: what this planner explicitly refuses to do.

## Guardrails

- Do not move Rust implementation automatically from this skill alone.
- Do not split by line count alone; split by responsibility and stable seams.
- Do not replace specific concerns with generic `common`, `helpers`, or `utils` buckets.
- Do not claim the Rust refactor is complete without a later code-moving pass plus verification.
- Do not widen a local Tauri backend cleanup into a repository-wide architecture rewrite.

## Examples

### Example 1: Generate a split plan

```bash
python scripts/plan_tauri_rust_split.py --root . --target src-tauri/src/app.rs
```

### Example 2: Scaffold approved destinations

```bash
python scripts/plan_tauri_rust_split.py --root . --target src-tauri/src/app.rs --scaffold
```

## References

- [references/tauri-boundaries.md](references/tauri-boundaries.md): Tauri-oriented split buckets and stop conditions.
- [references/naming-conventions.md](references/naming-conventions.md): Rust naming rules and anti-patterns to fix or avoid.
- [references/output-contract.md](references/output-contract.md): JSON and Markdown fields emitted by the planner.

## Script

- `scripts/plan_tauri_rust_split.py`: Inspect a `src-tauri` Rust target, emit JSON and Markdown split plans, and optionally scaffold placeholder destination files.

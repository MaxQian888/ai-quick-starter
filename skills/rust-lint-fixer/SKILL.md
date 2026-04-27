---
name: rust-lint-fixer
description: |
  Use whenever you need to lint or repair Rust crates or Tauri backends, discover the real Cargo or CI Rust quality gate, fix clippy or rustc warnings without weakening checks, decide whether unused code should be wired in or removed, or verify Rust warnings against current official documentation when behavior is unclear. Make sure to use this skill whenever the user mentions "Rust", "Cargo", "clippy", "rustc", "lint", "warnings", "src-tauri", "Tauri backend", or "fix Rust" — even for a single warning or a small crate. Also trigger when the user needs to understand a Rust compiler error, set up CI for Rust, or choose between workspace-wide and crate-specific lint scopes. Covers single crates, workspaces, Tauri v2 backends, and mixed Rust/frontend projects.
---

# Rust Lint Fixer

## Overview

Discover the repository's real Rust lint surface before editing code. Use the helper script to find `Cargo.toml` targets, choose the right workspace or crate scope, run strict Rust quality gates, and keep unused-code decisions honest.

## Adaptive Detection

Before linting, detect the Rust environment:

1. **Workspace vs single crate**: Check for workspace `Cargo.toml` and member crates.
2. **Tauri project**: Look for `src-tauri/` directory and Tauri-specific dependencies.
3. **CI gate**: Check `.github/workflows/` or other CI for the actual lint commands.
4. **Toolchain**: Note `rust-toolchain.toml` or `rust-toolchain` files.
5. **Test scope**: Determine if tests should be included in lint/fix passes.

Use these signals to choose the narrowest valid target and avoid over-scanning.

## Workflow

1. Confirm the repository root and the requested Rust scope.
2. Run the helper script before editing code.

```bash
python scripts/run_rust_lint_surface.py --root . --mode discover --json
```

3. Read the JSON output first.
4. If the script reports zero Rust targets, stop and report that truthfully.
5. Choose the narrowest recommended target that can reproduce the warning.
6. Run lint mode or verify mode at that scope.

```bash
python scripts/run_rust_lint_surface.py --root . --mode lint --json
python scripts/run_rust_lint_surface.py --root . --target path/to/crate --mode verify --include-tests --json
```

7. Capture the first failing command and fix one warning class or root cause at a time.
8. Re-run the same command before widening verification.

## Scope Rules

- Prefer a member crate over the whole workspace when the warning reproduces there.
- Prefer a workspace root when CI or the repository's real gate clearly lint the full workspace.
- Stop and report when `--target` does not resolve to a crate.
- Treat fixture or example crates as lower-priority unless the user explicitly targets them.

## Unused Code Rules

Default to tracing unused code before deleting it.

Check these paths first:

- missing Tauri command registration,
- missing module exports or `pub use`,
- feature-gated code that should still be wired,
- helpers that exist for an unfinished but real call path,
- tests that should exercise the code but do not.

Only delete unused code when:

- no real call path exists,
- the feature is actually gone,
- wiring it back in would be speculative or incorrect,
- removal is safer than preservation.

Do not normalize blanket `#[allow(dead_code)]`, `#[allow(unused_imports)]`, or crate-wide allow attributes as the default fix.

## Documentation Rules

When warning repair reveals uncertain behavior, check current official documentation before changing code.

Read `references/official-rust-lint-workflow.md` first, then widen only as needed:

- Rust official Cargo docs for `cargo fmt`, `cargo clippy`, and `cargo test`,
- Clippy official docs for lint behavior and command-line configuration,
- docs.rs or official framework docs for crate-specific APIs,
- official Tauri docs when the Rust target is `src-tauri`.

Do not rely on memory or third-party blog posts for version-sensitive behavior.

## Guardrails

- Do not weaken lint levels just to get green output.
- Do not comment out intended behavior to remove warnings.
- Do not claim success from discovery mode alone.
- Do not hide toolchain, permission, lockfile, or cache blockers.
- Do not widen the task into a repository-wide refactor when the failure is local.

## Verification

Before claiming the Rust lint work is complete:

1. Re-run the first failing command successfully.
2. Run the next broader verification command.
3. If requested or if the repository gate requires it, include tests.
4. Report:
   - commands run,
   - exit status,
   - remaining blockers,
   - whether any slice is still unverified.

## Examples

### Example 1: Discover Rust targets

```bash
python scripts/run_rust_lint_surface.py --root . --mode discover --json
```

### Example 2: Fix warnings in a specific crate

```bash
python scripts/run_rust_lint_surface.py --root . --target src-tauri --mode lint --json
```

## References

- `references/official-rust-lint-workflow.md`: official command usage, installation notes, and workspace-scoping reminders.

## Script

- `scripts/run_rust_lint_surface.py`: discover Rust targets, rank recommended commands, and optionally execute lint or verification passes with structured JSON output.

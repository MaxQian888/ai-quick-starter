---
name: configuring-commit-checks
description: Use when Codex needs to inspect an existing repository's commit-hook or pre-commit tooling, preserve and complete the current setup, or choose and configure the most suitable husky or pre-commit style checks when no setup exists.
---

# Configuring Commit Checks

Inspect the repository before changing commit hooks. Prefer the current toolchain when one already exists. Only add a default stack when the repository has no commit-check setup.

## Workflow

1. Locate the real repository root first.
   - Run:
     ```bash
     uv run --python 3.11 scripts/detect_commit_setup.py --project-root . --json
     ```
   - If the current directory is nested inside a repository, use the script's `detected_root` instead of guessing.

2. Read the recommendation before editing files.
   - `preserve-existing`: keep the current primary tool and add only missing pieces.
   - `complete-existing`: finish a partial existing stack.
   - `add-default`: add the default stack for the detected project type.
   - `review-manually`: stop and inspect the repo instead of guessing.

3. Apply the default choice only when no primary hook tool exists.
   - Node-only: use `husky` with `lint-staged`.
   - Python-only: use `pre-commit`.
   - Mixed Node + Python: use `pre-commit` as the top-level orchestrator.

4. Make the smallest compatible change set.
   - If the repo already uses `husky`, extend `.husky/` and related package config.
   - If the repo already uses `pre-commit`, extend `.pre-commit-config.yaml`.
   - If the repo already uses `lefthook`, keep `lefthook.yml` as the entry point.

5. Verify after changes.
   - Run the hook tool's install or validation command.
   - Run the project-native lint, format, typecheck, or test commands the hook will call.
   - Do not claim the setup is complete without fresh verification output.

## Guardrails

- Do not replace `pre-commit` with `husky`, or `husky` with `pre-commit`, unless the user explicitly asks for migration.
- Do not add a second competing hook framework when one already governs commits successfully.
- Do not assume the current working directory is the repository root.
- Do not weaken lint, typecheck, test, or formatting rules just to make hooks pass.
- Do not invent a generic hook stack when the repository already has a local convention.

## References

- Selection rules and defaults: `references/selection-matrix.md`
- Minimal completion patterns: `references/config-patterns.md`
- Detection helper: `scripts/detect_commit_setup.py`

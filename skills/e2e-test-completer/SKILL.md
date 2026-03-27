---
name: e2e-test-completer
description: Use when recent implementation changes may have invalidated Playwright or Cypress style end-to-end tests and Codex needs to discover the real E2E command surface, map changed files to affected user flows, update or add the corresponding E2E specs, raise coverage on uncovered flows, and simulate the safest next E2E run before broader verification.
---

# E2E Test Completer

Sync E2E coverage with the latest implementation truth before touching assertions. Use the helper script to discover the current runner surface, rank affected specs from changed files, highlight uncovered flows, and build a dry-run command plan.

## Workflow

1. Discover the current E2E surface.
   - Run:
     ```bash
     uv run --python 3.11 scripts/build_e2e_change_plan.py --project-root . --mode discover --json
     ```
   - Read `runner.framework`, `runner.primary_command`, `runner.config_paths`, `runner.working_directory`, and `spec_count`.

2. Build a change-driven E2E plan.
   - Prefer explicit changed paths when the user gives them:
     ```bash
     uv run --python 3.11 scripts/build_e2e_change_plan.py --project-root . --mode plan --changed-file src/features/auth/login-form.tsx --json
     ```
   - If the repo is a git checkout and no `--changed-file` values are passed, the helper tries `git status --porcelain` automatically.
   - If you need branch-relative change detection, prefer:
     ```bash
     uv run --python 3.11 scripts/build_e2e_change_plan.py --project-root . --mode plan --git-base origin/main --json
     ```
   - Read `change_reports` first, then `coverage_gaps`.

3. Update the affected E2E specs.
   - Prefer existing Playwright or Cypress conventions, fixtures, page objects, and selectors.
   - Extend an existing spec when the changed flow is already represented there.
   - Create a new spec only when no existing candidate can absorb the new flow cleanly.
   - Cover the happy path plus the highest-risk branch introduced by the implementation change.

4. Simulate the first verification command before widening.
   - Run:
     ```bash
     uv run --python 3.11 scripts/build_e2e_change_plan.py --project-root . --mode simulate --changed-file src/features/auth/login-form.tsx --json
     ```
   - Use `execution_plan.targeted_command` as the first real run candidate.
   - Treat `simulate` as command planning only. It does not prove the suite passed.

5. Run targeted verification, then widen.
   - First run the targeted command suggested by the helper.
   - Only after the targeted scope passes should you run the broader E2E or repo verification path.
   - If the targeted scope fails, fix that root cause before expanding.

## Helper Script

`scripts/build_e2e_change_plan.py` returns one structured report with:

- detected runner surface and main command,
- detected nested app working directory when the E2E stack lives below repo root,
- discovered spec files,
- changed-file to spec ranking using both path tokens and spec content tokens,
- uncovered implementation paths that likely need new or expanded E2E coverage,
- a dry-run execution plan for the smallest useful verification scope.

Useful flags:

- `--changed-file <path>`: repeat for explicit implementation paths.
- `--changed-file-list <file>`: load newline-delimited changes from a file.
- `--git-base <rev>`: use `git diff --name-only <rev>` when branch-relative changes matter more than worktree status.
- `--framework playwright|cypress`: override auto-detection when the repo is mixed or ambiguous.
- `--max-matches <n>`: cap candidate specs per changed file.

## References

- Read `references/change-mapping.md` for the path-token heuristics and how to review false positives.
- Read `references/coverage-playbook.md` for what to add when a flow is only partially covered.
- Read `references/execution-policy.md` before converting a dry-run plan into an actual E2E execution strategy.

## Guardrails

- Do not delete or weaken existing E2E assertions just to make the targeted run pass.
- Do not claim `--mode simulate` means the tests passed. It only proves the command selection and scope mapping are coherent.
- Do not introduce a new E2E runner when the repo already has one.
- Prefer updating existing user-flow specs over creating duplicate parallel suites.
- If the helper returns `overall_status=blocked`, inspect the repo's real manifests and config files before guessing commands.

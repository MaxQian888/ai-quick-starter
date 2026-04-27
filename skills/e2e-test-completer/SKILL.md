---
name: e2e-test-completer
description: Use whenever Playwright or Cypress E2E tests may be broken by code changes, when coverage gaps need closing, or when mapping implementation changes to affected test specs. Make sure to use this skill for end-to-end test repair, test coverage analysis, QA automation updates, UI test synchronization, or planning the safest verification command before running the full suite. Also triggers for test discovery, spec ranking against changed files, dry-run verification planning, or any request involving keeping E2E tests in sync with implementation changes.
---

# E2E Test Completer

Bring E2E tests back in sync with the code before editing assertions. Use the helper script to discover the current runner, rank affected specs from changed files, highlight uncovered flows, and build a dry-run command plan.

## Adaptive Detection

Before planning E2E work, scan the workspace to understand the test setup:

1. Detect the E2E runner:
   - Look for `playwright.config.ts`, `playwright.config.js`, or `@playwright/test` in `package.json`.
   - Look for `cypress.config.ts`, `cypress.config.js`, or `cypress` in `package.json`.
   - Check `package.json` scripts for `test:e2e`, `e2e`, or `playwright` commands.
2. Detect test structure:
   - Look for `e2e/`, `tests/e2e/`, `cypress/`, or `playwright/` directories.
   - Check for existing fixtures, page objects, or support files.
3. Detect app structure:
   - Identify nested app working directories in monorepos.
   - Check for `vite.config.ts`, `next.config.js`, or similar to understand the dev server setup.

## Workflow

1. **Discover the E2E surface.**
   Run:
   ```bash
   uv run --python 3.11 scripts/build_e2e_change_plan.py --project-root . --mode discover --json
   ```
   Read `runner.framework`, `runner.primary_command`, `runner.config_paths`, `runner.working_directory`, and `spec_count`.

2. **Build a change-driven E2E plan.**
   - When the user gives explicit changed paths:
     ```bash
     uv run --python 3.11 scripts/build_e2e_change_plan.py --project-root . --mode plan --changed-file src/features/auth/login-form.tsx --json
     ```
   - If the repo is a git checkout and no `--changed-file` values are passed, the helper runs `git status --porcelain` automatically.
   - For branch-relative change detection, use:
     ```bash
     uv run --python 3.11 scripts/build_e2e_change_plan.py --project-root . --mode plan --git-base origin/main --json
     ```
   - Read `change_reports` first, then `coverage_gaps`.

3. **Update the affected E2E specs.**
   - Follow existing Playwright or Cypress conventions, fixtures, page objects, and selectors.
   - Extend an existing spec when the changed flow is already represented there.
   - Create a new spec only when no existing candidate can absorb the new flow cleanly.
   - Cover the happy path plus the highest-risk branch introduced by the implementation change.

4. **Simulate the first verification command before widening.**
   Run:
   ```bash
   uv run --python 3.11 scripts/build_e2e_change_plan.py --project-root . --mode simulate --changed-file src/features/auth/login-form.tsx --json
   ```
   - Use `execution_plan.targeted_command` as the first real run candidate.
   - `simulate` is command planning only. It does not prove the suite passed.

5. **Run targeted verification, then widen.**
   - Run the targeted command suggested by the helper first.
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

## Examples

### Example 1: Post-Refactor Test Sync

**Input:** "I refactored the auth flow. Update the E2E tests."

**Output:**
- Discovers Playwright or Cypress runner.
- Maps changed auth files to affected specs.
- Updates login/logout specs to match new flow.
- Provides targeted verification command.

### Example 2: Coverage Gap Analysis

**Input:** "What E2E coverage is missing for the checkout feature?"

**Output:**
- Identifies checkout-related implementation files.
- Ranks existing specs by relevance.
- Lists uncovered paths (e.g., error states, payment validation).
- Suggests new spec files or extensions.

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

---
name: local-ci-fixer
description: |
  Use this skill whenever a project uses GitHub Actions and you need to reproduce CI locally, inspect workflow jobs or steps,
  diagnose a failing workflow, or safely repair CI-related code or config issues before push.
  Make sure to use this skill whenever the user mentions GitHub Actions, CI failure, workflow fix, "my tests pass locally but fail in CI",
  local CI reproduction, act (nektos/act), workflow debugging, or pre-push verification.
  Also trigger for requests like "fix my CI", "run this workflow locally", "why is my build failing on GitHub",
  "diagnose the test step", or "simulate CI on my machine". Covers workflow discovery, mode selection (act vs fallback),
  targeted repair, and verification without weakening gates.
---

# Local CI Fixer

Use GitHub Actions workflow files as the source of truth. Start with the helper script so the execution mode, runnable commands, skipped steps, and blockers are explicit before making repairs.

## Adaptive Detection

Before running or fixing CI, detect the project setup:

1. **CI provider**: confirm GitHub Actions (look for `.github/workflows/*.yml` or `.github/workflows/*.yaml`).
2. **Workflow scope**: identify which workflow and job are relevant to the user's issue.
3. **Local tooling**: check if Docker and `act` are available; if not, plan fallback mode.
4. **Project stack**: read `package.json`, `pyproject.toml`, or similar to understand test/lint/build commands.
5. **Failure history**: look at recent workflow runs or error logs the user provides.

## Workflow

1. Run `uv run --python 3.11 scripts/local_ci_gate.py --project-root <repo> --discover-only --json`.
2. If the repository has multiple workflows or jobs, narrow with `--workflow` and `--job`.
3. Run `uv run --python 3.11 scripts/local_ci_gate.py --project-root <repo> --plan-only --json` and read `selected_mode`, `runnable_commands`, `skipped_steps`, and `blockers`.
4. If the plan selects `act`, prefer `uv run --python 3.11 scripts/local_ci_gate.py --project-root <repo> --mode act --json`.
5. Otherwise use `uv run --python 3.11 scripts/local_ci_gate.py --project-root <repo> --mode fallback --json`.
6. Fix the first failing step or command at the root cause.
7. Re-run the failing scope, then re-run the broader local CI path.
8. Report what was verified locally versus what remained skipped or blocked.

## Guardrails

- Do not install Docker, `act`, or other system dependencies without explicit approval.
- Do not weaken lint, typecheck, coverage, or test gates just to make local CI pass.
- Do not edit workflow files merely to make them easier to simulate.
- Do not treat skipped or unsupported steps as passed.
- Keep fixes targeted and preserve unrelated user changes.

## Examples

**Diagnose a failing test step in CI:**
```bash
uv run --python 3.11 scripts/local_ci_gate.py --project-root . --discover-only --json
uv run --python 3.11 scripts/local_ci_gate.py --project-root . --plan-only --json
# Read selected_mode, runnable_commands, skipped_steps, and blockers.
# Fix the root cause of the first failing step, then re-run.
```

**Run CI locally before pushing:**
```bash
uv run --python 3.11 scripts/local_ci_gate.py --project-root . --mode fallback --json
# Verify what passed locally and what was skipped or blocked.
```

## References

- Read `references/execution-policy.md` for mode selection, approval boundaries, and stop conditions.
- Read `references/workflow-mapping.md` when workflow structure or `uses:` steps need interpretation.
- Read `references/repair-guardrails.md` before changing code or configuration to address failures.


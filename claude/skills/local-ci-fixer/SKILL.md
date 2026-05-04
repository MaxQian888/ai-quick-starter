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

Treat `.github/workflows/*.yml` and `*.yaml` as the source of truth. Use the helper script to make execution mode, runnable commands, skipped steps, and blockers explicit before touching anything.

The helper lives at `scripts/local_ci_gate.py` inside this skill folder. Resolve it against the skill's install path (e.g. `~/.claude/skills/local-ci-fixer/scripts/local_ci_gate.py` on Linux/macOS, `%USERPROFILE%/.claude/skills/local-ci-fixer/scripts/local_ci_gate.py` on Windows). Pass the user's repository to `--project-root`.

## Adaptive Detection

Before running or fixing CI, gather context:

1. **CI provider**: confirm GitHub Actions (look for `.github/workflows/*.yml` or `*.yaml`). Other providers fall outside this skill.
2. **Workflow scope**: identify which workflow and job match the user's issue; narrow with `--workflow` and `--job` so you do not run unrelated jobs.
3. **Local tooling**: the script reports whether `act`, Docker, and `git` are available. If `act` or Docker is missing, plan fallback mode and surface that to the user.
4. **Project stack**: read `package.json`, `pyproject.toml`, `Cargo.toml`, etc., so you can interpret what each `run:` step actually does.
5. **Failure history**: read any logs the user pasted and map them back to a specific job/step before guessing.

## Workflow

1. Plan first:
   ```bash
   uv run --python 3.11 <skill-path>/scripts/local_ci_gate.py \
     --project-root <repo> --plan-only --json
   ```
   Read `selected_mode`, `runnable_commands`, `skipped_steps`, and `blockers`. If multiple workflows or jobs exist, rerun with `--workflow <stem-or-name>` and `--job <id-or-name>` to target the relevant scope.
2. Execute with the planned mode (`auto` is the default and resolves to `act` when both `act` and Docker are available, otherwise `fallback`):
   ```bash
   uv run --python 3.11 <skill-path>/scripts/local_ci_gate.py \
     --project-root <repo> --json
   ```
   Add `--fail-fast` when you want to stop at the first failing step instead of continuing.
3. For each failing command, fix the root cause in the user's repository, not the workflow file.
4. Re-run the failing scope first, then the broader local CI path, to confirm the fix did not regress neighbours.
5. Report what was verified locally, what remained skipped (for example unsupported `uses:` actions), and what is genuinely blocked (deploy-only workflows, missing secrets, hosted services).

## Guardrails

- Do not install Docker, `act`, or other system dependencies without explicit user approval.
- Do not weaken lint, typecheck, coverage, or test gates to make local CI green.
- Do not edit workflow files just to make them easier to simulate; fix the underlying code or config instead.
- Do not treat skipped or unsupported steps as passed — surface them.
- Keep fixes targeted and preserve unrelated user changes.

## Examples

**Diagnose a failing test job:**
```bash
uv run --python 3.11 <skill-path>/scripts/local_ci_gate.py \
  --project-root . --workflow ci --job test --plan-only --json
# Then run the same command without --plan-only to actually execute,
# fix the first failing step at the root cause, and re-run.
```

**Pre-push verification when act is unavailable:**
```bash
uv run --python 3.11 <skill-path>/scripts/local_ci_gate.py \
  --project-root . --mode fallback --json
# Report which run: steps passed locally and which uses: steps stayed skipped.
```

## References

- `references/execution-policy.md` — when to choose `act` vs fallback, approval boundaries, stop conditions.
- `references/workflow-mapping.md` — how `run:` and `uses:` steps map to local intent, validation/deploy heuristics.
- `references/repair-guardrails.md` — allowed fixes, forbidden shortcuts, the repair loop.
- `references/linked-skills.md` — when to hand off to `$github-actions-ci-builder` (workflow design) or `$build-project-fixer` (build/test failures).

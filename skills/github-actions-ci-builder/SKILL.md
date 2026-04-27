---
name: github-actions-ci-builder
description: >
  Build, modernize, audit, and orchestrate GitHub Actions CI workflows.
  Use this skill whenever the user mentions CI, continuous integration,
  GitHub Actions, workflow files, `.github/workflows`, action versions,
  deployment automation, build pipelines, or any kind of automated
  testing, linting, building, or releasing on GitHub — even if they
  don't use the exact words "GitHub Actions."
  Also use it for local CI simulation with `act`, workflow splitting,
  governance reviews (permissions, SHA pinning, concurrency), matrix
  strategy design, caching optimization, and creating reusable workflows
  or composite actions.
---

# GitHub Actions CI Builder

## Adaptive Detection

Before planning CI changes, scan for:
- `package.json` / `Cargo.toml` / `pyproject.toml` / `go.mod` to detect the project stack
- Existing `.github/workflows/*.yml` files to understand current CI topology
- Action version patterns (`uses:` entries) that may need updating
- Monorepo signals (`pnpm-workspace.yaml`, `nx.json`, `turbo.json`) for matrix design
- Local simulation tools (`act` installed, Docker available)
- Secret and environment requirements in existing workflows

## Overview

Turn repository reality into a solid CI setup. This skill reads what
already exists — project type, existing workflows, dependencies — and
designs a maintainable CI topology that matches.

Use the **orchestration path** for big-picture work: architecture,
governance, completeness, and performance. Use the **narrow helper
scripts** only when the task is clearly scoped to a single concern
like action version checks, one oversized workflow, or a quick local
run.

## Workflow

1. **Inspect first.** Look at repository manifests (package.json,
   Cargo.toml, pyproject.toml, etc.) and any existing
   `.github/workflows/*.yml` files.

2. **Match the mode.** Choose the narrowest fit:
   - Action version verification
   - Workflow split planning
   - Local CI simulation
   - Full CI orchestration

3. **Run orchestration for broad work.** When the user asks about
   overall CI health, architecture, governance, or completeness:

   ```bash
   python scripts/orchestrate_ci_topology.py --project-root . --plan-local --json
   ```

4. **Read the payload in order:**
   - `workflow_inventory` — what's there now
   - `architecture_plan` — what shape it should take
   - `governance_findings` — risks and gaps
   - `performance_plan` — speed and efficiency wins
   - `local_verification_plan` — what can run locally
   - `repair_queue` — what to fix first
   - `scope_limits` — what's honest to claim

5. **Verify before editing.** Run `scripts/discover_latest_actions.py`
   before changing any external `uses:` reference.

6. **Split when bloated.** If one workflow does too much, run
   `scripts/plan_workflow_split.py`.

7. **Plan before running locally.** Run
   `scripts/run_local_ci.py --plan-only --json` so the mode, commands,
   blockers, and limits are explicit.

8. **Prefer `act` for fidelity.** If the plan selects `act`, use it
   for high-fidelity local simulation. Otherwise use fallback command
   execution and keep the scope narrow.

9. **Pin with care.** After resolving an action, pin the commit SHA
   and keep the release tag as a comment hint.

## Quick Commands

**Full orchestration pass:**

```bash
python scripts/orchestrate_ci_topology.py --project-root . --plan-local --json
```

**Discover components for a need:**

```bash
python scripts/discover_latest_actions.py --query "node pnpm cache" --limit 4 --json
```

**Verify existing `uses:` entries:**

```bash
python scripts/discover_latest_actions.py --workflow .github/workflows/ci.yml --json
```

**Plan splitting a large workflow:**

```bash
python scripts/plan_workflow_split.py --workflow .github/workflows/ci.yml --json
```

**Plan local execution:**

```bash
python scripts/run_local_ci.py --project-root . --plan-only --json
```

**Run a workflow locally with `act`:**

```bash
python scripts/run_local_ci.py --project-root . --workflow ci.yml --event pull_request --mode auto --json
```

**Run with secrets and env files:**

```bash
python scripts/run_local_ci.py --project-root . --workflow ci.yml \
  --secret-file .secrets --env-file .env.act --event-file event.json --json
```

## Guardrails

- **Never trust static examples.** Re-run live verification every time
  a workflow is edited.
- **Rate limited?** Set `GITHUB_TOKEN` or `GH_TOKEN` and retry instead
  of guessing.
- **Blocked verification?** Report items as `verification-blocked`
  rather than failing open.
- **Floating refs are not verified.** Resolve the latest release tag
  and commit SHA before treating anything as current.
- **Don't skip orchestration** for broad CI completeness or topology
  work.
- **Reusable workflows go directly under `.github/workflows`.**
  GitHub does not support subdirectories for them.
- **Start permissions narrow.** Default to `contents: read`, then add
  only what the workflow needs.
- **Private actions need direct inspection.** Don't claim they're
  latest based on public API results.
- **Split by meaning, not mechanically.** Split by trigger, lifecycle,
  or repeated structure so the resulting files are easier to own.
- **Don't force `act` on deploy workflows** without explicit secret
  setup and a clear reason.
- **Surface unsupported steps.** Don't silently treat them as passed.
- **Keep claims separate.** Findings, proposed files, and local
  verification scope are three different things.

## References

- `references/orchestration-contract.md` — Top-level orchestration
  payload and interpretation rules.
- `references/governance-and-performance.md` — Permissions,
  concurrency, SHA pinning, matrix, cache, and monorepo guidance.
- `references/modern-workflow-patterns.md` — Official workflow
  structure and split rules.
- `references/act-local-simulation.md` — `act` usage, runner image
  mapping, and local execution guardrails.
- `references/verified-component-snapshot-2026-04-09.md` — Verified
  component snapshot and source URLs.

## Examples

**Example 1: Modernize outdated action versions**
```
User: "Our CI workflow is using old action versions. Can you update them?"
Agent: Run `scripts/discover_latest_actions.py --workflow .github/workflows/ci.yml --json`, read the verification results, pin updated SHAs with release tag comments, and re-run live verification.
```

**Example 2: Design CI for a new Node.js monorepo**
```
User: "Set up GitHub Actions CI for our pnpm monorepo with lint, test, and build."
Agent: Run `scripts/orchestrate_ci_topology.py --project-root . --plan-local --json`, read workflow_inventory and architecture_plan, design matrix strategy per package, set narrow permissions, and plan caching for pnpm.
```

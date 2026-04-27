# Orchestration Contract

Use this file when running `scripts/orchestrate_ci_topology.py` or interpreting its output.

## Required top-level sections

The orchestration payload must expose:

- `workflow_inventory`
- `architecture_plan`
- `governance_findings`
- `performance_plan`
- `local_verification_plan`
- `repair_queue`
- `proposed_files`
- `scope_limits`

## Status meanings

- `passed`: a local execution path ran successfully for the covered scope.
- `planned`: the repository was analyzed and a local plan may exist, but execution was not performed for the full scope.
- `blocked`: local execution or a confident recommendation path is limited by missing workflows, secrets, private actions, unsupported steps, or environment blockers.

Do not treat `planned` as equivalent to `passed`.

## Section interpretation

### `workflow_inventory`

Treat this as the current observed topology:

- workflow file path,
- workflow name,
- triggers,
- job ids,
- major `uses:` entries,
- major `run:` commands,
- inferred responsibility.

### `architecture_plan`

Treat this as the recommended future shape:

- split-by-lifecycle suggestions,
- split-by-trigger suggestions,
- reusable workflow suggestions,
- composite action suggestions,
- target file paths.

### `governance_findings`

Treat this as static risk analysis, not proof that a workflow is broken. Typical categories include:

- missing or weak `permissions`,
- missing `concurrency`,
- floating refs instead of pinned SHAs,
- missing Dependabot coverage for GitHub Actions.

### `performance_plan`

Treat this as workflow-efficiency guidance. Each item should explain:

- current pattern,
- issue,
- proposed change,
- expected tradeoff.

### `local_verification_plan`

Treat this as the current executable boundary. It should state:

- `selected_mode`
- `runnable_commands`
- `blockers`
- `scope_limits`

If the plan is blocked or partial, keep the claim narrow.
If the plan was only generated and not executed, `scope_limits` should say so explicitly.

### `repair_queue`

Treat this as the suggested order of attack. Version one should prefer:

1. `workflow-structure`
2. `action-versioning`
3. `permissions-and-governance`
4. `environment-and-tooling`
5. `repository-quality-gates`
6. `product-code-failures`

### `proposed_files`

Treat these as the file-level destinations for the recommended topology. Examples:

- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`
- `.github/workflows/nightly.yml`
- `.github/workflows/reusable-node-quality.yml`
- `.github/actions/node-pnpm-bootstrap/action.yml`

### `scope_limits`

Treat this as the honesty boundary. This section should explain what was not verified or why a recommendation remains advisory, especially for:

- secret-dependent workflows,
- deploy-only workflows,
- unsupported or private actions,
- unexecuted but recommended file changes.

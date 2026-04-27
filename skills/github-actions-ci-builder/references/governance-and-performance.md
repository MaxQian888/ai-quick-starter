# Governance And Performance

Use this file after topology analysis and before editing workflow YAML.

## Governance checks

### Permissions

- Keep `permissions` explicit.
- Default to `contents: read`, then widen only per workflow or job need.
- Treat missing `permissions` as a governance gap even when the workflow still runs.

### Concurrency

- Use workflow-level `concurrency` for branch-feedback paths such as `pull_request` and default-branch validation.
- Prefer `cancel-in-progress: true` for PR feedback loops unless the workflow needs every historical run.

### Action refs

- Treat floating refs such as `@v6`, `@main`, and `@latest` as convenient aliases, not immutable pins.
- Verify the latest stable release first, then pin the full commit SHA.
- Keep the release tag as a comment hint when it helps maintainability.

### Dependabot

- Add a GitHub Actions Dependabot entry when the repository owns workflow YAML.
- Minimal baseline:

```yaml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

### Secret and fork boundaries

- Keep deploy-only or secret-heavy flows separate from PR validation when possible.
- Do not pretend local simulation covers secret-dependent paths without explicit secret files and a safe reason to run them.

## Performance checks

### Matrix

- Prefer matrix jobs over near-identical duplicated jobs when the only variation is runtime, operating system, or one narrow dimension.
- Keep matrix dimensions intentional. Do not explode the matrix without a clear coverage need.

### Cache

- Prefer setup-action native cache support when it matches the stack.
- Otherwise use `actions/cache` with lockfile-driven keys.
- Treat lockfile-backed repositories without cache strategy as a common performance gap.

### Repeated bootstrap

- When multiple jobs repeat the same checkout, setup, and install prefix, extract that bootstrap into:
  - a composite action for repeated step blocks,
  - or a reusable workflow for repeated job graphs.

### Monorepo fan-out

- If the repository has workspace or multi-package structure, consider path-aware workflow fan-out instead of running every package on every change.
- Always state the tradeoff: faster PR feedback versus more path-filter maintenance.

### Artifacts

- Upload artifacts only when they improve debugging, handoff, or packaging.
- Treat noisy or redundant artifact uploads as a maintenance and runtime cost.

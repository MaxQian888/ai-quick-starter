# Modern Workflow Patterns

Use this file after repo inspection and before editing workflow YAML.

## Official docs to anchor decisions

- Workflow syntax: `https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax`
- Reusable workflows: `https://docs.github.com/en/actions/sharing-automations/reusing-workflows`
- Matrix jobs: `https://docs.github.com/en/actions/using-jobs/using-a-matrix-for-your-jobs`
- Dependency caching: `https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/caching-dependencies-to-speed-up-workflows`
- Concurrency: `https://docs.github.com/en/actions/how-tos/writing-workflows/choosing-when-your-workflow-runs/control-the-concurrency-of-workflows-and-jobs`
- Security hardening: `https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions`
- Dependabot for actions: `https://docs.github.com/en/code-security/dependabot/working-with-dependabot/keeping-your-actions-up-to-date-with-dependabot`

## Baseline CI shape

- Store workflow files directly in `.github/workflows/`.
- Start validation with `pull_request` plus `push` to the default branch.
- Add `workflow_dispatch` for manual reruns or controlled operational flows.
- Set workflow-level `concurrency` with `cancel-in-progress: true` for branch feedback loops.
- Keep `permissions` explicit. Default to `contents: read`, then expand per workflow or per job only when required.
- Prefer matrix jobs over duplicating nearly identical jobs for multiple runtimes or operating systems.

## Caching and artifacts

- Prefer cache support built into setup actions when it exists and matches the stack.
- Use `actions/cache` when setup actions do not cover the dependency or build cache you need.
- Keep cache keys deterministic and tied to lockfiles or dependency manifests.
- Upload artifacts only when they help diagnosis, handoff, or release packaging.

## Verification before editing refs

- Resolve the latest stable release or tag before touching any external `uses:` reference.
- Pin the full commit SHA after verification; keep the release tag as a comment hint.
- Treat floating major tags like `@v6` as convenient but not exact-latest.
- If unauthenticated GitHub API calls hit rate limits, set `GITHUB_TOKEN` or `GH_TOKEN` before retrying the resolver.
- Use Dependabot with `package-ecosystem: "github-actions"` and `directory: "/"` to keep workflows current after the initial upgrade.

Minimal Dependabot example:

```yaml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

## Splitting large workflow files

- Split by lifecycle first:
  - `ci.yml` for PR and branch validation
  - `release.yml` or `deploy.yml` for publish and environment changes
  - `nightly.yml` for scheduled automation
- Keep governance and performance interpretation in `governance-and-performance.md`; keep this file focused on structure and file placement.
- Use reusable workflows when multiple entrypoint workflows share the same job structure.
- Use composite actions when multiple jobs repeat the same setup step block.
- Keep reusable workflows directly under `.github/workflows`; GitHub does not support subdirectories for them.
- Keep composite actions under `.github/actions/<name>/action.yml`.

## When to extract a reusable workflow

- Two or more workflows repeat the same job graph.
- The shared part needs typed inputs or secrets via `workflow_call`.
- You want one place to maintain matrix or verification structure across multiple entrypoints.

## When to extract a composite action

- Two or more jobs repeat the same checkout, tool setup, cache, or install prefix.
- The repeated block is step-oriented instead of job-graph-oriented.
- The repetition should stay inside a single job after extraction.

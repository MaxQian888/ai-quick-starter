# Linked Skills

Use this file when a batch plan reveals quality-gate failures that need deeper repair, or when the user wants CI/CD follow-up after consolidation.

## `$commit-quality-fixer`

Use when:
- a single batch's quality-gate failure is complex and needs focused repair,
- the user wants to commit one batch at a time with full quality gate enforcement,
- lint, test, or typecheck failures inside a batch need root-cause tracing beyond the batch boundary.

## `$build-project-fixer`

Use when:
- batch-level quality gate failures stem from broader build or test surface issues,
- the failure is not isolated to the staged batch.

## `$github-actions-ci-builder`

Use when:
- all batches commit cleanly and the user wants to harden CI/CD,
- the consolidated history should be validated against CI workflows before pushing.

## Routing Rules

- Prefer `$commit-quality-fixer` when the repair is scoped to one batch and needs the full quality-gate discovery loop.
- Prefer `$build-project-fixer` when the failure indicates a repository-wide build or test problem.
- Prefer `$github-actions-ci-builder` after consolidation when the user mentions CI or workflow validation.
- Do not use `git commit --no-verify` unless the user explicitly asks.
- Do not squash checkpoint commits while any batch remains blocked.

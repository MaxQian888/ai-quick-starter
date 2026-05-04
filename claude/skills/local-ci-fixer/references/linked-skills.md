# Linked Skills

Use this file when local CI simulation reveals workflow design or build verification needs.

## `$github-actions-ci-builder`

Use when:
- the local CI fix identifies workflow design flaws,
- the user wants to modernize, split, or govern GitHub Actions workflows.

## `$build-project-fixer`

Use when:
- local CI failures stem from build, test, or lint errors rather than workflow design.

## Routing Rules

- Prefer `$github-actions-ci-builder` when the fix is architectural (workflow splitting, permissions, matrix design).
- Prefer `$build-project-fixer` when the fix is code-level (compilation, tests, lint).

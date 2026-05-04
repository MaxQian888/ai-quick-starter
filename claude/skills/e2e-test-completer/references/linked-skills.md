# Linked Skills

Use this file when E2E test work reveals build issues, coverage gaps, or needs verification.

## `$build-project-fixer`

Use when:
- E2E tests fail due to build errors, type issues, or broken dependencies,
- the runner command itself is unknown or fails.

## `$component-unit-test-completer`

Use when:
- the E2E gaps are accompanied by missing unit tests at the component level,
- the user wants to close both unit and E2E coverage.

## `$commit-quality-fixer`

Use when:
- E2E test updates are complete and the user wants to commit.

## Routing Rules

- Prefer `$build-project-fixer` when the E2E runner or app server does not start.
- Prefer `$component-unit-test-completer` when gaps exist at both test layers.
- Do not claim `--mode simulate` means tests passed; it only proves command selection.
- Do not introduce a new E2E runner when the repo already has one.

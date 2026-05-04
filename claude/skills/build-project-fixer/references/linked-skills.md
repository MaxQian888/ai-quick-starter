# Linked Skills

Use this file when the build is green and the user wants to commit, or when the fix reveals deeper planning or testing needs.

## `$commit-quality-fixer`

Use when:
- the build passes and the user wants to stage and commit changes,
- pre-commit quality gates need to be discovered and enforced.

## `$feature-optimization-planner`

Use when:
- the build failure was a symptom of deeper technical debt,
- the user wants an evidence-backed optimization plan to prevent similar failures.

## `$component-unit-test-completer`

Use when:
- the fix touched components that lack unit test coverage,
- the user wants to close test gaps before considering the work complete.

## `$e2e-test-completer`

Use when:
- the fix changed user-facing flows that may need E2E test updates.

## `$github-actions-ci-builder`

Use when:
- the fix revealed CI workflow gaps or the user wants to harden the CI pipeline.

## Routing Rules

- Prefer `$commit-quality-fixer` as the final gate before finishing.
- Prefer `$feature-optimization-planner` only when the user explicitly asks for broader improvement after the immediate fix.
- Do not skip verification steps to get green output faster.
- Do not claim full success when only a subset of commands was re-run.

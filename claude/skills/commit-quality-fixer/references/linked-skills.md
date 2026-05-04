# Linked Skills

Use this file when the commit workflow reveals deeper issues or when the user wants CI/CD follow-up after committing.

## `$split-commit-fixer`

Use when:
- the staged changes are too large for one commit,
- files span multiple features, subsystems, or concerns,
- the user says "my changes are too big for one commit", "split this", or "organize commits",
- mixed concerns in the worktree would produce an unreadable or overly broad commit message.

## `$github-actions-ci-builder`

Use when:
- the local quality gates pass but the user wants to harden CI/CD,
- GitHub Actions workflows need modernization, splitting, or governance review.

## `$build-project-fixer`

Use when:
- pre-commit checks fail and the root cause is not in the staged files,
- a broader build or test failure blocks the commit.

## `$local-ci-fixer`

Use when:
- the user wants to simulate CI locally before pushing,
- local CI behavior diverges from GitHub Actions.

## Routing Rules

- Prefer `$split-commit-fixer` when the dirty worktree mixes multiple concerns or exceeds a reasonable single-commit scope.
- Prefer `$github-actions-ci-builder` when the user mentions CI, deployment automation, or workflow files.
- Prefer `$build-project-fixer` when the failure is a build, test, or lint error unrelated to commit scope.
- Do not bypass checks with `--no-verify` unless the user explicitly asks.
- Do not weaken lint rules or delete tests to make the commit pass.

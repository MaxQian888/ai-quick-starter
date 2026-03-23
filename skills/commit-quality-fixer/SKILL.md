---
name: commit-quality-fixer
description: Generate Conventional Commit messages and drive an end-to-end commit workflow that discovers, runs, and fixes pre-commit quality checks. Use when users ask to commit code, standardize commit messages, resolve lint/test/type-check failures that block `git commit`, or complete a safe "fix checks then commit" flow.
---

# Commit Quality Fixer

Drive a reliable commit flow: run quality gates, fix failures, generate a standard message, and commit only after checks pass.

## Workflow

1. Confirm commit intent and staged scope.
2. Run quality-gate discovery to collect project-specific checks.
3. Run checks and capture failing command output.
4. Fix failures with minimal, targeted code changes.
5. Re-run failing checks, then re-run the full suite until all pass.
6. Draft a Conventional Commit message from staged diff.
7. Commit and report the final result with latest commit summary.

## Quality Gate Commands

Discover checks:

```bash
uv run --python 3.11 scripts/commit_quality_gate.py --discover-only
```

Run checks (text output):

```bash
uv run --python 3.11 scripts/commit_quality_gate.py
```

Run checks (JSON output for diagnostics):

```bash
uv run --python 3.11 scripts/commit_quality_gate.py --json
```

Use `--fail-fast` to stop after the first failed command:

```bash
uv run --python 3.11 scripts/commit_quality_gate.py --fail-fast
```

## Repair Loop

1. Run the quality gate script.
2. Select the first failed command.
3. Read stack traces or linter messages and fix root cause, not symptoms.
4. Re-run that failed command directly.
5. Re-run the full quality gate script.
6. Repeat until all checks pass.

If the same check fails repeatedly after three repair attempts, stop and report:
- failing command
- unresolved error summary
- attempted fixes

## Commit Message Rules

Always follow `references/conventional-commits.md`.

Required format:

```text
<type>(<scope>): <subject>
```

Rules:
- Keep subject imperative and concise (usually <= 72 chars).
- Use one meaningful scope when obvious; omit scope if unclear.
- Add body bullets for non-trivial commits.
- Add footer for breaking changes or issue references when relevant.

## Guardrails

- Never use `git commit --no-verify` unless user explicitly asks.
- Never silence checks by deleting tests or weakening lint rules without approval.
- Keep fixes limited to files that are required for passing checks.
- Preserve user changes and avoid unrelated refactors.

## Resources

- `scripts/commit_quality_gate.py`: Discover and run common pre-commit quality checks.
- `references/conventional-commits.md`: Commit message standard, type mapping, and examples.

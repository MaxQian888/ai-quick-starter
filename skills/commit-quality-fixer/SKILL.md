---
name: commit-quality-fixer
description: >
  Make sure to use this skill whenever the user needs to commit changes, write a
  commit message, fix pre-commit failures, clean up code before pushing, or pass
  quality gates. Also trigger when they mention lint errors, test failures,
  type-check errors, "can't commit," "fix my code," "make this commit-ready,"
  or "help me push." Covers synonyms like "commit helper," "pre-commit fixer,"
  "quality gate runner," "Conventional Commit writer," "commit message
  standardizer," and "lint/test repair." Use it even when the user only says
  "I want to commit" or "my commit is failing" without specifying the exact
  check that is blocking them.
---

# Commit Quality Fixer

Guide the user through a reliable commit workflow: discover the project's quality gates, fix any failures, draft a clean Conventional Commit message, and only commit once everything passes.

## Adaptive Detection

Before acting, detect the repository's quality toolchain:

- Check for `.pre-commit-config.yaml` (pre-commit framework).
- Read `package.json` scripts for `lint`, `test`, `typecheck`, `build`, `check`.
- Check `pyproject.toml` / `setup.py` for Python tools (ruff, pytest, mypy).
- Check `Cargo.toml` for Rust (cargo fmt, clippy, test).
- Check `go.mod` for Go (go test, go vet).
- Detect package manager: pnpm, yarn, bun, npm, uv, poetry, pipenv.
- Use the helper script to auto-discover all applicable checks.

## Workflow

1. Confirm what the user wants to commit and which files are staged.
2. Discover project-specific quality checks using the helper script.
3. Run the checks and capture the output from any failures.
4. Fix each failure with the smallest, most targeted change possible.
5. Re-run the failing checks, then re-run the full suite until everything passes.
6. Draft a Conventional Commit message from the staged diff.
7. Commit and report the final result with a summary of the latest commit.

## Quality Gate Commands

Discover the checks that apply to this repository:

```bash
uv run --python 3.11 scripts/commit_quality_gate.py --discover-only
```

Run all checks (text output):

```bash
uv run --python 3.11 scripts/commit_quality_gate.py
```

Run checks with structured JSON output for diagnostics:

```bash
uv run --python 3.11 scripts/commit_quality_gate.py --json
```

Stop after the first failure:

```bash
uv run --python 3.11 scripts/commit_quality_gate.py --fail-fast
```

## Repair Loop

When checks fail, work through them methodically:

1. Run the quality gate script to see the full picture.
2. Pick the first failed command and read its output carefully.
3. Trace the error to its root cause rather than patching symptoms.
4. Apply the fix and re-run that specific command.
5. Re-run the full quality gate script to confirm nothing else broke.
6. Repeat until all checks pass.

If the same check fails three times in a row, stop and report:
- the failing command
- a summary of the unresolved error
- what fixes were already attempted

## Commit Message Rules

Commit messages must follow the standard in `references/conventional-commits.md`.

Required format:

```text
<type>(<scope>): <subject>
```

Guidelines:
- Write the subject in imperative mood and keep it concise (usually <= 72 chars).
- Use a meaningful scope when one is obvious from the changed files; omit it when the change spans many unrelated areas.
- Add body bullets for non-trivial commits that need explanation.
- Add a footer for breaking changes or issue references when relevant.

## Guardrails

- Do not bypass checks with `git commit --no-verify` unless the user explicitly asks for it.
- Do not silence failures by deleting tests or weakening lint rules without the user's approval.
- Keep fixes limited to the files required for passing checks.
- Preserve the user's original changes and avoid unrelated refactors.

## Examples

**Commit with full quality gate:**
```bash
uv run --python 3.11 scripts/commit_quality_gate.py
```
Then draft a Conventional Commit from the staged diff and commit.

**Fix lint failures in a Node project:**
```bash
uv run --python 3.11 scripts/commit_quality_gate.py --json
```
Trace ESLint errors, apply fixes, re-run the gate, then commit.

## Resources

- `scripts/commit_quality_gate.py` — Discover and run project-specific pre-commit quality checks.
- `references/conventional-commits.md` — Commit message standard, type mapping, and examples.

---
name: commit-quality-fixer
description: >
  Make sure to use this skill whenever the user is preparing a commit, asking
  for a commit message, or stuck on pre-commit, lint, type-check, or test
  failures that block them from committing. Trigger on phrases like "commit",
  "push", "pre-commit", "make this commit-ready", "fix my code so I can
  commit", "write a Conventional Commit", "lint is failing", "tests are
  failing", "type errors", "ci is red on my branch", or simple statements
  such as "I want to commit" or "my commit keeps failing" — even when the
  user does not name the specific check that is blocking them. Also covers
  synonyms like "commit helper", "pre-commit fixer", "quality gate runner",
  "commit message standardizer", and "lint/test repair before push".
---

# Commit Quality Fixer

Guide the user through a reliable commit workflow: discover the project's quality gates, fix any failures, draft a clean Conventional Commit message, and only commit once everything passes.

The user's goal is a green commit, not a perfect refactor. Keep changes minimal, scoped to the failing checks, and preserve the user's original intent.

## Workflow

1. Confirm what the user wants to commit. If nothing is staged yet, run `git status` to see what changed and ask which files belong in this commit before running `git add`.
2. Discover project-specific quality checks using the helper script (see "Quality Gate Commands" below).
3. Run the checks. Capture the failing output verbatim — do not paraphrase errors.
4. Fix each failure with the smallest, most targeted change possible (see "Repair Loop").
5. Re-run the failing check, then re-run the full suite, until everything passes.
6. Draft a Conventional Commit message from the staged diff (see `references/conventional-commits.md`).
7. Commit and report the resulting hash plus a one-line summary.

If the staged diff mixes unrelated concerns or grows beyond what one message can describe well, see `references/linked-skills.md` for routing to a split-commit helper before continuing.

## Adaptive Detection

The helper script reads project files and emits the right command for the toolchain it finds:

- `.pre-commit-config.yaml` → `pre-commit run --all-files`
- `package.json` scripts → `lint`, `typecheck`, `test`, `build`, `check`, `ci`, `validate`, `verify`, `format:check`, plus aliases `precommit` / `pre-commit` / `qa` / `quality`
- `pyproject.toml` / `setup.py` / `setup.cfg` / `requirements*.txt` → `ruff check`, `ruff format --check`, `black --check`, `isort --check-only`, `pytest`, `mypy`, `pyright` — only when those tools appear in the project's declared dependencies
- `Cargo.toml` → `cargo fmt --all --check`, `cargo clippy`, `cargo test`
- `go.mod` → `go vet ./...`, `go test ./...`
- `gradlew` → `./gradlew check` (Windows uses `gradlew.bat`)
- `mvnw` → `./mvnw -q verify` (Windows uses `mvnw.cmd`)
- `*.sln` / `*.csproj` → `dotnet build`, `dotnet test`
- `deno.json` / `deno.jsonc` → `deno lint`, `deno test`
- Fallback (git repo) → `git diff --check`

Package manager and Python runner are auto-detected: pnpm/yarn/bun/npm for Node, uv/poetry/pipenv for Python.

## Quality Gate Commands

Discover the checks that apply to this repository:

```bash
uv run --python 3.11 scripts/commit_quality_gate.py --discover-only
```

Run all checks (text output):

```bash
uv run --python 3.11 scripts/commit_quality_gate.py
```

Run with structured JSON for diagnostics or downstream tooling:

```bash
uv run --python 3.11 scripts/commit_quality_gate.py --json
```

Stop after the first failure (useful when iterating on one check):

```bash
uv run --python 3.11 scripts/commit_quality_gate.py --fail-fast
```

When iterating on a single broken check, run that command directly (e.g., `pnpm lint`) instead of the full gate — it is faster and the output is easier to read. Re-run the full gate before committing to confirm nothing else broke.

## Repair Loop

When checks fail, work through them methodically:

1. Run the gate once with `--fail-fast` to surface the blocking failure cleanly.
2. Read the error output and trace the failure to its root cause. A type error often stems from a renamed field upstream; a lint error often stems from an unused import the user just removed. Fix the cause, not the symptom.
3. Apply the smallest fix that addresses the root cause. Avoid drive-by refactors.
4. Re-run that one command. Once it passes, re-run the full gate to confirm nothing else regressed.
5. Repeat for the next failure.

If the same check fails three times in a row with different attempted fixes, stop and report:

- the failing command
- a one-paragraph summary of what the error says
- the fixes already attempted and why each one did not resolve it

This signals the issue is outside the staged diff (e.g., a flaky test, an environment problem, or a pre-existing bug). At that point, see `references/linked-skills.md` for handoff options.

## Commit Message Rules

Use the Conventional Commits standard in `references/conventional-commits.md`. Required header format:

```text
<type>(<scope>): <subject>
```

- Imperative subject, no trailing period, usually <= 72 chars.
- Use a meaningful scope when one is obvious from the changed files; omit it when the change spans many unrelated areas.
- Add body bullets for non-trivial changes that need a "why".
- Add a footer for breaking changes or issue references.

Draft the message from the staged diff so it reflects what is actually being committed, not what the user said they were doing.

## Guardrails

- Do not bypass checks with `git commit --no-verify` unless the user explicitly asks.
- Do not silence failures by deleting tests, weakening lint rules, or relaxing type configs without the user's approval.
- Keep fixes scoped to what is needed for the checks to pass; do not refactor unrelated code.
- Preserve the user's original changes. If a fix conflicts with their intent, surface the conflict instead of overwriting their work.
- Never commit on behalf of the user without showing them the final message and confirming.

## Examples

**Commit with the full quality gate:**

```bash
uv run --python 3.11 scripts/commit_quality_gate.py
```

Then draft a Conventional Commit from the staged diff and commit.

**Iterate on a single failing lint command:**

```bash
uv run --python 3.11 scripts/commit_quality_gate.py --fail-fast
# fix the reported file, then:
pnpm lint
# once green, re-run the full gate before committing
```

## Resources

- `scripts/commit_quality_gate.py` — Discover and run project-specific pre-commit quality checks.
- `references/conventional-commits.md` — Commit message standard, type mapping, and examples.
- `references/linked-skills.md` — When to hand off to a split-commit helper, build fixer, or CI builder.

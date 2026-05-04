---
name: configuring-commit-checks
description: >
  Make sure to use this skill whenever the user wants to set up, configure, or
  repair commit hooks, pre-commit checks, git hooks, husky, lint-staged,
  lefthook, simple-git-hooks, or commitlint. Also trigger when they mention
  "run checks before commits," "add pre-commit hooks," "fix my git hooks,"
  "set up lint-staged," "wire ruff/mypy into commits," or "configure commit
  checks." Covers synonyms like "hook setup," "pre-commit configuration,"
  "commit gate," "quality checks on commit," "git hook repair," and "lint
  before push." Use it even when the user only says "I want checks to run
  before I commit" or "help me set up git hooks" without naming a specific
  tool, and even in monorepos where the working directory is a nested package.
---

# Configuring Commit Checks

Look before you change. The fastest way to break a working hook setup is to layer a second framework on top of one that already works. Inspect the repository's existing commit-hook tooling before adding or modifying anything, respect the current toolchain when one is in place, and only introduce a default stack when the project genuinely has no commit-check tooling.

## Why this matters

Hook frameworks (`husky`, `pre-commit`, `lefthook`, `simple-git-hooks`) are mutually exclusive entry points. Two hook runners installed in the same repo race for the same `.git/hooks/*` files; whichever one was installed last wins, and the team usually doesn't notice until a check silently stops running. Migrating frameworks is a deliberate decision, not a fix for a missing hook.

## Adaptive detection

Before changing anything, learn the repository's shape and current setup. The bundled detection script does the lookups consistently and returns structured JSON.

```bash
python scripts/detect_commit_setup.py --project-root . --json
```

The script is pure-stdlib Python (3.8+), so any local interpreter works — `python3`, `py`, or `uv run --python 3.11 scripts/detect_commit_setup.py ...` are all fine. Pick whichever the repo's contributors already use.

What it looks for:

- **Primary hook runners**: `.husky/` directory; `.pre-commit-config.yaml` / `.yml`; `lefthook.yml` / `.yaml` / `.toml` (and dotfile variants); `simple-git-hooks` config block in `package.json`. Also catches the case where the package is declared in `package.json` / `pyproject.toml` but its config files aren't generated yet.
- **Supporting tools**: `lint-staged` (block in `package.json` or in `devDependencies`), `commitlint` (any of its config filenames or `@commitlint/cli` in deps).
- **Project type**: Node (any `package.json` or lockfile), Python (`pyproject.toml`, `setup.py`, `requirements*.txt`, `Pipfile`, `uv.lock`, `poetry.lock`), or `mixed`.
- **Real repo root**: walks up from the start path looking for `.git`, then for monorepo markers (`pnpm-workspace.yaml`, `turbo.json`, `nx.json`, `lerna.json`, `rush.json`).

## Workflow

1. **Find the real repository root.** Run the detection script and trust its `detected_root`. If the user invoked you from `apps/web/src/`, the relevant `package.json` and hook config probably live several levels up.

2. **Read the recommendation.** The script returns one of four strategies:
   - `preserve-existing` — a primary hook runner is already wired up; extend it instead of replacing it.
   - `complete-existing` — supporting tools (typically `lint-staged`) are configured but no runner is installed; add the runner that fits the existing config.
   - `add-default` — no hook tooling at all; install the standard stack for the detected project type.
   - `review-manually` — project type is unclear; stop and inspect.

3. **Apply defaults only when nothing exists.**
   - Node-only project → `husky` + `lint-staged`.
   - Python-only project → `pre-commit`.
   - Mixed Node + Python → `pre-commit` as the top-level orchestrator (it can call into Node commands without forcing both frameworks).

4. **Make the smallest compatible change.**
   - `husky` already present → extend `.husky/` and `package.json` (`lint-staged`, `prepare` script, etc.).
   - `pre-commit` already present → extend `.pre-commit-config.yaml`.
   - `lefthook` already present → extend the existing `lefthook.{yml,yaml,toml}`.
   - `simple-git-hooks` already present → extend the `simple-git-hooks` block in `package.json`.

5. **Verify before claiming done.** Run the hook tool's install / validation command (e.g. `npx husky`, `pre-commit run --all-files`, `lefthook validate`, `npx simple-git-hooks`). Then run the project-native lint, format, typecheck, or test commands the hook will invoke. Report the actual output, not a confident guess.

## Guardrails

- **Don't swap frameworks casually.** Replacing `pre-commit` with `husky` (or vice versa) is a migration. Only do it when the user explicitly asks — and even then, remove the old framework cleanly rather than leaving both in place.
- **Don't add competing systems.** If one framework already governs commits successfully, don't layer another on top. The detection script will surface this; honor it.
- **Don't assume the working directory is the repository root.** Monorepos and nested apps are common. Use `detected_root`.
- **Don't weaken rules to make hooks pass.** If a lint or test is too strict, fix the code or adjust the rule at the project level — never silence it inside the hook just to get a green commit.
- **Don't invent a generic stack when a local convention exists.** Reuse the team's existing scripts (`npm run lint`, `pnpm check`, `make test`) instead of writing parallel commands inside the hook.

## Examples

**Fresh Node project, no hooks yet.**
```bash
python scripts/detect_commit_setup.py --project-root . --json
# -> recommendation: add-default, recommended_tool: husky, supporting_tools: [lint-staged]
```
Apply the `add-default` strategy: install husky + lint-staged, wire a `pre-commit` hook to `npx lint-staged`, and reuse the project's existing eslint/prettier scripts.

**Existing pre-commit, missing mypy.**
```bash
python scripts/detect_commit_setup.py --project-root . --json
# -> recommendation: preserve-existing, recommended_tool: pre-commit
```
Apply `preserve-existing`: edit the existing `.pre-commit-config.yaml` to add a mypy hook entry. Don't introduce husky.

**Mixed Node + Python repo with `.husky/` already in place.**
```bash
python scripts/detect_commit_setup.py --project-root . --json
# -> recommendation: preserve-existing, recommended_tool: husky
```
Apply `preserve-existing`: keep husky, extend `lint-staged` for Node files, and call Python checks (e.g. `ruff check`, `mypy`) from a hook script in `.husky/pre-commit` rather than adding `pre-commit` alongside it.

## References

- Selection rules and defaults: `references/selection-matrix.md`
- Minimal completion patterns: `references/config-patterns.md`
- Detection helper: `scripts/detect_commit_setup.py`
- Tests for the detection helper: `tests/test_detect_commit_setup.py`

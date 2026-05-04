# Config Patterns

Apply the smallest compatible configuration that matches the repository's current stack. The patterns below are starting points — always reuse the team's existing scripts and tools instead of inventing new ones.

## Node repositories

### If `husky` already exists

- Check `.husky/` for `pre-commit`, `commit-msg`, or other hook files.
- Check `package.json` for:
  - quality scripts such as `lint`, `typecheck`, `test`, or `check`,
  - `lint-staged`,
  - `@commitlint/cli` or related config.
- Add only the missing pieces needed to wire the existing quality commands into the hook flow.

### If no hook tool exists

- Add `husky` as the primary hook runner.
- Add `lint-staged` for staged-file formatting and linting.
- Reuse existing package scripts instead of inventing parallel commands.

Minimal pattern:

```json
{
  "scripts": {
    "prepare": "husky"
  },
  "lint-staged": {
    "*.{js,ts,tsx,jsx}": [
      "eslint --fix",
      "prettier --write"
    ]
  }
}
```

The `.husky/pre-commit` file then contains:

```sh
npx lint-staged
```

### If `simple-git-hooks` already exists

The `package.json` block is the entry point. Extend it directly:

```json
{
  "simple-git-hooks": {
    "pre-commit": "npx lint-staged"
  }
}
```

After editing, run `npx simple-git-hooks` so the hook script gets reinstalled into `.git/hooks/`.

## Python repositories

### If `pre-commit` already exists

- Extend `.pre-commit-config.yaml`.
- Prefer the repository's existing Python tools such as `ruff`, `black`, `pytest`, or `mypy`.
- Keep one entry point instead of adding `husky`.

### If no hook tool exists

- Add `.pre-commit-config.yaml`.
- Start with formatting and linting hooks that match the current toolchain.
- Add test-related hooks only when they are fast enough for commit-time use.

Minimal pattern:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.0
    hooks:
      - id: ruff-check
      - id: ruff-format
```

To add mypy without disturbing existing ruff hooks, append a new `repos:` entry rather than modifying the existing one:

```yaml
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.2
    hooks:
      - id: mypy
        additional_dependencies: []
```

## Mixed Node and Python repositories

- Prefer `pre-commit` as the top-level orchestrator when no hook tool exists. It can run Node commands via `language: system` entries.
- If `husky` is already in place, **don't** add `pre-commit` alongside it. Call Python checks from `.husky/pre-commit` directly, e.g.:

  ```sh
  npx lint-staged
  ruff check .
  mypy src
  ```

- If `pre-commit` is already in place, call Node commands from inside it:

  ```yaml
  repos:
    - repo: local
      hooks:
        - id: node-lint
          name: node-lint
          entry: npm run lint
          language: system
          pass_filenames: false
        - id: python-lint
          name: python-lint
          entry: ruff check .
          language: system
          pass_filenames: false
  ```

## Verification

- For `husky`: run `npx husky` (v9+) or the project's prepare script, inspect the generated hook files, and execute the actual commands the hook will run.
- For `pre-commit`: run `pre-commit install` once, then `pre-commit run --all-files` to verify every hook resolves and passes.
- For `lefthook`: run `lefthook install` then `lefthook run pre-commit`.
- For `simple-git-hooks`: run `npx simple-git-hooks` to reinstall hooks after editing the config block.

In every case, run the project's own quality commands (lint, format, typecheck, tests) once outside the hook so you can distinguish between a misconfigured hook and a genuinely failing project.

## Anti-patterns

- Replacing the repository's current hook framework without approval.
- Adding both `husky` and `pre-commit` so "everyone gets what they want" — they fight over `.git/hooks/*`.
- Adding slow end-to-end suites to `pre-commit` by default. Hooks should stay sub-second when possible; push slow checks to CI or a `pre-push` hook.
- Creating new lint or test commands when suitable package scripts already exist.
- Claiming success without running the hook tool and the underlying project checks.

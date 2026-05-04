# Selection Matrix

Use this matrix after running `scripts/detect_commit_setup.py`. The script returns the same four recommendations the matrix encodes; this table is a quick way to read the rationale.

| Repository shape | Existing primary tool | Recommendation | Why |
| --- | --- | --- | --- |
| Node-only | `husky` | Preserve `husky` | Keep the existing hook entry point and add only missing support such as `lint-staged` or `commitlint`. |
| Node-only | `pre-commit` | Preserve `pre-commit` | The repository already chose a top-level orchestrator; do not migrate to `husky` unless the user explicitly asks. |
| Node-only | `lefthook` | Preserve `lefthook` | Existing hook tooling stays. |
| Node-only | `simple-git-hooks` | Preserve `simple-git-hooks` | The team picked a deliberately minimal hook runner; respect it. |
| Node-only | none, but `lint-staged` is configured | Complete with `husky` | The Node commit-check stack is half-built. Add a runner that fits the existing config. |
| Node-only | none | Add `husky` + `lint-staged` | This is the best default for a JavaScript or TypeScript repo with no hook system. |
| Python-only | `pre-commit` | Preserve `pre-commit` | The natural default for Python repositories; extend, don't replace. |
| Python-only | `lefthook` | Preserve `lefthook` | Existing tooling takes precedence over preference. |
| Python-only | none | Add `pre-commit` | One top-level config is the simplest and most conventional default. |
| Mixed Node + Python | `pre-commit` | Preserve `pre-commit` | One orchestrator is ideal for multi-language repositories. |
| Mixed Node + Python | `husky` | Preserve `husky` | The repository already standardized on a hook runner; extend it instead of layering another framework. Call Python checks from `.husky/pre-commit`. |
| Mixed Node + Python | `lefthook` | Preserve `lefthook` | Existing multi-language hook tooling should stay in place. |
| Mixed Node + Python | `simple-git-hooks` | Preserve `simple-git-hooks` | Use the existing entry point; add Python commands inside the same block. |
| Mixed Node + Python | none, but `lint-staged` is configured | Complete with `husky` | A Node-style stack is partway done; preserve user intent. |
| Mixed Node + Python | none | Add `pre-commit` | It can orchestrate both Python and Node commands without adding multiple competing systems. |
| Unknown | anything | Preserve existing | Existing evidence is safer than inventing a new stack. |
| Unknown | none | Review manually | Do not guess when the project type is unclear. |

## Primary vs. supporting tools

- **Primary hook runners** (mutually exclusive): `husky`, `pre-commit`, `lefthook`, `simple-git-hooks`. Only one should govern `.git/hooks/*`.
- **Supporting tools**: `lint-staged`, `commitlint`. They plug into a primary runner; their presence alone never satisfies a "hooks are configured" claim.
- If only supporting tools are present, complete the likely stack — don't declare the repo done.

## Detection nuance

The detector treats a tool as "present" when *either* its config files exist *or* the package is declared in `package.json` / `pyproject.toml`. A repo that has `husky` listed in `devDependencies` but no `.husky/` directory has chosen husky and just hasn't run `husky init` yet — finish that path instead of installing pre-commit on top of it.

## Red flags

- Replacing a working hook system to match a personal preference.
- Adding both `husky` and `pre-commit` to a repository that already has one clear entry point.
- Treating a nested sample app as the real repository root. Use `detected_root` from the script.
- Adding `lint-staged` config without also wiring a primary runner to invoke it.

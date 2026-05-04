---
name: build-project-fixer
description: >
  Use this skill whenever you need to build, test, lint, typecheck, or verify code in an existing repository — especially when checks are failing, commands are unknown, or you are onboarding to an unfamiliar codebase.
  Make sure to use this skill whenever the user reports build errors, test failures, CI breakage, compilation failures, broken pipelines, red GitHub checks, "make it green", or asks to validate code quality before a PR.
  It also applies when you need to discover the correct install scripts, package manager (npm/pnpm/yarn/bun/uv/poetry/cargo/go), task runner, or monorepo workspace commands before making changes.
  Covers Node.js, Python, Rust, Go, and multi-language projects, including monorepos with pnpm workspaces, turbo, or nx.
---

# Build Project Fixer

Discover the repository's real commands before changing any code. Run the helper script to collect evidence, reproduce the smallest failing path, fix the root cause, and expand verification only after the local failure is resolved.

The point of the discovery-first discipline is to stop guessing. A repo's `npm test` may actually be `pnpm exec vitest run --reporter=dot` in CI; running the wrong command produces misleading failures and wastes time. Read what the project actually says about itself before reaching for a fix.

## Adaptive Detection

Before applying any fixes, scan for:
- `package.json` / `Cargo.toml` / `pyproject.toml` / `go.mod` to detect the stack
- Lockfiles (`pnpm-lock.yaml`, `package-lock.json`, `yarn.lock`, `bun.lock*`, `uv.lock`, `poetry.lock`, `Cargo.lock`) to confirm the package manager
- Existing config files (`.eslintrc`, `tsconfig.json`, `pytest.ini`, `Makefile`, `ruff.toml`)
- CI workflow files in `.github/workflows/` for canonical commands (highest evidence weight)
- Test framework in use (jest, vitest, playwright, pytest, cargo test, go test)
- Monorepo signals (`pnpm-workspace.yaml`, `nx.json`, `turbo.json`, `workspaces` field)

## Workflow

1. Inspect manifests, lockfiles, task runners, and `.github/workflows`.
2. Run the helper script (path is relative to this skill's folder; resolve it against the skill's install path):

   ```bash
   python scripts/discover_build_surface.py --project-root <repo> --json
   ```

3. Read the output and pick the narrowest command matching the reported failure or target quality gate. CI `run:` steps win over guessed local commands when they map cleanly.
4. If dependencies look stale or missing, run the most repository-specific install command first (e.g. `pnpm install --frozen-lockfile`, `uv sync`, not generic `npm install`).
5. Run the first failing command, capture its output, and identify the root cause.
6. Apply the smallest valid repair.
7. Re-run the same failing command to confirm the fix.
8. Run the next broader verification command, then the main build or verify step.
9. Report what passed, what was fixed, and what remains unverified or blocked. Be explicit about the difference between "fixed and re-verified" and "looks fixed but not yet rerun".

## Command Selection Rules

- Prefer CI `run:` commands over guessed local ones when they map cleanly to the repository.
- Prefer manifest scripts, Make targets, and task-runner targets over generic ecosystem defaults.
- If multiple package managers appear, pick the one backed by lockfiles, manifest metadata, or CI evidence.
- If monorepo signals appear, narrow to the affected package or app before broad verification.

## Dependency Upgrade Rules

- Allow targeted dependency or lockfile updates when the failure indicates version incompatibility, stale lockfiles, missing transitive packages, or removed APIs.
- Upgrade the narrowest scope possible and re-run the failing command immediately afterward.
- Do not use speculative mass upgrades as a first repair move.

## Guardrails

- Do not delete tests, lower coverage, weaken lint or typecheck rules, or comment out intended behavior to get green output.
- Do not claim full success when only a subset of commands was re-run.
- Do not overwrite unrelated user changes.
- Prefer reporting an environmental blocker (missing system tool, unavailable secret) over forcing a risky workaround.

## References

- Read [references/command-discovery.md](references/command-discovery.md) for source-of-truth priority and command classification rules.
- Read [references/repair-guardrails.md](references/repair-guardrails.md) before changing code, config, or dependencies.
- Read [references/verification-policy.md](references/verification-policy.md) before claiming the repair is complete.
- Read [references/linked-skills.md](references/linked-skills.md) when the build is green and you need to decide what comes next (commit, optimization plan, test gap closure, CI hardening).

## Helper Script

```bash
python scripts/discover_build_surface.py --project-root <repo> --json
```

Use `--category install|build|test|lint|typecheck|verify|all` to narrow the output when one class of command matters more than the rest. The script is read-only — it never installs, builds, or modifies the repository; it only reports candidate commands ranked by evidence strength.

## Examples

**Example 1 — Fix failing TypeScript tests**
```
User: "npm test fails with TypeScript errors in ./my-project."
Agent: Run `python scripts/discover_build_surface.py --project-root ./my-project --json`,
       confirm the project actually uses pnpm (lockfile + CI evidence), reproduce
       with `pnpm test`, fix the TS error in the implicated file, re-run the same
       command, then run `pnpm typecheck` for broader verification.
```

**Example 2 — Validate an unfamiliar Rust repo before PR**
```
User: "Make sure this Rust project builds and passes tests before I open a PR."
Agent: Run the discovery script with `--category all`, run `cargo check`, then
       `cargo test`, fix any failures with the smallest valid change, and report
       what passed and what remains.
```

**Example 3 — Python project where CI lint is red**
```
User: "Our CI is failing on the lint step for ./python-service."
Agent: Discovery surfaces `python -m ruff check .` from pyproject.toml and the
       same command from the CI workflow (priority 100). Reproduce locally,
       identify the new file or rule violation, apply the narrow fix
       (not weakening the rule), re-run ruff, then run pytest to confirm
       behavior is unchanged.
```

**Example 4 — Monorepo: only one package is broken**
```
User: "The build is failing somewhere in our pnpm workspace."
Agent: Discovery surfaces a workspace risk note. Narrow to the failing package
       using `pnpm --filter <pkg> build` rather than running the root `pnpm -r build`,
       fix that package, re-run the filtered build, then run the full
       recursive build last.
```

---
name: build-project-fixer
description: >
  Use this skill whenever you need to build, test, lint, typecheck, or verify code in an existing repository — especially when checks are failing, commands are unknown, or you are onboarding to an unfamiliar codebase.
  Make sure to use this skill whenever the user reports build errors, test failures, CI breakage, compilation failures, broken pipelines, or asks to validate code quality.
  It also applies when you need to discover the correct install scripts, package manager, task runner, or monorepo workspace commands before making changes.
  Covers Node.js, Python, Rust, Go, and multi-language projects.
---

# Build Project Fixer

Discover the repository's real commands before changing any code. Run the helper script to collect evidence, reproduce the smallest failing path, fix the root cause, and expand verification only after the local failure is resolved.

## Adaptive Detection

Before applying any fixes, scan for:
- `package.json` / `Cargo.toml` / `pyproject.toml` / `go.mod` to detect the stack
- Lockfiles (`pnpm-lock.yaml`, `uv.lock`, `poetry.lock`, `Cargo.lock`) to confirm the package manager
- Existing config files (`.eslintrc`, `tsconfig.json`, `pytest.ini`, `Makefile`)
- CI workflow files in `.github/workflows/` for canonical commands
- Test framework in use (jest, vitest, playwright, pytest, cargo test)
- Monorepo signals (`pnpm-workspace.yaml`, `nx.json`, `turbo.json`)

## Workflow

1. Inspect manifests, lockfiles, task runners, and `.github/workflows`.
2. Run the helper script:

   ```bash
   python scripts/discover_build_surface.py --project-root <repo> --json
   ```

3. Read the output and pick the narrowest command matching the reported failure or target quality gate.
4. If dependencies are missing, run the most repository-specific install command first.
5. Run the first failing command, capture its output, and identify the root cause.
6. Apply the smallest valid repair.
7. Re-run the same failing command.
8. Run the next broader verification command, then the main build or verify step.
9. Report what passed, what was fixed, and what remains unverified or blocked.

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
- Prefer reporting an environmental blocker over forcing a risky workaround.

## References

- Read [references/command-discovery.md](references/command-discovery.md) for source-of-truth priority and command classification rules.
- Read [references/repair-guardrails.md](references/repair-guardrails.md) before changing code, config, or dependencies.
- Read [references/verification-policy.md](references/verification-policy.md) before claiming the repair is complete.

## Helper Script

```bash
python scripts/discover_build_surface.py --project-root <repo> --json
```

Use `--category install|build|test|lint|typecheck|verify|all` to narrow the output when one class of command matters more than the rest.

## Examples

**Example 1: Fix failing TypeScript tests**
```
User: "npm test fails with TypeScript errors in ./my-project."
Agent: Run `python scripts/discover_build_surface.py --project-root ./my-project --json`, read the output, run the narrowest failing test command, fix the root cause, re-run the same command, then run broader verification.
```

**Example 2: Validate an unfamiliar Rust repo before PR**
```
User: "Make sure this Rust project builds and passes tests before I open a PR."
Agent: Run `python scripts/discover_build_surface.py --project-root ./rust-app --category all --json`, run `cargo check`, then `cargo test`, fix any failures with the smallest valid change, and report what passed and what remains.
```

---
name: build-project-fixer
description: Use when Codex must build or validate an existing repository, discover the real project-specific install or build or test or lint or typecheck commands, reproduce the first failing check, repair the root cause, and re-run targeted plus broader verification without weakening checks or breaking existing functionality.
---

# Build Project Fixer

Discover the repository's real command surface before changing code. Use the helper script to collect evidence, reproduce the smallest failing path, repair the root cause, and widen verification only after the local failure is fixed.

## Workflow

1. Inspect manifests, lockfiles, task runners, and `.github/workflows`.
2. Run `python scripts/discover_build_surface.py --project-root <repo> --json`.
3. Read the suggested commands and choose the narrowest one that matches the reported failure or target quality gate.
4. If dependencies are missing, run the most repository-specific install command first.
5. Capture the first failing command output and identify the root cause.
6. Apply the smallest valid repair.
7. Re-run the same failing command.
8. Re-run the next broader verification command, then the main build or verify path.
9. Report what passed, what was fixed, and what remains unverified or blocked.

## Command Selection Rules

- Prefer CI `run:` commands over guessed local commands when they map cleanly to the repository.
- Prefer manifest scripts, Make targets, and task-runner targets over generic ecosystem defaults.
- If multiple package managers appear, pick the one backed by lockfiles, manifest metadata, or CI evidence.
- If monorepo signals appear, narrow to the affected package or app before broad verification.

## Dependency Upgrade Rules

- Allow targeted dependency or lockfile updates when the failure points to version incompatibility, stale lockfiles, missing transitive packages, or removed APIs.
- Upgrade the narrowest scope possible and re-run the failing command immediately afterward.
- Do not use speculative mass upgrades as a first repair move.

## Guardrails

- Do not delete tests, lower coverage, weaken lint or typecheck rules, or comment out intended behavior to get green output.
- Do not claim full success when only a subset of commands was re-run.
- Do not overwrite unrelated user changes.
- Prefer reporting an environmental blocker over forcing a risky workaround.

## References

- Read `references/command-discovery.md` for source-of-truth priority and command classification rules.
- Read `references/repair-guardrails.md` before changing code, config, or dependencies.
- Read `references/verification-policy.md` before claiming the repair is complete.

## Helper Script

Run:

```bash
python scripts/discover_build_surface.py --project-root <repo> --json
```

Use `--category install|build|test|lint|typecheck|verify|all` to narrow the output when one class of command matters more than the rest.

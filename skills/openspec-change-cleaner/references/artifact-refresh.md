# Artifact Refresh Loop

Use this file when the latest implementation no longer matches the current OpenSpec change artifacts.

## Goal

Refresh `proposal.md`, `design.md`, delta specs, and `tasks.md` so they describe the latest implementation truth instead of an earlier plan snapshot.

When the repository follows this repo's script-backed skill-module contract, prefer `scripts/reconcile_change_artifacts.py` for the first repair pass. That orchestrator consumes the cleanup report, infers the module, rewrites stale artifacts, re-runs OpenSpec checks, and can archive the change with `--archive-when-ready` once the repaired change is complete.

## Refresh Order

1. Inspect the latest implementation first.
   Read the real code paths, tests, workflows, and shipped behavior. Separate observed truth from assumptions.
2. Refresh `proposal.md`.
   Keep the "Why / What / Impact" aligned to what is actually being maintained or cleaned now.
3. Refresh `design.md` if the change still has technical decisions worth preserving.
   Remove stale architecture claims instead of leaving contradictory design text behind.
4. Refresh `openspec/changes/<change>/specs/**/spec.md`.
   Update the delta requirements so `openspec show <change-id> --json` exposes the real capability deltas again.
5. Refresh `tasks.md`.
   Mark only verified work complete. Add detail lines that explain why a task is done, blocked, or intentionally preserved.
6. Re-run `openspec validate <change-id> --json --no-interactive`.
7. Re-run `openspec status --change <change-id> --json`.

## Deterministic Task Sync

When the semantic task state is already known, encode it into a JSON payload and apply it through `scripts/sync_change_tasks.py`. This keeps checkbox edits and implementation-note sections consistent across repeated cleanup passes.

## Auto-Archive Boundary

Auto-archive belongs at the end of the repair loop, not at the start. Only let `scripts/reconcile_change_artifacts.py --archive-when-ready` archive a change after:

- regenerated artifacts are on disk,
- `openspec show` exposes parsed deltas,
- `openspec status --change <id> --json` reports a complete artifact set,
- `openspec validate <id> --json --no-interactive` reports a valid change.

## Do Not Skip

- Do not let `tasks.md` drift from the latest implementation.
- Do not refresh `tasks.md` without re-checking validation.
- Do not treat `completedTasks` in `openspec list --json` as the whole story. The file content still matters.

---
name: openspec-change-cleaner
description: >
  Use this skill whenever you need to audit, reconcile, clean up, or refresh OpenSpec changes in a repository.
  Make sure to use it when active changes have drifted from implementation, tasks.md looks stale, archive entries seem obsolete, or the user wants to validate proposals, designs, specs, or tasks before archiving.
  Also trigger for OpenSpec hygiene work, change artifact repair, delta spec synchronization, and conservative archive cleanup.
  Covers OpenSpec 1.2.0+ workflows and script-backed change management.
---

# OpenSpec Change Cleaner

Audit active OpenSpec changes against the current implementation before touching archive state.

## Adaptive Detection

Before running any cleanup, scan for:
- `openspec/` directory structure and installed CLI version
- `openspec/changes/<id>/` directories for active changes
- `openspec/archive/` for candidate cleanup entries
- `tasks.md` files within active changes for staleness signals
- Repository type (script-backed skill module, application, library) to choose the right repair path
- Existing `proposal.md`, `design.md`, and `specs/**/spec.md` files to compare against implementation
Rebuild stale artifacts, synchronize `tasks.md` deterministically, and only clean archive noise when the evidence is explicit.

## Workflow

1. Confirm the repository root, the local `openspec/` tree, and the installed CLI version.
   Read `references/current-workflow.md` first when the repository uses OpenSpec 1.2.0 or later.

2. Run the audit helper before editing any artifacts:

   ```bash
   python scripts/build_change_cleanup_report.py \
     --repo-root <repo-root> \
     --json-out <report.json> \
     --markdown-out <report.md>
   ```

3. Classify each active change from the report:

   | Classification | When to use |
   | --- | --- |
   | `repair-artifacts` | Missing deltas, blocked artifacts, validation errors, placeholder content, or stale `tasks.md` |
   | `active-work` | Artifacts are coherent but implementation is still in progress |
   | `ready-for-verify-or-archive` | Tasks and validation are complete, ready for the final pass |

4. Compare change artifacts with the latest implementation, not memory.
   Inspect actual code paths, tests, workflows, and shipped behavior before editing `proposal.md`, `design.md`, `specs/**/spec.md`, or `tasks.md`.

5. When the repository follows this repo's script-backed skill-module pattern, prefer the full repair orchestrator:

   ```bash
   python scripts/reconcile_change_artifacts.py \
     --repo-root <repo-root> \
     --change <change-id>
   ```

   Add `--archive-when-ready` only when the repaired change is complete and validates cleanly.

6. Use `references/artifact-refresh.md` to refresh artifacts in the right order.
   When the checklist state is already known, apply it with:

   ```bash
   python scripts/sync_change_tasks.py \
     --tasks-file <tasks.md> \
     --update-file <task-updates.json> \
     --write-in-place
   ```

7. Re-run `openspec show --json`, `openspec status --change <id> --json`, and `openspec validate <id> --json --no-interactive` after every material refresh.
   Do not call a change clean until artifacts and validation agree.

8. Review archived entries with `references/cleanup-rules.md`.
   Only clean folders classified as `safe-cleanup-candidate`; keep `keep-history` entries intact.

## Guardrails

- **Do not edit `openspec/specs/` directly** while repairing an active change.
  Update delta specs under `openspec/changes/<change>/specs/` first.
- **Do not mark tasks complete from guesswork.**
  Confirm the latest implementation and record the evidence in task detail lines or change notes.
- **Do not delete archive history on the first pass.**
  A suspicious archive folder is a review target until it is proven to be placeholder-only, duplicated noise, or an empty scaffold.
- **Do not archive a broken change** just to make `openspec list` look cleaner.
  If artifacts drifted, repair them before the archive decision.
- **Do not rely on `completedTasks` alone.**
  Cross-check `tasks.md`, CLI validation, and the actual codebase.

## References

- `references/current-workflow.md` — OpenSpec 1.2.0 workflow and CLI surfaces.
- `references/cleanup-rules.md` — Conservative cleanup classifications and archive-preservation rules.
- `references/artifact-refresh.md` — Artifact-by-artifact reconciliation loop against the latest implementation.

## Examples

**Example 1: Repair a stale active change**
```
User: "The auth-refactor change looks outdated. Can you clean it up?"
Agent: Run the cleanup report, classify the change as repair-artifacts, compare artifacts with the latest implementation, run the reconciliation orchestrator, and re-run openspec validate before archiving.
```

**Example 2: Conservative archive cleanup**
```
User: "Can you clean up old archive entries in openspec?"
Agent: Run the cleanup report, review archive classifications (safe-cleanup-candidate vs keep-history), only remove entries proven placeholder-only or duplicated, and preserve meaningful history.
```

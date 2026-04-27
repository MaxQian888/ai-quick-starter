# OpenSpec 1.2.0 Workflow

Use this file when the repository already has `openspec/` initialized and the task is about maintaining or cleaning existing changes.

## Verified Surface

This module is aligned to OpenSpec 1.2.0. The current workflow is still:

1. create or refresh a change proposal
2. implement against the proposal artifacts
3. archive the completed change so the delta specs merge back into `openspec/specs/`

The official docs still describe `changes/` as the working area and `specs/` as the current truth. The 1.2.0 release added a one-step propose workflow, but it did not change the closeout rule: `openspec archive <change-id>` remains the operation that moves a completed change into history and syncs main specs.

## CLI Commands This Skill Relies On

- `openspec list --json`
  Use to enumerate active changes and their coarse task completion counters.
- `openspec show <change-id> --json`
  Use to inspect parsed deltas and change structure without guessing from file names.
- `openspec status --change <change-id> --json`
  Use to inspect artifact readiness, blocked dependencies, and whether `apply` still requires files such as `tasks`.
- `openspec validate <change-id> --json --no-interactive`
  Use to catch delta-format, scenario, or artifact-shape problems after each refresh.
- `openspec archive <change-id>`
  Use only after implementation and validation agree with the latest implementation.
- `openspec instructions tasks --change <change-id> --json`
  Use when you need the CLI's current task-artifact instructions before rebuilding or rewriting `tasks.md`.

## Maintenance Reading Order

1. `openspec list --json`
2. `openspec show <change-id> --json`
3. `openspec status --change <change-id> --json`
4. `openspec validate <change-id> --json --no-interactive`
5. inspect the latest implementation
6. refresh artifacts
7. re-run the same CLI checks before archive

## Notes For Cleanup Work

- `openspec/changes/archive/` is history, not a trash bin.
- A change that validates cleanly but no longer matches the latest implementation still needs reconciliation before archive.
- A change with zero parsed deltas is structurally broken even if `proposal.md` exists.

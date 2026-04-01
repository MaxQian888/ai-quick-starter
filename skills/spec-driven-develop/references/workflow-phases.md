# Workflow Phases

Use this file when the request is large enough that the preparation work needs explicit phases, or when an existing `docs/progress/MASTER.md` must be resumed instead of recreated.

## Resume First

1. Check for `docs/progress/MASTER.md`.
2. If it exists, read:
   - the current phase,
   - incomplete checklist items,
   - the most recent session-log entry,
   - and the linked phase file for the active phase.
3. Resume from that point. Do not restart Phase 0 unless the user explicitly discards the old plan.
4. Mirror the active phase into the platform's native task tool when one exists.
   - Use TodoWrite or the local equivalent for in-session visibility only.
   - Load the active phase's pending tasks into that tool.
   - Mark the current task as `in-progress` and the rest as `todo`.
   - Map priorities as `P0=high`, `P1=medium`, `P2=low`.
   - If no native task tool is available, skip this mirror step and keep `MASTER.md` as the only source of truth.

## Phase 0: Intent Recognition And Confirmation

Use this phase to remove ambiguity before analysis.

- Confirm the requested transformation.
- Confirm the target end state and constraints.
- Confirm whether the user wants:
  - planning only,
  - planning plus execution setup,
  - or planning plus immediate execution after handoff.
- If the user only wants a small localized change, stop and use a narrower skill.

## Phase 1: Deep Project Analysis

Use this phase to gather project truth.

- Inspect entrypoints, manifests, CI workflows, tests, runtime seams, and risky dependencies.
- Record stable facts in analysis notes before inferring strategy.
- Call out migration blockers, missing verification surfaces, and hidden coupling.
- If the platform supports subagents and the project is large, parallelize read-only analysis by concern. Keep synthesis on the main thread.

## Phase 2: Task Decomposition

Use this phase to convert analysis into an executable phase plan.

- Break the work into phases with clear names and end conditions.
- Give each phase a bounded objective, task list, dependency story, and verification boundary.
- Separate tasks that can run in parallel from tasks that require sequencing.
- Prefer natural checkpoints such as "shared types complete" or "verification harness green" over arbitrary file-count splits.

## Phase 3: Progress Tracking Documentation

Use this phase to materialize the progress contract.

- Create `docs/progress/MASTER.md`.
- Create one `phase-N-<name>.md` file per phase.
- Use `scripts/bootstrap_progress_docs.py` when the phase list is already structured.
- Use `references/doc-templates.md` only for manual repair or exceptional layouts.

## Phase 4: Execution-Skill Generation

Use this phase to create a child skill that can carry the work through later sessions.

- Keep the child skill scoped to the actual project and phase plan.
- Require the child skill to read `docs/progress/MASTER.md` first in every new session.
- Encode the verification boundaries and cleanup trigger.
- Avoid recreating the broad planning workflow inside the child skill.

## Phase 5: Handoff

Use this phase to make the preparation output usable.

- Summarize the target transformation.
- Summarize the main analysis findings.
- Point to `MASTER.md`, the phase files, and the child skill location.
- State what is ready for execution and what remains uncertain.

## Phase 6: Cleanup

Enter cleanup mode when all tracked tasks are complete.

- Ask whether to keep or remove `docs/progress/`.
- Ask whether the child skill should be kept for reuse.
- Remove temporary artifacts only after the user confirms.

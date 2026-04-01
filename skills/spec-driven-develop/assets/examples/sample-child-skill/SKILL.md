---
name: sample-migration-dev
description: Use when continuing the active migration or rewrite after `docs/progress/MASTER.md` already exists and execution should resume from the current phase instead of recreating the planning workflow.
---

# Sample Migration Dev

Resume the active migration from the progress files. Read the current phase, execute the next coherent task, update the phase file immediately, and leave `MASTER.md` reconciliation to the main thread.

## Session Start

1. Read `docs/progress/MASTER.md` first.
2. Identify the active phase and open the linked phase file.
3. Confirm the next task or checkpoint before changing code.
4. If the progress files are missing, stop and return to `$spec-driven-develop` instead of inventing a new plan.

## Execution Loop

1. Work only on the current phase file's next coherent task or checkpoint.
2. Preserve the verification boundaries defined by the phase plan.
3. Update the phase file immediately after finishing a task.
4. Let the main thread reconcile `MASTER.md` counts and current status after integration.

## Parallel Execution

1. Read the current phase's lane notes before parallelizing.
2. Only parallelize when write scopes are separate and the merge point is explicit.
3. Keep blocker resolution, merge decisions, and final verification synthesis on the main thread.
4. If the phase is high-risk or sequential, do not force parallel execution.

## Progress Updates

- Check off the completed task in the active phase file.
- Add a short blocker or handoff note when the task cannot be completed.
- Do not directly reconcile `MASTER.md` unless the main thread explicitly owns that step.

## Guardrails

- Do not recreate the broad planning workflow inside this child skill.
- Do not skip the phase file just because the code change looks small.
- Do not claim a task is complete until the relevant verification has run or is explicitly marked blocked.
- Do not widen scope beyond the active phase without updating the progress files first.

## Cleanup Trigger

When all tracked tasks are complete, notify the main thread so it can enter cleanup mode and ask whether to keep or remove the progress docs and this child skill.

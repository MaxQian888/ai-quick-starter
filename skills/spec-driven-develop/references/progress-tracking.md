# Progress Tracking

Use this file when creating, updating, or repairing `docs/progress/`.

## Purpose

`docs/progress/` is the durable cross-session memory surface for long-running work.

- `MASTER.md` is the top-level truth source.
- `phase-N-<name>.md` files hold task-level detail.
- Native task tools are optional mirrors for the current session only.
- The native task tool provides in-session visibility; `MASTER.md` remains the cross-session source of truth.

## Required Layout

```text
docs/
  progress/
    MASTER.md
    phase-1-<name>.md
    phase-2-<name>.md
    ...
```

## When To Use The Bootstrap Script

Use `scripts/bootstrap_progress_docs.py` when you already have a structured phase list with:

- a task name,
- a short task summary,
- one or more phase names,
- and one or more tasks per phase.

The script creates the Markdown skeleton consistently and prevents copy-paste drift.

## What MASTER.md Must Contain

- the task name and summary,
- references to the phase files,
- a phase summary table,
- a phase checklist with `(done/total tasks)` counts,
- the current status,
- the next step,
- and a short session log.

## What Each Phase File Must Contain

- the phase header and purpose,
- the task checklist with stable task IDs,
- dependencies,
- verification notes,
- freeform phase notes,
- and a short completion checklist.

## Update Rules

- Check off the phase task in the relevant phase file as soon as it is complete.
- If a native task tool exists, dual-write the active phase there as well:
  - `P0` maps to high priority,
  - `P1` maps to medium priority,
  - `P2` maps to low priority.
- Reconcile the `MASTER.md` counts after the local work is merged or the main thread has verified the result.
- If a task is blocked, leave it unchecked and add a short note instead of pretending it is done.
- If the phase ordering changes, regenerate or repair both `MASTER.md` and the phase files together.

## File Ownership Rules

- Child executors may update their phase file tasks.
- The orchestrating agent owns `MASTER.md` count reconciliation and current-status updates.
- Do not let multiple writers race on `MASTER.md`.

# Checkpoint Policy

Every execution wave must end at a checkpoint. A checkpoint is where the orchestration regains control.

## Required Checkpoint Questions

Answer all of these before starting the next wave:

1. Which work items are complete?
2. Which work items partially completed but need follow-up?
3. Did any task touch files outside its allowed write scope?
4. What verification ran, and what did not?
5. What new blockers or dependency changes appeared?
6. Are the remaining waves still valid, or must they be rebuilt?

## Minimum Return Contract

Each delegated task should come back with:

- claimed work-item id,
- changed files,
- verification run,
- open issues,
- and anything that blocks merge.

## Re-Plan Triggers

Rebuild the remaining orchestration when:

- a task discovers a new dependency,
- two write scopes collide,
- a verification command fails unexpectedly,
- the user changes scope,
- or the returned work invalidates the planned merge point.

## Closure Rule

Do not say the whole execution succeeded merely because one wave landed. Summarize verified progress, remaining scope, and anything still blocked or unverified.

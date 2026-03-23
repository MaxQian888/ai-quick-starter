# Decomposition Rules

Use this file when the team split or parallel boundary is unclear.

## Core Rules

1. Split tasks by dependency and write scope, not by vanity role names.
2. Prefer the smallest team that can work in parallel without merge collisions.
3. A task belongs in a parallel batch only if its next action does not require another task's fresh output.
4. Read-heavy discovery belongs to `explorer` first.
5. Write-heavy implementation belongs to `worker`.
6. Cross-task synthesis, docs, and cleanup default to `default`.

## Safe First-Pass Categories

- `Research`: discovery, usually `explorer`
- `Data Collection`: discovery, usually `explorer`
- `Documentation`: synthesis, usually `default`
- `Database`: implementation, usually `worker`
- `Frontend`: implementation, usually `worker`
- `Backend`: implementation, usually `worker`
- `Testing` or `Debugging`: verification, usually `worker` or custom `reviewer`

## Parallelism Heuristics

Prefer parallel:

- research + data collection
- frontend + backend, if API contracts or merge points are explicit
- docs + implementation only when the docs are scoped to active findings or status reporting

Keep serial:

- migration design before data backfill if schema is unsettled
- debugging before claiming completion
- any pair of tasks that touch the same files or same narrow interface simultaneously

## Merge-Point Rule

Every parallel batch must define:

- what gets handed off,
- who integrates it,
- and what verification happens before the next batch starts.

If you cannot describe the merge point, the batch is not ready.

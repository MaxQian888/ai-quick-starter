# Parallelism Rules

Use these rules before placing tasks in the same execution wave.

## Parallelize Only When All Of These Are True

- The next action for each task is unblocked.
- The tasks do not need each other's output to start.
- The write scopes are separate or intentionally read-only.
- The merge point is known in advance.
- The return condition is specific enough to review.

## Keep Serial When Any Of These Are True

- Two tasks edit the same file or the same narrow module boundary.
- One task defines interfaces the other task must consume.
- The work is mostly integration rather than isolated implementation.
- The batch would create more merge risk than schedule gain.
- The output contract is still unclear.

## Write-Scope Heuristics

Treat these as conflicting unless proven otherwise:

- same file,
- same component directory,
- same feature module with shared exports,
- same schema or API contract surface,
- same test file.

Read-only research can often run in parallel with write-heavy tasks, but do not hide write operations inside “research”.

## Recommended Ownership Pattern

For each delegated task, state:

- exact work-item id,
- owner,
- allowed write scope,
- forbidden areas,
- expected return artifact,
- and the checkpoint that consumes the result.

## Anti-Patterns

- “frontend” and “backend” as one vague parallel batch without file boundaries
- two agents both “helping with tests” across the same package
- delegating blocker triage away from the main thread
- using parallelism just because subagents exist

# Parallel Execution

Use this file before parallelizing analysis or later execution lanes.

## Analysis Parallelism

Parallelize analysis only when:

- the project is large enough that one pass would be slow or noisy,
- the analysis slices are independent,
- and the platform actually supports subagents.

Good splits:

- architecture versus test surface,
- backend versus frontend,
- runtime seams versus build surface.

Bad splits:

- two agents reading the same subsystem,
- overlapping write-heavy work,
- or any split where the main thread is blocked on the very next answer.

## Execution Parallelism

Parallel execution is appropriate when:

- tasks belong to the same phase or explicitly parallel phases,
- write scopes are disjoint,
- dependencies are already satisfied,
- and the merge point is clear.

## Main-Thread Duties

Keep these responsibilities on the main thread:

- blocker resolution,
- cross-cutting integration,
- merge decisions,
- verification synthesis,
- and `MASTER.md` reconciliation.

## Progress Synchronization

- Child executors update only their assigned phase file tasks.
- The main thread reconciles `MASTER.md` after the lane returns.
- If parallel work exposes new dependencies or file collisions, stop and re-plan instead of forcing the old split.

## Risk Checks

Before parallelizing, answer all three questions:

1. Are the write scopes actually separate?
2. Is the merge point explicit?
3. Can the work return to a checkpoint without hidden coupling?

If any answer is "no", keep the work sequential.

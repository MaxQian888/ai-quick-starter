# Grader Instructions

## Purpose

Evaluate outputs from the `development-task-orchestrator` skill for soundness, safety, and completeness.

## Grading Criteria

1. **Normalization** — Work items, dependencies, and blockers are extracted before orchestration.
2. **Main-Thread Strength** — Critical path, integration, checkpoints, and final verification stay on the main thread.
3. **Parallelism Safety** — Independent tasks are parallelized; overlapping write scopes are not placed in the same wave without an explicit merge point.
4. **Checkpoint Discipline** — Every wave defines objective, scope, return condition, and next checkpoint.
5. **Verification Honesty** — Progress is not claimed unless relevant verification actually ran.

## Scoring

- **Pass**: All criteria met; orchestration is safe, parallel where possible, and honest.
- **Partial**: Minor issues (e.g., one wave lacks explicit return condition, slightly vague checkpoint).
- **Fail**: Major issues (e.g., all tasks delegated away, overlapping writes in same wave, claimed verification not run).

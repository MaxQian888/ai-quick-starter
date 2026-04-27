---
name: development-task-orchestrator
description: Use whenever orchestrating development tasks from an existing spec, implementation plan, checklist, issue list, or tasks document. Make sure to use this skill for parallel execution planning, subagent coordination, checkpoint definition, blocker surfacing, merge point planning, or turning a plan into actionable execution waves. Also triggers for sprint execution, task batching, cross-cutting integration planning, or any request involving structured task orchestration with verification boundaries.
---

# Development Task Orchestrator

Turn an existing plan into an execution-ready orchestration. Normalize the task source, keep parallelism honest, reserve the main thread for integration and blockers, and make every execution wave end at a checkpoint.

## Adaptive Detection

Before orchestrating, scan the workspace to understand the project context:

1. Detect existing planning artifacts:
   - Look for `spec.md`, `tasks.md`, `TODO.md`, `checklist.md`, or `plan.md`.
   - Check for GitHub issues, project boards, or milestone files.
2. Detect project structure:
   - Look at root directories to understand monorepo vs single-package layout.
   - Check for `package.json`, `Cargo.toml`, `pyproject.toml` to infer tech stack.
3. Detect existing automation:
   - Check for CI/CD configs (`.github/workflows/`, `.gitlab-ci.yml`) to align verification steps.
   - Look for existing test scripts and lint commands.
4. Detect team conventions:
   - Check `AGENTS.md` or `CLAUDE.md` for project-specific orchestration rules.

## Start Here

1. Confirm the request already contains enough planning context:
   - spec,
   - tasks doc,
   - checklist,
   - issue list,
   - or a concrete execution brief.
2. If the input is still vague product design, stop and use a planning or design skill first.
3. Normalize the input before you talk about roles or batches.
4. Default to parallel subagent work for independent tasks, but keep integration, blockers, and final verification on the main thread.

## Workflow Rules

### 1. Normalize Before Orchestrating

Extract work items, dependencies, write scopes, blockers, merge points, and verification expectations from the source material.

Read [references/input-normalization.md](references/input-normalization.md) when the source mixes checklist items, freeform prose, and spec sections.

### 2. Keep The Main Thread Strong

The main thread owns:

- critical-path blockers,
- cross-cutting integration,
- checkpoint review,
- user-facing progress synthesis,
- and final verification.

Do not delegate all decision-making away.

### 3. Prefer Parallelism, Not Chaos

Parallelize independent work by default, but only when the next action is not blocked and the write scopes are cleanly separated.

Read [references/parallelism-rules.md](references/parallelism-rules.md) before putting two write-heavy tasks in the same wave.

### 4. Make Every Wave Return To A Checkpoint

Each batch must define:

- the objective,
- the included work items,
- the allowed write scope,
- the return condition,
- and the next checkpoint.

Read [references/checkpoint-policy.md](references/checkpoint-policy.md) when deciding whether a wave is ready to merge or must be re-planned.

### 5. Re-Plan After New Information

If returned work changes dependencies, reveals collisions, or exposes a blocker, stop and rebuild the remaining orchestration instead of pretending the old batch plan is still valid.

### 6. Verify Before Claiming Progress

Do not call a wave complete unless the relevant verification actually ran. If only part of the work was verified, say so explicitly.

## Command Shape

Generate stable artifacts before freehand orchestration edits:

```bash
python scripts/build_execution_orchestration.py --input <plan-or-checklist.md> --format auto --output-dir <out-dir>
```

Use `--format brief|tasks|checklist|spec` when auto-detection is misleading.

Read the JSON first for exact structure. Use the Markdown report for user-facing review and orchestration discussion.

## Output Contract

The generated artifacts should include:

- normalized work items,
- dependency edges,
- blocked items,
- parallel batches,
- main-thread duties,
- merge points,
- checkpoint sequence,
- risks,
- and verification boundaries.

## Examples

### Example 1: Feature Implementation Plan

**Input:** A `spec.md` with 5 features to implement across frontend and backend.

**Output:**
- Normalized work items with dependencies.
- Wave 1: Backend API changes (parallel, no frontend dependency).
- Wave 2: Frontend components (depends on Wave 1 API contracts).
- Wave 3: Integration and E2E tests (main thread, cross-cutting).

### Example 2: Bug Fix Batch

**Input:** A checklist of 10 bugs to fix.

**Output:**
- Grouped by file ownership and risk.
- Low-risk fixes in parallel waves.
- High-risk or cross-file fixes on the main thread with explicit verification.

## Guardrails

- Do not redo brainstorming when the user already handed you an execution-ready plan.
- Do not turn this into team-design work or `.toml` draft generation. That belongs to `agents-team-builder`.
- Do not place overlapping write scopes in the same batch unless the merge point is explicit and immediate.
- Do not leave a parallel wave without a checkpoint.
- Do not hide blockers inside a generic "follow-up later" bucket.
- Do not claim verification you did not run.

## Reference Files

- Read [references/execution-workflow.md](references/execution-workflow.md) for the six-step orchestration loop and main-thread duties.
- Read [references/parallelism-rules.md](references/parallelism-rules.md) for dependency and write-scope heuristics.
- Read [references/checkpoint-policy.md](references/checkpoint-policy.md) for required checkpoint questions and re-planning triggers.
- Read [references/input-normalization.md](references/input-normalization.md) for input-shape handling and normalization rules.

## Example Assets

- Use [assets/examples/sample-input.md](assets/examples/sample-input.md) for one representative source task artifact.
- Use [assets/examples/sample-orchestration.json](assets/examples/sample-orchestration.json) for the machine-readable output shape.
- Use [assets/examples/sample-orchestration.md](assets/examples/sample-orchestration.md) for the rendered review format.

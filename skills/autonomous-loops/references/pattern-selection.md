# Pattern Selection

Use this file when the user asks for autonomous execution but has not yet chosen the loop shape.

## Fast Decision Table

| Signal | Recommended Pattern | Why |
| --- | --- | --- |
| One focused change, short feedback loop, easy manual supervision | `sequential` | Fresh context every pass and low orchestration overhead |
| Repeated backlog reduction, CI repair, or progressive hardening | `iterative-pr` | Each iteration lands one coherent step and updates a notes file |
| Existing session already contains high-value context | `resume` | Reuse the session instead of replaying everything in a new prompt |
| Multiple work units with real dependencies and likely file overlap | parallel DAG | Requires explicit planning, dependency layers, and merge strategy |

## Sequential Pattern

Use when a task can be expressed as:
1. implement,
2. cleanup or review,
3. verify.

Prefer this for:
- single bugfixes,
- one feature branch,
- targeted migration slices,
- repo-local validation repair.

Avoid this when several workers need to edit the same area independently.

## Iterative PR Pattern

Use when you want repeated non-interactive runs, but each run should still stop after one meaningful increment.

Required controls:
- a notes file,
- a completion signal or hard cap,
- a review or verification gate,
- explicit handling for failed checks.

Prefer this for:
- CI failure burn-down,
- backlog cleanup,
- test coverage expansion,
- long-running “improve until done” tasks with human checkpoints.

## Resume Pattern

Use when:
- the previous session already explored the codebase deeply,
- the current task is a continuation rather than a fresh objective,
- replaying context into a new prompt would be noisy or lossy.

Do not resume blindly if:
- the scope changed materially,
- the working tree changed outside the session,
- the new task needs a different model or permission profile.

## Parallel DAG Pattern

Only use when the work truly decomposes into dependency layers.

Minimum contract:
- upfront unit decomposition,
- explicit dependency graph,
- isolated workspaces or worktrees,
- merge order or conflict recovery plan,
- independent verification per unit,
- a separate review step for non-trivial units.

Starter helper support:
- `scripts/render_loop_command.py --pattern parallel-dag` generates a conservative three-step scaffold:
  decompose,
  one-layer execution,
  merge-review.
- Use it to seed the orchestration, then adapt the unit or layer prompts to the actual repository.

If you cannot describe the dependency graph clearly, fall back to `sequential` or `iterative-pr`.

## Shared Guardrails

- Keep one notes file per loop, not one per prompt.
- Record what passed and what remains unverified.
- Carry forward concrete failure context, not generic “please fix this.”
- Stop after repeated “done” signals or repeated no-op iterations.

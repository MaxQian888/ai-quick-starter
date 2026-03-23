---
name: wave-orchestration
description: Use when a task is too large for one agent pass and Codex or Claude Code needs iterative waves of parallel subagents, explicit dependency boundaries, checkpoint-based synthesis, and concrete completion criteria instead of one-shot multi-agent advice.
---

# Wave Orchestration

## Overview

Run complex work as repeated waves:

1. assess the current state,
2. decompose only the unblocked work,
3. dispatch parallel agents,
4. integrate what came back,
5. decide whether another wave is justified.

Keep one coordinator responsible for scope, merge decisions, and completion.
Use waves when a single pass would leave too much blocked work, too many coupled threads, or too much unintegrated agent output.

## Start Here

1. Write the goal, hard constraints, and exact done condition before spawning anything.
2. Separate the immediate blocking path from sidecar work. Keep the coordinator on the blocking path.
3. Decide the output shape for the next wave.
   - Examples: patch, investigation memo, failing-test diagnosis, validation log, route map.
4. Read [references/patterns.md](references/patterns.md) when the task matches a common delivery shape.
5. Read [references/codex-adaptation.md](references/codex-adaptation.md) when operating in Codex and you need tool-level dispatch rules or prompt templates.

## Optional State Artifacts

- Default to in-memory coordination for short tasks.
- Persist wave summaries only when the work spans long runs, handoffs, or multiple synthesis passes.
- Prefer stable repo-local paths such as `artifacts/waves/wave-02-summary.md` and `artifacts/waves/wave-02/<agent>.md`.

## Wave Loop

### 1. Assess

- Review prior outputs, current repo state, and known blockers.
- Collapse duplicate threads and stale hypotheses.
- Restate what is blocked, what is unblocked, and what changed since the last wave.

### 2. Decompose

- Create only tasks that can advance now.
- Keep write scopes disjoint.
- Prefer one merge point per wave.
- Cut work into artifacts that are easy to compare and reject if needed.

### 3. Dispatch

- Spawn the smallest useful number of agents.
- Give each agent one job, one ownership boundary, and one expected artifact.
- Use read-heavy exploration agents for discovery and code-changing agents only where the merge boundary is clear.

### 4. Work Locally In Parallel

- While agents run, do coordinator work that does not duplicate them.
- Prepare integration seams, validation commands, and next-wave decisions.
- Do not sit idle waiting for results that are not yet on the critical path.

### 5. Synthesize

- Read outputs, merge the useful parts, reject weak work, and repair edges.
- Update the task state and decide whether another wave is justified.
- Stop only when the done condition is satisfied, not when agents merely stop producing output.

## Codex Rules

- Use `spawn_agent` only for independent sidecar tasks. Do not delegate the immediate blocker when the next local action depends on it.
- Reuse an existing agent with `send_input` when the follow-up stays in the same context.
- Call `wait_agent` only when blocked on a result; otherwise keep integrating local work.
- Close stale agents with `close_agent` after their outputs are consumed.
- Use `multi_tool_use.parallel` for parallel file reads and other independent local tool calls, not as a substitute for subagents.
- Keep the coordinator-visible state short and structured. Long freeform wave logs become noise quickly.

## Guardrails

- Do not use wave orchestration for single-file or clearly serial tasks.
- Do not run parallel agents against overlapping write scopes unless the merge contract is explicit.
- Do not let agents invent new scope, validation criteria, or rollout order.
- Do not use another wave as a substitute for fixing poor decomposition.
- Do not declare completion without the promised verification or delivery artifact.

## Completion Checklist

- The final state still matches the user request.
- Remaining blockers are resolved or explicitly reported.
- Required verification or review evidence exists.
- Another wave would be genuinely incremental, not retry noise.

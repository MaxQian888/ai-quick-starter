# Codex Adaptation

## Tool Mapping

| Need | Codex tool | Use it for | Avoid |
| --- | --- | --- | --- |
| Spawn new parallel work | `spawn_agent` | Independent research, scoped edits, isolated validation | Urgent blocking work the coordinator needs immediately |
| Continue same thread | `send_input` | Follow-up tasks that reuse the same context or ownership | Replacing a finished agent instead of starting clean |
| Block for a result | `wait_agent` | True critical-path waits | Polling reflexively while other local work exists |
| Clean up finished agents | `close_agent` | Shutting down stale agents after synthesis | Leaving idle agents open after integration |
| Parallel local inspection | `multi_tool_use.parallel` | Independent reads, search, and metadata collection | Multi-agent execution or dependent steps |

## Dispatch Rules

1. Keep the coordinator on the critical path.
   - If the next local step depends on the answer, do that work locally.
2. Send only bounded sidecar work to agents.
   - Good: trace one subsystem, patch one module group, verify one route family.
   - Bad: "finish the task" or "handle whatever is next."
3. Make ownership explicit for code changes.
   - Name the files or directories the agent owns.
   - Tell the agent it is not alone in the repo and must not revert unrelated edits.
4. Expect artifacts, not vibes.
   - Ask for a patch, report, checklist, or verification result.
5. Reuse agents when context is expensive.
   - If the same agent is continuing the same subsystem, use `send_input`.
   - If the task changes shape, spawn a fresh agent instead.

## Suggested Wave Shapes

### Investigation wave

- Coordinator: reproduce or inspect the blocker locally.
- Agent A: map the relevant entrypoints.
- Agent B: inspect adjacent configs or workflows.
- Agent C: gather narrow evidence from logs or docs.

### Implementation wave

- Coordinator: patch the critical seam or integration layer.
- Agent A: implement one disjoint module group.
- Agent B: update tests for the same module group only if ownership is explicit.
- Agent C: prepare validation commands or fixture updates.

### Verification wave

- Coordinator: run the main verification path and integrate quick fixes.
- Agent A: inspect failures from one subsystem.
- Agent B: review changed files for regressions or missing edge cases.

## Prompt Shapes

### Research agent

```text
Investigate <scope>. Stay inside <paths>. Return a concise report with findings, evidence, and unresolved questions. Do not edit files.
```

### Implementation agent

```text
Own <paths>. Implement <task>. You are not alone in the repo; do not revert others' work. Validate touched files if possible and report exactly what changed.
```

### Verification agent

```text
Check <scope> after the latest changes. Focus on regressions, risky assumptions, and missing validation. Return findings first with file references when possible.
```

## Waiting Discipline

- If one agent is still running but the coordinator can integrate another result, integrate first.
- If two agents return conflicting approaches, prefer the one with cleaner ownership and lower merge cost.
- If a wave returns mostly weak results, stop and redesign the decomposition before spawning again.

## Common Failure Modes

- Delegating the blocker and then waiting with nothing else to do.
- Giving multiple agents overlapping write scopes.
- Spawning a new wave before finishing the current merge.
- Treating repeated retries as progress instead of narrowing the task.
- Leaving finished agents open and losing track of ownership.

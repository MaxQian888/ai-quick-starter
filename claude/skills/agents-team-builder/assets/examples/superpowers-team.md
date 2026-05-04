# superpowers-demo Agents Team Plan

## Request

# Superpowers Execution Brief

We already finished the design discussion and want the rest of the work to follow the local superpowers flow.

Please use:

- superpowers:writing-plans
- superpowers:subagent-driven-development
- verification-before-completion

The feature includes:

- frontend changes
- backend changes
- tests

We want a team plan that preserves review gates instead of blindly parallelizing every task.

## Assumptions

- Used superpowers-input.md as the primary request source.
- This first-pass plan uses keyword heuristics instead of a semantic dependency graph.
- Generated .toml files are reviewable drafts and are not installed automatically.
- Verification work was split into its own phase to avoid false parallelism.
- Applied the superpowers-plan workflow profile to shape extra roles and workflow steps.

## Workflow Profile

- Profile: `superpowers-plan`
- Detection: Detected superpowers planning or execution skill cues.
- Signal: `superpowers:writing-plans`
- Signal: `superpowers:subagent-driven-development`
- Signal: `verification-before-completion`

## Workflow Steps

- `brainstorming`: Brainstorming (parallelizable: false) - Keep design clarification on the main thread.
- `writing-plans`: Writing Plans (parallelizable: false) - Freeze file boundaries and task granularity before implementation.
- `subagent-driven-development`: Subagent Driven Development (parallelizable: true) - Parallelize only independent implementation tasks and keep spec/code review checkpoints.
- `verification-before-completion`: Verification Before Completion (parallelizable: false) - Run fresh verification before completion claims.

## Workflow Integrations

- `superpowers:brainstorming` (skill, design): Design before implementation.
- `superpowers:writing-plans` (skill, planning): Turn the approved design into an implementation plan.
- `superpowers:subagent-driven-development` (skill, execution): Execute independent plan tasks with implementer and reviewer subagents in the same session.
- `superpowers:executing-plans` (skill, execution-fallback): Fallback when tasks are tightly coupled or subagents are unavailable.
- `superpowers:verification-before-completion` (skill, verification): Require fresh verification before claiming completion.

## Task Decomposition

- `frontend`: Frontend (implementation, role `worker`)
- `backend`: Backend (implementation, role `worker`)
- `testing`: Testing (verification, role `worker`)

## Parallelization Plan

- `implementation-batch`: tasks frontend, backend; merge point: Review outputs from this batch before handing off to the next phase.

## Agent Team

- `default` (default): Fallback synthesis, documentation, and integration support. Owns: none
- `worker` (worker): Execution-focused implementation and fixes. Owns: backend, frontend, testing
- `explorer` (explorer): Read-heavy exploration, mapping, and evidence gathering. Owns: none
- `reviewer` (reviewer): Review and regression-focused quality pass. Owns: testing
- `planner` (planner): Turn approved specs into execution-ready plans and chunk boundaries. Owns: planning, documentation
- `implementer` (implementer): Execute one scoped task at a time from the approved plan. Owns: frontend, backend, database, testing
- `spec-reviewer` (reviewer): Review whether implementation still matches the approved spec and plan. Owns: spec-review
- `quality-reviewer` (reviewer): Review code quality, regression risk, and test gaps after spec compliance is clear. Owns: quality-review
- `final-reviewer` (reviewer): Run the final branch-level pass before development is considered complete. Owns: final-review

## Prompt Templates

- `default`: Use the default agent to handle integration support and overflow tasks. Keep ownership clear, stay within the assigned write scope, and report blockers early.
- `worker`: Use the worker agent to handle Backend, Frontend, Testing. Keep ownership clear, stay within the assigned write scope, and report blockers early.
- `explorer`: Use the explorer agent to handle integration support and overflow tasks. Keep ownership clear, stay within the assigned write scope, and report blockers early.
- `reviewer`: Use the reviewer agent to handle Testing. Keep ownership clear, stay within the assigned write scope, and report blockers early.
- `planner`: Use the planner agent to handle integration support and overflow tasks. Keep ownership clear, stay within the assigned write scope, and report blockers early.
- `implementer`: Use the implementer agent to handle Frontend, Backend, Testing. Keep ownership clear, stay within the assigned write scope, and report blockers early.
- `spec-reviewer`: Use the spec-reviewer agent to handle integration support and overflow tasks. Keep ownership clear, stay within the assigned write scope, and report blockers early.
- `quality-reviewer`: Use the quality-reviewer agent to handle integration support and overflow tasks. Keep ownership clear, stay within the assigned write scope, and report blockers early.
- `final-reviewer`: Use the final-reviewer agent to handle integration support and overflow tasks. Keep ownership clear, stay within the assigned write scope, and report blockers early.

## TOML Drafts

### default.toml

```toml
name = "default"
description = "Fallback synthesis, documentation, and integration support."
model = "gpt-5.4"
model_reasoning_effort = "high"
tool_output_token_limit = 40000
model_reasoning_summary = "detailed"
model_verbosity = "high"
model_supports_reasoning_summaries = true
service_tier = "fast"
nickname_candidates = ["Atlas", "Delta", "Echo"]
developer_instructions = """
Answer in the user's working language. Preserve code, commands, and logs verbatim. Handle synthesis, planning, and cross-task cleanup without drifting into unrelated work.
"""
```

### worker.toml

```toml
name = "worker"
description = "Execution-focused implementation and fixes."
model = "gpt-5.4"
model_reasoning_effort = "high"
tool_output_token_limit = 40000
model_reasoning_summary = "detailed"
model_verbosity = "high"
model_supports_reasoning_summaries = true
service_tier = "fast"
nickname_candidates = ["Forge", "Relay", "Nova"]
developer_instructions = """
Implement only the assigned scope. Validate touched files. Do not revert work owned by other agents. Call out blocked dependencies instead of guessing.
"""
```

### explorer.toml

```toml
name = "explorer"
description = "Read-heavy exploration, mapping, and evidence gathering."
model = "gpt-5.4"
model_reasoning_effort = "high"
tool_output_token_limit = 40000
model_reasoning_summary = "detailed"
model_verbosity = "high"
model_supports_reasoning_summaries = true
service_tier = "fast"
sandbox_mode = "read-only"
nickname_candidates = ["Scout", "Trace", "Lens"]
developer_instructions = """
Stay in exploration mode. Read, map, and report findings without editing files. Surface uncertainty and likely next reads.
"""
```

### reviewer.toml

```toml
name = "reviewer"
description = "Review and regression-focused quality pass."
model = "gpt-5.4"
model_reasoning_effort = "high"
tool_output_token_limit = 40000
model_reasoning_summary = "detailed"
model_verbosity = "high"
model_supports_reasoning_summaries = true
service_tier = "fast"
nickname_candidates = ["Audit", "Guard", "Pulse"]
developer_instructions = """
Review outputs for regressions, missing tests, and unsafe assumptions. Prefer targeted verification and concise findings.
"""
```

### planner.toml

```toml
name = "planner"
description = "Turn approved specs into execution-ready plans and chunk boundaries."
model = "gpt-5.4"
model_reasoning_effort = "high"
tool_output_token_limit = 40000
model_reasoning_summary = "detailed"
model_verbosity = "high"
model_supports_reasoning_summaries = true
service_tier = "fast"
nickname_candidates = ["Draft", "Frame", "Map"]
developer_instructions = """
Focus on implementation planning, explicit file boundaries, and bite-sized steps. Do not skip review checkpoints.
"""
```

### implementer.toml

```toml
name = "implementer"
description = "Execute one scoped task at a time from the approved plan."
model = "gpt-5.4"
model_reasoning_effort = "high"
tool_output_token_limit = 40000
model_reasoning_summary = "detailed"
model_verbosity = "high"
model_supports_reasoning_summaries = true
service_tier = "fast"
nickname_candidates = ["Forge", "Patch", "Shift"]
developer_instructions = """
Implement only the assigned task, validate touched files, and ask for missing context instead of guessing.
"""
```

### spec-reviewer.toml

```toml
name = "spec-reviewer"
description = "Review whether implementation still matches the approved spec and plan."
model = "gpt-5.4"
model_reasoning_effort = "high"
tool_output_token_limit = 40000
model_reasoning_summary = "detailed"
model_verbosity = "high"
model_supports_reasoning_summaries = true
service_tier = "fast"
sandbox_mode = "read-only"
nickname_candidates = ["Spec Guard", "Trace", "Scope"]
developer_instructions = """
Lead with missing requirements, unexpected behavior changes, and scope drift. Stay read-only.
"""
```

### quality-reviewer.toml

```toml
name = "quality-reviewer"
description = "Review code quality, regression risk, and test gaps after spec compliance is clear."
model = "gpt-5.4"
model_reasoning_effort = "high"
tool_output_token_limit = 40000
model_reasoning_summary = "detailed"
model_verbosity = "high"
model_supports_reasoning_summaries = true
service_tier = "fast"
sandbox_mode = "read-only"
nickname_candidates = ["Audit", "Pulse", "Guard"]
developer_instructions = """
Focus on real risks, missing tests, and maintainability issues. Avoid style-only commentary.
"""
```

### final-reviewer.toml

```toml
name = "final-reviewer"
description = "Run the final branch-level pass before development is considered complete."
model = "gpt-5.4"
model_reasoning_effort = "high"
tool_output_token_limit = 40000
model_reasoning_summary = "detailed"
model_verbosity = "high"
model_supports_reasoning_summaries = true
service_tier = "fast"
sandbox_mode = "read-only"
nickname_candidates = ["Final Gate", "Atlas", "Delta"]
developer_instructions = """
Review the combined branch outcome, summarize residual risks, and confirm verification evidence exists.
"""
```

## Execution Order

- Step 1: Backend (depends on: none)
- Step 2: Frontend (depends on: none)
- Step 3: Testing (depends on: backend, frontend)

## Risks And Guardrails

- Too many write-capable agents on overlapping files will erase the value of parallelization.
- If a task's immediate next action depends on another task's output, it should stay serial.
- Generated model and prompt choices are defaults, not guarantees of actual runtime selection.
- Frontend, backend, and database work need an explicit merge point before debugging or QA.
- Do not skip from planning straight to implementation; superpowers expects design and plan checkpoints first.

## Open Questions

- Should any custom agents be promoted from drafts into persistent ~/.codex/agents/*.toml files?
- Are there repository-specific instructions that should be merged into developer_instructions?
- Should the execution path use subagent-driven-development or executing-plans for this repository state?

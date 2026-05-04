# ecommerce-rebuild Agents Team Plan

## Request

# Ecommerce Rebuild Brief

We are starting a new ecommerce project and want to try Codex subagents for parallel work.

Tasks:

- write product documentation
- research current competitors
- build the database schema
- collect seed catalog data from public sites
- write frontend pages
- write backend APIs
- debug integration issues

Constraints:

- keep the team small
- prefer built-in roles first
- generate reviewable `.toml` drafts instead of installing them automatically

## Assumptions

- Used ecommerce-input.md as the primary request source.
- This first-pass plan uses keyword heuristics instead of a semantic dependency graph.
- Generated .toml files are reviewable drafts and are not installed automatically.
- Verification work was split into its own phase to avoid false parallelism.

## Task Decomposition

- `research`: Research (discovery, role `explorer`)
- `documentation`: Documentation (synthesis, role `default`)
- `database`: Database (implementation, role `worker`)
- `data-collection`: Data Collection (discovery, role `explorer`)
- `frontend`: Frontend (implementation, role `worker`)
- `backend`: Backend (implementation, role `worker`)
- `debugging`: Debugging (verification, role `worker`)

## Parallelization Plan

- `discovery-batch`: tasks research, data-collection; merge point: Review outputs from this batch before handing off to the next phase.
- `implementation-batch`: tasks database, frontend, backend; merge point: Review outputs from this batch before handing off to the next phase.
- `synthesis-batch`: tasks documentation; merge point: Review outputs from this batch before handing off to the next phase.

## Agent Team

- `default` (default): Fallback synthesis, documentation, and integration support. Owns: documentation
- `worker` (worker): Execution-focused implementation and fixes. Owns: backend, database, debugging, frontend
- `explorer` (explorer): Read-heavy exploration, mapping, and evidence gathering. Owns: data-collection, research
- `reviewer` (reviewer): Review and regression-focused quality pass. Owns: debugging

## Prompt Templates

- `default`: Use the default agent to handle Documentation. Keep ownership clear, stay within the assigned write scope, and report blockers early.
- `worker`: Use the worker agent to handle Backend, Database, Debugging, Frontend. Keep ownership clear, stay within the assigned write scope, and report blockers early.
- `explorer`: Use the explorer agent to handle Data Collection, Research. Keep ownership clear, stay within the assigned write scope, and report blockers early.
- `reviewer`: Use the reviewer agent to handle Debugging. Keep ownership clear, stay within the assigned write scope, and report blockers early.

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

## Execution Order

- Step 1: Data Collection (depends on: none)
- Step 2: Research (depends on: none)
- Step 3: Backend (depends on: research, data-collection)
- Step 4: Database (depends on: research, data-collection)
- Step 5: Frontend (depends on: research, data-collection)
- Step 6: Documentation (depends on: research, data-collection, backend, database, frontend)
- Step 7: Debugging (depends on: backend, database, frontend)

## Risks And Guardrails

- Too many write-capable agents on overlapping files will erase the value of parallelization.
- If a task's immediate next action depends on another task's output, it should stay serial.
- Generated model and prompt choices are defaults, not guarantees of actual runtime selection.
- Frontend, backend, and database work need an explicit merge point before debugging or QA.

## Open Questions

- Should any custom agents be promoted from drafts into persistent ~/.codex/agents/*.toml files?
- Are there repository-specific instructions that should be merged into developer_instructions?
- Does data collection require credentials, APIs, or legal review before delegation?

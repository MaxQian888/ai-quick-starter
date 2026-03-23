# openspec-demo Agents Team Plan

## Request

# OpenSpec Workflow Brief

Use OpenSpec for this change.

Preferred command path:

- /opsx:explore
- /opsx:new
- /opsx:continue
- /opsx:ff
- /opsx:apply
- /opsx:verify
- /opsx:sync
- /opsx:archive

The change touches docs, database work, frontend, backend, and verification.

## Assumptions

- Used openspec-input.md as the primary request source.
- This first-pass plan uses keyword heuristics instead of a semantic dependency graph.
- Generated .toml files are reviewable drafts and are not installed automatically.
- Verification work was split into its own phase to avoid false parallelism.
- Applied the openspec-expanded workflow profile to shape extra roles and workflow steps.

## Workflow Profile

- Profile: `openspec-expanded`
- Detection: Detected expanded OpenSpec workflow cues from OPSX commands.
- Signal: `/opsx:explore`
- Signal: `/opsx:new`
- Signal: `/opsx:continue`
- Signal: `/opsx:ff`
- Signal: `/opsx:verify`
- Signal: `/opsx:sync`

## Workflow Steps

- `opsx:explore`: Explore (parallelizable: true) - Parallelize exploration, not artifact writes.
- `opsx:new`: New (parallelizable: false) - Create the change scaffold.
- `opsx:continue`: Continue (parallelizable: false) - Create the next dependency-ready artifact.
- `opsx:ff`: Fast Forward (parallelizable: false) - Generate planning artifacts when the shape is already clear.
- `opsx:apply`: Apply (parallelizable: true) - Parallelize implementation tasks only after artifacts are stable.
- `opsx:verify`: Verify (parallelizable: false) - Validate work against artifacts before closeout.
- `opsx:sync`: Sync (parallelizable: false) - Sync delta specs to the main spec set.
- `opsx:archive`: Archive (parallelizable: false) - Archive after verification and sync decisions.

## Workflow Integrations

- `opsx:explore` (command, discovery): Think through requirements and options before planning.
- `opsx:new` (command, planning): Scaffold a new change without filling every artifact at once.
- `opsx:continue` (command, planning): Create the next artifact when its dependencies are ready.
- `opsx:ff` (command, planning): Fast-forward planning artifacts when the scope is already clear.
- `opsx:apply` (command, execution): Implement tasks while keeping artifacts in sync.
- `opsx:verify` (command, verification): Validate implementation against artifacts.
- `opsx:sync` (command, sync): Sync delta specs to the main spec set when needed.
- `opsx:archive` (command, closeout): Archive the completed change.

## Task Decomposition

- `research`: Research (discovery, role `explorer`)
- `documentation`: Documentation (synthesis, role `default`)
- `database`: Database (implementation, role `worker`)
- `frontend`: Frontend (implementation, role `worker`)
- `backend`: Backend (implementation, role `worker`)
- `testing`: Testing (verification, role `worker`)

## Parallelization Plan

- `discovery-batch`: tasks research; merge point: Review outputs from this batch before handing off to the next phase.
- `implementation-batch`: tasks database, frontend, backend; merge point: Review outputs from this batch before handing off to the next phase.
- `synthesis-batch`: tasks documentation; merge point: Review outputs from this batch before handing off to the next phase.

## Agent Team

- `default` (default): Fallback synthesis, documentation, and integration support. Owns: documentation
- `worker` (worker): Execution-focused implementation and fixes. Owns: backend, database, frontend, testing
- `explorer` (explorer): Read-heavy exploration, mapping, and evidence gathering. Owns: research
- `reviewer` (reviewer): Review and regression-focused quality pass. Owns: testing
- `proposal-writer` (planner): Own the proposal and change framing for OpenSpec propose. Owns: proposal
- `spec-author` (planner): Define requirement-level artifacts and scenarios. Owns: specs
- `design-author` (planner): Write or refine the technical design for the change. Owns: design
- `task-planner` (planner): Break the approved design into implementation tasks. Owns: tasks
- `archiver` (archiver): Close the OpenSpec change cleanly after verification. Owns: archive
- `workflow-explorer` (explorer): Own the exploratory OpenSpec steps before artifacts are written. Owns: explore
- `verifier` (reviewer): Run the OpenSpec verify pass against artifacts and implementation. Owns: verify
- `sync-manager` (planner): Manage spec sync decisions before archiving expanded OpenSpec changes. Owns: sync

## Prompt Templates

- `default`: Use the default agent to handle Documentation. Keep ownership clear, stay within the assigned write scope, and report blockers early.
- `worker`: Use the worker agent to handle Backend, Database, Frontend, Testing. Keep ownership clear, stay within the assigned write scope, and report blockers early.
- `explorer`: Use the explorer agent to handle Research. Keep ownership clear, stay within the assigned write scope, and report blockers early.
- `reviewer`: Use the reviewer agent to handle Testing. Keep ownership clear, stay within the assigned write scope, and report blockers early.
- `proposal-writer`: Use the proposal-writer agent to handle integration support and overflow tasks. Keep ownership clear, stay within the assigned write scope, and report blockers early.
- `spec-author`: Use the spec-author agent to handle integration support and overflow tasks. Keep ownership clear, stay within the assigned write scope, and report blockers early.
- `design-author`: Use the design-author agent to handle integration support and overflow tasks. Keep ownership clear, stay within the assigned write scope, and report blockers early.
- `task-planner`: Use the task-planner agent to handle integration support and overflow tasks. Keep ownership clear, stay within the assigned write scope, and report blockers early.
- `archiver`: Use the archiver agent to handle integration support and overflow tasks. Keep ownership clear, stay within the assigned write scope, and report blockers early.
- `workflow-explorer`: Use the workflow-explorer agent to handle integration support and overflow tasks. Keep ownership clear, stay within the assigned write scope, and report blockers early.
- `verifier`: Use the verifier agent to handle integration support and overflow tasks. Keep ownership clear, stay within the assigned write scope, and report blockers early.
- `sync-manager`: Use the sync-manager agent to handle integration support and overflow tasks. Keep ownership clear, stay within the assigned write scope, and report blockers early.

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

### proposal-writer.toml

```toml
name = "proposal-writer"
description = "Own the proposal and change framing for OpenSpec propose."
model = "gpt-5.4"
model_reasoning_effort = "high"
tool_output_token_limit = 40000
model_reasoning_summary = "detailed"
model_verbosity = "high"
model_supports_reasoning_summaries = true
service_tier = "fast"
nickname_candidates = ["Pitch", "Frame", "Intent"]
developer_instructions = """
Write a clear proposal that captures intent, scope, and approach without prematurely implementing.
"""
```

### spec-author.toml

```toml
name = "spec-author"
description = "Define requirement-level artifacts and scenarios."
model = "gpt-5.4"
model_reasoning_effort = "high"
tool_output_token_limit = 40000
model_reasoning_summary = "detailed"
model_verbosity = "high"
model_supports_reasoning_summaries = true
service_tier = "fast"
nickname_candidates = ["Spec", "Scenario", "Clause"]
developer_instructions = """
Convert the proposal into concrete requirements and scenarios without collapsing into implementation chatter.
"""
```

### design-author.toml

```toml
name = "design-author"
description = "Write or refine the technical design for the change."
model = "gpt-5.4"
model_reasoning_effort = "high"
tool_output_token_limit = 40000
model_reasoning_summary = "detailed"
model_verbosity = "high"
model_supports_reasoning_summaries = true
service_tier = "fast"
nickname_candidates = ["Design", "Flow", "Bridge"]
developer_instructions = """
Translate requirements into a concrete technical approach and call out dependencies or risks.
"""
```

### task-planner.toml

```toml
name = "task-planner"
description = "Break the approved design into implementation tasks."
model = "gpt-5.4"
model_reasoning_effort = "high"
tool_output_token_limit = 40000
model_reasoning_summary = "detailed"
model_verbosity = "high"
model_supports_reasoning_summaries = true
service_tier = "fast"
nickname_candidates = ["Task", "Grid", "Sprint"]
developer_instructions = """
Write tasks that are executable, verifiable, and review-friendly. Keep dependencies explicit.
"""
```

### archiver.toml

```toml
name = "archiver"
description = "Close the OpenSpec change cleanly after verification."
model = "gpt-5.4"
model_reasoning_effort = "high"
tool_output_token_limit = 40000
model_reasoning_summary = "detailed"
model_verbosity = "high"
model_supports_reasoning_summaries = true
service_tier = "fast"
nickname_candidates = ["Archive", "Vault", "Ledger"]
developer_instructions = """
Archive only after implementation and verification are complete. Preserve artifact integrity and sync decisions.
"""
```

### workflow-explorer.toml

```toml
name = "workflow-explorer"
description = "Own the exploratory OpenSpec steps before artifacts are written."
model = "gpt-5.4-mini"
model_reasoning_effort = "medium"
tool_output_token_limit = 40000
model_reasoning_summary = "detailed"
model_verbosity = "high"
model_supports_reasoning_summaries = true
service_tier = "fast"
sandbox_mode = "read-only"
nickname_candidates = ["Explore", "Scout", "Lens"]
developer_instructions = """
Investigate options, edge cases, and repository context without editing files.
"""
```

### verifier.toml

```toml
name = "verifier"
description = "Run the OpenSpec verify pass against artifacts and implementation."
model = "gpt-5.4"
model_reasoning_effort = "high"
tool_output_token_limit = 40000
model_reasoning_summary = "detailed"
model_verbosity = "high"
model_supports_reasoning_summaries = true
service_tier = "fast"
sandbox_mode = "read-only"
nickname_candidates = ["Verify", "Check", "Proof"]
developer_instructions = """
Compare implementation against artifacts and report any mismatch before archive.
"""
```

### sync-manager.toml

```toml
name = "sync-manager"
description = "Manage spec sync decisions before archiving expanded OpenSpec changes."
model = "gpt-5.4"
model_reasoning_effort = "high"
tool_output_token_limit = 40000
model_reasoning_summary = "detailed"
model_verbosity = "high"
model_supports_reasoning_summaries = true
service_tier = "fast"
nickname_candidates = ["Sync", "Merge", "Align"]
developer_instructions = """
Sync delta specs into the main spec set carefully and avoid losing artifact intent.
"""
```

## Execution Order

- Step 1: Research (depends on: none)
- Step 2: Backend (depends on: research)
- Step 3: Database (depends on: research)
- Step 4: Frontend (depends on: research)
- Step 5: Documentation (depends on: research, backend, database, frontend)
- Step 6: Testing (depends on: backend, database, frontend)

## Risks And Guardrails

- Too many write-capable agents on overlapping files will erase the value of parallelization.
- If a task's immediate next action depends on another task's output, it should stay serial.
- Generated model and prompt choices are defaults, not guarantees of actual runtime selection.
- Frontend, backend, and database work need an explicit merge point before debugging or QA.
- Do not parallelize artifact-authoring commands and implementation in the same uncontrolled batch.
- Verify and sync are closeout gates; they should not run concurrently with active feature implementation.

## Open Questions

- Should any custom agents be promoted from drafts into persistent ~/.codex/agents/*.toml files?
- Are there repository-specific instructions that should be merged into developer_instructions?
- Does this repository use the core OpenSpec profile or the expanded OPSX command set in practice?

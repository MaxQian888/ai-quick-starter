---
name: agent-tool-benchmark-builder
description: Use when designing or upgrading benchmark suites for tool-using LLM agents, especially to score tool selection and argument correctness, convert real agent tasks into structured eval cases, compare coding agents with function-calling agents, or produce reusable benchmark packs with tasks, rubrics, judge prompts, and result tables.
---

# Agent Tool Benchmark Builder

## Overview

Design benchmark packs for tool-using agents instead of writing loose eval advice. Default to a benchmark whose primary signal is `tool selection + argument correctness`, then layer stricter trajectory checks only when the user asks for multi-step planning or recovery behavior.

Treat this skill as the default path when a request sounds like:
- "Design a benchmark for a tool-using agent."
- "Turn these agent tasks into an eval set."
- "Compare function-calling models on tool choice."
- "Create judge prompts and scoring rules for agent traces."

## Start Here

1. Confirm the benchmark surface:
   - Coding/tool agent with rich tools.
   - Function-calling agent with explicit JSON schema.
   - Hybrid benchmark that must compare both.
2. Confirm the primary capability under test.
   - Default: tool choice and argument correctness.
   - Optional expansion: ordering, multi-turn clarification, recovery.
3. Read [references/official-sources.md](references/official-sources.md) first for benchmark patterns worth reusing.
4. Read only the reference files needed for the current task:
   - Quick scoping: [references/triage-checklist.md](references/triage-checklist.md)
   - Workflow and benchmark assembly: [references/benchmark-workflow.md](references/benchmark-workflow.md)
   - Task field definitions: [references/task-schema.md](references/task-schema.md)
   - Scoring design: [references/scoring-rubric.md](references/scoring-rubric.md)
   - Judge prompt and metrics: [references/judge-and-metrics.md](references/judge-and-metrics.md)
   - Leakage and validity checks: [references/leakage-and-validity.md](references/leakage-and-validity.md)
   - Cross-runtime mapping: [references/portability-map.md](references/portability-map.md)

## Workflow

### 1. Normalize the Agent Surface

Extract the benchmark into a vendor-neutral middle layer:
- user request
- available tools
- tool argument contract
- environment or preconditions
- acceptable outcomes
- forbidden shortcuts

If the user gives only tool names or only traces, stop and reconstruct the missing contracts before writing tasks.

### 2. Start from Real Tasks

Prefer real agent work over synthetic trivia. Convert concrete tasks into eval cases that preserve:
- the actual ambiguity between tools
- the parameter burden
- the dependency on prior state
- the reason a wrong tool is plausibly tempting

Do not write twenty shallow tasks that differ only by nouns. A smaller pack with real tool confusion is better.

### 3. Write Structured Tasks

Every task should define:
- the user request
- the available tools
- the expected primary tool
- the required arguments
- allowed alternative calls, if any
- forbidden tools or invalid shortcuts
- evidence for why the gold call is right
- expected failure modes

Use [references/task-schema.md](references/task-schema.md) and start from `assets/benchmark-pack/tasks.template.yaml`.

### 4. Score the Right Failure Boundary

Default scoring splits into:
- `tool_choice`
- `arg_correctness`
- `call_format`
- `misuse_penalty`

This keeps the benchmark diagnostic. A task can fail overall while still revealing whether the model picked the right tool but filled the wrong parameters.

Default to both scoring modes:
- `strict`: exact tool, required args, and ordering expectations
- `tolerant`: allow aliases, harmless extra fields, or semantically equivalent arguments

### 5. Build the Judge Carefully

The judge should consume:
- the task definition
- the tool contract
- the agent trace or final tool call
- the scoring mode

The judge should output structured JSON, not prose. Start from `assets/benchmark-pack/judge-prompt.template.md` and [references/judge-and-metrics.md](references/judge-and-metrics.md).

### 6. Run Validity Checks Before Declaring the Benchmark Good

Check for:
- answer leakage through tool names or task wording
- hidden environment assumptions
- overfit gold answers that reject valid equivalents
- score inflation from chatty but wrong traces
- benchmark structure that only works for one agent runtime

Use [references/leakage-and-validity.md](references/leakage-and-validity.md) before handing off the pack.

## Output Requirements

Unless the user narrows the scope, produce all of the following:

1. A benchmark task pack.
2. A tool contract file.
3. A scoring rubric with strict and tolerant modes.
4. A judge prompt with JSON output requirements.
5. A result table template.
6. A short note explaining what the benchmark truly measures and what it does not.

## Implementation Rules

- Optimize first for tool selection and parameter correctness. Do not quietly drift into a generic "agent quality" benchmark.
- Prefer executable or near-executable tool contracts over vague tool descriptions.
- Include irrelevance or abstention cases when the right behavior is "do not call any tool."
- Penalize unnecessary tool calls separately from wrong primary-tool selection.
- If the benchmark must compare coding agents and function-calling agents, write tasks against the neutral schema first, then map them with [references/portability-map.md](references/portability-map.md).
- Keep benchmark tasks independent unless the user explicitly asks for multi-turn or stateful trajectories.

## Assets

Use the bundled assets as the starting point:
- `assets/benchmark-pack/tasks.template.yaml`
- `assets/benchmark-pack/tools.template.yaml`
- `assets/benchmark-pack/rubric.template.yaml`
- `assets/benchmark-pack/judge-prompt.template.md`
- `assets/benchmark-pack/results.template.csv`
- `assets/examples/tool-selection-baseline.yaml`

Copy and adapt them instead of inventing ad hoc output formats.

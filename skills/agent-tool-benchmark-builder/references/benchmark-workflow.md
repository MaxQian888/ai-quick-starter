# Benchmark Workflow

Follow this workflow to turn real agent work into a benchmark pack.

## 1. Collect Candidate Tasks

Start from real workflows, support tickets, playground traces, or existing eval cases. Favor tasks where:
- two or more tools plausibly compete
- required arguments are non-trivial
- the wrong tool can still look superficially reasonable

Discard tasks that only test memorized facts or can be solved without touching the tool layer.

## 2. Normalize the Task

Write each task in a neutral form:
- user request
- context and preconditions
- available tools
- expected primary tool
- expected arguments
- acceptable alternatives
- forbidden shortcuts

Use the neutral form before mapping to a concrete runtime.

## 3. Pick the Validation Boundary

Choose the lowest truthful boundary:
- structured-call matching only
- structured-call plus argument semantics
- executable environment outcome

Use executable checks when the environment is stable enough. Otherwise keep the benchmark at the trace layer and say so explicitly.

## 4. Add Negative Coverage

Do not create only positive examples. Include:
- irrelevance or abstention tasks
- confusing near-neighbor tools
- incomplete user requests that should trigger clarification
- parameter traps, such as missing required fields or wrong field names

## 5. Write the Judge

The judge should read only the task, tool contract, trace, and scoring mode. It should not depend on hidden human context.

Prefer structured JSON outputs with:
- per-dimension scores
- a final score
- brief machine-readable reason codes

## 6. Package the Benchmark

Ship the benchmark as:
- tasks file
- tools file
- rubric file
- judge prompt
- results table template
- example case

Keep the pack editable by humans. YAML, Markdown, and CSV are the default choices here.

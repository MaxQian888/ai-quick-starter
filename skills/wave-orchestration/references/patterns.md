# Wave Patterns

## Contents

- [Feature delivery](#feature-delivery)
- [Repository investigation](#repository-investigation)
- [Review-and-fix loop](#review-and-fix-loop)
- [Research synthesis](#research-synthesis)
- [Anti-patterns](#anti-patterns)

## Feature Delivery

Use when one feature spans multiple seams but the work can still be merged in stages.

### Wave 1

- Coordinator: pin the acceptance criteria and inspect existing seams.
- Agent A: map the backend or data boundary.
- Agent B: map the UI or caller boundary.
- Agent C: identify tests or verification commands that will prove the change.

### Wave 2

- Coordinator: implement the main integration seam.
- Agent A: patch one disjoint module group.
- Agent B: patch another disjoint module group.

### Wave 3

- Coordinator: run validation and merge quick repairs.
- Agent A: investigate the first failure cluster.
- Agent B: review changed files for regressions.

## Repository Investigation

Use when the goal is understanding before editing.

### Wave 1

- Coordinator: define the exact question.
- Agent A: find entrypoints.
- Agent B: find configs, scripts, or workflows tied to the question.
- Agent C: locate tests, docs, or prior artifacts.

### Wave 2

- Coordinator: narrow the answer shape.
- Agent A: deep-dive subsystem one.
- Agent B: deep-dive subsystem two.

### Wave 3

- Coordinator: synthesize a single map or report.
- Optional agent: spot-check unclear evidence only.

## Review-And-Fix Loop

Use when a review or failing gate surfaces multiple issues with different scopes.

### Wave 1

- Coordinator: cluster findings by subsystem and severity.
- Agent A: verify finding cluster one.
- Agent B: verify finding cluster two.
- Agent C: verify whether a suspected regression is real.

### Wave 2

- Coordinator: fix the main blocker locally.
- Agent A: fix one independent cluster with explicit ownership.
- Agent B: prepare or update focused validation for that cluster.

### Wave 3

- Coordinator: run the gate again.
- Agent A: inspect any new failure that appeared after the fixes.

## Research Synthesis

Use when the user needs breadth first, then a single merged answer.

### Wave 1

- Coordinator: define the comparison rubric.
- Agent A: collect track one.
- Agent B: collect track two.
- Agent C: collect current constraints or baseline facts.

### Wave 2

- Coordinator: normalize the evidence into one table or matrix.
- Optional agent: fill one specific evidence gap.

### Wave 3

- Coordinator: write the recommendation, caveats, and next steps.

## Anti-Patterns

- Spawning a wave for work that is already obviously serial.
- Letting every agent touch the same files.
- Asking agents to "just keep going" without a concrete artifact.
- Starting the next wave before merging the current one.
- Treating wave count as a success metric.

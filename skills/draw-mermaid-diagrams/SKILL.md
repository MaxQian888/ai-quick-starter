---
name: draw-mermaid-diagrams
description: Create, revise, and explain Mermaid diagram source (.mmd files or fenced mermaid blocks) from natural-language requirements. Use when users ask to draw process or architecture diagrams, convert text/specs to Mermaid, fix Mermaid syntax/rendering errors, or improve diagram readability and layout.
---

# Draw Mermaid Diagrams

## Overview

Generate valid Mermaid code quickly, with the right diagram type and clear structure.
Produce outputs that are easy to paste into Markdown, docs, or Mermaid-compatible tools.

## Core Workflow

1. Extract intent and entities.
Determine what must be shown: actors, states, steps, decisions, data objects, and relationships.

2. Select the diagram type before writing code.
Use:
- `flowchart` for process logic and branching.
- `sequenceDiagram` for interactions over time.
- `stateDiagram-v2` for state transitions.
- `classDiagram` for object models.
- `erDiagram` for data entities and cardinality.
- `journey`, `gantt`, `mindmap`, or `pie` for specialized views.
Use [Mermaid Cheat Sheet](references/mermaid-cheatsheet.md) for syntax patterns.

3. Draft a minimal valid diagram first.
Start with the smallest structure that renders correctly, then add detail incrementally.
Prefer stable IDs and short labels to reduce parse issues.

4. Apply readability rules.
- Keep edge labels concise.
- Split large graphs into subgraphs or multiple diagrams.
- Avoid excessive crossing edges.
- Use consistent direction (`TD` or `LR`) and naming style.

5. Validate before returning.
Check for balanced brackets, valid arrows, proper keywords, and coherent node references.
If user input is ambiguous, state assumptions explicitly and continue with a best-fit draft.

## Output Contract

- Default to fenced Markdown Mermaid output:
```mermaid
flowchart TD
  A[Start] --> B[Do Work]
```
- Add a short "Assumptions" section only when needed.
- If asked to edit existing Mermaid, preserve original semantics and only change requested parts.
- If asked for multiple options, provide 2-3 variants with brief tradeoffs.

## Debugging Rules

- Reproduce and isolate the smallest failing snippet.
- Check diagram-type-specific syntax first (for example `sequenceDiagram` participants, `erDiagram` relationship forms).
- Replace suspicious labels with plain ASCII if parser errors are unclear.
- When syntax cannot be fully verified locally, mark uncertain lines and provide a conservative fallback version.

## Quality Checklist

- Diagram type matches the user goal.
- Code is syntactically plausible Mermaid.
- Node IDs are unique and reused consistently.
- Direction and naming are consistent.
- Output is copy-paste ready.

# Grader Instructions

## Purpose

Evaluate outputs from the `draw-mermaid-diagrams` skill for syntactic correctness, readability, and intent match.

## Grading Criteria

1. **Syntax Validity** — Mermaid code has balanced brackets, valid arrows, proper keywords, and coherent node references.
2. **Diagram Type Match** — Selected diagram type (flowchart, sequenceDiagram, etc.) fits the user's intent.
3. **Readability** — Edge labels are concise; large graphs are split; direction and naming are consistent.
4. **Copy-Paste Ready** — Output is fenced Markdown that renders without modification.
5. **Edit Preservation** — When editing existing diagrams, original semantics are preserved except for requested changes.

## Scoring

- **Pass**: All criteria met; diagram is valid, readable, and intent-aligned.
- **Partial**: Minor issues (e.g., one unclear label, slightly inconsistent naming).
- **Fail**: Major issues (e.g., syntax errors, wrong diagram type, altered unrequested semantics).

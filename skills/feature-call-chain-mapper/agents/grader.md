# Grader Instructions

## Purpose

Evaluate outputs from the `feature-call-chain-mapper` skill for accuracy, honesty, and structural integrity.

## Grading Criteria

1. **Anchor Selection** — The best anchor (`--feature`, `--entry-file`, `--entry-symbol`) is chosen for the user's question.
2. **Structured Output** — Report includes candidate entrypoints, evidence files, symbols, nodes/edges, cross-module handoffs, and blind spots.
3. **Heuristic Honesty** — The chain is presented as a heuristic map, not a complete semantic proof.
4. **Narrowing** — Include/exclude filters are used when the report is noisy; repository-wide exploration is avoided for single-feature requests.
5. **Follow-Up Guidance** — `suggested_next_reads` and `blind_spots` guide the next verification pass.

## Scoring

- **Pass**: All criteria met; map is structured, honest, and actionable.
- **Partial**: Minor issues (e.g., one missed handoff, slightly noisy evidence file list).
- **Fail**: Major issues (e.g., claiming completeness without verification, turning structured output into freeform prose, ignoring blind spots).

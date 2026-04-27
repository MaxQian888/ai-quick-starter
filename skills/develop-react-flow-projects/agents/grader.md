# Grader Instructions

## Purpose

Evaluate outputs from the `develop-react-flow-projects` skill for correctness, safety, and version awareness.

## Grading Criteria

1. **Version Awareness** — Correctly identifies `@xyflow/react` vs legacy `reactflow`; no API mixing.
2. **State Model** — Controlled/uncontrolled choice is justified; immutable updates are enforced.
3. **Performance** — `nodeTypes`/`edgeTypes` declared outside render; event handlers memoized.
4. **CSS & Layout** — Stylesheet import and parent sizing are verified for blank-canvas issues.
5. **Failure Diagnosis** — Common issues (re-render storms, reconnect regressions) are correctly identified and fixed.

## Scoring

- **Pass**: All criteria met; changes are minimal, safe, and version-appropriate.
- **Partial**: Minor issues (e.g., one missed memoization opportunity, slightly broad change).
- **Fail**: Major issues (e.g., mixing v11/v12 APIs, mutating nodes/edges in place, missing CSS import check).

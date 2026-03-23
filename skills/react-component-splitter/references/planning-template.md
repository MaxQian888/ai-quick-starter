# Planning Template

Use this template before editing files when the component is large or high-risk.

## 1) Scope and Constraints

- Target file:
- Must-preserve behavior:
- Public API constraints (props/export/import path):
- Non-goals (what not to change):

## 2) Structure Detection Summary

- Framework + router:
- Architecture style:
- Recommended directories:
  - components:
  - hooks:
  - utils:
  - types:
- Evidence notes:

## 3) Candidate Split Map

List each planned extraction from the analysis script and your decision.

| Candidate ID | Decision (Use/Skip) | Destination File | Responsibility |
| --- | --- | --- | --- |
| C1 |  |  |  |
| C2 |  |  |  |
| C3 |  |  |  |

## 4) Stepwise Edit Plan

1. Create destination files with minimal skeletons and exports.
2. Move presentational JSX blocks first and keep props explicit.
3. Move reusable logic into hooks/utilities.
4. Move shared types/constants last.
5. Replace original blocks with imports.
6. Remove dead code and unused imports.

## 5) Verification Plan

- Lint/typecheck command:
- Unit/integration test command:
- Manual check scenarios:
  - Loading state
  - Error state
  - Empty state
  - Primary user interaction path

## 6) Rollback Point

- Smallest safe rollback commit boundary:
- Files that should not be touched in this refactor:

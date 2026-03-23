# Split Playbook

Use this sequence to split a large React component with minimal regression risk.

## 1. Classify Responsibilities

Tag each block in the source component:

- `UI`: JSX rendering and visual composition
- `State`: local state, reducers, memoized derivations
- `Effect`: async side effects, subscriptions, timers
- `Data`: fetch/mutation client interaction
- `Domain`: validation, transforms, formatting

Use these tags to define extraction boundaries instead of splitting by line count.

## 2. Define Target File Set

Create the smallest useful set:

- Container/orchestrator component (keeps state wiring and composition)
- 1..N presentational components
- Optional custom hooks for reusable state/effect logic
- Optional utility module for pure functions
- Optional type module if types are shared across extracted files

## 3. Extraction Order

1. Extract pure presentational components first.
2. Extract pure helper functions next.
3. Extract custom hooks after UI shape stabilizes.
4. Leave routing/data orchestration in the container unless it is clearly reusable.

This order keeps behavior easy to verify after each step.

## 4. Boundary Heuristics

- Extract when JSX block is repeated or has a clear semantic role.
- Extract hook when state/effect logic can be reused or independently tested.
- Keep logic in container when it is route-specific and single-use.
- Avoid creating one-file-per-fragment noise.

## 5. Prop and State Rules

- Pass the minimal prop surface to each child.
- Avoid deep prop chains; consider a local context only when many siblings share state.
- Preserve controlled/uncontrolled input behavior.
- Keep memoization only when profiling or existing code indicates need.

## 6. Regression Checklist

- Preserve DOM semantics and accessibility attributes.
- Preserve public exports and import paths unless explicitly changing API.
- Preserve loading/empty/error states.
- Preserve keyboard interactions and event ordering.
- Preserve test expectations or update tests with documented rationale.

## 7. Anti-patterns

- Splitting solely by file length.
- Moving all logic to hooks without ownership clarity.
- Creating a new architecture that conflicts with repository conventions.
- Introducing barrel files where none exist.
- Performing broad rename/move alongside behavior changes.

## 8. Interpreting Analyzer Output

Use `scripts/analyze_component_split.py` output as triage input:

- `risk_level=high`: require a written split plan before editing.
- `risk_level=medium`: prefer two-phase extraction (UI first, then logic).
- `risk_level=low`: direct refactor is acceptable if tests are strong.

Candidate handling rules:

1. Apply `high` priority candidates unless they conflict with local architecture.
2. Apply `medium` candidates when they reduce coupling or test complexity.
3. Apply `low` candidates only when they improve readability without churn.

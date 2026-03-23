---
name: react-component-splitter
description: Split large React or Next.js components into maintainable small components while preserving behavior and matching the repository's existing structure. Use when a .tsx/.jsx file mixes UI, state, side effects, and data fetching, when users ask to refactor or decompose components, or when a component becomes hard to test and reuse.
---

# React Component Splitter

## Overview

Refactor monolithic React components into focused files with clear responsibilities.
Detect local project conventions first, then place extracted files where the repository already expects them.

## Workflow

1. Identify non-negotiables before editing: behavior, public props, exported names, route contract, visual output, and test expectations.
2. Detect project conventions before creating files.
   - Run `python scripts/detect_react_layout.py --root <repo-root> --target <component-file> --pretty`.
   - Load `references/structure-mapping.md` and select the closest matching placement pattern.
3. Analyze the target component to produce split candidates.
   - Run `python scripts/analyze_component_split.py --file <component-file> [--layout-json <layout-json-file>] --pretty`.
   - Use the candidate list as a starting point, not a strict mandate.
4. Build a split plan using `references/split-playbook.md` and `references/planning-template.md`.
   - Keep one container component as orchestrator.
   - Extract leaf UI subcomponents first, then custom hooks, then pure utilities.
   - Move types/constants with their owners.
5. Implement incrementally.
   - Keep existing props/API stable unless the user requests a breaking change.
   - Replace extracted JSX blocks with imports one block at a time.
   - Avoid broad path reshuffles.
6. Verify and report.
   - Run lint/typecheck/tests for touched scope.
   - Check for import cycles and unnecessary prop drilling.
   - Confirm new file locations still match detected project structure.

## Execution Snippets

```bash
# 1) Detect repository layout
python scripts/detect_react_layout.py --root . --target src/features/orders/OrdersPage.tsx --pretty > .tmp.layout.json

# 2) Analyze split candidates for the large component
python scripts/analyze_component_split.py --file src/features/orders/OrdersPage.tsx --layout-json .tmp.layout.json --pretty > .tmp.split.json
```

Use `.tmp.layout.json` and `.tmp.split.json` to fill the plan template before editing code.

## Placement Rules

- Follow existing folder conventions over generic best practices.
- Prefer nearest-neighbor placement: mimic sibling feature/page directories before introducing new top-level folders.
- Keep route entry files thin (`page.tsx`, `layout.tsx`, `index.tsx`) and move heavy logic below route-level folders when the project already does this.
- Co-locate styles/tests/stories only when the repository already co-locates them.
- Reuse established alias and barrel-export patterns; do not introduce new conventions unprompted.

## Guardrails

- Preserve runtime behavior by default; treat behavior change as opt-in.
- Separate concerns by role: container/state, presentational UI, hooks, and utilities.
- Keep state ownership near the highest component that needs to coordinate it.
- Avoid extracting tiny wrappers that reduce readability without reuse value.
- Keep names explicit: `<Feature><Role>.tsx`, `use<Feature><Action>.ts`, `<feature>.types.ts`.

## Deliverables

Return these items in the final response:

1. Split plan (for large refactors) with boundaries and file destinations.
2. List of created/updated files and each file's responsibility.
3. Validation summary and residual risks.
4. Optional: attach analysis JSON summaries when the refactor is large or high risk.

## Reference Files

- `references/split-playbook.md`: Extraction order, boundary heuristics, and anti-pattern checks.
- `references/structure-mapping.md`: Placement rules for Next.js/Vite/CRA and feature-first vs layer-first repos.
- `references/planning-template.md`: Copyable split plan template with destination mapping and rollback points.

## Script

- `scripts/detect_react_layout.py`: Scan a repository and output JSON recommendations for component/hook/utility placement.
- `scripts/analyze_component_split.py`: Analyze a target component and output split candidates with risk level and suggested destination files.

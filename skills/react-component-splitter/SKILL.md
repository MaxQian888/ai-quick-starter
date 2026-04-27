---
name: react-component-splitter
description: |
  Use whenever you need to split large React or Next.js components into maintainable smaller components while preserving behavior and matching existing repository structure, especially when a .tsx or .jsx file mixes UI, state, side effects, and data fetching or becomes hard to test and reuse. Make sure to use this skill whenever the user says "split this component", "refactor React", "component too big", "extract hook", "break into smaller files", or "make this testable" — even for partial extractions or when only one concern (like a hook or utility) should be pulled out. Also trigger when a component exceeds 300 lines, has deeply nested JSX, or mixes presentation with data fetching. Covers React, Next.js, Vite, CRA, and feature-based or layer-based repositories.
---

# React Component Splitter

## Overview

Refactor monolithic React components into focused files with clear responsibilities.
Detect local project conventions first, then place extracted files where the repository already expects them.

## Adaptive Detection

Before splitting, detect project conventions:

1. **Framework**: Check for Next.js (`app/`, `pages/`), Vite, CRA, or Remix.
2. **Folder structure**: Look for feature-based (`features/`), layer-based (`components/`, `hooks/`, `utils/`), or domain-based organization.
3. **Styling**: Note CSS Modules, Styled Components, Tailwind, or inline styles.
4. **State management**: Identify Redux, Zustand, Context API, or local state patterns.
5. **Testing**: Check for Jest, Vitest, React Testing Library, or Playwright conventions.

Use these signals to match the split plan to existing conventions.

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

## Examples

### Example 1: Detect layout and analyze a large page

```bash
python scripts/detect_react_layout.py --root . --target src/features/orders/OrdersPage.tsx --pretty > .tmp.layout.json
python scripts/analyze_component_split.py --file src/features/orders/OrdersPage.tsx --layout-json .tmp.layout.json --pretty > .tmp.split.json
```

## Reference Files

- `references/split-playbook.md`: Extraction order, boundary heuristics, and anti-pattern checks.
- `references/structure-mapping.md`: Placement rules for Next.js/Vite/CRA and feature-first vs layer-first repos.
- `references/planning-template.md`: Copyable split plan template with destination mapping and rollback points.

## Script

- `scripts/detect_react_layout.py`: Scan a repository and output JSON recommendations for component/hook/utility placement.
- `scripts/analyze_component_split.py`: Analyze a target component and output split candidates with risk level and suggested destination files.

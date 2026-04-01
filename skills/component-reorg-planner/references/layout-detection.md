# Layout Detection

Use `scripts/detect_component_context.py` before interpreting any component names.

## Detection Order

1. Detect `framework` from `package.json`.
2. Detect `router` from `src/app`, `app`, `src/pages`, or `pages`.
3. Prefer a target-local boundary over repo-wide guesses:
   - if the target sits under `features/`, `modules/`, or `domains/`, treat it as `feature-first`
   - if the target sits under a Next.js route segment with `page.tsx`, `layout.tsx`, or `route.ts`, treat it as `route-first`
   - otherwise fall back to repo-wide `layer-first`, `mixed`, or `unknown`

## Recommended Support Paths

- `feature-first`: keep hooks, utils, and types under the same feature root
- `route-first`: keep hooks and utils under the same route segment
- `layer-first` or `mixed`: keep support files in the existing shared layer roots and only reorganize the target component directory

## Stop Conditions

- If the target cannot be mapped to a stable local boundary, do not invent one.
- If the repository is `mixed`, keep the plan local to the target directory.
- If the target is not a component directory, stop and confirm scope before planning.

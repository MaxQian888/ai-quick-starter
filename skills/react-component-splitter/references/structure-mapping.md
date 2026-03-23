# Structure Mapping

Use this file after running `scripts/detect_react_layout.py`.
Apply the "closest existing convention wins" rule: mimic nearby patterns before inventing new ones.

## Framework + Router Placement

### Next.js App Router

- Keep route entry files thin: `app/**/page.tsx`, `app/**/layout.tsx`.
- Place extracted UI blocks under the nearest route folder first:
  - `app/<segment>/components/`
  - `app/<segment>/hooks/` when route-specific logic exists
- If the repository already has shared feature folders, place reusable units there instead:
  - `src/features/<feature>/components/`
  - `src/features/<feature>/hooks/`

### Next.js Pages Router

- Keep page files orchestration-only: `pages/**/*.tsx`.
- Extract page-specific parts into:
  - `pages/<feature>/components/` when project keeps page-local modules
  - `src/features/<feature>/...` when repository is feature-first

### Vite / CRA / Generic React

- If layer-first:
  - `src/components/`
  - `src/hooks/`
  - `src/lib/` or `src/utils/`
- If feature-first:
  - `src/features/<feature>/components/`
  - `src/features/<feature>/hooks/`
  - `src/features/<feature>/services/`

## Architecture Decision Rules

1. Follow existing dominant pattern detected in siblings and imports.
2. Keep all extracted files inside the same feature boundary unless cross-feature reuse is proven.
3. Promote to shared folders only for real multi-feature reuse.
4. Do not create new top-level folders without evidence of existing equivalents.

## Monorepo and Package Boundaries

- Keep extracted files inside the same package/workspace as the source component by default.
- Do not move feature code across package boundaries during split-only refactors.
- Share logic across packages only through existing shared packages (for example `ui`, `shared`, `design-system`) already used in the repo.
- Preserve each package's local lint, tsconfig alias, and test conventions.

## Naming Rules

- Component: `<Feature><Role>.tsx` (example: `OrdersFilterPanel.tsx`)
- Hook: `use<Feature><Action>.ts` (example: `useOrdersFilter.ts`)
- Utility: `<feature>.<purpose>.ts` or existing local style
- Types: `<feature>.types.ts` or `types.ts` if already standard in that folder

## Sidecar File Rules

- Keep style files where the component currently expects them.
- Keep stories/tests near component only if co-location is already standard.
- Keep index barrel files only when the folder already uses barrels.

## Import and Alias Rules

- Preserve alias style (`@/`, `~`, relative-only) used by nearby files.
- Prefer existing path depth style (short alias vs relative) for consistency.
- Validate no circular imports after extraction.

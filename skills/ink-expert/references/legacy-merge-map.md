# Legacy Merge Map (ink-cli + ink-skill-main/ink)

This skill intentionally merges and normalizes two existing local skill sets:

1. `D:\Project\skills-test\ink-cli`
2. `D:\Project\skills-test\ink-skill-main\ink`

## What Was Kept from `ink-cli`

- Quick-start usage orientation.
- Practical CLI patterns (spinner, list, progress UI).
- Ecosystem package awareness.

## What Was Kept from `ink-skill-main/ink`

- API-by-surface organization (components/hooks/render/instance/focus/input).
- Stronger documentation granularity for lifecycle and accessibility concerns.

## What Was Upgraded in `ink-expert`

- Version baseline updated to current Ink v6 era and React 19 baseline.
- Added missing modern APIs (`usePaste`, `useBoxMetrics`, `useWindowSize`, `useCursor`, `renderToString`, `waitUntilRenderFlush`).
- Added scaffold drift warnings for `create-ink-app` template versions.
- Added migration and triage workflows for real maintenance tasks.

## Maintenance Rule

When either legacy source skill is updated, re-run this merge map and refresh:

- `official-sources.md`
- `api-v6.md`
- `bootstrap-and-migration.md`
- `testing-and-debugging.md`
- `component-ecosystem.md`

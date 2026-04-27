# Official Sources (Snapshot: 2026-03-18)

Use this file as the single source of truth for version-sensitive guidance.
Re-check these URLs when a task explicitly requests "latest" details.

## Core Ink

- Repository: https://github.com/vadimdemedes/ink
- Latest release shown on repo page: `v6.8.0` (published 2026-02-19)
- Package metadata source: https://raw.githubusercontent.com/vadimdemedes/ink/master/package.json
- Observed baseline from package metadata:
  - `version`: `6.8.0`
  - `engines.node`: `>=20`
  - `peerDependencies.react`: `>=19.1.1`

## create-ink-app (Scaffold Tool)

- Repository: https://github.com/vadimdemedes/create-ink-app
- Latest release shown on repo page: `v3.0.2` (2023)
- Package metadata source: https://raw.githubusercontent.com/vadimdemedes/create-ink-app/main/package.json
- Template package files (important for drift checks):
  - JS template: https://github.com/vadimdemedes/create-ink-app/blob/main/templates/js/_package.json
  - TS template: https://github.com/vadimdemedes/create-ink-app/blob/main/templates/ts/_package.json
- Observed template baseline (both JS/TS templates):
  - `ink`: `4.1.0`
  - `react`: `18.2.0`

## Testing Library

- Repository: https://github.com/vadimdemedes/ink-testing-library
- Package metadata source: https://raw.githubusercontent.com/vadimdemedes/ink-testing-library/master/package.json
- Observed baseline:
  - `version`: `4.0.0`
  - `engines.node`: `>=20`

## Component Ecosystem

- Official component suite: https://github.com/vadimdemedes/ink-ui
- Package metadata source: https://raw.githubusercontent.com/vadimdemedes/ink-ui/main/package.json
- Observed baseline:
  - `package`: `@inkjs/ui`
  - `version`: `2.0.0`
  - `engines.node`: `>=20`

## Version Drift Policy

When implementation details depend on fresh package publication status:

1. Trust official repositories and package metadata URLs first.
2. Treat third-party blog/tutorial snippets as non-authoritative.
3. If local environment can run package manager queries, validate with:
   - `npm view ink version`
   - `npm view ink-testing-library version`
   - `npm view @inkjs/ui version`
4. If package-manager queries are blocked, continue from this file and state that runtime verification was blocked.

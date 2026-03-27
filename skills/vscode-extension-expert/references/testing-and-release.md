# Testing And Release

Follow this sequence when validating template-based extension changes.

## Validation Order

1. `pnpm lint`
2. `pnpm test`
3. `pnpm test:extension`
4. `pnpm test:e2e` (if feature affects end-to-end behavior)
5. `pnpm build`
6. `pnpm package` (when distribution artifact is required)

Use targeted runs early, then run the full sequence before completion.

## Test Layers

## Webview Unit Tests (`pnpm test`)

- Uses Vitest + jsdom + React Testing Library.
- Setup file: `webview/__tests__/setup.ts`.
- Good for component behavior, message payload creation, and state helper logic.

## Extension Integration Tests (`pnpm test:extension`)

- Compiles extension tests with `tsc -p __tests__/tsconfig.json`.
- Runs via `@vscode/test-electron` from `__tests__/extension/runTests.ts`.
- Good for command registration and VS Code API interactions.

## E2E Tests (`pnpm test:e2e`)

- Uses Playwright.
- Good for behavior that spans extension host + webview UI + runtime wiring.

## CI Parity

The template CI workflow runs jobs equivalent to:

- `pnpm lint`
- `pnpm test:coverage`
- `pnpm build`
- `xvfb-run -a pnpm test:extension`
- `pnpm test:e2e`

When debugging CI-only failures, replay this order locally as closely as possible.

## Packaging And Release

- Package artifact:
  - `pnpm package` -> runs production build and `vsce package --no-dependencies`
- Publish:
  - `pnpm publish` -> runs production build and `vsce publish --no-dependencies`
- Template release workflow (tag-triggered) runs:
  - tests
  - build
  - package
  - GitHub release upload of `.vsix`

## Definition Of Done For This Template

- Command wiring works in Extension Development Host.
- Webview message flow works both directions.
- Relevant unit/integration/e2e checks pass (or blocker is explicit and reproducible).
- Build output stays at `dist/extension/index.js`.
- Packaging succeeds when requested.

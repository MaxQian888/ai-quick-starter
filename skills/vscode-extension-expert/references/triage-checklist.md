# Triage Checklist

Use this checklist before broad refactors. Verify the failing layer first.

## 1) Command Not Available

Symptoms:

- Command palette cannot find expected command.
- `executeCommand` fails with command-not-found behavior.

Checks:

- Confirm command exists in `package.json` `contributes.commands`.
- Confirm same command ID is registered in `extension/index.ts`.
- Confirm extension activated in Extension Development Host.

## 2) Webview Opens Blank

Symptoms:

- Panel opens but content is empty.
- Panel shows stale/non-HMR content in dev mode.

Checks:

- Confirm `extension/views/helper.ts` still uses `virtual:vscode`.
- Confirm launch config sets `VITE_DEV_SERVER_URL` in dev profile.
- Run `pnpm build` to ensure production artifacts still compile.

## 3) Messages Not Crossing Boundary

Symptoms:

- `vscode.postMessage` runs but extension logic does not execute.
- Extension posts messages but webview never reacts.

Checks:

- Confirm message `type` names match sender and receiver.
- Confirm `setupWebviewHooks` is called when panel is constructed.
- Add temporary logging on both sides to verify one-way vs two-way failure.

## 4) Unit Tests Fail Outside VS Code

Symptoms:

- `acquireVsCodeApi is not defined`.
- React tests fail due to missing webview globals.

Checks:

- Ensure `webview/__tests__/setup.ts` defines mocked `acquireVsCodeApi`.
- Ensure `vitest.config.ts` includes setup file and jsdom environment.
- Verify tests import webview code through alias/config consistent with Vite.

## 5) Extension Integration Tests Fail

Symptoms:

- `pnpm test:extension` fails before test assertions.
- Runner cannot resolve extension path or compiled suite.

Checks:

- Ensure `tsc -p __tests__/tsconfig.json` output exists under `__tests__/out`.
- Confirm `__tests__/extension/runTests.ts` path resolution still matches output layout.
- Re-run `pnpm build` before `pnpm test:extension` when touching entrypoints.

## 6) E2E or CI Drift

Symptoms:

- Local tests pass; CI fails.
- Playwright suite fails only in pipeline.

Checks:

- Mirror CI order: `pnpm lint`, `pnpm test:coverage`, `pnpm build`, `pnpm test:extension`, `pnpm test:e2e`.
- Verify Node 20 and pnpm toolchain match CI.
- Install Playwright browser dependencies when reproducing CI e2e failures.

## 7) Packaging and Publish Failures

Symptoms:

- `pnpm package` fails to emit `.vsix`.
- Marketplace publish command fails validation.

Checks:

- Run `pnpm build:prod` directly to isolate build vs packaging.
- Confirm `vsce` commands still map to template scripts.
- Confirm manifest fields (`publisher`, `name`, `version`, `engines`) are valid for distribution.

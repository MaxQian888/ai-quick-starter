---
name: vscode-extension-expert
description: Use when building, debugging, reviewing, or releasing a VS Code extension that follows the vscode-extension-quick-starter template (extension/ + webview/ + Vite + @tomjs/vite-plugin-vscode), especially for command wiring, webview messaging, test pipelines, and VSIX packaging.
---

# VS Code Extension Expert

Keep all changes aligned with the `D:\Project\vscode-extension-quick-starter` template contract.
Treat that template as the source of truth for structure, build flow, test flow, and release flow.

## Quick Start

1. Confirm template contract first. Read `references/template-contract.md`.
2. Identify the change surface before editing:
   - Extension host (`extension/`)
   - Webview app (`webview/`)
   - Build and test pipeline (`package.json`, `.vscode/`, `vitest.config.ts`, `__tests__/`)
3. Apply the smallest compatible change that keeps all template invariants intact.
4. Validate in layers (lint, unit, extension, e2e, build, package). See `references/testing-and-release.md`.

## Template-First Workflow

### 1) Run baseline checks before code changes

- Verify required folders and entrypoints still match template:
  - `extension/index.ts`
  - `extension/views/panel.ts`
  - `extension/views/helper.ts`
  - `webview/App.tsx`
  - `webview/utils/vscode.ts`
  - `vite.config.ts`
  - `package.json` (`main` points to `dist/extension/index.js`)
- Verify core scripts exist and are not silently changed:
  - `dev`, `build`, `typecheck`, `lint`
  - `test`, `test:extension`, `test:e2e`
  - `package`, `publish`

### 2) Implement extension-host changes safely (`extension/`)

- Register commands in `activate(context)` and always push disposables into `context.subscriptions`.
- Keep command IDs synchronized in three places:
  - `package.json` `contributes.commands[*].command`
  - `commands.registerCommand("<id>", ...)`
  - tests or call sites that execute the command
- Preserve single-panel lifecycle behavior in `MainPanel` unless the task explicitly changes it.

### 3) Implement webview-side changes safely (`webview/`)

- Keep VS Code bridge access via `webview/utils/vscode.ts`.
- Maintain mock fallback behavior for non-extension contexts (tests and browser runs).
- Keep alias-based imports (`@/...`) consistent with `vite.config.ts` and `tsconfig`.

### 4) Maintain extension-webview message contract

- Route extension-side receive logic through `WebviewHelper.setupWebviewHooks`.
- Route webview-side send logic through `vscode.postMessage`.
- Use stable message `type` values and update both sender and receiver when contract changes.
- For new message types, add coverage on both sides:
  - extension behavior test (or integration assertion)
  - webview unit test where possible

### 5) Preserve dev-host behavior (`F5` flow)

- Keep `.vscode/launch.json` and `.vscode/tasks.json` coherent:
  - Dev launch uses preLaunchTask `dev`.
  - Dev launch passes `VITE_DEV_SERVER_URL`.
  - Production launch uses preLaunchTask `build`.
- Do not break `virtual:vscode` HTML injection flow in `extension/views/helper.ts`.

### 6) Validate and release in template order

- Follow validation order from `references/testing-and-release.md`.
- If packaging or publishing is in scope, verify `pnpm package` (and `pnpm publish` when requested) after all tests pass.

## Guardrails

- Do not migrate to `src/extension.ts` or other legacy layouts in this skill.
- Do not bypass `@tomjs/vite-plugin-vscode` with ad-hoc webview HTML generation unless the task explicitly requires a controlled migration.
- Do not change `main` away from `dist/extension/index.js` without coordinated build/test updates.
- Do not claim completion on extension features without at least:
  - one webview-side validation (`pnpm test` or targeted equivalent)
  - one extension-host validation (`pnpm test:extension` or explicit blocker)

## Symptom Triage

- `Command '<id>' not found`
  - Check command ID parity between `package.json` and `registerCommand`.
  - Verify extension activation path and command contribution.
- Webview shows blank or stale content
  - Check `virtual:vscode` integration and launch `VITE_DEV_SERVER_URL`.
  - Check build output and `outFiles` paths in `.vscode/launch.json`.
- Message sends but extension does not react
  - Check `type` switch in `setupWebviewHooks`.
  - Confirm the posted payload shape matches receiver expectations.
- Tests pass locally but fail in CI
  - Align Node/pnpm versions and run pipeline in CI order from `references/testing-and-release.md`.

## Reference Routing

- Template structure and invariants: `references/template-contract.md`
- Execution-time troubleshooting: `references/triage-checklist.md`
- Test and release sequence: `references/testing-and-release.md`
- Canonical external docs and template provenance: `references/official-sources.md`

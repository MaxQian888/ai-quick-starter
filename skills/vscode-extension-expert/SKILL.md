---
name: vscode-extension-expert
description: |
  Use whenever the user is building, debugging, reviewing, or releasing a VS Code extension—especially one based on the vscode-extension-quick-starter template (extension/ + webview/ + Vite + @tomjs/vite-plugin-vscode). Make sure to use this skill whenever the user mentions "VS Code extension", "VSIX", "webview", "extension host", "F5 dev host", "command registration", "panel", "sidebar", or "publish to marketplace" — even for small extensions or quick fixes. Also trigger when the user mentions Vite-based VS Code extension development, webview-to-extension messaging, VSIX packaging, or publishing to the VS Code Marketplace—even if they don't explicitly name this skill or the template. Covers the full extension lifecycle from development to release.
---

# VS Code Extension Expert

Align every change with the `vscode-extension-quick-starter` template contract.
Treat that template as the single source of truth for structure, build flow, test flow, and release flow.

## Adaptive Detection

Before making changes, detect the project state:

1. **Template compliance**: Verify the project matches the `vscode-extension-quick-starter` template structure.
2. **Extension host**: Check `extension/` for command registration and panel lifecycle.
3. **Webview state**: Check `webview/` for build output, message contract, and alias consistency.
4. **Build health**: Verify `pnpm build`, `pnpm typecheck`, and `pnpm lint` pass.
5. **Test coverage**: Check for webview unit tests, extension integration tests, and e2e tests.

Use these signals to decide which validation layer to run first.

## Quick Start

1. Read `references/template-contract.md` to confirm the template invariants.
2. Before editing, identify which surface the change touches:
   - Extension host (`extension/`)
   - Webview app (`webview/`)
   - Build and test pipeline (`package.json`, `.vscode/`, `vitest.config.ts`, `__tests__/`, `e2e/`)
3. Apply the smallest compatible change that preserves all template invariants.
4. Validate in layers: lint → unit → extension → e2e → build → package. See `references/testing-and-release.md` for the full sequence.

## Template-First Workflow

### 1) Run baseline checks before code changes

- Verify required folders and entrypoints still match the template:
  - `extension/index.ts`
  - `extension/views/panel.ts`
  - `extension/views/helper.ts`
  - `webview/App.tsx`
  - `webview/utils/vscode.ts`
  - `vite.config.ts`
  - `package.json` (`main` points to `dist/extension/index.js`)
- Verify core scripts are present and unchanged:
  - `dev`, `build`, `typecheck`, `lint`
  - `test`, `test:extension`, `test:e2e`
  - `package`, `publish`

### 2) Implement extension-host changes safely (`extension/`)

- Register commands inside `activate(context)` and push every disposable into `context.subscriptions`. This prevents memory leaks when the extension deactivates.
- Keep command IDs synchronized across three places:
  1. `package.json` → `contributes.commands[*].command`
  2. `commands.registerCommand("<id>", ...)`
  3. Tests or call sites that execute the command
- Preserve the single-panel lifecycle behavior in `MainPanel` unless the task explicitly asks to change it. Recreating the panel on every command invocation destroys webview state.

### 3) Implement webview-side changes safely (`webview/`)

- Route all VS Code API access through `webview/utils/vscode.ts`. This centralizes the bridge and keeps mock fallback behavior intact for non-extension contexts (tests and browser runs).
- Keep alias-based imports (`@/...`) consistent with `vite.config.ts` and `tsconfig.json`. Mismatched aliases break both the build and the test runner.

### 4) Maintain the extension-webview message contract

- Route extension-side receive logic through `WebviewHelper.setupWebviewHooks`.
- Route webview-side send logic through `vscode.postMessage`.
- Use stable message `type` values. When the contract changes, update both sender and receiver together—partial updates cause silent failures.
- For every new message type, add coverage on both sides:
  - an extension behavior test (or integration assertion)
  - a webview unit test where feasible

### 5) Preserve dev-host behavior (`F5` flow)

- Keep `.vscode/launch.json` and `.vscode/tasks.json` coherent:
  - Dev launch uses preLaunchTask `dev` and passes `VITE_DEV_SERVER_URL`.
  - Production launch uses preLaunchTask `build`.
- Do not break the `virtual:vscode` HTML injection flow in `extension/views/helper.ts`. This is how the dev server URL reaches the webview in development mode.

### 6) Validate and release in template order

- Follow the validation order from `references/testing-and-release.md`.
- If packaging or publishing is in scope, verify `pnpm package` (and `pnpm publish` when requested) only after all tests pass.

## Guardrails

- Stay with the `extension/` + `webview/` layout. Legacy `src/extension.ts` patterns do not apply to this template.
- Do not bypass `@tomjs/vite-plugin-vscode` with ad-hoc HTML generation unless the task explicitly calls for a controlled migration. The plugin handles dev-server injection, production bundling, and manifest integration.
- Do not change `main` away from `dist/extension/index.js` without coordinated updates to the build output, launch config, and test runner paths.
- Do not mark a feature complete without at least:
  - one webview-side validation (`pnpm test` or targeted equivalent)
  - one extension-host validation (`pnpm test:extension` or an explicit blocker with a reason)

## Symptom Triage

- `Command '<id>' not found`
  - Check command ID parity between `package.json` and `registerCommand`.
  - Verify the extension activation path and command contribution.
- Webview shows blank or stale content
  - Check `virtual:vscode` integration and the `VITE_DEV_SERVER_URL` launch variable.
  - Check build output and `outFiles` paths in `.vscode/launch.json`.
- Message sends but extension does not react
  - Check the `type` switch in `setupWebviewHooks`.
  - Confirm the posted payload shape matches the receiver's expectations.
- Tests pass locally but fail in CI
  - Align Node/pnpm versions and replay the pipeline in CI order from `references/testing-and-release.md`.

## Examples

### Example 1: Validate the full pipeline

```bash
pnpm lint && pnpm test && pnpm test:extension && pnpm build && pnpm package
```

### Example 2: Add a new command with webview message

1. Add command ID to `package.json` contributes.commands.
2. Register command in `extension/index.ts`.
3. Add message type to both `webview/utils/vscode.ts` and `extension/views/helper.ts`.
4. Add tests on both sides.

## Reference Routing

- Template structure and invariants: `references/template-contract.md`
- Execution-time troubleshooting: `references/triage-checklist.md`
- Test and release sequence: `references/testing-and-release.md`
- Canonical external docs and template provenance: `references/official-sources.md`

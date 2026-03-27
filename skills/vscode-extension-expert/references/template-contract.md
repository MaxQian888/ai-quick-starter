# Template Contract

Use this contract to keep implementations fully aligned with `vscode-extension-quick-starter`.

## Canonical Layout

```text
extension/
  index.ts
  views/
    panel.ts
    helper.ts
webview/
  App.tsx
  utils/vscode.ts
  __tests__/
__tests__/extension/
.vscode/launch.json
.vscode/tasks.json
vite.config.ts
vitest.config.ts
package.json
```

## Required Runtime Wiring

- Extension entrypoint: `extension/index.ts`
- Package main: `dist/extension/index.js`
- Webview HTML generation: `virtual:vscode` in `extension/views/helper.ts`
- Dev host URL injection: `process.env.VITE_DEV_SERVER_URL`
- Panel creation path: `MainPanel.render(context)`

## Package Contract

Keep these fields coherent when refactoring:

- `name`, `publisher`, `version`
- `main` -> `dist/extension/index.js`
- `engines.node` -> `>=20` (template baseline)
- `engines.vscode` -> `^1.93.0` (template baseline)
- `contributes.commands[*].command` matches runtime registration

## Script Contract

Template scripts and intent:

- `pnpm dev`: Vite dev server with HMR
- `pnpm build`: clean + typecheck + vite build
- `pnpm lint`: lint all files
- `pnpm test`: webview unit tests (Vitest)
- `pnpm test:extension`: extension-host integration tests
- `pnpm test:e2e`: Playwright e2e tests
- `pnpm package`: build production + create `.vsix`
- `pnpm publish`: build production + publish package

## Launch and Task Contract

From `.vscode/launch.json` and `.vscode/tasks.json`:

- `Run Extension (Dev)`:
  - preLaunchTask: `dev`
  - sets `VITE_DEV_SERVER_URL`
- `Run Extension (Production)`:
  - preLaunchTask: `build`
- `Extension Tests`:
  - preLaunchTask: `compile-tests`
  - points to `__tests__/out/extension/suite`

## Change Impact Map

When changing command IDs:

1. `package.json` `contributes.commands`
2. `extension/index.ts` registration
3. tests that call or assert the command
4. docs and user-facing command names

When changing webview messaging:

1. sender in `webview/`
2. receiver in `extension/views/helper.ts`
3. message type constants and payload shape
4. related tests

## Anti-Drift Rules

- Do not reintroduce legacy `src/extension.ts` layout for this template.
- Do not bypass `@tomjs/vite-plugin-vscode` unless performing an explicit migration.
- Do not alter `main` output path without synchronized build and launch updates.

---
name: local-javascript-scripting
description: |
  Use whenever you need to write, review, scaffold, or validate local Node.js or JavaScript automation scripts for filesystem work, CLI tools, batch jobs, JSON or CSV transforms, child-process orchestration, or any code that runs on the local machine rather than in a browser. Make sure to use this skill whenever the task involves local automation, server-side scripting, build tooling, data pipelines, or dev-ops helpers — even if the user says "script", "tool", "automation", "batch job", or "CLI". Also trigger when converting browser code to Node.js, choosing between ESM and CJS, or validating that a script does not accidentally import browser-only APIs like `window` or `document`. Covers one-off scripts, reusable modules, and CLI wrappers.
---

# Local Javascript Scripting

## Overview

Write local automation scripts the same way you would onboard into a small Node tool: inspect the repo or machine context first, choose ESM or CJS deliberately, prefer core Node modules, and keep browser-only patterns out unless the user explicitly wants web code.

## Adaptive Detection

Before writing or reviewing a script, scan for project signals:

1. **Module system**: Check `package.json` for `"type": "module"` or `"type": "commonjs"`. Look at existing `.js` / `.mjs` / `.cjs` files.
2. **Package manager**: Detect `package-lock.json` (npm), `yarn.lock` (Yarn), or `pnpm-lock.yaml` (pnpm).
3. **Existing scripts**: Look in `scripts/`, `tools/`, `bin/`, or `src/` for current conventions.
4. **Runtime constraints**: Check `engines` in `package.json` for Node version requirements.
5. **Build tools**: Note presence of `tsconfig.json`, `vite.config.*`, or bundlers that may affect output.

Match the detected conventions rather than introducing new ones.

## Workflow

1. Confirm the target is a local script, not a web page, frontend component, or browser runtime.
2. Inspect repository truth first when the script will live inside an existing repo:
   - `package.json`
   - lockfiles
   - existing `scripts/`, `tools/`, or `bin/` folders
   - current `.js` / `.mjs` / `.cjs` patterns
3. Choose the smallest viable output shape:
   - one-off script
   - CLI wrapper
   - reusable module plus thin entry script
4. Read `references/runtime-and-module-choice.md` before deciding ESM vs CJS.
5. Scaffold a starter when the file is new:

```bash
node scripts/scaffold-local-node-script.mjs --output ./scripts/sync-files.mjs --kind cli --module esm --name sync-files
```

6. Read `references/local-script-patterns.md` when the task touches file IO, path handling, or child-process orchestration.
7. Keep the entrypoint thin and use `main().catch(...)` for predictable failures.
8. Validate the finished file:

```bash
node scripts/check-local-node-script.mjs --json ./scripts/sync-files.mjs
```

9. Return at least one real invocation example that matches the user's machine-local workflow.

## Guardrails

- Do not use this skill for React, Next.js, browser, or DOM tasks.
- Do not introduce `window`, `document`, `navigator`, `localStorage`, or `sessionStorage` in a supposed local script.
- Do not assume bundlers, transpilers, or web loaders unless the repo already proves that setup.
- Do not add third-party dependencies when the task is easily handled by core Node modules.
- Do not silently switch module systems. Match the repo if it already has a pattern; otherwise prefer ESM for new standalone scripts.

## Examples

### Example 1: Scaffold an ESM CLI

```bash
node scripts/scaffold-local-node-script.mjs --output ./scripts/example.mjs --kind cli --module esm --name example
```

### Example 2: Check a finished script

```bash
node scripts/check-local-node-script.mjs --json ./scripts/example.mjs
```

## References

- `references/runtime-and-module-choice.md`: Use for local-vs-web boundaries, ESM or CJS selection, and extension heuristics.
- `references/local-script-patterns.md`: Use for file transforms, CLI wrappers, error handling, and child-process execution.

## Scripts

- `scripts/scaffold-local-node-script.mjs`: Generate a local Node.js script or CLI skeleton.
- `scripts/check-local-node-script.mjs`: Run `node --check` and reject browser-only globals in a supposed local script.

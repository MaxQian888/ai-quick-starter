# Runtime And Module Choice

Use this reference when the request is local JavaScript but the runtime shape is still unclear.

## Scope Boundary

- Treat this skill as Node.js-first.
- Reject browser-only APIs by default: `window`, `document`, `navigator`, `localStorage`, `sessionStorage`.
- If the request is clearly about a frontend app, React component, Next.js route, or browser behavior, switch to a web-focused skill instead of stretching this one.

## Choose The Smallest Viable Shape

- One-off file transform or batch task: plain script.
- Reusable command with flags and help text: CLI script.
- Multi-file reusable logic: module plus a thin entry script.

## Choose ESM Or CJS Deliberately

- Prefer ESM for new standalone scripts, especially `.mjs`.
- Use CJS when the surrounding repo is clearly CJS or the script must drop into an older Node setup without extra changes.
- For `.js`, confirm the nearest `package.json` `type` field before assuming import style.

## Default Recommendations

- New standalone script: `.mjs` + ESM.
- New repo-local helper inside a legacy CommonJS repo: `.cjs` + CJS.
- Mixed or ambiguous repo: inspect existing scripts and match the dominant pattern.

## Import Patterns

### ESM

```js
import { readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
```

### CJS

```js
const { readFile, writeFile } = require('node:fs/promises');
const { join } = require('node:path');
```

## Keep Local Scripts Local

- Prefer core Node modules before adding dependencies.
- Prefer explicit file paths and environment variables over browser concepts.
- Use `node --check` and a real local invocation before calling the script done.

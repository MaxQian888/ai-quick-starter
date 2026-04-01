# Local Script Patterns

Use this reference after the runtime choice is clear and you are writing the actual local script.

## Starting Workflow

1. Inspect `package.json`, lockfiles, and existing `scripts/` or `tools/` folders.
2. Match the repo's current Node version, module format, and style.
3. Keep the entrypoint thin; move repeated logic into small helpers when the task grows.

## Safe Defaults

- Use `node:fs/promises` for file IO.
- Use `node:path` instead of string-concatenating paths.
- Use `node:child_process` `spawn` or `execFile` instead of shell-built command strings when wrapping another CLI.
- Normalize exit handling with `main().catch(...)`.
- Print diagnostics to `stderr`, not `stdout`, when reporting failures.

## Common Task Skeletons

### File Transform

```js
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';

async function main() {
  const inputPath = resolve(process.argv[2]);
  const outputPath = resolve(process.argv[3]);
  const input = await readFile(inputPath, 'utf8');
  const output = transform(input);
  await mkdir(dirname(outputPath), { recursive: true });
  await writeFile(outputPath, output, 'utf8');
}
```

### Child Process Wrapper

```js
import { spawn } from 'node:child_process';

function runCommand(command, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { stdio: 'inherit', ...options });
    child.on('error', reject);
    child.on('close', (code) => {
      if (code === 0) {
        resolve();
        return;
      }
      reject(new Error(`${command} exited with code ${code}`));
    });
  });
}
```

## Review Checklist

- Does the script run locally without a bundler?
- Does it avoid DOM or frontend-only globals?
- Does it emit clear usage or help text when the script behaves like a CLI?
- Does it fail with a non-zero exit code on real errors?
- Did you run `scripts/check-local-node-script.mjs` before delivery?

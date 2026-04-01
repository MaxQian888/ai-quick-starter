import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));
const skillRoot = resolve(__dirname, '..');
const checkerScript = resolve(skillRoot, 'scripts', 'check-local-node-script.mjs');

function runNode(args, options = {}) {
  return new Promise((resolveRun, rejectRun) => {
    const child = spawn(process.execPath, args, {
      cwd: options.cwd,
      env: { ...process.env, FORCE_COLOR: '0' },
      stdio: ['ignore', 'pipe', 'pipe'],
    });

    let stdout = '';
    let stderr = '';
    child.stdout.setEncoding('utf8');
    child.stderr.setEncoding('utf8');
    child.stdout.on('data', (chunk) => {
      stdout += chunk;
    });
    child.stderr.on('data', (chunk) => {
      stderr += chunk;
    });
    child.on('error', rejectRun);
    child.on('close', (code, signal) => {
      resolveRun({ code, signal, stdout, stderr });
    });
  });
}

test('checker reports success for a valid local esm script', async (t) => {
  const tempRoot = await mkdtemp(join(tmpdir(), 'local-js-skill-'));
  t.after(async () => {
    await rm(tempRoot, { recursive: true, force: true });
  });

  const scriptPath = join(tempRoot, 'valid-script.mjs');
  await writeFile(
    scriptPath,
    [
      '#!/usr/bin/env node',
      "import { readFile } from 'node:fs/promises';",
      '',
      'const raw = await readFile(new URL(import.meta.url), "utf8");',
      'console.log(raw.length);',
      '',
    ].join('\n'),
    'utf8',
  );

  const result = await runNode([checkerScript, '--json', scriptPath]);
  assert.equal(result.code, 0, result.stderr || result.stdout);

  const payload = JSON.parse(result.stdout);
  assert.equal(payload.ok, true);
  assert.equal(payload.path, scriptPath);
  assert.deepEqual(payload.issues, []);
});

test('checker fails when browser-only globals appear in a supposed local script', async (t) => {
  const tempRoot = await mkdtemp(join(tmpdir(), 'local-js-skill-'));
  t.after(async () => {
    await rm(tempRoot, { recursive: true, force: true });
  });

  const scriptPath = join(tempRoot, 'browser-leak.js');
  await writeFile(scriptPath, 'console.log(window.location.href);\n', 'utf8');

  const result = await runNode([checkerScript, '--json', scriptPath]);
  assert.notEqual(result.code, 0);

  const payload = JSON.parse(result.stdout);
  assert.equal(payload.ok, false);
  assert.match(payload.summary, /browser/i);
  assert.equal(payload.issues[0].rule, 'no-browser-globals');
  assert.match(payload.issues[0].message, /window/);
});

test('checker reports node-check failures for invalid JavaScript syntax', async (t) => {
  const tempRoot = await mkdtemp(join(tmpdir(), 'local-js-skill-'));
  t.after(async () => {
    await rm(tempRoot, { recursive: true, force: true });
  });

  const scriptPath = join(tempRoot, 'broken-script.mjs');
  await writeFile(scriptPath, 'const value = ;\n', 'utf8');

  const result = await runNode([checkerScript, '--json', scriptPath]);
  assert.notEqual(result.code, 0);

  const payload = JSON.parse(result.stdout);
  assert.equal(payload.ok, false);
  assert.equal(payload.issues[0].rule, 'node-check');
  assert.match(payload.issues[0].message, /SyntaxError|Unexpected token|Expression expected/i);
});

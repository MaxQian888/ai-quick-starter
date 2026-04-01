import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));
const skillRoot = resolve(__dirname, '..');
const scaffoldScript = resolve(skillRoot, 'scripts', 'scaffold-local-node-script.mjs');

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

test('scaffold helper creates an esm cli skeleton that passes node --check', async (t) => {
  const tempRoot = await mkdtemp(join(tmpdir(), 'local-js-skill-'));
  t.after(async () => {
    await rm(tempRoot, { recursive: true, force: true });
  });

  const outputPath = join(tempRoot, 'sync-files.mjs');
  const result = await runNode([
    scaffoldScript,
    '--output',
    outputPath,
    '--kind',
    'cli',
    '--module',
    'esm',
    '--name',
    'sync-files',
  ]);

  assert.equal(result.code, 0, result.stderr || result.stdout);

  const content = await readFile(outputPath, 'utf8');
  assert.match(content, /^#!\/usr\/bin\/env node/m);
  assert.match(content, /import \{ argv, exit, stderr \} from 'node:process';/);
  assert.match(content, /if \(args\.includes\('--help'\)\)/);

  const syntaxCheck = await runNode(['--check', outputPath]);
  assert.equal(syntaxCheck.code, 0, syntaxCheck.stderr || syntaxCheck.stdout);
});

test('scaffold helper refuses to overwrite an existing file without --force', async (t) => {
  const tempRoot = await mkdtemp(join(tmpdir(), 'local-js-skill-'));
  t.after(async () => {
    await rm(tempRoot, { recursive: true, force: true });
  });

  const outputPath = join(tempRoot, 'existing-script.mjs');
  await writeFile(outputPath, 'console.log("keep");\n', 'utf8');

  const result = await runNode([scaffoldScript, '--output', outputPath]);

  assert.notEqual(result.code, 0);
  assert.match(result.stderr, /already exists/i);
});

test('scaffold helper creates a cjs script with require-based runtime imports', async (t) => {
  const tempRoot = await mkdtemp(join(tmpdir(), 'local-js-skill-'));
  t.after(async () => {
    await rm(tempRoot, { recursive: true, force: true });
  });

  const outputPath = join(tempRoot, 'cleanup-cache.cjs');
  const result = await runNode([
    scaffoldScript,
    '--output',
    outputPath,
    '--kind',
    'script',
    '--module',
    'cjs',
    '--name',
    'cleanup-cache',
  ]);

  assert.equal(result.code, 0, result.stderr || result.stdout);

  const content = await readFile(outputPath, 'utf8');
  assert.match(content, /const \{ argv, exit, stderr \} = require\('node:process'\);/);
  assert.doesNotMatch(content, /import \{ argv, exit, stderr \}/);

  const syntaxCheck = await runNode(['--check', outputPath]);
  assert.equal(syntaxCheck.code, 0, syntaxCheck.stderr || syntaxCheck.stdout);
});

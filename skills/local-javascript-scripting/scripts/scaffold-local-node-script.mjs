#!/usr/bin/env node

import { mkdir, stat, writeFile } from 'node:fs/promises';
import { basename, dirname, extname, resolve } from 'node:path';
import { argv, exit, stderr, stdout } from 'node:process';

function printHelp() {
  stdout.write(`Scaffold a local Node.js script template.

Usage:
  node scaffold-local-node-script.mjs --output <path> [options]

Options:
  --output <path>   Required target file path
  --name <name>     Logical script name used in help text
  --kind <kind>     script | cli (default: script)
  --module <kind>   esm | cjs (default: esm)
  --force           Overwrite existing file
  --help            Show this message
`);
}

function parseArgs(rawArgs) {
  const options = {
    force: false,
    kind: 'script',
    module: 'esm',
    output: '',
    name: '',
  };

  for (let index = 0; index < rawArgs.length; index += 1) {
    const arg = rawArgs[index];
    if (arg === '--help') {
      options.help = true;
      continue;
    }
    if (arg === '--force') {
      options.force = true;
      continue;
    }
    if (arg === '--output' || arg === '--name' || arg === '--kind' || arg === '--module') {
      const nextValue = rawArgs[index + 1];
      if (!nextValue || nextValue.startsWith('--')) {
        throw new Error(`Missing value for ${arg}.`);
      }
      options[arg.slice(2)] = nextValue;
      index += 1;
      continue;
    }
    throw new Error(`Unknown argument: ${arg}`);
  }

  return options;
}

function inferScriptName(outputPath, providedName) {
  if (providedName) {
    return providedName;
  }
  return basename(outputPath, extname(outputPath));
}

function toFunctionName(scriptName) {
  const collapsed = scriptName.replace(/[^a-zA-Z0-9]+/g, ' ').trim();
  const parts = collapsed.length === 0 ? ['local', 'task'] : collapsed.split(/\s+/);
  const [first, ...rest] = parts;
  const normalizedFirst = first.toLowerCase();
  const normalizedRest = rest.map((part) => part[0].toUpperCase() + part.slice(1).toLowerCase());
  return [normalizedFirst, ...normalizedRest].join('');
}

function createCliHelp(scriptName) {
  return [
    `Usage: ${scriptName} [options]`,
    '',
    'Options:',
    '  --help    Show this message',
  ].join('\\n');
}

function createScriptContent({ scriptName, functionName, kind, module }) {
  const cliBlock =
    kind === 'cli'
      ? [
          '',
          "  if (args.includes('--help')) {",
          '    stderr.write(`${HELP_TEXT}\\n`);',
          '    return;',
          '  }',
        ].join('\n')
      : '';

  const todoComment =
    kind === 'cli'
      ? `  // TODO: implement ${scriptName} CLI behavior.`
      : `  // TODO: implement ${scriptName} automation logic.`;

  if (module === 'cjs') {
    return [
      '#!/usr/bin/env node',
      '',
      "const { argv, exit, stderr } = require('node:process');",
      '',
      `const HELP_TEXT = ${JSON.stringify(createCliHelp(scriptName))};`,
      '',
      `async function ${functionName}Main() {`,
      '  const args = argv.slice(2);',
      cliBlock,
      '',
      todoComment,
      '  void args;',
      '}',
      '',
      `${functionName}Main().catch((error) => {`,
      '  stderr.write(`${error?.stack ?? String(error)}\\n`);',
      '  exit(1);',
      '});',
      '',
    ]
      .filter(Boolean)
      .join('\n');
  }

  return [
    '#!/usr/bin/env node',
    '',
    "import { argv, exit, stderr } from 'node:process';",
    '',
    `const HELP_TEXT = ${JSON.stringify(createCliHelp(scriptName))};`,
    '',
    `async function ${functionName}Main() {`,
    '  const args = argv.slice(2);',
    cliBlock,
    '',
    todoComment,
    '  void args;',
    '}',
    '',
    `${functionName}Main().catch((error) => {`,
    '  stderr.write(`${error?.stack ?? String(error)}\\n`);',
    '  exit(1);',
    '});',
    '',
  ]
    .filter(Boolean)
    .join('\n');
}

async function ensureWritableTarget(outputPath, force) {
  try {
    await stat(outputPath);
    if (!force) {
      throw new Error(`Output file already exists: ${outputPath}`);
    }
  } catch (error) {
    if (error?.code === 'ENOENT') {
      return;
    }
    throw error;
  }
}

async function main() {
  let options;
  try {
    options = parseArgs(argv.slice(2));
  } catch (error) {
    stderr.write(`${error.message}\n`);
    exit(1);
  }

  if (options.help) {
    printHelp();
    return;
  }

  if (!options.output) {
    stderr.write('Missing required --output argument.\n');
    exit(1);
  }

  if (!['script', 'cli'].includes(options.kind)) {
    stderr.write(`Unsupported --kind value: ${options.kind}\n`);
    exit(1);
  }

  if (!['esm', 'cjs'].includes(options.module)) {
    stderr.write(`Unsupported --module value: ${options.module}\n`);
    exit(1);
  }

  const outputPath = resolve(options.output);
  await ensureWritableTarget(outputPath, options.force);
  await mkdir(dirname(outputPath), { recursive: true });

  const scriptName = inferScriptName(outputPath, options.name);
  const functionName = toFunctionName(scriptName);
  const content = createScriptContent({
    functionName,
    kind: options.kind,
    module: options.module,
    scriptName,
  });

  await writeFile(outputPath, content, 'utf8');
  stdout.write(`Created ${outputPath}\n`);
}

main().catch((error) => {
  stderr.write(`${error?.stack ?? String(error)}\n`);
  exit(1);
});

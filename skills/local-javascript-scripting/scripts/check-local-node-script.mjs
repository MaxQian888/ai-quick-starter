#!/usr/bin/env node

import { readFile, stat } from 'node:fs/promises';
import { dirname, extname, resolve } from 'node:path';
import { argv, exit, stderr, stdout } from 'node:process';
import { spawn } from 'node:child_process';

const BROWSER_GLOBALS = ['window', 'document', 'navigator', 'localStorage', 'sessionStorage'];

function printHelp() {
  stdout.write(`Check whether a JavaScript file is a valid local Node.js script.

Usage:
  node check-local-node-script.mjs [--json] <path>

Options:
  --json    Emit machine-readable JSON
  --help    Show this message
`);
}

function parseArgs(rawArgs) {
  const options = {
    json: false,
    path: '',
  };

  for (const arg of rawArgs) {
    if (arg === '--help') {
      options.help = true;
      continue;
    }
    if (arg === '--json') {
      options.json = true;
      continue;
    }
    if (!options.path) {
      options.path = arg;
      continue;
    }
    throw new Error(`Unknown argument: ${arg}`);
  }

  return options;
}

function inferModuleKind(filePath) {
  const extension = extname(filePath).toLowerCase();
  if (extension === '.mjs') {
    return 'esm';
  }
  if (extension === '.cjs') {
    return 'cjs';
  }
  return 'js';
}

function positionFromIndex(content, index) {
  const before = content.slice(0, index);
  const line = before.split('\n').length;
  const column = index - before.lastIndexOf('\n');
  return { line, column };
}

function sanitizeExecutableText(content) {
  let result = '';
  const stack = [{ type: 'code' }];

  for (let index = 0; index < content.length; index += 1) {
    const char = content[index];
    const next = content[index + 1] ?? '';
    const state = stack[stack.length - 1];

    if (state.type === 'line-comment') {
      if (char === '\n') {
        stack.pop();
        result += '\n';
      } else {
        result += ' ';
      }
      continue;
    }

    if (state.type === 'block-comment') {
      if (char === '*' && next === '/') {
        result += '  ';
        index += 1;
        stack.pop();
      } else {
        result += char === '\n' ? '\n' : ' ';
      }
      continue;
    }

    if (state.type === 'string') {
      if (char === '\\') {
        result += ' ';
        if (next) {
          result += next === '\n' ? '\n' : ' ';
          index += 1;
        }
        continue;
      }
      if (char === state.quote) {
        stack.pop();
      }
      result += char === '\n' ? '\n' : ' ';
      continue;
    }

    if (state.type === 'template') {
      if (char === '\\') {
        result += ' ';
        if (next) {
          result += next === '\n' ? '\n' : ' ';
          index += 1;
        }
        continue;
      }
      if (char === '`') {
        result += ' ';
        stack.pop();
        continue;
      }
      if (char === '$' && next === '{') {
        result += '${';
        index += 1;
        stack.push({ type: 'template-expression', braceDepth: 1 });
        continue;
      }
      result += char === '\n' ? '\n' : ' ';
      continue;
    }

    if (char === '/' && next === '/') {
      result += '  ';
      index += 1;
      stack.push({ type: 'line-comment' });
      continue;
    }

    if (char === '/' && next === '*') {
      result += '  ';
      index += 1;
      stack.push({ type: 'block-comment' });
      continue;
    }

    if (char === '"' || char === "'") {
      stack.push({ quote: char, type: 'string' });
      result += ' ';
      continue;
    }

    if (char === '`') {
      stack.push({ type: 'template' });
      result += ' ';
      continue;
    }

    if (state.type === 'template-expression') {
      if (char === '{') {
        state.braceDepth += 1;
      } else if (char === '}') {
        state.braceDepth -= 1;
        if (state.braceDepth === 0) {
          result += '}';
          stack.pop();
          continue;
        }
      }
    }

    result += char;
  }

  return result;
}

function findBrowserGlobalIssues(content) {
  const issues = [];
  const executableText = sanitizeExecutableText(content);
  for (const name of BROWSER_GLOBALS) {
    const pattern = new RegExp(`\\b${name}\\b`, 'g');
    for (const match of executableText.matchAll(pattern)) {
      const { line, column } = positionFromIndex(content, match.index ?? 0);
      issues.push({
        column,
        line,
        message: `Found browser-only global "${name}" in a supposed local script.`,
        rule: 'no-browser-globals',
        severity: 'error',
      });
    }
  }
  return issues;
}

function runNodeCheck(filePath) {
  return new Promise((resolveRun, rejectRun) => {
    const child = spawn(process.execPath, ['--check', filePath], {
      cwd: dirname(filePath),
      stdio: ['ignore', 'pipe', 'pipe'],
    });

    let stdoutText = '';
    let stderrText = '';
    child.stdout.setEncoding('utf8');
    child.stderr.setEncoding('utf8');
    child.stdout.on('data', (chunk) => {
      stdoutText += chunk;
    });
    child.stderr.on('data', (chunk) => {
      stderrText += chunk;
    });
    child.on('error', rejectRun);
    child.on('close', (code, signal) => {
      resolveRun({ code, signal, stdout: stdoutText, stderr: stderrText });
    });
  });
}

function serializeReport(report, asJson) {
  if (asJson) {
    return `${JSON.stringify(report, null, 2)}\n`;
  }

  const lines = [
    report.ok ? 'OK: local Node.js script check passed.' : 'FAIL: local Node.js script check failed.',
    `Path: ${report.path}`,
    `Module kind: ${report.moduleKind}`,
    report.summary,
  ];

  if (report.issues.length > 0) {
    lines.push('Issues:');
    for (const issue of report.issues) {
      const location = issue.line ? `:${issue.line}:${issue.column}` : '';
      lines.push(`- [${issue.severity}] ${issue.rule}${location} ${issue.message}`);
    }
  }

  return `${lines.join('\n')}\n`;
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

  if (!options.path) {
    stderr.write('Missing required <path> argument.\n');
    exit(1);
  }

  const targetPath = resolve(options.path);
  const extension = extname(targetPath).toLowerCase();
  if (!['.js', '.mjs', '.cjs'].includes(extension)) {
    stderr.write('Target must be a .js, .mjs, or .cjs file.\n');
    exit(1);
  }

  await stat(targetPath);
  const content = await readFile(targetPath, 'utf8');
  const issues = [];
  const syntaxResult = await runNodeCheck(targetPath);
  if (syntaxResult.code !== 0) {
    issues.push({
      message: syntaxResult.stderr.trim() || 'node --check reported a syntax failure.',
      rule: 'node-check',
      severity: 'error',
    });
  }

  issues.push(...findBrowserGlobalIssues(content));

  const report = {
    issues,
    moduleKind: inferModuleKind(targetPath),
    ok: issues.length === 0,
    path: targetPath,
    summary:
      issues.length === 0
        ? 'Ready for local Node.js execution.'
        : 'Found local-script blockers such as syntax problems or browser-only globals.',
  };

  stdout.write(serializeReport(report, options.json));
  if (!report.ok) {
    exit(1);
  }
}

main().catch((error) => {
  stderr.write(`${error?.stack ?? String(error)}\n`);
  exit(1);
});

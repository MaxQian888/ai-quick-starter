---
name: create-mcp-server
description: Use whenever scaffolding a new Model Context Protocol (MCP) server, building AI tool integrations, creating stdio-based tool servers for Claude or Codex, or generating MCP starter projects from scratch. Make sure to use this skill for any request involving MCP SDK setup, TypeScript or Python tool servers, AI assistant extensions, or integrating custom tools with MCP. Also triggers for questions about MCP server architecture, stdio transport setup, or generating runnable MCP server boilerplate.
---

# Create MCP Server

## Overview

Scaffold a minimal MCP server instead of freehanding starter files. Default to TypeScript and Node.js unless the user explicitly asks for Python.

## Adaptive Detection

Before scaffolding, scan the workspace to choose the right stack and conventions:

1. Detect language preference:
   - Look for `package.json`, `tsconfig.json`, or `node_modules` to prefer TypeScript.
   - Look for `pyproject.toml`, `requirements.txt`, or `setup.py` to prefer Python.
   - Default to TypeScript when no signal is found.
2. Detect existing MCP patterns:
   - Check for existing `@modelcontextprotocol/sdk` or `mcp` dependencies.
   - Look for existing `server.py` or `index.ts` with MCP imports.
3. Detect package manager:
   - Prefer `npm` when `package-lock.json` exists.
   - Prefer `pnpm` when `pnpm-lock.yaml` exists.
   - Prefer `uv` or `pip` when `pyproject.toml` exists.

## Workflow

1. Confirm the target output directory.
2. Choose the stack:
   - Keep `typescript` as the default.
   - Switch to `python` only when the user asks or the surrounding project is clearly Python-first.
3. Keep the first pass minimal:
   - stdio transport,
   - one example `echo` tool,
   - no deployment, auth, database, or remote transport work.
4. Run the helper script:

```bash
python scripts/scaffold_mcp_server.py --output-dir <target-dir> --stack typescript
```

5. Open the generated entrypoint plus manifest files before making further edits.
6. Validate locally with the runtime command in `README-snippet.md` and MCP Inspector when the user wants a runnable check.
7. Extend toward resources, prompts, HTTP, or real integrations only if the user explicitly asks.

## Defaults

- Prefer `typescript` unless the request clearly says `python`.
- Prefer stdio for the initial scaffold.
- Generate exactly one example tool.
- Keep the generated project readable and small.

## Guardrails

- Do not install dependencies automatically.
- Do not run the generated server automatically unless the user asked for execution.
- Do not overwrite a non-empty target directory without `--force`.
- Do not add resources, prompts, or HTTP transport to the first pass unless the user requested them.
- Do not log to stdout in stdio server examples.

## References

- Read `references/scaffold-workflow.md` when deciding between TypeScript and Python or when reviewing the generated file set.
- Read `references/official-notes.md` when you need the narrow official MCP facts behind stdio, tools, Inspector, or SDK expectations.

## Output Contract

### TypeScript

Generate:

- `package.json`
- `tsconfig.json`
- `src/index.ts`
- `.gitignore`
- `README-snippet.md`

### Python

Generate:

- `pyproject.toml`
- `server.py`
- `.gitignore`
- `README-snippet.md`

## Examples

### Example 1: TypeScript MCP Server Scaffold

**Input:** "Create a new MCP server in the `tools/` directory."

**Output:**
- TypeScript scaffold with `package.json`, `tsconfig.json`, and `src/index.ts`.
- One `echo` tool demonstrating stdio transport.
- `README-snippet.md` with install and run instructions.

### Example 2: Python MCP Server Scaffold

**Input:** "I need a Python MCP server for my data pipeline."

**Output:**
- Python scaffold with `pyproject.toml` and `server.py`.
- One `echo` tool using the Python MCP SDK.
- Instructions to run with `uv run server.py`.

## Extension Rule

After scaffolding, pause and inspect the generated files. Treat the scaffold as a starting point for later customization, not as permission to invent a larger MCP platform.

# Scaffold Workflow

## Goal

Generate the smallest credible MCP server starter, then stop.

## Stack Selection

### Keep TypeScript

Use `typescript` when:

- the user gives no stack preference,
- the surrounding repo is JavaScript or TypeScript,
- the user wants a Node-first starter,
- or they mainly want a generic MCP skeleton quickly.

### Switch To Python

Use `python` when:

- the user explicitly asks for Python,
- the destination project is already Python-first,
- or the user plans to run the server with `uv` or a Python virtual environment.

## Transport Rule

Use stdio for the first scaffold.

Do not add HTTP transport to the initial output unless the user explicitly asks for it. A minimal local starter is easier to inspect, debug, and integrate.

## Generated Files

### TypeScript

- `package.json`
- `tsconfig.json`
- `src/index.ts`
- `.gitignore`
- `README-snippet.md`

### Python

- `pyproject.toml`
- `server.py`
- `.gitignore`
- `README-snippet.md`

## Post-Generation Checks

After running the generator:

1. Open the entrypoint file.
2. Confirm the example tool is named `echo`.
3. Confirm the transport is stdio.
4. Read `README-snippet.md`.
5. Only then add host-specific setup, additional tools, resources, or prompts.

## Non-Goals For Version One

Do not automatically add:

- deployment files,
- CI pipelines,
- registry metadata,
- auth flows,
- databases,
- remote transports,
- large example suites.

If the user wants those later, build them as a second step after the starter exists.

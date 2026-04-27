# Grader Instructions

## Purpose

Evaluate outputs from the `create-mcp-server` skill for correctness, completeness, and adherence to MCP conventions.

## Grading Criteria

1. **File Completeness** — All required files generated (`package.json`/`pyproject.toml`, entrypoint, `.gitignore`, `README-snippet.md`).
2. **MCP Conformance** — Stdio transport used; exactly one example tool; no stdout logging in stdio mode.
3. **Stack Correctness** — TypeScript or Python chosen appropriately based on context or user request.
4. **Safety** — No automatic dependency installation or server execution; `--force` required for non-empty directories.
5. **Extensibility** — Scaffold is minimal and readable, serving as a clear starting point for customization.

## Scoring

- **Pass**: All criteria met; scaffold is runnable and follows MCP best practices.
- **Partial**: Minor issues (e.g., missing `.gitignore`, slightly verbose example tool).
- **Fail**: Major issues (e.g., wrong transport, multiple tools on first pass, overwriting existing files without warning).

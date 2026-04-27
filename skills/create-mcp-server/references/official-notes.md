# Official Notes

This skill only needs a few official MCP facts.

## Core Capabilities

MCP servers can expose three main capability types:

- resources,
- tools,
- prompts.

This skill focuses only on the smallest useful tool example.

## TypeScript Starter Facts

The official "Build an MCP server" guide uses:

- `McpServer`,
- `StdioServerTransport`,
- `zod` for tool input schemas.

That is why the TypeScript scaffold starts with one stdio server and one typed tool.

## Python Starter Facts

The official Python guide uses `FastMCP` and runs the server with stdio. That is why the Python scaffold uses:

- `from mcp.server.fastmcp import FastMCP`
- `mcp.run(transport="stdio")`

## Logging Rule

For stdio-based MCP servers, never write logs to stdout. Stdout carries JSON-RPC traffic and noisy prints can break the server. Use stderr for diagnostics.

## Inspector Rule

MCP Inspector is the preferred local developer tool for testing and debugging servers. The official docs show it running directly through `npx`, and they document separate launch patterns for npm, PyPI, and locally developed servers.

## Source Links

- Build an MCP server: `https://modelcontextprotocol.io/docs/develop/build-server`
- MCP Inspector: `https://modelcontextprotocol.io/docs/tools/inspector`

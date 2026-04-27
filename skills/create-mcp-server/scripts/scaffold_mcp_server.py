#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


GITIGNORE = """node_modules/
dist/
.venv/
__pycache__/
.pytest_cache/
*.pyc
"""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scaffold a minimal MCP server project in TypeScript or Python."
    )
    parser.add_argument("--output-dir", required=True, help="Directory where the scaffold is created.")
    parser.add_argument(
        "--stack",
        required=True,
        choices=("typescript", "python"),
        help="Implementation stack for the scaffold.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow writing into an existing non-empty directory.",
    )
    return parser.parse_args(argv)


def normalize_project_name(path: Path) -> str:
    lowered = path.name.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return normalized or "minimal-mcp-server"


def ensure_output_dir(path: Path, force: bool) -> None:
    if path.exists():
        if not path.is_dir():
            raise ValueError(f"Output path '{path}' exists and must be a directory.")
        existing = list(path.iterdir())
        if existing and not force:
            raise ValueError(
                f"Output directory '{path}' already exists and is not empty. "
                "Re-run with --force to allow overwriting scaffold files."
            )
    else:
        path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def typescript_package_json(project_name: str) -> str:
    payload = {
        "name": project_name,
        "version": "0.1.0",
        "private": True,
        "type": "module",
        "scripts": {
            "build": "tsc -p tsconfig.json",
            "dev": "tsx src/index.ts",
            "start": "node dist/index.js",
        },
        "dependencies": {
            "@modelcontextprotocol/sdk": "^1.0.0",
            "zod": "^3.24.0",
        },
        "devDependencies": {
            "@types/node": "^22.10.0",
            "tsx": "^4.19.0",
            "typescript": "^5.7.0",
        },
    }
    return json.dumps(payload, indent=2) + "\n"


def typescript_tsconfig() -> str:
    payload = {
        "compilerOptions": {
            "target": "ES2022",
            "module": "NodeNext",
            "moduleResolution": "NodeNext",
            "outDir": "dist",
            "rootDir": "src",
            "strict": True,
            "esModuleInterop": True,
            "forceConsistentCasingInFileNames": True,
            "skipLibCheck": True,
        },
        "include": ["src/**/*.ts"],
    }
    return json.dumps(payload, indent=2) + "\n"


def typescript_index(project_name: str) -> str:
    return f"""import {{ McpServer }} from "@modelcontextprotocol/sdk/server/mcp.js";
import {{ StdioServerTransport }} from "@modelcontextprotocol/sdk/server/stdio.js";
import {{ z }} from "zod";

const server = new McpServer({{
  name: "{project_name}",
  version: "0.1.0",
}});

server.tool(
  "echo",
  "Echo back the message that the caller sends.",
  {{
    message: z.string().describe("Text to echo back"),
  }},
  async ({{ message }}) => ({{
    content: [
      {{
        type: "text",
        text: `Echo: ${{message}}`,
      }},
    ],
  }})
);

const transport = new StdioServerTransport();
await server.connect(transport);
"""


def python_pyproject(project_name: str) -> str:
    return f"""[project]
name = "{project_name}"
version = "0.1.0"
description = "Minimal MCP server scaffold"
requires-python = ">=3.11"
dependencies = [
  "mcp[cli]>=1.0.0",
]
"""


def python_server(project_name: str) -> str:
    return f"""from mcp.server.fastmcp import FastMCP


mcp = FastMCP("{project_name}")


@mcp.tool()
def echo(message: str) -> str:
    \"\"\"Echo back the provided message.\"\"\"
    return f"Echo: {{message}}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
"""


def readme_snippet(project_name: str, stack: str) -> str:
    if stack == "typescript":
        return f"""# {project_name}

This scaffold creates a minimal stdio MCP server with one example `echo` tool.

## Install

```bash
npm install
```

## Run in development

```bash
npm run dev
```

## Build and run

```bash
npm run build
npm start
```

## Validate locally

Use MCP Inspector against the server command for this project after installing dependencies.
Keep stdout reserved for the MCP transport. Write diagnostics to stderr if you add logging.
"""

    return f"""# {project_name}

This scaffold creates a minimal stdio MCP server with one example `echo` tool.

## Install

```bash
python -m pip install -e .
```

## Run

```bash
python server.py
```

## Validate locally

Use MCP Inspector against the server command for this project after installing dependencies.
Keep stdout reserved for the MCP transport. Write diagnostics to stderr if you add logging.
"""


def scaffold_typescript(output_dir: Path, project_name: str) -> list[Path]:
    files = [
        output_dir / "package.json",
        output_dir / "tsconfig.json",
        output_dir / "src" / "index.ts",
        output_dir / ".gitignore",
        output_dir / "README-snippet.md",
    ]
    write_text(output_dir / "package.json", typescript_package_json(project_name))
    write_text(output_dir / "tsconfig.json", typescript_tsconfig())
    write_text(output_dir / "src" / "index.ts", typescript_index(project_name))
    write_text(output_dir / ".gitignore", GITIGNORE)
    write_text(output_dir / "README-snippet.md", readme_snippet(project_name, "typescript"))
    return files


def scaffold_python(output_dir: Path, project_name: str) -> list[Path]:
    files = [
        output_dir / "pyproject.toml",
        output_dir / "server.py",
        output_dir / ".gitignore",
        output_dir / "README-snippet.md",
    ]
    write_text(output_dir / "pyproject.toml", python_pyproject(project_name))
    write_text(output_dir / "server.py", python_server(project_name))
    write_text(output_dir / ".gitignore", GITIGNORE)
    write_text(output_dir / "README-snippet.md", readme_snippet(project_name, "python"))
    return files


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = Path(args.output_dir).resolve()
    project_name = normalize_project_name(output_dir)

    try:
        ensure_output_dir(output_dir, args.force)
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.stack == "typescript":
        files = scaffold_typescript(output_dir, project_name)
    else:
        files = scaffold_python(output_dir, project_name)

    print(f"Created {args.stack} MCP scaffold at {output_dir}")
    for file_path in files:
        print(file_path.relative_to(output_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

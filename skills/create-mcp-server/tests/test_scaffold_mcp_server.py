from __future__ import annotations

import subprocess
import tempfile
import unittest
import py_compile
from pathlib import Path
import json


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
PYTHON = WORKSPACE_ROOT / ".uv-python" / "cpython-3.11.15-windows-x86_64-none" / "python.exe"
SCRIPT = WORKSPACE_ROOT / "create-mcp-server" / "scripts" / "scaffold_mcp_server.py"


class ScaffoldMcpServerTests(unittest.TestCase):
    def make_output_dir(self, prefix: str) -> Path:
        return Path(tempfile.mkdtemp(prefix=prefix))

    def make_named_output_dir(self, name: str) -> Path:
        base = self.make_output_dir("create-mcp-named-")
        target = base / name
        target.mkdir(parents=True, exist_ok=True)
        return target

    def run_cli(self, output_dir: Path, stack: str, *extra_args: str) -> subprocess.CompletedProcess[str]:
        command = [
            str(PYTHON),
            str(SCRIPT),
            "--output-dir",
            str(output_dir),
            "--stack",
            stack,
            *extra_args,
        ]
        return subprocess.run(command, capture_output=True, text=True, check=False)

    def test_typescript_scaffold_contains_expected_files(self) -> None:
        output_dir = self.make_output_dir("create-mcp-ts-")
        result = self.run_cli(output_dir, "typescript", "--force")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue((output_dir / "package.json").exists())
        self.assertTrue((output_dir / "tsconfig.json").exists())
        self.assertTrue((output_dir / "src" / "index.ts").exists())
        self.assertTrue((output_dir / ".gitignore").exists())
        self.assertTrue((output_dir / "README-snippet.md").exists())

        source = (output_dir / "src" / "index.ts").read_text(encoding="utf-8")
        self.assertIn("StdioServerTransport", source)
        self.assertIn("server.tool(", source)
        self.assertIn('"echo"', source)

        package_json = (output_dir / "package.json").read_text(encoding="utf-8")
        self.assertIn('"@modelcontextprotocol/sdk"', package_json)
        self.assertIn('"zod"', package_json)

    def test_python_scaffold_contains_expected_files(self) -> None:
        output_dir = self.make_output_dir("create-mcp-py-")
        result = self.run_cli(output_dir, "python", "--force")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue((output_dir / "pyproject.toml").exists())
        self.assertTrue((output_dir / "server.py").exists())
        self.assertTrue((output_dir / ".gitignore").exists())
        self.assertTrue((output_dir / "README-snippet.md").exists())

        source = (output_dir / "server.py").read_text(encoding="utf-8")
        self.assertIn("FastMCP", source)
        self.assertIn("@mcp.tool()", source)
        self.assertIn("mcp = FastMCP(", source)

        pyproject = (output_dir / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('mcp[cli]', pyproject)

    def test_existing_output_dir_requires_force(self) -> None:
        output_dir = self.make_output_dir("create-mcp-existing-")
        (output_dir / "keep.txt").write_text("keep", encoding="utf-8")

        result = self.run_cli(output_dir, "typescript")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--force", result.stderr or result.stdout)
        self.assertTrue((output_dir / "keep.txt").exists())

    def test_force_overwrites_scaffold_files_but_preserves_unrelated_files(self) -> None:
        output_dir = self.make_named_output_dir("Create MCP Server 01")
        (output_dir / "keep.txt").write_text("keep", encoding="utf-8")
        (output_dir / "package.json").write_text('{"name":"stale"}', encoding="utf-8")

        result = self.run_cli(output_dir, "typescript", "--force")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue((output_dir / "keep.txt").exists())
        package_payload = json.loads((output_dir / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(package_payload["name"], "create-mcp-server-01")
        source = (output_dir / "src" / "index.ts").read_text(encoding="utf-8")
        self.assertIn('name: "create-mcp-server-01"', source)

    def test_python_scaffold_server_file_is_syntax_valid_and_readme_matches_entrypoint(self) -> None:
        output_dir = self.make_named_output_dir("Create MCP Server Python")
        result = self.run_cli(output_dir, "python", "--force")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        server_path = output_dir / "server.py"
        py_compile.compile(str(server_path), doraise=True)
        source = server_path.read_text(encoding="utf-8")
        self.assertIn('mcp = FastMCP("create-mcp-server-python")', source)
        readme = (output_dir / "README-snippet.md").read_text(encoding="utf-8")
        self.assertIn("python server.py", readme)
        self.assertIn("MCP Inspector", readme)

    def test_existing_file_path_is_rejected_as_output_dir(self) -> None:
        base = self.make_output_dir("create-mcp-file-")
        file_path = base / "scaffold-target"
        file_path.write_text("not a directory", encoding="utf-8")

        result = self.run_cli(file_path, "typescript")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be a directory", result.stderr or result.stdout)


if __name__ == "__main__":
    unittest.main()

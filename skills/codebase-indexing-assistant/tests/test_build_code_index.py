from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
PYTHON = WORKSPACE_ROOT / ".uv-python" / "cpython-3.11.15-windows-x86_64-none" / "python.exe"
SCRIPT = WORKSPACE_ROOT / "codebase-indexing-assistant" / "scripts" / "build_code_index.py"


class BuildCodeIndexTests(unittest.TestCase):
    def make_repo(self, files: dict[str, str]) -> Path:
        repo_root = Path(tempfile.mkdtemp(prefix="codebase-indexing-assistant-"))
        for relative_path, content in files.items():
            file_path = repo_root / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
        return repo_root

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        command = [str(PYTHON), str(SCRIPT), *args]
        return subprocess.run(command, capture_output=True, text=True, check=False)

    def read_output_path(self, stdout: str, key: str) -> Path:
        prefix = f"{key}="
        for line in stdout.splitlines():
            if line.startswith(prefix):
                return Path(line[len(prefix) :].strip())
        self.fail(f"Could not find {key}=... in stdout:\n{stdout}")

    def load_payload_from_stdout(self, stdout: str) -> dict[str, object]:
        json_path = self.read_output_path(stdout, "JSON_OUT")
        return json.loads(json_path.read_text(encoding="utf-8"))

    def test_writes_requested_markdown_and_json_outputs(self) -> None:
        repo_root = self.make_repo(
            {
                "main.py": "from app import start\n",
                "app.py": "def start():\n    return 1\n",
                "README.md": "# Demo\n",
            }
        )
        temp_root = Path(tempfile.mkdtemp(prefix="codebase-indexing-out-"))
        markdown_path = temp_root / "index.md"
        json_path = temp_root / "index.json"

        result = self.run_cli(
            "--root",
            str(repo_root),
            "--markdown-out",
            str(markdown_path),
            "--json-out",
            str(json_path),
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue(markdown_path.exists())
        self.assertTrue(json_path.exists())

        markdown = markdown_path.read_text(encoding="utf-8")
        self.assertIn("## Repository Overview", markdown)
        self.assertIn("## Likely Entrypoints and Key Files", markdown)

        payload = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertIn("summary", payload)
        self.assertIn("files", payload)
        self.assertIn("entry_candidates", payload)
        self.assertIn("reading_order", payload)
        self.assertEqual(payload["entry_candidates"][0]["path"], "main.py")

    def test_collects_manifest_and_docs_signals(self) -> None:
        repo_root = self.make_repo(
            {
                "README.md": "# Demo\n",
                "package.json": json.dumps(
                    {
                        "name": "demo",
                        "scripts": {
                            "dev": "vite",
                            "test": "vitest run",
                        },
                    }
                ),
                "src/index.ts": "export const ready = true;\n",
            }
        )

        result = self.run_cli("--root", str(repo_root))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload_from_stdout(result.stdout)
        self.assertIn("README.md", payload["summary"]["docs"])
        self.assertIn("package.json", payload["summary"]["manifests"])
        self.assertEqual(payload["commands"][0]["command"], "npm run dev")

    def test_creates_temp_outputs_when_paths_omitted(self) -> None:
        repo_root = self.make_repo(
            {
                "src/server.py": "from routes import router\n",
                "src/routes.py": "router = object()\n",
            }
        )

        result = self.run_cli("--root", str(repo_root))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        markdown_path = self.read_output_path(result.stdout, "MARKDOWN_OUT")
        json_path = self.read_output_path(result.stdout, "JSON_OUT")
        self.assertTrue(markdown_path.exists())
        self.assertTrue(json_path.exists())

        payload = self.load_payload_from_stdout(result.stdout)
        self.assertTrue(payload["entry_candidates"])
        self.assertTrue(payload["reading_order"])

    def test_respects_include_and_exclude_filters(self) -> None:
        repo_root = self.make_repo(
            {
                "src/server.py": "from lib.db import connect\n",
                "src/lib/db.py": "def connect():\n    return None\n",
                "vendor/generated.js": "console.log('ignore')\n",
            }
        )

        result = self.run_cli(
            "--root",
            str(repo_root),
            "--include",
            "src",
            "--exclude",
            "vendor",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload_from_stdout(result.stdout)
        indexed_paths = {entry["path"] for entry in payload["files"]}
        self.assertIn("src/server.py", indexed_paths)
        self.assertIn("src/lib/db.py", indexed_paths)
        self.assertNotIn("vendor/generated.js", indexed_paths)

    def test_reports_limits_when_scan_is_capped(self) -> None:
        repo_root = self.make_repo(
            {
                f"src/file_{index}.py": f"value_{index} = {index}\n"
                for index in range(5)
            }
        )

        result = self.run_cli("--root", str(repo_root), "--max-files", "2")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload_from_stdout(result.stdout)
        self.assertTrue(payload["limits"])
        self.assertEqual(payload["limits"][0]["kind"], "max-files")

    def test_markdown_guides_named_index_are_not_entrypoints(self) -> None:
        repo_root = self.make_repo(
            {
                "docs/indexing-playbook.md": "# Guide\n",
                "src/server.py": "def main():\n    return None\n",
            }
        )

        result = self.run_cli("--root", str(repo_root))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload_from_stdout(result.stdout)
        entry_paths = {entry["path"] for entry in payload["entry_candidates"]}
        self.assertIn("src/server.py", entry_paths)
        self.assertNotIn("docs/indexing-playbook.md", entry_paths)

    def test_nested_component_index_barrels_are_not_promoted_to_entry_candidates(self) -> None:
        repo_root = self.make_repo(
            {
                "src/index.ts": "export const bootstrap = true;\n",
                "src/components/index.ts": "export * from './button';\n",
                "src/components/button.tsx": "export const Button = () => null;\n",
            }
        )

        result = self.run_cli("--root", str(repo_root))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload_from_stdout(result.stdout)
        entry_paths = {entry["path"] for entry in payload["entry_candidates"]}
        self.assertIn("src/index.ts", entry_paths)
        self.assertNotIn("src/components/index.ts", entry_paths)


if __name__ == "__main__":
    unittest.main()

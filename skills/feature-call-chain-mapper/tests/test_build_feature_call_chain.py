from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
PYTHON = WORKSPACE_ROOT / ".uv-python" / "cpython-3.11.15-windows-x86_64-none" / "python.exe"
SCRIPT = WORKSPACE_ROOT / "feature-call-chain-mapper" / "scripts" / "build_feature_call_chain.py"


class BuildFeatureCallChainTests(unittest.TestCase):
    def make_repo(self, files: dict[str, str]) -> Path:
        repo_root = Path(tempfile.mkdtemp(prefix="feature-call-chain-"))
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

    def load_json_from_stdout(self, stdout: str) -> dict[str, object]:
        json_path = self.read_output_path(stdout, "JSON_OUT")
        return json.loads(json_path.read_text(encoding="utf-8"))

    def test_typescript_feature_trace_reports_nodes_edges_and_sections(self) -> None:
        repo_root = self.make_repo(
            {
                "src/routes/login.ts": (
                    "import {handleLogin} from '../services/auth';\n"
                    "export function loginRoute() {\n"
                    "  return handleLogin();\n"
                    "}\n"
                ),
                "src/services/auth.ts": (
                    "export function handleLogin() {\n"
                    "  return loadUser();\n"
                    "}\n"
                    "function loadUser() {\n"
                    "  return true;\n"
                    "}\n"
                ),
            }
        )

        result = self.run_cli("--root", str(repo_root), "--feature", "login")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json_from_stdout(result.stdout)
        self.assertTrue(payload["nodes"])
        self.assertTrue(payload["edges"])
        self.assertTrue(payload["blind_spots"])

    def test_python_feature_trace_promotes_entrypoint_and_symbol_chain(self) -> None:
        repo_root = self.make_repo(
            {
                "src/server.py": (
                    "from service import handle_login\n\n"
                    "def route():\n"
                    "    return handle_login()\n"
                ),
                "src/service.py": (
                    "def handle_login():\n"
                    "    return persist_login()\n\n"
                    "def persist_login():\n"
                    "    return 'ok'\n"
                ),
            }
        )

        result = self.run_cli("--root", str(repo_root), "--feature", "login")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json_from_stdout(result.stdout)
        self.assertTrue(payload["candidate_entrypoints"])
        self.assertTrue(any(node["symbol"] == "handle_login" for node in payload["nodes"]))

    def test_markdown_contains_required_report_sections(self) -> None:
        repo_root = self.make_repo(
            {
                "src/server.py": (
                    "from service import handle_login\n\n"
                    "def route():\n"
                    "    return handle_login()\n"
                ),
                "src/service.py": (
                    "def handle_login():\n"
                    "    return 'ok'\n"
                ),
            }
        )

        result = self.run_cli("--root", str(repo_root), "--feature", "login")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        markdown_path = self.read_output_path(result.stdout, "MARKDOWN_OUT")
        markdown = markdown_path.read_text(encoding="utf-8")
        self.assertIn("## Candidate Entrypoints", markdown)
        self.assertIn("## Call Chain", markdown)
        self.assertIn("## Blind Spots", markdown)

    def test_respects_include_and_exclude_filters(self) -> None:
        repo_root = self.make_repo(
            {
                "src/server.py": (
                    "from service import handle_login\n\n"
                    "def route():\n"
                    "    return handle_login()\n"
                ),
                "src/service.py": (
                    "def handle_login():\n"
                    "    return 'ok'\n"
                ),
                "vendor/generated.py": "def handle_login():\n    return 'ignore'\n",
            }
        )

        result = self.run_cli(
            "--root",
            str(repo_root),
            "--feature",
            "login",
            "--include",
            "src",
            "--exclude",
            "vendor",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json_from_stdout(result.stdout)
        evidence_paths = {record["path"] for record in payload["evidence_files"]}
        self.assertIn("src/server.py", evidence_paths)
        self.assertNotIn("vendor/generated.py", evidence_paths)

    def test_entry_file_anchor_promotes_requested_file(self) -> None:
        repo_root = self.make_repo(
            {
                "src/http/entry.py": (
                    "from feature_logic import run_flow\n\n"
                    "def dispatch():\n"
                    "    return run_flow()\n"
                ),
                "src/http/feature_logic.py": "def run_flow():\n    return 'ok'\n",
            }
        )

        result = self.run_cli(
            "--root",
            str(repo_root),
            "--feature",
            "flow",
            "--entry-file",
            "src/http/entry.py",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json_from_stdout(result.stdout)
        self.assertEqual(payload["candidate_entrypoints"][0]["path"], "src/http/entry.py")
        self.assertEqual(payload["candidate_entrypoints"][0]["confidence"], "high")

    def test_reports_low_confidence_when_chain_is_weak(self) -> None:
        repo_root = self.make_repo(
            {
                "src/misc.py": (
                    "def helper():\n"
                    "    return 'ok'\n"
                ),
            }
        )

        result = self.run_cli("--root", str(repo_root), "--feature", "nonexistent-feature")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json_from_stdout(result.stdout)
        self.assertTrue(any(node["confidence"] == "low" for node in payload["nodes"]))
        self.assertTrue(any("heuristics" in item.lower() for item in payload["blind_spots"]))

    def test_python_cross_module_handoff_is_reported(self) -> None:
        repo_root = self.make_repo(
            {
                "src/server.py": (
                    "from service import handle_login\n\n"
                    "def route():\n"
                    "    return handle_login()\n"
                ),
                "src/service.py": (
                    "def handle_login():\n"
                    "    return persist_login()\n\n"
                    "def persist_login():\n"
                    "    return 'ok'\n"
                ),
            }
        )

        result = self.run_cli("--root", str(repo_root), "--feature", "login")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json_from_stdout(result.stdout)
        self.assertTrue(payload["cross_module_handoffs"])
        self.assertEqual(payload["cross_module_handoffs"][0]["from_file"], "src/server.py")
        self.assertEqual(payload["cross_module_handoffs"][0]["to_file"], "src/service.py")


if __name__ == "__main__":
    unittest.main()

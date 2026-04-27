from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path
from uuid import uuid4


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
PYTHON = WORKSPACE_ROOT / ".uv-python" / "cpython-3.11.15-windows-x86_64-none" / "python.exe"
SCRIPT = (
    WORKSPACE_ROOT
    / "project-architecture-design-analyzer"
    / "scripts"
    / "build_project_architecture_report.py"
)
TMP_ROOT = WORKSPACE_ROOT / "project-architecture-design-analyzer" / ".tmp-tests"
TMP_ROOT.mkdir(parents=True, exist_ok=True)


class BuildProjectArchitectureReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self._paths_to_cleanup: list[Path] = []

    def tearDown(self) -> None:
        for target in reversed(self._paths_to_cleanup):
            shutil.rmtree(target, ignore_errors=True)

    def make_temp_dir(self, prefix: str) -> Path:
        path = TMP_ROOT / f"{prefix}{uuid4().hex}"
        path.mkdir(parents=True, exist_ok=False)
        self._paths_to_cleanup.append(path)
        return path

    def make_repo(self, files: dict[str, str]) -> Path:
        root = self.make_temp_dir("source-")
        for relative_path, content in files.items():
            file_path = root / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
        return root

    def run_cli(self, repo_root: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
        command = [
            str(PYTHON),
            str(SCRIPT),
            "--root",
            str(repo_root),
            *extra_args,
        ]
        return subprocess.run(command, capture_output=True, text=True, check=False)

    def read_output_path(self, stdout: str, key: str) -> Path:
        prefix = f"{key}="
        for line in stdout.splitlines():
            if line.startswith(prefix):
                return Path(line[len(prefix) :].strip())
        self.fail(f"Missing {key}=... in stdout:\n{stdout}")

    def load_payload_from_stdout(self, stdout: str) -> dict[str, object]:
        json_path = self.read_output_path(stdout, "JSON_OUT")
        return json.loads(json_path.read_text(encoding="utf-8"))

    def test_writes_markdown_and_json_reports_with_required_sections(self) -> None:
        repo_root = self.make_repo(
            {
                "README.md": "# Demo system\n",
                "docs/architecture.md": "# Architecture\n",
                "package.json": json.dumps({"name": "demo-ui", "scripts": {"dev": "vite"}}),
                "src/app.tsx": "import { Dashboard } from './components/Dashboard';\nexport default function App() { return <Dashboard />; }\n",
                "src/components/Dashboard.tsx": "export function Dashboard() { return <section>ok</section>; }\n",
                "src/services/api.ts": "export async function fetchDashboard() { return []; }\n",
            }
        )
        output_dir = self.make_temp_dir("output-")
        markdown_path = output_dir / "architecture-report.md"
        json_path = output_dir / "architecture-report.json"

        result = self.run_cli(
            repo_root,
            "--markdown-out",
            str(markdown_path),
            "--json-out",
            str(json_path),
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue(markdown_path.exists())
        self.assertTrue(json_path.exists())

        markdown = markdown_path.read_text(encoding="utf-8")
        self.assertIn("## Repository Snapshot", markdown)
        self.assertIn("## Architecture Shape", markdown)
        self.assertIn("## Design Signals", markdown)
        self.assertIn("## Linked Skills", markdown)

        payload = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertIn("summary", payload)
        self.assertIn("files", payload)
        self.assertIn("architecture", payload)
        self.assertIn("linked_skills", payload)
        self.assertIn("suggested_next_reads", payload)
        self.assertTrue(payload["architecture"]["design_patterns"])

    def test_recommends_linked_skills_from_focus_docs_and_command_signals(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": json.dumps(
                    {
                        "name": "service-app",
                        "scripts": {
                            "dev": "node src/server.js",
                            "test": "vitest run",
                        },
                    }
                ),
                "src/server.js": "const { loginRoute } = require('./routes/login');\nfunction start(){ return loginRoute(); }\n",
                "src/routes/login.js": "const { loginUser } = require('../services/auth');\nfunction loginRoute(){ return loginUser(); }\nmodule.exports = { loginRoute };\n",
                "src/services/auth.js": "function loginUser(){ return { ok: true }; }\nmodule.exports = { loginUser };\n",
            }
        )

        result = self.run_cli(repo_root, "--focus", "login")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload_from_stdout(result.stdout)
        recommended = {entry["skill"] for entry in payload["linked_skills"]}
        self.assertIn("feature-call-chain-mapper", recommended)
        self.assertIn("build-project-fixer", recommended)
        self.assertIn("project-ai-context-initializer", recommended)

    def test_respects_include_and_exclude_filters(self) -> None:
        repo_root = self.make_repo(
            {
                "apps/web/package.json": json.dumps({"name": "web", "scripts": {"dev": "next dev"}}),
                "apps/web/app/page.tsx": "export default function Page() { return null; }\n",
                "vendor/generated.js": "console.log('ignore');\n",
            }
        )

        result = self.run_cli(
            repo_root,
            "--include",
            "apps/web",
            "--exclude",
            "vendor",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload_from_stdout(result.stdout)
        indexed_paths = {entry["path"] for entry in payload["files"]}
        self.assertIn("apps/web/package.json", indexed_paths)
        self.assertIn("apps/web/app/page.tsx", indexed_paths)
        self.assertNotIn("vendor/generated.js", indexed_paths)

    def test_reports_limits_when_scan_is_capped(self) -> None:
        repo_root = self.make_repo(
            {
                f"src/file_{index}.py": f"value_{index} = {index}\n"
                for index in range(6)
            }
        )

        result = self.run_cli(repo_root, "--max-files", "2")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload_from_stdout(result.stdout)
        self.assertTrue(payload["limits"])
        self.assertEqual(payload["limits"][0]["kind"], "max-files")

    def test_detects_layered_design_signals_and_boundary_handoffs(self) -> None:
        repo_root = self.make_repo(
            {
                "src/routes/login.py": "from services.auth import login_user\n\ndef login_route():\n    return login_user()\n",
                "src/services/auth.py": "from repositories.user_repo import load_user\n\ndef login_user():\n    return load_user()\n",
                "src/repositories/user_repo.py": "from models.user import User\n\ndef load_user():\n    return User()\n",
                "src/models/user.py": "class User:\n    pass\n",
            }
        )

        result = self.run_cli(repo_root, "--focus", "login")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload_from_stdout(result.stdout)
        pattern_names = {entry["name"] for entry in payload["architecture"]["design_patterns"]}
        boundaries = {
            (entry["from"], entry["to"])
            for entry in payload["architecture"]["boundaries"]
        }
        drift_risks = {entry["kind"] for entry in payload["architecture"]["drift_risks"]}

        self.assertIn("layered-application-surface", pattern_names)
        self.assertIn(("src/routes", "src/services"), boundaries)
        self.assertIn("missing-root-context-docs", drift_risks)

    def test_handles_utf8_bom_in_python_imports(self) -> None:
        repo_root = self.make_repo(
            {
                "src/routes/login.py": "\ufefffrom services.auth import login_user\n\ndef login_route():\n    return login_user()\n",
                "src/services/auth.py": "def login_user():\n    return True\n",
            }
        )

        result = self.run_cli(repo_root, "--focus", "login")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload_from_stdout(result.stdout)
        boundaries = {
            (entry["from"], entry["to"])
            for entry in payload["architecture"]["boundaries"]
        }

        self.assertIn(("src/routes", "src/services"), boundaries)


if __name__ == "__main__":
    unittest.main()

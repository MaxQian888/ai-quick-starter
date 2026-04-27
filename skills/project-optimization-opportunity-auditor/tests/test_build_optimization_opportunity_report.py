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
    / "project-optimization-opportunity-auditor"
    / "scripts"
    / "build_optimization_opportunity_report.py"
)
TMP_ROOT = WORKSPACE_ROOT / "project-optimization-opportunity-auditor" / ".tmp-tests"
TMP_ROOT.mkdir(parents=True, exist_ok=True)


class BuildOptimizationOpportunityReportTests(unittest.TestCase):
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
                "docs/roadmap.md": "# Roadmap\n- Improve auth observability.\n",
                "package.json": json.dumps({"name": "demo-ui", "scripts": {"dev": "vite", "test": "vitest"}}),
                "src/routes/login.py": "from services.auth import login_user\n\ndef login_route():\n    return login_user()\n",
                "src/services/auth.py": "def login_user():\n    return True\n",
            }
        )
        output_dir = self.make_temp_dir("output-")
        markdown_path = output_dir / "optimization-report.md"
        json_path = output_dir / "optimization-report.json"

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
        self.assertIn("## Evidence Sources", markdown)
        self.assertIn("## Optimization Opportunities", markdown)
        self.assertIn("## Top Backlog", markdown)
        self.assertIn("## Category Summary", markdown)

        payload = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertIn("repository_snapshot", payload)
        self.assertIn("evidence_sources", payload)
        self.assertIn("opportunities", payload)
        self.assertIn("top_backlog", payload)
        self.assertIn("category_summary", payload)
        self.assertIn("linked_skills", payload)
        self.assertIn("blind_spots", payload)
        self.assertTrue(payload["top_backlog"])

    def test_top_backlog_respects_top_limit_and_descending_score(self) -> None:
        repo_root = self.make_repo(
            {
                "docs/roadmap.md": "# Roadmap\n- Add regression coverage for auth.\n- Clarify service boundaries.\n",
                "package.json": json.dumps({"name": "svc", "scripts": {"dev": "node server.js"}}),
                "src/routes/login.py": "from services.auth import login_user\n\ndef login_route():\n    return login_user()\n",
                "src/services/auth.py": "from repositories.user_repo import load_user\n\ndef login_user():\n    return load_user()\n",
                "src/repositories/user_repo.py": "def load_user():\n    return {'ok': True}\n",
            }
        )

        result = self.run_cli(repo_root, "--focus", "auth", "--top", "2")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload_from_stdout(result.stdout)
        top_backlog = payload["top_backlog"]

        self.assertEqual(len(top_backlog), 2)
        self.assertGreaterEqual(top_backlog[0]["score"], top_backlog[1]["score"])
        self.assertIn(top_backlog[0]["priority"], {"high", "medium", "low"})
        self.assertIn(top_backlog[0]["category"], payload["category_summary"])

    def test_target_and_explicit_docs_narrow_the_surface(self) -> None:
        repo_root = self.make_repo(
            {
                "docs/auth-plan.md": "# Auth Plan\n- Add login audit logs.\n",
                "docs/billing-plan.md": "# Billing Plan\n- Add invoice export.\n",
                "src/auth/service.py": "def login_user():\n    return True\n",
                "src/billing/service.py": "def create_invoice():\n    return True\n",
            }
        )

        result = self.run_cli(
            repo_root,
            "--target",
            "src/auth",
            "--doc",
            "docs/auth-plan.md",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload_from_stdout(result.stdout)
        surface_paths = {entry["path"] for entry in payload["surface_records"]}
        discovered_docs = {entry["path"] for entry in payload["discovered_docs"]}

        self.assertEqual(payload["request"]["target"], "src/auth")
        self.assertEqual(surface_paths, {"src/auth/service.py"})
        self.assertIn("docs/auth-plan.md", discovered_docs)
        self.assertNotIn("src/billing/service.py", surface_paths)

    def test_respects_include_exclude_filters_and_reports_limits(self) -> None:
        repo_root = self.make_repo(
            {
                "apps/web/package.json": json.dumps({"name": "web", "scripts": {"dev": "next dev"}}),
                "apps/web/app/layout.tsx": "export default function Layout({ children }) { return children; }\n",
                "apps/web/app/page.tsx": "export default function Page() { return null; }\n",
                "apps/api/server.py": "def start():\n    return True\n",
                "vendor/generated.js": "console.log('ignore');\n",
            }
        )

        result = self.run_cli(
            repo_root,
            "--include",
            "apps/web",
            "--exclude",
            "vendor",
            "--max-files",
            "1",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload_from_stdout(result.stdout)
        indexed_paths = {entry["path"] for entry in payload["surface_records"]}

        self.assertTrue(indexed_paths)
        self.assertTrue(all(path.startswith("apps/web/") for path in indexed_paths))
        self.assertNotIn("vendor/generated.js", indexed_paths)
        self.assertTrue(payload["limits"])
        self.assertEqual(payload["limits"][0]["kind"], "max-files")

    def test_recommends_linked_skills_from_docs_target_and_command_signals(self) -> None:
        repo_root = self.make_repo(
            {
                "docs/specs/auth.md": "# Auth Spec\n- Support safer login retries.\n",
                "package.json": json.dumps({"name": "app", "scripts": {"test": "vitest run", "lint": "eslint ."}}),
                "src/auth/login.py": "def login_user():\n    return True\n",
            }
        )

        result = self.run_cli(
            repo_root,
            "--target",
            "src/auth",
            "--focus",
            "login",
            "--doc",
            "docs/specs/auth.md",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload_from_stdout(result.stdout)
        recommended = {entry["skill"] for entry in payload["linked_skills"]}

        self.assertIn("project-architecture-design-analyzer", recommended)
        self.assertIn("feature-gap-requirements-auditor", recommended)
        self.assertIn("build-project-fixer", recommended)

    def test_skips_hidden_and_cache_directories_by_default(self) -> None:
        repo_root = self.make_repo(
            {
                "src/core/service.py": "def run():\n    return True\n",
                ".uv-cache-local/pkg/file.py": "raise RuntimeError('cache noise')\n",
                ".codex-uv-cache/pkg/file.py": "raise RuntimeError('cache noise')\n",
                ".github/workflows/ci.yml": "name: ci\n",
            }
        )

        result = self.run_cli(repo_root, "--max-files", "20")
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

        payload = self.load_payload_from_stdout(result.stdout)
        surface_paths = {entry["path"] for entry in payload["surface_records"]}

        self.assertIn("src/core/service.py", surface_paths)
        self.assertIn(".github/workflows/ci.yml", surface_paths)
        self.assertNotIn(".uv-cache-local/pkg/file.py", surface_paths)
        self.assertNotIn(".codex-uv-cache/pkg/file.py", surface_paths)


if __name__ == "__main__":
    unittest.main()

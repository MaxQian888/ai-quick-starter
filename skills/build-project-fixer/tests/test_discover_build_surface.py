from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
PYTHON = WORKSPACE_ROOT / ".uv-python" / "cpython-3.11.15-windows-x86_64-none" / "python.exe"
SCRIPT = WORKSPACE_ROOT / "build-project-fixer" / "scripts" / "discover_build_surface.py"


class DiscoverBuildSurfaceTests(unittest.TestCase):
    def make_repo(self, files: dict[str, str]) -> Path:
        temp_dir = Path(tempfile.mkdtemp(prefix="build-project-fixer-"))
        for relative_path, content in files.items():
            file_path = temp_dir / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
        return temp_dir

    def run_cli(self, repo_root: Path, *args: str) -> dict[str, object]:
        command = [
            str(PYTHON),
            str(SCRIPT),
            "--project-root",
            str(repo_root),
            "--json",
            *args,
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        return json.loads(result.stdout)

    def test_node_package_json_prefers_pnpm_scripts(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": json.dumps(
                    {
                        "name": "demo",
                        "scripts": {
                            "build": "vite build",
                            "test": "vitest run",
                            "lint": "eslint .",
                            "typecheck": "tsc --noEmit",
                        },
                    }
                ),
                "pnpm-lock.yaml": "lockfileVersion: '9.0'\n",
            }
        )

        payload = self.run_cli(repo_root)

        self.assertEqual(payload["package_managers"][0], "pnpm")
        self.assertEqual(payload["commands"]["build"][0]["command"], "pnpm build")
        self.assertEqual(payload["commands"]["test"][0]["command"], "pnpm test")

    def test_pyproject_reports_python_tool_commands(self) -> None:
        repo_root = self.make_repo(
            {
                "pyproject.toml": (
                    "[project]\n"
                    "name = 'demo'\n"
                    "[tool.pytest.ini_options]\n"
                    "testpaths = ['tests']\n"
                    "[tool.ruff]\n"
                    "line-length = 88\n"
                    "[tool.mypy]\n"
                    "python_version = '3.11'\n"
                ),
            }
        )

        payload = self.run_cli(repo_root)

        self.assertEqual(payload["commands"]["test"][0]["command"], "python -m pytest")
        self.assertEqual(payload["commands"]["lint"][0]["command"], "python -m ruff check .")
        self.assertEqual(payload["commands"]["typecheck"][0]["command"], "python -m mypy .")

    def test_ci_run_steps_raise_command_priority(self) -> None:
        repo_root = self.make_repo(
            {
                ".github/workflows/ci.yml": (
                    "name: CI\n"
                    "jobs:\n"
                    "  checks:\n"
                    "    runs-on: ubuntu-latest\n"
                    "    steps:\n"
                    "      - run: pnpm lint\n"
                    "      - run: pnpm test --runInBand\n"
                ),
            }
        )

        payload = self.run_cli(repo_root)

        self.assertEqual(payload["commands"]["lint"][0]["command"], "pnpm lint")
        self.assertEqual(payload["commands"]["test"][0]["command"], "pnpm test --runInBand")

    def test_makefile_targets_are_classified(self) -> None:
        repo_root = self.make_repo(
            {
                "Makefile": (
                    "build:\n\tpython -m build\n\n"
                    "test:\n\tpython -m pytest\n\n"
                    "lint:\n\tpython -m ruff check .\n"
                ),
            }
        )

        payload = self.run_cli(repo_root)

        self.assertEqual(payload["commands"]["build"][0]["command"], "make build")
        self.assertEqual(payload["commands"]["lint"][0]["command"], "make lint")

    def test_ci_tsc_noemit_is_classified_as_typecheck(self) -> None:
        repo_root = self.make_repo(
            {
                ".github/workflows/ci.yml": (
                    "name: CI\n"
                    "jobs:\n"
                    "  checks:\n"
                    "    runs-on: ubuntu-latest\n"
                    "    steps:\n"
                    "      - run: pnpm exec tsc --noEmit\n"
                ),
            }
        )

        payload = self.run_cli(repo_root)

        self.assertEqual(payload["commands"]["typecheck"][0]["command"], "pnpm exec tsc --noEmit")
        self.assertNotIn("build", payload["commands"])

    def test_category_filter_returns_only_requested_bucket(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": json.dumps(
                    {
                        "name": "demo",
                        "scripts": {
                            "build": "vite build",
                            "test": "vitest",
                        },
                    }
                ),
                "pnpm-lock.yaml": "lockfileVersion: '9.0'\n",
            }
        )

        payload = self.run_cli(repo_root, "--category", "build")

        self.assertEqual(sorted(payload["commands"].keys()), ["build"])


if __name__ == "__main__":
    unittest.main()

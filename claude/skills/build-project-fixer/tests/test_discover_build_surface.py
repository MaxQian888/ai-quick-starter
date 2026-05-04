from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
PYTHON = Path(sys.executable)
SCRIPT = SKILL_ROOT / "scripts" / "discover_build_surface.py"


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

    def test_requirements_txt_adds_python_install_command(self) -> None:
        repo_root = self.make_repo(
            {
                "requirements.txt": "requests==2.32.0\npytest==8.3.0\n",
                "tests/test_smoke.py": "def test_ok():\n    assert True\n",
            }
        )

        payload = self.run_cli(repo_root)

        self.assertEqual(payload["commands"]["install"][0]["command"], "python -m pip install -r requirements.txt")
        self.assertEqual(payload["commands"]["test"][0]["command"], "python -m pytest")

    def test_gomod_detection_emits_go_commands(self) -> None:
        repo_root = self.make_repo(
            {
                "go.mod": "module example.com/demo\n\ngo 1.22\n",
                "main.go": "package main\nfunc main() {}\n",
            }
        )

        payload = self.run_cli(repo_root)

        self.assertIn("go", payload["package_managers"])
        self.assertEqual(payload["commands"]["build"][0]["command"], "go build ./...")
        self.assertEqual(payload["commands"]["test"][0]["command"], "go test ./...")
        self.assertEqual(payload["commands"]["install"][0]["command"], "go mod download")

    def test_pyproject_without_lockfile_falls_back_to_pip_install_e(self) -> None:
        repo_root = self.make_repo(
            {
                "pyproject.toml": (
                    "[project]\n"
                    "name = 'demo'\n"
                    "version = '0.1.0'\n"
                ),
            }
        )

        payload = self.run_cli(repo_root)

        self.assertEqual(
            payload["commands"]["install"][0]["command"],
            "python -m pip install -e .",
        )

    def test_ci_run_block_pipe_extracts_each_line(self) -> None:
        repo_root = self.make_repo(
            {
                ".github/workflows/ci.yml": (
                    "name: CI\n"
                    "jobs:\n"
                    "  checks:\n"
                    "    runs-on: ubuntu-latest\n"
                    "    steps:\n"
                    "      - run: |\n"
                    "          pnpm install --frozen-lockfile\n"
                    "          pnpm lint\n"
                    "          pnpm test --runInBand\n"
                ),
            }
        )

        payload = self.run_cli(repo_root)

        lint_commands = [item["command"] for item in payload["commands"].get("lint", [])]
        test_commands = [item["command"] for item in payload["commands"].get("test", [])]
        self.assertIn("pnpm lint", lint_commands)
        self.assertIn("pnpm test --runInBand", test_commands)

    def test_poetry_lock_prefers_poetry_install(self) -> None:
        repo_root = self.make_repo(
            {
                "pyproject.toml": (
                    "[tool.poetry]\n"
                    "name = 'demo'\n"
                    "version = '0.1.0'\n"
                    "description = ''\n"
                    "authors = ['demo <demo@example.com>']\n"
                    "[tool.poetry.dependencies]\n"
                    "python = '^3.11'\n"
                ),
                "poetry.lock": "[[package]]\nname = 'demo'\nversion = '0.1.0'\n",
            }
        )

        payload = self.run_cli(repo_root)

        self.assertEqual(payload["package_managers"][0], "poetry")
        self.assertEqual(payload["commands"]["install"][0]["command"], "poetry install")


if __name__ == "__main__":
    unittest.main()

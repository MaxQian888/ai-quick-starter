from __future__ import annotations

import json
import shutil
import subprocess
import unittest
import uuid
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
SKILL_ROOT = WORKSPACE_ROOT / "build-debug-script-generator"
PYTHON = WORKSPACE_ROOT / ".uv-python" / "cpython-3.11.15-windows-x86_64-none" / "python.exe"
SCRIPT = SKILL_ROOT / "scripts" / "generate_build_debug_scripts.py"
TMP_ROOT = SKILL_ROOT / ".tmp-tests"


class GenerateBuildDebugScriptsTests(unittest.TestCase):
    def setUp(self) -> None:
        TMP_ROOT.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        if TMP_ROOT.exists():
            shutil.rmtree(TMP_ROOT, ignore_errors=True)

    def make_repo(self, files: dict[str, str]) -> Path:
        repo_root = TMP_ROOT / f"repo-{uuid.uuid4().hex}"
        repo_root.mkdir(parents=True, exist_ok=True)
        for relative_path, content in files.items():
            file_path = repo_root / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
        return repo_root

    def make_output_dir(self) -> Path:
        output_dir = TMP_ROOT / f"output-{uuid.uuid4().hex}"
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def run_cli(self, repo_root: Path, output_dir: Path) -> tuple[subprocess.CompletedProcess[str], Path, Path, Path, Path]:
        json_path = output_dir / "build-debug-bundle.json"
        markdown_path = output_dir / "build-debug-bundle.md"
        build_script = output_dir / "build.ps1"
        debug_script = output_dir / "debug.ps1"
        command = [
            str(PYTHON),
            str(SCRIPT),
            "--project-root",
            str(repo_root),
            "--output-dir",
            str(output_dir),
            "--json-out",
            str(json_path),
            "--markdown-out",
            str(markdown_path),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        return result, json_path, markdown_path, build_script, debug_script

    def load_json(self, path: Path) -> dict[str, object]:
        return json.loads(path.read_text(encoding="utf-8"))

    def test_generates_pnpm_build_and_debug_scripts(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": json.dumps(
                    {
                        "name": "demo",
                        "scripts": {
                            "build": "vite build",
                            "dev": "vite",
                            "lint": "eslint .",
                            "test": "vitest run",
                            "typecheck": "tsc --noEmit",
                        },
                    }
                ),
                "pnpm-lock.yaml": "lockfileVersion: '9.0'\n",
            }
        )
        output_dir = self.make_output_dir()

        result, json_path, markdown_path, build_script, debug_script = self.run_cli(repo_root, output_dir)

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json(json_path)
        self.assertEqual(payload["package_managers"][0], "pnpm")
        self.assertEqual(payload["selected_commands"]["install"]["command"], "pnpm install --frozen-lockfile")
        self.assertEqual(payload["selected_commands"]["build"]["command"], "pnpm build")
        self.assertEqual(payload["selected_commands"]["debug"]["command"], "pnpm dev")
        build_text = build_script.read_text(encoding="utf-8")
        debug_text = debug_script.read_text(encoding="utf-8")
        self.assertIn('Invoke-RepositoryCommand "pnpm build"', build_text)
        self.assertIn('Invoke-RepositoryCommand "pnpm lint"', build_text)
        self.assertIn('Invoke-RepositoryCommand "pnpm dev"', debug_text)
        self.assertTrue(markdown_path.exists())

    def test_generates_uv_build_and_debug_scripts(self) -> None:
        repo_root = self.make_repo(
            {
                "pyproject.toml": (
                    "[project]\n"
                    "name = 'demo'\n"
                    "dependencies = ['fastapi', 'uvicorn']\n"
                    "\n"
                    "[build-system]\n"
                    "requires = ['setuptools>=68']\n"
                    "build-backend = 'setuptools.build_meta'\n"
                    "\n"
                    "[tool.pytest.ini_options]\n"
                    "testpaths = ['tests']\n"
                ),
                "uv.lock": "version = 1\n",
                "app.py": "from fastapi import FastAPI\napp = FastAPI()\n",
            }
        )
        output_dir = self.make_output_dir()

        result, json_path, _, build_script, debug_script = self.run_cli(repo_root, output_dir)

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json(json_path)
        self.assertEqual(payload["package_managers"][0], "uv")
        self.assertEqual(payload["selected_commands"]["install"]["command"], "uv sync")
        self.assertEqual(payload["selected_commands"]["build"]["command"], "uv run python -m build")
        self.assertEqual(payload["selected_commands"]["debug"]["command"], "uv run uvicorn app:app --reload")
        self.assertIn('Invoke-RepositoryCommand "uv run python -m build"', build_script.read_text(encoding="utf-8"))
        self.assertIn('Invoke-RepositoryCommand "uv run uvicorn app:app --reload"', debug_script.read_text(encoding="utf-8"))

    def test_makefile_targets_fill_missing_build_and_debug_commands(self) -> None:
        repo_root = self.make_repo(
            {
                "Makefile": (
                    "build:\n"
                    "\tpython -m build\n\n"
                    "debug:\n"
                    "\tpython -m debugpy --listen 5678 main.py\n"
                ),
                "main.py": "print('demo')\n",
            }
        )
        output_dir = self.make_output_dir()

        result, json_path, markdown_path, build_script, debug_script = self.run_cli(repo_root, output_dir)

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json(json_path)
        self.assertEqual(payload["selected_commands"]["build"]["command"], "make build")
        self.assertEqual(payload["selected_commands"]["debug"]["command"], "make debug")
        self.assertIn('Invoke-RepositoryCommand "make build"', build_script.read_text(encoding="utf-8"))
        self.assertIn('Invoke-RepositoryCommand "make debug"', debug_script.read_text(encoding="utf-8"))
        self.assertIn("## Selected Commands", markdown_path.read_text(encoding="utf-8"))

    def test_ci_run_steps_can_supply_a_debug_command_when_it_appears_at_command_start(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": json.dumps({"name": "demo"}),
                "pnpm-lock.yaml": "lockfileVersion: '9.0'\n",
                ".github/workflows/ci.yml": (
                    "name: ci\n"
                    "jobs:\n"
                    "  app:\n"
                    "    runs-on: ubuntu-latest\n"
                    "    steps:\n"
                    "      - run: pnpm build\n"
                    "      - run: pnpm dev\n"
                ),
            }
        )
        output_dir = self.make_output_dir()

        result, json_path, _, _, _ = self.run_cli(repo_root, output_dir)

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json(json_path)
        self.assertEqual(payload["selected_commands"]["build"]["command"], "pnpm build")
        self.assertEqual(payload["selected_commands"]["debug"]["command"], "pnpm dev")
        self.assertFalse(payload["blockers"])

    def test_ci_run_steps_detect_uvicorn_debug_commands_without_reload_flag(self) -> None:
        repo_root = self.make_repo(
            {
                "pyproject.toml": (
                    "[project]\n"
                    "name = 'demo'\n"
                    "dependencies = ['fastapi', 'uvicorn']\n"
                ),
                ".github/workflows/ci.yml": (
                    "name: ci\n"
                    "jobs:\n"
                    "  app:\n"
                    "    runs-on: ubuntu-latest\n"
                    "    steps:\n"
                    "      - run: python -m build\n"
                    "      - run: uvicorn main:app\n"
                ),
            }
        )
        output_dir = self.make_output_dir()

        result, json_path, _, _, _ = self.run_cli(repo_root, output_dir)

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json(json_path)
        self.assertEqual(payload["selected_commands"]["build"]["command"], "python -m build")
        self.assertEqual(payload["selected_commands"]["debug"]["command"], "uvicorn main:app")
        self.assertFalse(
            any("No credible quick-debug command was found" in item for item in payload["blockers"]),
            msg=payload["blockers"],
        )

    def test_ci_multiline_run_block_can_supply_debug_command(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": json.dumps({"name": "demo"}),
                "pnpm-lock.yaml": "lockfileVersion: '9.0'\n",
                ".github/workflows/ci.yml": (
                    "name: ci\n"
                    "jobs:\n"
                    "  app:\n"
                    "    runs-on: ubuntu-latest\n"
                    "    steps:\n"
                    "      - run: |\n"
                    "          pnpm dev\n"
                ),
            }
        )
        output_dir = self.make_output_dir()

        result, json_path, _, _, _ = self.run_cli(repo_root, output_dir)

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json(json_path)
        self.assertEqual(payload["selected_commands"]["debug"]["command"], "pnpm dev")
        self.assertFalse(
            any("No credible quick-debug command was found" in item for item in payload["blockers"]),
            msg=payload["blockers"],
        )


if __name__ == "__main__":
    unittest.main()

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "commit_quality_gate.py"
SPEC = importlib.util.spec_from_file_location("commit_quality_gate", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class CommitQualityGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="commit-quality-gate-"))
        self.addCleanup(lambda: shutil.rmtree(self.temp_dir, ignore_errors=True))

    def _commands_for(self, root: Path):
        return [entry.command for entry in MODULE.detect_commands(root)]

    def test_detect_commands_prefers_repo_specific_checks(self) -> None:
        (self.temp_dir / "package.json").write_text(
            json.dumps(
                {
                    "scripts": {
                        "lint": "eslint .",
                        "test": "vitest run",
                    }
                }
            ),
            encoding="utf-8",
        )
        (self.temp_dir / "pnpm-lock.yaml").write_text("", encoding="utf-8")
        (self.temp_dir / ".pre-commit-config.yaml").write_text("repos: []\n", encoding="utf-8")
        (self.temp_dir / "pyproject.toml").write_text("[tool.uv]\n", encoding="utf-8")

        rendered = self._commands_for(self.temp_dir)

        self.assertIn("uv run pre-commit run --all-files", rendered)
        self.assertIn("pnpm lint", rendered)
        self.assertIn("pnpm test", rendered)

    def test_python_ruff_and_pytest_only_when_dependencies_declare_them(self) -> None:
        (self.temp_dir / "pyproject.toml").write_text(
            "[project]\nname = 'demo'\ndependencies = ['ruff', 'pytest']\n",
            encoding="utf-8",
        )

        rendered = self._commands_for(self.temp_dir)

        self.assertIn("ruff check .", rendered)
        self.assertIn("ruff format --check .", rendered)
        self.assertIn("pytest", rendered)

    def test_pytest_not_added_when_only_tests_directory_exists(self) -> None:
        (self.temp_dir / "pyproject.toml").write_text(
            "[project]\nname = 'demo'\n",
            encoding="utf-8",
        )
        (self.temp_dir / "tests").mkdir()

        rendered = self._commands_for(self.temp_dir)

        self.assertNotIn("pytest", rendered)

    def test_python_black_and_isort_detection(self) -> None:
        (self.temp_dir / "requirements-dev.txt").write_text(
            "black==24.0\nisort==5.0\n",
            encoding="utf-8",
        )

        rendered = self._commands_for(self.temp_dir)

        self.assertIn("black --check .", rendered)
        self.assertIn("isort --check-only .", rendered)

    def test_rust_project_detection(self) -> None:
        (self.temp_dir / "Cargo.toml").write_text(
            "[package]\nname = 'demo'\n",
            encoding="utf-8",
        )

        rendered = self._commands_for(self.temp_dir)

        self.assertIn("cargo fmt --all --check", rendered)
        self.assertIn("cargo test", rendered)

    def test_go_project_detection_runs_vet_before_test(self) -> None:
        (self.temp_dir / "go.mod").write_text("module demo\n", encoding="utf-8")

        rendered = self._commands_for(self.temp_dir)

        self.assertIn("go vet ./...", rendered)
        self.assertIn("go test ./...", rendered)
        self.assertLess(
            rendered.index("go vet ./..."),
            rendered.index("go test ./..."),
            "go vet should run before go test",
        )

    def test_deno_project_detection(self) -> None:
        (self.temp_dir / "deno.json").write_text(
            json.dumps({"tasks": {}}),
            encoding="utf-8",
        )

        rendered = self._commands_for(self.temp_dir)

        self.assertIn("deno lint", rendered)
        self.assertIn("deno test -A", rendered)

    def test_fallback_to_echo_when_no_signals(self) -> None:
        commands = MODULE.detect_commands(self.temp_dir)
        self.assertEqual(len(commands), 1)
        # Either git fallback (if git is on PATH and the temp dir resolves to a
        # repo somehow) or the echo fallback. We only require one of them.
        self.assertIn(
            commands[0].command,
            {
                "git diff --check",
                "echo No known quality gate commands detected.",
            },
        )

    def test_truncate_text_marks_truncated_output(self) -> None:
        result = MODULE.truncate_text("abcdefghij", 5)
        self.assertEqual(result, "abcde\n...[truncated]...")

    def test_run_command_reports_passed_status(self) -> None:
        entry = MODULE.GateCommand(command="echo ok", reason="smoke", source="test")

        result = MODULE.run_command(self.temp_dir, entry, max_output_chars=100)

        self.assertEqual(result.status, "passed")
        self.assertEqual(result.returncode, 0)
        self.assertIn("ok", result.stdout.lower())

    def test_run_command_reports_failed_status_with_nonzero_exit(self) -> None:
        # `python -c "import sys; sys.exit(7)"` is portable across platforms.
        entry = MODULE.GateCommand(
            command=f'"{sys.executable}" -c "import sys; sys.exit(7)"',
            reason="failure",
            source="test",
        )

        result = MODULE.run_command(self.temp_dir, entry, max_output_chars=100)

        self.assertEqual(result.status, "failed")
        self.assertEqual(result.returncode, 7)

    def test_discover_only_json_cli_returns_commands(self) -> None:
        (self.temp_dir / "package.json").write_text(
            json.dumps({"scripts": {"lint": "eslint ."}}),
            encoding="utf-8",
        )
        (self.temp_dir / "pnpm-lock.yaml").write_text("", encoding="utf-8")

        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--project-root",
                str(self.temp_dir),
                "--discover-only",
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        commands = [entry["command"] for entry in payload["commands"]]
        self.assertIn("pnpm lint", commands)


if __name__ == "__main__":
    unittest.main()

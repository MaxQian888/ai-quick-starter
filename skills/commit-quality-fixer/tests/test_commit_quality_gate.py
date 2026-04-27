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

        commands = MODULE.detect_commands(self.temp_dir)
        rendered = [entry.command for entry in commands]

        self.assertIn("uv run pre-commit run --all-files", rendered)
        self.assertIn("pnpm lint", rendered)
        self.assertIn("pnpm test", rendered)

    def test_truncate_text_marks_truncated_output(self) -> None:
        result = MODULE.truncate_text("abcdefghij", 5)
        self.assertEqual(result, "abcde\n...[truncated]...")

    def test_run_command_reports_passed_status(self) -> None:
        entry = MODULE.GateCommand(command="echo ok", reason="smoke", source="test")

        result = MODULE.run_command(self.temp_dir, entry, max_output_chars=100)

        self.assertEqual(result.status, "passed")
        self.assertEqual(result.returncode, 0)
        self.assertIn("ok", result.stdout.lower())

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

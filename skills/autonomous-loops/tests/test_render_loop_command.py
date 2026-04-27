from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
PYTHON = WORKSPACE_ROOT / ".uv-python" / "cpython-3.11.15-windows-x86_64-none" / "python.exe"
SCRIPT = WORKSPACE_ROOT / "autonomous-loops" / "scripts" / "render_loop_command.py"


class RenderLoopCommandTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        command = [str(PYTHON), str(SCRIPT), *args]
        return subprocess.run(command, capture_output=True, text=True, check=False)

    def test_codex_sequential_includes_skip_git_repo_check(self) -> None:
        result = self.run_cli(
            "--cli",
            "codex",
            "--pattern",
            "sequential",
            "--task",
            "Repair the flaky lint rule",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("codex exec --skip-git-repo-check", result.stdout)
        self.assertIn("1. implement", result.stdout)
        self.assertIn("3. verify", result.stdout)

    def test_claude_resume_uses_continue_print_mode(self) -> None:
        result = self.run_cli(
            "--cli",
            "claude",
            "--pattern",
            "resume",
            "--task",
            "Continue the auth cleanup",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn('claude -c -p "Read SHARED_TASK_NOTES.md first if it exists.', result.stdout)

    def test_opencode_iterative_json_output_uses_continue_free_run_commands(self) -> None:
        result = self.run_cli(
            "--cli",
            "opencode",
            "--pattern",
            "iterative-pr",
            "--task",
            "Burn down the test backlog",
            "--json",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["cli"], "opencode")
        self.assertEqual(payload["pattern"], "iterative-pr")
        self.assertEqual(len(payload["steps"]), 3)
        self.assertTrue(payload["steps"][0]["command"].startswith('opencode run "Read SHARED_TASK_NOTES.md'))

    def test_custom_model_is_applied(self) -> None:
        result = self.run_cli(
            "--cli",
            "codex",
            "--pattern",
            "resume",
            "--task",
            "Continue the docs polish",
            "--model",
            "gpt-5.2",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("--model gpt-5.2", result.stdout)

    def test_codex_resume_uses_top_level_resume_command(self) -> None:
        result = self.run_cli(
            "--cli",
            "codex",
            "--pattern",
            "resume",
            "--task",
            "Continue the migration cleanup",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("codex resume --last", result.stdout)
        self.assertNotIn("codex exec resume --last", result.stdout)

    def test_parallel_dag_json_output_contains_planning_and_merge_steps(self) -> None:
        result = self.run_cli(
            "--cli",
            "codex",
            "--pattern",
            "parallel-dag",
            "--task",
            "Implement the approved RFC in dependency layers",
            "--json",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["pattern"], "parallel-dag")
        self.assertEqual([step["label"] for step in payload["steps"]], ["decompose", "layer-execution", "merge-review"])
        self.assertIn("dependency-aware work units", payload["steps"][0]["command"])
        self.assertIn("merge queue", payload["steps"][2]["command"])

    def test_parallel_dag_claude_text_output_mentions_layer_execution(self) -> None:
        result = self.run_cli(
            "--cli",
            "claude",
            "--pattern",
            "parallel-dag",
            "--task",
            "Deliver the multi-module platform change",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("Pattern: parallel-dag", result.stdout)
        self.assertIn("2. layer-execution", result.stdout)
        self.assertIn("3. merge-review", result.stdout)


if __name__ == "__main__":
    unittest.main()

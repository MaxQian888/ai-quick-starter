from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import textwrap
import unittest
import uuid
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "local_ci_gate.py"
TMP_ROOT = Path(__file__).resolve().parents[2] / "tmp" / "local-ci-fixer-tests"
PYTHON_COMMAND = sys.executable.replace("\\", "/")


class LocalCiGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dirs: list[Path] = []
        TMP_ROOT.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        for path in reversed(self._temp_dirs):
            shutil.rmtree(path, ignore_errors=True)

    def make_temp_dir(self, prefix: str) -> Path:
        root = TMP_ROOT / f"{prefix}-{uuid.uuid4().hex}"
        root.mkdir(parents=True, exist_ok=False)
        self._temp_dirs.append(root)
        return root

    def make_repo(self, files: dict[str, str]) -> Path:
        root = self.make_temp_dir("local-ci-fixer-repo")
        for relative_path, content in files.items():
            target = root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        return root

    def make_tool_dir(self, tool_names: list[str]) -> Path:
        tool_dir = self.make_temp_dir("local-ci-fixer-tools")
        for tool_name in tool_names:
            script_path = tool_dir / f"{tool_name}.cmd"
            script_path.write_text("@echo off\r\nexit /b 0\r\n", encoding="utf-8")
        return tool_dir

    def build_env(self, tool_names: list[str] | None = None) -> dict[str, str]:
        env = os.environ.copy()
        path_entries = [str(Path(sys.executable).parent)]
        if tool_names:
            path_entries.insert(0, str(self.make_tool_dir(tool_names)))
        env["PATH"] = os.pathsep.join(path_entries)
        return env

    def run_cli(self, *args: str, tool_names: list[str] | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *args],
            capture_output=True,
            text=True,
            env=self.build_env(tool_names),
        )

    def test_discover_only_reports_workflow_and_job_names(self) -> None:
        repo_root = self.make_repo(
            {
                ".github/workflows/ci.yml": textwrap.dedent(
                    """
                    name: CI
                    jobs:
                      checks:
                        runs-on: ubuntu-latest
                        steps:
                          - uses: actions/checkout@v4
                          - run: npm test
                    """
                ).strip()
                + "\n",
            }
        )

        result = self.run_cli("--project-root", str(repo_root), "--discover-only", "--json")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["workflow_count"], 1)
        self.assertEqual(payload["workflows"][0]["name"], "CI")
        self.assertEqual(payload["workflows"][0]["jobs"][0]["id"], "checks")
        self.assertEqual(payload["workflows"][0]["jobs"][0]["steps"][1]["value"], "npm test")

    def test_plan_only_prefers_fallback_when_act_is_unavailable(self) -> None:
        repo_root = self.make_repo(
            {
                ".github/workflows/ci.yml": textwrap.dedent(
                    """
                    name: CI
                    jobs:
                      checks:
                        runs-on: ubuntu-latest
                        steps:
                          - run: python -m unittest
                    """
                ).strip()
                + "\n",
            }
        )

        result = self.run_cli("--project-root", str(repo_root), "--plan-only", "--json")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["selected_mode"], "fallback")
        self.assertEqual(payload["runnable_commands"], ["python -m unittest"])

    def test_plan_only_prefers_act_when_act_and_docker_are_available(self) -> None:
        repo_root = self.make_repo(
            {
                ".github/workflows/ci.yml": textwrap.dedent(
                    """
                    name: CI
                    jobs:
                      checks:
                        runs-on: ubuntu-latest
                        steps:
                          - uses: actions/checkout@v4
                          - run: python -m unittest
                    """
                ).strip()
                + "\n",
            }
        )

        result = self.run_cli(
            "--project-root",
            str(repo_root),
            "--plan-only",
            "--json",
            tool_names=["act", "docker"],
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["selected_mode"], "act")

    def test_plan_only_marks_deploy_only_workflow_as_unsupported(self) -> None:
        repo_root = self.make_repo(
            {
                ".github/workflows/deploy.yml": textwrap.dedent(
                    """
                    name: Deploy
                    jobs:
                      release:
                        runs-on: ubuntu-latest
                        steps:
                          - uses: actions/checkout@v4
                          - run: ./deploy.sh
                    """
                ).strip()
                + "\n",
            }
        )

        result = self.run_cli("--project-root", str(repo_root), "--plan-only", "--json")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["selected_mode"], "unsupported")
        self.assertIn("deploy-only", payload["blockers"][0].lower())

    def test_fallback_execution_runs_reproducible_commands_in_order(self) -> None:
        first_command = f"{PYTHON_COMMAND} -c \"print('first')\""
        second_command = f"{PYTHON_COMMAND} -c \"print('second')\""
        repo_root = self.make_repo(
            {
                ".github/workflows/ci.yml": textwrap.dedent(
                    f"""
                    name: CI
                    jobs:
                      checks:
                        runs-on: ubuntu-latest
                        steps:
                          - run: {first_command}
                          - run: {second_command}
                    """
                ).strip()
                + "\n",
            }
        )

        result = self.run_cli("--project-root", str(repo_root), "--mode", "fallback", "--json")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual([item["command"] for item in payload["results"]], [first_command, second_command])
        self.assertTrue(all(item["status"] == "passed" for item in payload["results"]))
        self.assertEqual(payload["overall_status"], "passed")

    def test_fallback_execution_honors_fail_fast(self) -> None:
        first_command = f"{PYTHON_COMMAND} -c \"print('before-fail')\""
        failing_command = f"{PYTHON_COMMAND} -c \"import sys; sys.exit(2)\""
        skipped_command = f"{PYTHON_COMMAND} -c \"print('after-fail')\""
        repo_root = self.make_repo(
            {
                ".github/workflows/ci.yml": textwrap.dedent(
                    f"""
                    name: CI
                    jobs:
                      checks:
                        runs-on: ubuntu-latest
                        steps:
                          - run: {first_command}
                          - run: {failing_command}
                          - run: {skipped_command}
                    """
                ).strip()
                + "\n",
            }
        )

        result = self.run_cli(
            "--project-root",
            str(repo_root),
            "--mode",
            "fallback",
            "--json",
            "--fail-fast",
        )

        self.assertEqual(result.returncode, 1, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual([item["command"] for item in payload["results"]], [first_command, failing_command])
        self.assertEqual(payload["results"][1]["status"], "failed")
        self.assertEqual(payload["overall_status"], "failed")

    def test_plan_only_preserves_multiline_run_blocks(self) -> None:
        repo_root = self.make_repo(
            {
                ".github/workflows/ci.yml": textwrap.dedent(
                    """
                    name: CI
                    jobs:
                      checks:
                        runs-on: ubuntu-latest
                        steps:
                          - run: |
                              python -m unittest
                              python -m mypy .
                    """
                ).strip()
                + "\n",
            }
        )

        result = self.run_cli("--project-root", str(repo_root), "--plan-only", "--json")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["selected_mode"], "fallback")
        self.assertEqual(payload["runnable_commands"], ["python -m unittest\npython -m mypy ."])

    def test_fallback_execution_respects_step_working_directory(self) -> None:
        command = f"{PYTHON_COMMAND} -c \"from pathlib import Path; assert Path('marker.txt').exists()\""
        repo_root = self.make_repo(
            {
                ".github/workflows/ci.yml": textwrap.dedent(
                    f"""
                    name: CI
                    jobs:
                      checks:
                        runs-on: ubuntu-latest
                        steps:
                          - run: {command}
                            working-directory: tools/checks
                    """
                ).strip()
                + "\n",
                "tools/checks/marker.txt": "ok\n",
            }
        )

        result = self.run_cli("--project-root", str(repo_root), "--mode", "fallback", "--json")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["results"][0]["status"], "passed")
        self.assertEqual(payload["overall_status"], "passed")

    def test_fallback_execution_reports_missing_working_directory_as_failed_step(self) -> None:
        command = f"{PYTHON_COMMAND} -c \"print('should not start')\""
        repo_root = self.make_repo(
            {
                ".github/workflows/ci.yml": textwrap.dedent(
                    f"""
                    name: CI
                    jobs:
                      checks:
                        runs-on: ubuntu-latest
                        steps:
                          - run: {command}
                            working-directory: missing/subdir
                    """
                ).strip()
                + "\n",
            }
        )

        result = self.run_cli("--project-root", str(repo_root), "--mode", "fallback", "--json")

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["results"][0]["status"], "failed")
        self.assertEqual(payload["overall_status"], "failed")
        self.assertIn("missing/subdir", payload["results"][0]["stderr"].lower())

    def test_env_block_keys_do_not_override_step_properties(self) -> None:
        repo_root = self.make_repo(
            {
                ".github/workflows/ci.yml": textwrap.dedent(
                    """
                    name: CI
                    jobs:
                      checks:
                        runs-on: ubuntu-latest
                        steps:
                          - name: Real step name
                            env:
                              name: env-var-name
                              run: env-var-run
                              uses: env-var-uses
                              working-directory: env-var-wd
                            run: pytest -q
                          - uses: actions/setup-node@v4
                            with:
                              name: with-name
                              run: with-run
                    """
                ).strip()
                + "\n",
            }
        )

        result = self.run_cli("--project-root", str(repo_root), "--discover-only", "--json")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        steps = payload["workflows"][0]["jobs"][0]["steps"]
        self.assertEqual(steps[0]["name"], "Real step name")
        self.assertEqual(steps[0]["kind"], "run")
        self.assertEqual(steps[0]["value"], "pytest -q")
        self.assertEqual(steps[0]["working_directory"], "")
        self.assertEqual(steps[1]["kind"], "uses")
        self.assertEqual(steps[1]["value"], "actions/setup-node@v4")

    def test_multiline_run_blocks_still_honor_following_step_working_directory(self) -> None:
        repo_root = self.make_repo(
            {
                ".github/workflows/ci.yml": textwrap.dedent(
                    f"""
                    name: CI
                    jobs:
                      checks:
                        runs-on: ubuntu-latest
                        steps:
                          - run: |
                              {PYTHON_COMMAND} -c "from pathlib import Path; assert Path('marker.txt').exists()"
                            working-directory: tools/checks
                    """
                ).strip()
                + "\n",
                "tools/checks/marker.txt": "ok\n",
            }
        )

        result = self.run_cli("--project-root", str(repo_root), "--mode", "fallback", "--json")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["results"][0]["status"], "passed")
        self.assertEqual(payload["overall_status"], "passed")


if __name__ == "__main__":
    unittest.main()

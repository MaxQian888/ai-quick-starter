from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
import uuid
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
SCRIPT_ROOT = WORKSPACE_ROOT / "github-actions-ci-builder" / "scripts"
SUPPORT_PATH = SCRIPT_ROOT / "github_actions_support.py"
RUN_LOCAL_CI = SCRIPT_ROOT / "run_local_ci.py"
PYTHON_COMMAND = sys.executable.replace("\\", "/")


def load_support_module():
    spec = importlib.util.spec_from_file_location("github_actions_support", SUPPORT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load github_actions_support.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RunLocalCiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dirs: list[Path] = []
        self._tmp_root = Path(tempfile.gettempdir()) / "github-actions-ci-builder-tests"
        self._tmp_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        for path in reversed(self._temp_dirs):
            shutil.rmtree(path, ignore_errors=True)

    def make_temp_dir(self, prefix: str) -> Path:
        root = self._tmp_root / f"{prefix}-{uuid.uuid4().hex}"
        root.mkdir(parents=True, exist_ok=False)
        self._temp_dirs.append(root)
        return root

    def make_repo(self, files: dict[str, str]) -> Path:
        root = self.make_temp_dir("gacb-repo")
        for relative_path, content in files.items():
            target = root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        return root

    def make_tool_dir(self, tool_names: list[str]) -> Path:
        tool_dir = self.make_temp_dir("gacb-tools")
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
            [sys.executable, str(RUN_LOCAL_CI), *args],
            capture_output=True,
            text=True,
            env=self.build_env(tool_names),
        )

    def test_plan_prefers_act_when_docker_and_act_are_available(self) -> None:
        repo_root = self.make_repo(
            {
                ".github/workflows/ci.yml": textwrap.dedent(
                    """
                    name: CI
                    on:
                      push:
                    jobs:
                      checks:
                        runs-on: ubuntu-latest
                        steps:
                          - uses: actions/checkout@v6
                          - run: python -m unittest
                    """
                ).strip()
                + "\n",
            }
        )

        result = self.run_cli("--project-root", str(repo_root), "--plan-only", "--json", tool_names=["act", "docker"])

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["selected_mode"], "act")
        self.assertEqual(payload["act_command"], "act push -W .github/workflows/ci.yml")

    def test_plan_only_adds_not_executed_scope_limit(self) -> None:
        repo_root = self.make_repo(
            {
                ".github/workflows/ci.yml": textwrap.dedent(
                    """
                    name: CI
                    on:
                      push:
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
        self.assertTrue(any("not executed" in item.lower() for item in payload["scope_limits"]))

    def test_plan_builds_act_command_with_job_event_matrix_and_secret_files(self) -> None:
        support = load_support_module()

        command = support.build_act_command(
            workflow_path=Path(".github/workflows/ci.yml"),
            event_name="workflow_dispatch",
            job_id="lint",
            matrix_entries=["os:ubuntu-latest", "node:22"],
            secret_file=Path(".secrets"),
            env_file=Path(".env.act"),
            input_file=Path(".inputs"),
            event_file=Path("event.json"),
            container_architecture="linux/amd64",
            artifact_server_path=Path(".artifacts"),
            action_offline_mode=True,
        )

        self.assertEqual(
            command,
            "act workflow_dispatch -W .github/workflows/ci.yml -j lint --matrix os:ubuntu-latest --matrix node:22 --secret-file .secrets --env-file .env.act --input-file .inputs -e event.json --container-architecture linux/amd64 --artifact-server-path .artifacts --action-offline-mode",
        )

    def test_plan_blocks_secret_heavy_deploy_workflows_for_act(self) -> None:
        repo_root = self.make_repo(
            {
                ".github/workflows/deploy.yml": textwrap.dedent(
                    """
                    name: Deploy
                    on:
                      workflow_dispatch:
                    jobs:
                      deploy:
                        runs-on: ubuntu-latest
                        steps:
                          - uses: actions/checkout@v6
                          - run: ./deploy.sh
                            env:
                              API_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
                    """
                ).strip()
                + "\n",
            }
        )

        result = self.run_cli("--project-root", str(repo_root), "--plan-only", "--json", tool_names=["act", "docker"])

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["selected_mode"], "unsupported")
        self.assertTrue(any("secret" in item.lower() for item in payload["blockers"]))

    def test_plan_marks_secret_heavy_deploy_workflow_with_scope_limits(self) -> None:
        repo_root = self.make_repo(
            {
                ".github/workflows/deploy.yml": textwrap.dedent(
                    """
                    name: Deploy
                    on:
                      workflow_dispatch:
                    jobs:
                      deploy:
                        runs-on: ubuntu-latest
                        steps:
                          - uses: actions/checkout@v6
                          - run: ./deploy.sh
                            env:
                              API_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
                    """
                ).strip()
                + "\n",
            }
        )

        result = self.run_cli("--project-root", str(repo_root), "--plan-only", "--json", tool_names=["act", "docker"])

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(any("secret" in item.lower() for item in payload["scope_limits"]))

    def test_plan_uses_fallback_when_unsupported_action_is_present(self) -> None:
        repo_root = self.make_repo(
            {
                ".github/workflows/ci.yml": textwrap.dedent(
                    """
                    name: CI
                    on:
                      push:
                    jobs:
                      checks:
                        runs-on: ubuntu-latest
                        steps:
                          - uses: vendor/private-action@v1
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
        self.assertTrue(any("unsupported uses step" in item.lower() for item in payload["blockers"]))
        self.assertEqual(payload["runnable_commands"], ["python -m unittest"])

    def test_fallback_execution_runs_commands_in_order(self) -> None:
        first_command = f"{PYTHON_COMMAND} -c \"print('lint')\""
        second_command = f"{PYTHON_COMMAND} -c \"print('test')\""
        repo_root = self.make_repo(
            {
                ".github/workflows/ci.yml": textwrap.dedent(
                    f"""
                    name: CI
                    on:
                      push:
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


if __name__ == "__main__":
    unittest.main()

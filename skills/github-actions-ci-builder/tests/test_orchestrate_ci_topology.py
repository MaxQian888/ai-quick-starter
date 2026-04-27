from __future__ import annotations

import json
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
ORCHESTRATE_CI = SCRIPT_ROOT / "orchestrate_ci_topology.py"


class OrchestrateCiTopologyTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dirs: list[Path] = []
        self._tmp_root = Path(tempfile.gettempdir()) / "github-actions-ci-builder-orchestrator-tests"
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
        root = self.make_temp_dir("gacb-orchestrator-repo")
        for relative_path, content in files.items():
            target = root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        return root

    def run_cli(self, repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ORCHESTRATE_CI), "--project-root", str(repo_root), "--json", *args],
            capture_output=True,
            text=True,
        )

    def read_payload(self, result: subprocess.CompletedProcess[str]) -> dict[str, object]:
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        return json.loads(result.stdout)

    def test_orchestration_recommends_ci_release_split_for_mixed_workflow(self) -> None:
        repo_root = self.make_repo(
            {
                ".github/workflows/monolith.yml": textwrap.dedent(
                    """
                    name: Monolith
                    on:
                      pull_request:
                      push:
                        branches: [main]
                        tags: ["v*"]
                    jobs:
                      lint:
                        runs-on: ubuntu-latest
                        steps:
                          - uses: actions/checkout@v6
                          - run: pnpm lint
                      release:
                        runs-on: ubuntu-latest
                        steps:
                          - uses: actions/checkout@v6
                          - run: pnpm release
                    """
                ).strip()
                + "\n",
            }
        )

        payload = self.read_payload(self.run_cli(repo_root, "--plan-local"))

        self.assertIn(".github/workflows/ci.yml", payload["proposed_files"])
        self.assertIn(".github/workflows/release.yml", payload["proposed_files"])

    def test_orchestration_reports_missing_governance_basics(self) -> None:
        repo_root = self.make_repo(
            {
                ".github/workflows/ci.yml": textwrap.dedent(
                    """
                    name: CI
                    on:
                      pull_request:
                    jobs:
                      checks:
                        runs-on: ubuntu-latest
                        steps:
                          - uses: actions/checkout@v6
                          - run: pnpm lint
                    """
                ).strip()
                + "\n",
            }
        )

        payload = self.read_payload(self.run_cli(repo_root))
        categories = {item["category"] for item in payload["governance_findings"]}

        self.assertIn("missing-permissions", categories)
        self.assertIn("missing-concurrency", categories)
        self.assertIn("missing-actions-dependabot", categories)

    def test_orchestration_reports_matrix_and_cache_opportunities(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": '{"name":"demo","scripts":{"lint":"eslint .","test":"vitest","build":"vite build"}}',
                "pnpm-lock.yaml": "lockfileVersion: '9.0'\n",
                ".github/workflows/ci.yml": textwrap.dedent(
                    """
                    name: CI
                    on:
                      pull_request:
                    jobs:
                      node20:
                        runs-on: ubuntu-latest
                        steps:
                          - uses: actions/checkout@v6
                          - uses: actions/setup-node@v6
                          - run: pnpm lint
                      node22:
                        runs-on: ubuntu-latest
                        steps:
                          - uses: actions/checkout@v6
                          - uses: actions/setup-node@v6
                          - run: pnpm lint
                    """
                ).strip()
                + "\n",
            }
        )

        payload = self.read_payload(self.run_cli(repo_root))
        recommendation_kinds = {item["kind"] for item in payload["performance_plan"]}

        self.assertIn("use-matrix", recommendation_kinds)
        self.assertIn("add-cache-strategy", recommendation_kinds)

    def test_orchestration_payload_exposes_required_sections(self) -> None:
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

        payload = self.read_payload(self.run_cli(repo_root, "--plan-local"))

        self.assertEqual(
            list(payload["repair_queue"][0].keys()),
            ["kind", "reason", "evidence"],
        )
        self.assertIn("workflow_inventory", payload)
        self.assertIn("scope_limits", payload)
        self.assertIn("local_verification_plan", payload)
        self.assertTrue(any("not executed" in item.lower() for item in payload["scope_limits"]))


if __name__ == "__main__":
    unittest.main()

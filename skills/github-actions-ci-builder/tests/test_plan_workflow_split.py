from __future__ import annotations

import importlib.util
import sys
import textwrap
import unittest
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
SCRIPT_ROOT = WORKSPACE_ROOT / "github-actions-ci-builder" / "scripts"
SUPPORT_PATH = SCRIPT_ROOT / "github_actions_support.py"


def load_support_module():
    spec = importlib.util.spec_from_file_location("github_actions_support", SUPPORT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load github_actions_support.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PlanWorkflowSplitTests(unittest.TestCase):
    def test_plan_recommends_split_when_validation_and_release_are_mixed(self) -> None:
        support = load_support_module()
        workflow_text = textwrap.dedent(
            """
            name: Monolith
            on:
              pull_request:
              push:
                branches: [main]
                tags: ['v*']
              workflow_dispatch:
            jobs:
              lint:
                runs-on: ubuntu-latest
                steps:
                  - uses: actions/checkout@v6
                  - run: pnpm lint
              test:
                runs-on: ubuntu-latest
                steps:
                  - uses: actions/checkout@v6
                  - run: pnpm test
              release:
                runs-on: ubuntu-latest
                needs: [lint, test]
                steps:
                  - uses: actions/checkout@v6
                  - run: pnpm release
            """
        ).strip()

        plan = support.build_split_plan(workflow_text, workflow_name="monolith.yml")

        file_paths = {item["path"] for item in plan["target_files"]}
        recommendation_kinds = {item["kind"] for item in plan["recommendations"]}
        self.assertIn(".github/workflows/ci.yml", file_paths)
        self.assertIn(".github/workflows/release.yml", file_paths)
        self.assertIn("split-by-lifecycle", recommendation_kinds)

    def test_plan_recommends_reusable_workflow_and_composite_action_for_repeated_setup(self) -> None:
        support = load_support_module()
        workflow_text = textwrap.dedent(
            """
            name: Repeated
            on:
              pull_request:
            jobs:
              lint:
                runs-on: ubuntu-latest
                steps:
                  - uses: actions/checkout@v6
                  - uses: actions/setup-node@v6
                  - uses: pnpm/action-setup@v5
                  - run: pnpm install --frozen-lockfile
                  - run: pnpm lint
              test:
                runs-on: ubuntu-latest
                steps:
                  - uses: actions/checkout@v6
                  - uses: actions/setup-node@v6
                  - uses: pnpm/action-setup@v5
                  - run: pnpm install --frozen-lockfile
                  - run: pnpm test
              build:
                runs-on: ubuntu-latest
                steps:
                  - uses: actions/checkout@v6
                  - uses: actions/setup-node@v6
                  - uses: pnpm/action-setup@v5
                  - run: pnpm install --frozen-lockfile
                  - run: pnpm build
            """
        ).strip()

        plan = support.build_split_plan(workflow_text, workflow_name="quality.yml")

        recommendation_kinds = {item["kind"] for item in plan["recommendations"]}
        file_paths = {item["path"] for item in plan["target_files"]}
        self.assertIn("extract-composite-action", recommendation_kinds)
        self.assertIn("extract-reusable-workflow", recommendation_kinds)
        self.assertIn(".github/actions/node-pnpm-bootstrap/action.yml", file_paths)
        self.assertIn(".github/workflows/reusable-node-quality.yml", file_paths)

    def test_plan_recommends_nightly_file_when_schedule_is_mixed_with_pr_validation(self) -> None:
        support = load_support_module()
        workflow_text = textwrap.dedent(
            """
            name: Mixed Schedule
            on:
              pull_request:
              schedule:
                - cron: '0 2 * * *'
            jobs:
              checks:
                runs-on: ubuntu-latest
                steps:
                  - uses: actions/checkout@v6
                  - run: pnpm lint
            """
        ).strip()

        plan = support.build_split_plan(workflow_text, workflow_name="mixed.yml")

        file_paths = {item["path"] for item in plan["target_files"]}
        recommendation_kinds = {item["kind"] for item in plan["recommendations"]}
        self.assertIn(".github/workflows/nightly.yml", file_paths)
        self.assertIn("split-by-trigger", recommendation_kinds)


if __name__ == "__main__":
    unittest.main()

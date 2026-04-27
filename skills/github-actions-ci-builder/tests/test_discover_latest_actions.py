from __future__ import annotations

import importlib.util
import json
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


class FakeApiClient:
    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = responses

    def get_json(self, path: str) -> object:
        if path not in self.responses:
            raise AssertionError(f"Unexpected API request: {path}")
        value = self.responses[path]
        if isinstance(value, Exception):
            raise value
        return value


class DiscoverLatestActionsTests(unittest.TestCase):
    def test_discover_components_prioritizes_stack_specific_matches(self) -> None:
        support = load_support_module()

        matches = support.discover_components("node pnpm cache", limit=4)

        repos = [item.repo for item in matches]
        self.assertGreaterEqual(len(repos), 3)
        self.assertEqual(repos[0], "actions/setup-node")
        self.assertIn("pnpm/action-setup", repos)
        self.assertIn("actions/cache", repos)

    def test_resolve_latest_reference_uses_release_and_resolves_tag_sha(self) -> None:
        support = load_support_module()
        client = FakeApiClient(
            {
                "/repos/actions/setup-node/releases/latest": {
                    "tag_name": "v6.3.0",
                    "html_url": "https://github.com/actions/setup-node/releases/tag/v6.3.0",
                    "published_at": "2026-03-04T02:52:09Z",
                    "immutable": False,
                },
                "/repos/actions/setup-node/git/ref/tags/v6.3.0": {
                    "object": {
                        "type": "commit",
                        "sha": "0123456789abcdef0123456789abcdef01234567",
                    }
                },
            }
        )

        resolved = support.resolve_latest_reference("actions/setup-node", client=client)

        self.assertEqual(resolved.repo, "actions/setup-node")
        self.assertEqual(resolved.tag, "v6.3.0")
        self.assertEqual(resolved.commit_sha, "0123456789abcdef0123456789abcdef01234567")
        self.assertEqual(
            resolved.pin_hint,
            "actions/setup-node@0123456789abcdef0123456789abcdef01234567 # v6.3.0",
        )

    def test_scan_workflow_distinguishes_floating_and_outdated_remote_actions(self) -> None:
        support = load_support_module()
        client = FakeApiClient(
            {
                "/repos/actions/checkout/releases/latest": {
                    "tag_name": "v6.0.2",
                    "html_url": "https://github.com/actions/checkout/releases/tag/v6.0.2",
                    "published_at": "2026-01-09T19:53:28Z",
                    "immutable": False,
                },
                "/repos/actions/checkout/git/ref/tags/v6.0.2": {
                    "object": {
                        "type": "commit",
                        "sha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                    }
                },
                "/repos/actions/setup-node/releases/latest": {
                    "tag_name": "v6.3.0",
                    "html_url": "https://github.com/actions/setup-node/releases/tag/v6.3.0",
                    "published_at": "2026-03-04T02:52:09Z",
                    "immutable": False,
                },
                "/repos/actions/setup-node/git/ref/tags/v6.3.0": {
                    "object": {
                        "type": "commit",
                        "sha": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                    }
                },
            }
        )
        workflow_text = textwrap.dedent(
            """
            name: CI
            on:
              pull_request:
              push:
                branches: [main]
            jobs:
              checks:
                runs-on: ubuntu-latest
                steps:
                  - uses: actions/checkout@v6
                  - uses: actions/setup-node@v5
                  - uses: ./.github/actions/bootstrap
                  - uses: ./.github/workflows/reusable.yml
            """
        ).strip()

        report = support.scan_workflow_actions(workflow_text, client=client)
        items = {item.repo or item.current_ref: item for item in report}

        self.assertEqual(items["actions/checkout"].status, "floating-ref")
        self.assertEqual(items["actions/setup-node"].status, "outdated")
        self.assertEqual(items["./.github/actions/bootstrap"].status, "local-action")
        self.assertEqual(items["./.github/workflows/reusable.yml"].status, "local-reusable-workflow")

    def test_cli_output_includes_verified_release_data(self) -> None:
        support = load_support_module()
        client = FakeApiClient(
            {
                "/repos/actions/cache/releases/latest": {
                    "tag_name": "v5.0.4",
                    "html_url": "https://github.com/actions/cache/releases/tag/v5.0.4",
                    "published_at": "2026-03-18T15:04:42Z",
                    "immutable": False,
                },
                "/repos/actions/cache/git/ref/tags/v5.0.4": {
                    "object": {
                        "type": "commit",
                        "sha": "cccccccccccccccccccccccccccccccccccccccc",
                    }
                },
            }
        )

        payload = support.build_component_payload(repos=["actions/cache"], client=client)
        parsed = json.loads(json.dumps(payload))

        self.assertEqual(parsed["components"][0]["repo"], "actions/cache")
        self.assertEqual(parsed["components"][0]["latest_tag"], "v5.0.4")
        self.assertEqual(parsed["components"][0]["latest_commit_sha"], "cccccccccccccccccccccccccccccccccccccccc")

    def test_scan_workflow_marks_rate_limited_refs_as_verification_blocked(self) -> None:
        support = load_support_module()
        client = FakeApiClient(
            {
                "/repos/actions/checkout/releases/latest": support.GitHubApiError(
                    "GitHub API rate limit exceeded. Set GITHUB_TOKEN or GH_TOKEN, or narrow the query and retry."
                ),
            }
        )
        workflow_text = textwrap.dedent(
            """
            name: CI
            on:
              pull_request:
            jobs:
              checks:
                runs-on: ubuntu-latest
                steps:
                  - uses: actions/checkout@v6
            """
        ).strip()

        report = support.scan_workflow_actions(workflow_text, client=client)

        self.assertEqual(report[0].status, "verification-blocked")
        self.assertIn("rate limit", report[0].verification_error.lower())


if __name__ == "__main__":
    unittest.main()

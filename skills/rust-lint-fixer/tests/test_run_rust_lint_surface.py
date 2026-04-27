from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
PYTHON = WORKSPACE_ROOT / ".uv-python" / "cpython-3.11.15-windows-x86_64-none" / "python.exe"
SCRIPT = WORKSPACE_ROOT / "rust-lint-fixer" / "scripts" / "run_rust_lint_surface.py"
FIXTURES = WORKSPACE_ROOT / "rust-lint-fixer" / "tests" / "fixtures"


class RunRustLintSurfaceTests(unittest.TestCase):
    def fixture_repo(self, name: str) -> Path:
        return FIXTURES / name

    def run_cli(self, repo_root: Path, *extra_args: str) -> dict[str, object]:
        command = [
            str(PYTHON),
            str(SCRIPT),
            "--root",
            str(repo_root),
            "--json",
            *extra_args,
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        return json.loads(result.stdout)

    def recommended_for_kind(self, payload: dict[str, object], kind: str) -> list[dict[str, object]]:
        return [item for item in payload["recommended_commands"] if item["kind"] == kind]

    def test_discover_reports_no_rust_targets(self) -> None:
        repo_root = self.fixture_repo("no-rust")

        payload = self.run_cli(repo_root, "--mode", "discover")

        self.assertEqual(payload["crate_count"], 0)
        self.assertEqual(payload["recommended_commands"], [])
        self.assertIn("Current repository has no Rust targets.", payload["blockers"])
        self.assertEqual(payload["next_step_hint"], "Current repository has no Rust targets.")

    def test_standalone_crate_adds_strict_clippy_command(self) -> None:
        repo_root = self.fixture_repo("standalone")

        payload = self.run_cli(repo_root, "--mode", "discover")

        self.assertEqual(payload["crate_count"], 1)
        self.assertEqual(payload["selected_targets"][0]["package_name"], "demo")
        clippy_commands = self.recommended_for_kind(payload, "clippy")
        self.assertEqual(clippy_commands[0]["source"], "Cargo.toml")
        self.assertIn("cargo clippy --all-targets --all-features -- -D warnings", clippy_commands[0]["command"])

    def test_workspace_root_and_member_are_classified(self) -> None:
        repo_root = self.fixture_repo("workspace")

        payload = self.run_cli(repo_root, "--mode", "discover")

        kinds = {item["kind"] for item in payload["crate_targets"]}
        self.assertIn("workspace-root", kinds)
        self.assertIn("workspace-member", kinds)
        self.assertEqual(payload["workspace_roots"], ["Cargo.toml"])

    def test_target_directory_selects_member_crate(self) -> None:
        repo_root = self.fixture_repo("workspace")

        payload = self.run_cli(repo_root, "--mode", "discover", "--target", "crates/app")

        self.assertEqual(len(payload["selected_targets"]), 1)
        self.assertEqual(payload["selected_targets"][0]["package_name"], "app")
        clippy_commands = self.recommended_for_kind(payload, "clippy")
        self.assertTrue(clippy_commands[0]["cwd"].endswith("crates\\app"))

    def test_ci_cargo_clippy_outranks_generic_command(self) -> None:
        repo_root = self.fixture_repo("ci-standalone")

        payload = self.run_cli(repo_root, "--mode", "discover")

        clippy_commands = self.recommended_for_kind(payload, "clippy")
        self.assertEqual(clippy_commands[0]["source"], ".github/workflows/rust.yml")

    def test_lint_mode_with_no_crates_stays_conservative(self) -> None:
        repo_root = self.fixture_repo("no-rust")

        payload = self.run_cli(repo_root, "--mode", "lint")

        self.assertEqual(payload["executed_commands"], [])
        self.assertEqual(payload["failures"], [])
        self.assertIn("Current repository has no Rust targets.", payload["blockers"])


if __name__ == "__main__":
    unittest.main()

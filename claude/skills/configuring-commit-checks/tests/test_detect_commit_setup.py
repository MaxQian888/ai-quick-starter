from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class DetectCommitSetupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.script = (
            Path(__file__).resolve().parents[1] / "scripts" / "detect_commit_setup.py"
        )

    def make_repo(
        self, files: dict[str, str], nested: str | None = None, with_git: bool = True
    ) -> tuple[Path, Path]:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        repo_root = Path(temp_dir.name)
        if with_git:
            (repo_root / ".git").mkdir()

        for relative_path, content in files.items():
            target = repo_root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

        start_path = repo_root
        if nested:
            start_path = repo_root / nested
            start_path.mkdir(parents=True, exist_ok=True)

        return repo_root, start_path

    def run_cli(self, project_root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self.script), "--project-root", str(project_root), "--json"],
            capture_output=True,
            text=True,
            check=False,
        )

    def payload_for(self, project_root: Path) -> dict:
        result = self.run_cli(project_root)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        return json.loads(result.stdout)

    # --- Defaults --------------------------------------------------------

    def test_node_repo_without_hooks_recommends_husky(self) -> None:
        repo_root, _ = self.make_repo(
            {
                "package.json": json.dumps(
                    {"name": "demo-node", "scripts": {"lint": "eslint ."}}
                )
            }
        )
        payload = self.payload_for(repo_root)
        self.assertEqual(payload["project_type"], "node")
        self.assertEqual(payload["recommended_tool"], "husky")
        self.assertEqual(payload["recommendation"], "add-default")

    def test_python_repo_without_hooks_recommends_pre_commit(self) -> None:
        repo_root, _ = self.make_repo(
            {"pyproject.toml": "[project]\nname = 'demo-python'\n"}
        )
        payload = self.payload_for(repo_root)
        self.assertEqual(payload["project_type"], "python")
        self.assertEqual(payload["recommended_tool"], "pre-commit")
        self.assertEqual(payload["recommendation"], "add-default")

    def test_mixed_repo_without_hooks_recommends_pre_commit(self) -> None:
        repo_root, _ = self.make_repo(
            {
                "package.json": json.dumps({"name": "demo-mixed"}),
                "pyproject.toml": "[project]\nname = 'demo-mixed'\n",
            }
        )
        payload = self.payload_for(repo_root)
        self.assertEqual(payload["project_type"], "mixed")
        self.assertEqual(payload["recommended_tool"], "pre-commit")
        self.assertEqual(payload["recommendation"], "add-default")

    # --- Preserve-existing -----------------------------------------------

    def test_existing_husky_is_preserved(self) -> None:
        repo_root, _ = self.make_repo(
            {
                "package.json": json.dumps({"name": "demo-node"}),
                ".husky/pre-commit": "npm test\n",
            }
        )
        payload = self.payload_for(repo_root)
        self.assertIn("husky", payload["existing_tools"])
        self.assertEqual(payload["recommended_tool"], "husky")
        self.assertEqual(payload["recommendation"], "preserve-existing")

    def test_existing_lefthook_toml_is_preserved(self) -> None:
        repo_root, _ = self.make_repo(
            {
                "package.json": json.dumps({"name": "demo-node"}),
                "lefthook.toml": '[pre-commit]\ncommands = {}\n',
            }
        )
        payload = self.payload_for(repo_root)
        self.assertEqual(payload["recommended_tool"], "lefthook")
        self.assertEqual(payload["recommendation"], "preserve-existing")

    def test_existing_dotfile_lefthook_yaml_is_preserved(self) -> None:
        repo_root, _ = self.make_repo(
            {
                "package.json": json.dumps({"name": "demo-node"}),
                ".lefthook.yaml": "pre-commit:\n  commands: {}\n",
            }
        )
        payload = self.payload_for(repo_root)
        self.assertEqual(payload["recommended_tool"], "lefthook")
        self.assertEqual(payload["recommendation"], "preserve-existing")

    def test_simple_git_hooks_block_is_preserved(self) -> None:
        repo_root, _ = self.make_repo(
            {
                "package.json": json.dumps(
                    {
                        "name": "demo-node",
                        "simple-git-hooks": {"pre-commit": "npm test"},
                    }
                ),
            }
        )
        payload = self.payload_for(repo_root)
        self.assertIn("simple-git-hooks", payload["existing_tools"])
        self.assertEqual(payload["recommended_tool"], "simple-git-hooks")
        self.assertEqual(payload["recommendation"], "preserve-existing")

    def test_husky_in_dev_dependencies_without_dir_is_preserved(self) -> None:
        # The team picked husky and listed it in devDependencies, but `husky
        # init` hasn't been run yet. We should still treat husky as primary.
        repo_root, _ = self.make_repo(
            {
                "package.json": json.dumps(
                    {
                        "name": "demo-node",
                        "devDependencies": {"husky": "^9.0.0"},
                    }
                )
            }
        )
        payload = self.payload_for(repo_root)
        self.assertIn("husky", payload["existing_tools"])
        self.assertEqual(payload["recommended_tool"], "husky")
        self.assertEqual(payload["recommendation"], "preserve-existing")

    def test_pre_commit_in_pyproject_without_yaml_is_preserved(self) -> None:
        repo_root, _ = self.make_repo(
            {
                "pyproject.toml": (
                    "[project]\n"
                    "name = 'demo'\n"
                    "[project.optional-dependencies]\n"
                    "dev = ['pre-commit', 'ruff']\n"
                ),
            }
        )
        payload = self.payload_for(repo_root)
        self.assertIn("pre-commit", payload["existing_tools"])
        self.assertEqual(payload["recommended_tool"], "pre-commit")
        self.assertEqual(payload["recommendation"], "preserve-existing")

    # --- Complete-existing -----------------------------------------------

    def test_lint_staged_only_completes_with_husky(self) -> None:
        repo_root, _ = self.make_repo(
            {
                "package.json": json.dumps(
                    {
                        "name": "demo-node",
                        "lint-staged": {"*.js": ["eslint --fix"]},
                    }
                )
            }
        )
        payload = self.payload_for(repo_root)
        self.assertIn("lint-staged", payload["existing_tools"])
        self.assertEqual(payload["recommended_tool"], "husky")
        self.assertEqual(payload["recommendation"], "complete-existing")

    # --- Repo-root resolution -------------------------------------------

    def test_nested_path_resolves_repo_root_and_preserves_lefthook(self) -> None:
        repo_root, start_path = self.make_repo(
            {
                "package.json": json.dumps({"name": "demo-node"}),
                "lefthook.yml": "pre-commit:\n  commands: {}\n",
            },
            nested="apps/web/src",
        )
        payload = self.payload_for(start_path)
        self.assertEqual(payload["detected_root"], str(repo_root))
        self.assertEqual(payload["recommended_tool"], "lefthook")
        self.assertEqual(payload["recommendation"], "preserve-existing")

    def test_workspace_marker_resolves_root_without_git(self) -> None:
        # No .git directory, but a pnpm-workspace.yaml at the top: still find
        # the workspace root from a nested path so we don't apply a hook
        # config inside a sub-package.
        repo_root, start_path = self.make_repo(
            {
                "pnpm-workspace.yaml": "packages:\n  - apps/*\n",
                "apps/web/package.json": json.dumps({"name": "web"}),
            },
            nested="apps/web",
            with_git=False,
        )
        payload = self.payload_for(start_path)
        self.assertEqual(payload["detected_root"], str(repo_root))

    # --- Unknown ---------------------------------------------------------

    def test_empty_repo_returns_review_manually(self) -> None:
        repo_root, _ = self.make_repo({})
        payload = self.payload_for(repo_root)
        self.assertEqual(payload["project_type"], "unknown")
        self.assertEqual(payload["recommendation"], "review-manually")


if __name__ == "__main__":
    unittest.main()

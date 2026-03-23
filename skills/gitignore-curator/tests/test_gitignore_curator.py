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


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "gitignore_curator.py"
TMP_ROOT = Path(__file__).resolve().parents[2] / "tmp" / "gitignore-curator-tests"


class GitignoreCuratorTests(unittest.TestCase):
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

    def init_repo(self, root: Path) -> None:
        subprocess.run(
            ["git", "init", "--quiet"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Codex Tester"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "codex@example.com"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )

    def make_repo(self, files: dict[str, str]) -> Path:
        root = self.make_temp_dir("gitignore-curator-repo")
        self.init_repo(root)
        for relative_path, content in files.items():
            target = root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        return root

    def git_commit_all(self, repo_root: Path, message: str) -> None:
        subprocess.run(
            ["git", "add", "."],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "commit", "--quiet", "-m", message],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["UV_CACHE_DIR"] = str(Path(__file__).resolve().parents[2] / ".uv-cache")
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *args],
            capture_output=True,
            text=True,
            env=env,
        )

    def load_payload(self, *args: str) -> dict[str, object]:
        result = self.run_cli(*args)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        return json.loads(result.stdout)

    def find_candidate(
        self,
        payload: dict[str, object],
        *,
        pattern: str,
        target_file: str,
    ) -> dict[str, object]:
        for item in payload["candidate_rules"]:
            if item["pattern"] == pattern and item["target_file"] == target_file:
                return item
        self.fail(f"Missing candidate for {pattern!r} in {target_file!r}")

    def test_analyze_uses_git_status_signal_for_untracked_generated_dir(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": '{\n  "name": "demo"\n}\n',
                "coverage/lcov.info": "TN:\n",
            }
        )

        payload = self.load_payload("--project-root", str(repo_root), "--json")

        candidate = self.find_candidate(payload, pattern="coverage/", target_file=".gitignore")
        self.assertEqual(candidate["confidence"], "high")
        self.assertTrue(any("git-status" in item for item in candidate["evidence"]))
        self.assertIn(".git/info/exclude", payload["inspected_ignore_files"])

    def test_analyze_routes_editor_metadata_to_git_info_exclude(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": '{\n  "name": "demo"\n}\n',
                ".idea/workspace.xml": "<project />\n",
            }
        )

        payload = self.load_payload("--project-root", str(repo_root), "--json")

        candidate = self.find_candidate(payload, pattern=".idea/", target_file=".git/info/exclude")
        self.assertEqual(candidate["confidence"], "medium")
        self.assertTrue(any("git-status" in item for item in candidate["evidence"]))

    def test_analyze_routes_generated_dirs_to_existing_dockerignore(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": '{\n  "name": "demo"\n}\n',
                "Dockerfile": "FROM node:20-alpine\nWORKDIR /app\nCOPY . .\n",
                ".dockerignore": ".git/\n",
                "node_modules/pkg/index.js": "module.exports = {};\n",
            }
        )

        payload = self.load_payload("--project-root", str(repo_root), "--json")

        docker_candidate = self.find_candidate(payload, pattern="node_modules/", target_file=".dockerignore")
        self.assertEqual(docker_candidate["confidence"], "high")
        self.assertTrue(any("docker" in item for item in docker_candidate["evidence"]))
        git_candidate = self.find_candidate(payload, pattern="node_modules/", target_file=".gitignore")
        self.assertEqual(git_candidate["confidence"], "high")

    def test_recent_history_does_not_override_tracked_commitworthy_content(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": '{\n  "name": "demo"\n}\n',
                "dist/index.js": "console.log('tracked build');\n",
            }
        )
        self.git_commit_all(repo_root, "track dist intentionally")

        payload = self.load_payload("--project-root", str(repo_root), "--json")

        patterns = {(item["pattern"], item["target_file"]) for item in payload["candidate_rules"]}
        self.assertNotIn(("dist/", ".gitignore"), patterns)
        skipped = payload["skipped_rules"]
        self.assertTrue(any(item["pattern"] == "dist/" for item in skipped))
        self.assertTrue(any("tracked" in reason for item in skipped for reason in item["reasons"]))

    def test_apply_appends_missing_rules_to_multiple_target_files(self) -> None:
        repo_root = self.make_repo(
            {
                ".gitignore": "dist/\n",
                "Dockerfile": "FROM node:20-alpine\n",
                ".dockerignore": ".git/\n",
                "package.json": '{\n  "name": "demo"\n}\n',
                "node_modules/pkg/index.js": "module.exports = {};\n",
                ".idea/workspace.xml": "<project />\n",
            }
        )

        payload = self.load_payload("--project-root", str(repo_root), "--apply", "--json")

        gitignore_text = (repo_root / ".gitignore").read_text(encoding="utf-8")
        dockerignore_text = (repo_root / ".dockerignore").read_text(encoding="utf-8")
        exclude_text = (repo_root / ".git" / "info" / "exclude").read_text(encoding="utf-8")

        applied = {(item["pattern"], item["target_file"]) for item in payload["applied_rules"]}
        self.assertIn(("node_modules/", ".gitignore"), applied)
        self.assertIn(("node_modules/", ".dockerignore"), applied)
        self.assertIn((".idea/", ".git/info/exclude"), applied)
        self.assertIn("# Added by gitignore-curator", gitignore_text)
        self.assertIn("# Added by gitignore-curator", dockerignore_text)
        self.assertIn("# Added by gitignore-curator", exclude_text)
        self.assertEqual(gitignore_text.count("dist/"), 1)
        self.assertIn("node_modules/\n", gitignore_text)
        self.assertIn("node_modules/\n", dockerignore_text)
        self.assertIn(".idea/\n", exclude_text)

    def test_non_git_directory_returns_error(self) -> None:
        root = self.make_temp_dir("gitignore-curator-non-repo")
        (root / "package.json").write_text(
            textwrap.dedent(
                """
                {
                  "name": "demo"
                }
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )

        result = self.run_cli("--project-root", str(root), "--json")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("git repository", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()

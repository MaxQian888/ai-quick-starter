from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "detect_refinement_scope.py"


class DetectRefinementScopeTests(unittest.TestCase):
    def make_repo(self) -> Path:
        repo = Path(tempfile.mkdtemp(prefix="code-simplifier-"))
        self.run_command(repo, "git", "init", "--initial-branch=main")
        self.run_command(repo, "git", "config", "user.name", "Test User")
        self.run_command(repo, "git", "config", "user.email", "test@example.com")
        return repo

    def write_file(self, repo: Path, relative_path: str, content: str) -> None:
        file_path = repo / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

    def run_command(self, repo: Path, *command: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            list(command),
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        )

    def run_cli(self, repo: Path, *args: str) -> dict[str, object]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--repo-root", str(repo), "--json", *args],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        return json.loads(result.stdout)

    def test_worktree_scope_reports_staged_unstaged_and_untracked_files(self) -> None:
        repo = self.make_repo()
        self.write_file(repo, "src/app.ts", "export function app() {\n  return 1;\n}\n")
        self.write_file(repo, "src/util.ts", "export function util() {\n  return 2;\n}\n")
        self.run_command(repo, "git", "add", ".")
        self.run_command(repo, "git", "commit", "-m", "initial")

        self.write_file(repo, "src/app.ts", "export function app() {\n  return 3;\n}\n")
        self.write_file(repo, "src/util.ts", "export function util() {\n  return 4;\n}\n")
        self.run_command(repo, "git", "add", "src/util.ts")
        self.write_file(repo, "src/new.ts", "export const fresh = true;\n")

        payload = self.run_cli(repo)
        files = {entry["path"]: entry for entry in payload["files"]}

        self.assertEqual(files["src/app.ts"]["change_sources"], ["unstaged"])
        self.assertEqual(files["src/app.ts"]["line_ranges"][0]["start"], 2)
        self.assertEqual(files["src/util.ts"]["change_sources"], ["staged"])
        self.assertTrue(files["src/new.ts"]["treat_as_full_file"])
        self.assertEqual(files["src/new.ts"]["change_sources"], ["untracked"])

    def test_worktree_scope_merges_staged_and_unstaged_ranges_for_same_file(self) -> None:
        repo = self.make_repo()
        self.write_file(
            repo,
            "src/feature.ts",
            "export function feature() {\n  const first = 1;\n  const second = 2;\n  return first + second;\n}\n",
        )
        self.run_command(repo, "git", "add", ".")
        self.run_command(repo, "git", "commit", "-m", "initial")

        self.write_file(
            repo,
            "src/feature.ts",
            "export function feature() {\n  const first = 10;\n  const second = 2;\n  return first + second;\n}\n",
        )
        self.run_command(repo, "git", "add", "src/feature.ts")
        self.write_file(
            repo,
            "src/feature.ts",
            "export function feature() {\n  const first = 10;\n  const second = 20;\n  return first + second;\n}\n",
        )

        payload = self.run_cli(repo)
        entry = payload["files"][0]

        self.assertEqual(entry["path"], "src/feature.ts")
        self.assertEqual(entry["change_sources"], ["staged", "unstaged"])
        self.assertEqual([item["source"] for item in entry["line_ranges"]], ["staged", "unstaged"])
        self.assertEqual([item["start"] for item in entry["line_ranges"]], [2, 3])

    def test_base_ref_mode_reports_committed_diff_against_base_ref(self) -> None:
        repo = self.make_repo()
        self.write_file(repo, "src/module.ts", "export function value() {\n  return 1;\n}\n")
        self.run_command(repo, "git", "add", ".")
        self.run_command(repo, "git", "commit", "-m", "initial")

        self.write_file(repo, "src/module.ts", "export function value() {\n  return 2;\n}\n")
        self.run_command(repo, "git", "add", ".")
        self.run_command(repo, "git", "commit", "-m", "update")

        payload = self.run_cli(repo, "--mode", "base-ref", "--base-ref", "HEAD~1")
        entry = payload["files"][0]

        self.assertEqual(entry["path"], "src/module.ts")
        self.assertEqual(entry["change_sources"], ["base-ref"])
        self.assertEqual(entry["line_ranges"][0]["start"], 2)

    def test_non_git_directory_returns_warning_with_empty_scope(self) -> None:
        repo = Path(tempfile.mkdtemp(prefix="code-simplifier-nogit-"))

        payload = self.run_cli(repo)

        self.assertEqual(payload["files"], [])
        self.assertTrue(payload["warnings"])


if __name__ == "__main__":
    unittest.main()

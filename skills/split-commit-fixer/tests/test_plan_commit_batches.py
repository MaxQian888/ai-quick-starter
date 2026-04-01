from __future__ import annotations

import json
import shutil
import subprocess
import unittest
import uuid
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
SKILL_ROOT = WORKSPACE_ROOT / "split-commit-fixer"
PYTHON = WORKSPACE_ROOT / ".uv-python" / "cpython-3.11.15-windows-x86_64-none" / "python.exe"
SCRIPT = SKILL_ROOT / "scripts" / "plan_commit_batches.py"
TMP_ROOT = SKILL_ROOT / ".tmp-tests"


class PlanCommitBatchesTests(unittest.TestCase):
    def setUp(self) -> None:
        TMP_ROOT.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        if TMP_ROOT.exists():
            shutil.rmtree(TMP_ROOT, ignore_errors=True)

    def make_dir(self) -> Path:
        repo_root = TMP_ROOT / f"split-commit-fixer-{uuid.uuid4().hex}"
        repo_root.mkdir(parents=True, exist_ok=True)
        return repo_root

    def write_files(self, repo_root: Path, files: dict[str, str]) -> None:
        for relative_path, content in files.items():
            file_path = repo_root / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

    def git(self, repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

    def init_repo(self, files: dict[str, str]) -> Path:
        repo_root = self.make_dir()
        self.assertEqual(self.git(repo_root, "init").returncode, 0)
        self.assertEqual(self.git(repo_root, "config", "user.email", "skill@test.local").returncode, 0)
        self.assertEqual(self.git(repo_root, "config", "user.name", "Skill Test").returncode, 0)
        self.write_files(repo_root, files)
        self.assertEqual(self.git(repo_root, "add", ".").returncode, 0)
        self.assertEqual(self.git(repo_root, "commit", "-m", "initial").returncode, 0)
        return repo_root

    def run_cli(self, repo_root: Path) -> dict[str, object]:
        result = subprocess.run(
            [
                str(PYTHON),
                str(SCRIPT),
                "--project-root",
                str(repo_root),
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        return json.loads(result.stdout)

    def test_blocks_non_git_directory(self) -> None:
        repo_root = self.make_dir()

        payload = self.run_cli(repo_root)

        self.assertEqual(payload["status"], "blocked")
        self.assertFalse(payload["git_state"]["is_git_repo"])
        self.assertEqual(payload["batches"], [])
        self.assertIn("git worktree", payload["global_cautions"][0])

    def test_splits_independent_feature_batches_and_docs_last(self) -> None:
        repo_root = self.init_repo(
            {
                "src/auth/login.ts": "export const login = () => 'old';\n",
                "src/billing/invoice.ts": "export const invoice = () => 'old';\n",
                "docs/release-notes.md": "# Notes\n",
                "package.json": json.dumps(
                    {
                        "name": "demo",
                        "scripts": {
                            "lint": "eslint .",
                            "typecheck": "tsc --noEmit",
                            "test": "vitest run",
                            "build": "vite build",
                        },
                    }
                ),
                "pnpm-lock.yaml": "lockfileVersion: '9.0'\n",
            }
        )
        self.write_files(
            repo_root,
            {
                "src/auth/login.ts": "export const login = () => 'new-auth';\n",
                "src/billing/invoice.ts": "export const invoice = () => 'new-billing';\n",
                "docs/release-notes.md": "# Notes\n\n- update\n",
            },
        )

        payload = self.run_cli(repo_root)

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["quality_gate_commands"][0]["command"], "pnpm lint")
        self.assertEqual(len(payload["batches"]), 3)
        self.assertEqual(payload["batches"][0]["label"], "auth")
        self.assertEqual(payload["batches"][1]["label"], "billing")
        self.assertEqual(payload["batches"][2]["kind"], "docs")
        self.assertEqual(payload["recommended_order"][-1], payload["batches"][2]["key"])
        self.assertEqual(
            payload["batches"][0]["quality_gate_plan"]["narrow_commands"],
            ["pnpm lint", "pnpm typecheck", "pnpm test"],
        )
        self.assertEqual(
            payload["batches"][2]["quality_gate_plan"]["narrow_commands"],
            ["pnpm lint"],
        )

    def test_keeps_matching_tests_with_feature_scope(self) -> None:
        repo_root = self.init_repo(
            {
                "src/auth/login.ts": "export const login = () => 'old';\n",
                "tests/auth/test_login.py": "def test_login():\n    assert True\n",
                "pyproject.toml": (
                    "[project]\n"
                    "name = 'demo'\n"
                    "[tool.pytest.ini_options]\n"
                    "testpaths = ['tests']\n"
                    "[tool.ruff]\n"
                    "line-length = 88\n"
                ),
            }
        )
        self.write_files(
            repo_root,
            {
                "src/auth/login.ts": "export const login = () => 'new';\n",
                "tests/auth/test_login.py": "def test_login():\n    assert 'new'\n",
            },
        )

        payload = self.run_cli(repo_root)

        self.assertEqual(len(payload["batches"]), 1)
        batch = payload["batches"][0]
        self.assertEqual(batch["kind"], "feature")
        self.assertEqual(sorted(batch["files"]), ["src/auth/login.ts", "tests/auth/test_login.py"])
        self.assertEqual(batch["suggested_commit"]["type"], "feat")
        self.assertEqual(
            batch["quality_gate_plan"]["narrow_commands"],
            ["python -m ruff check .", "python -m pytest"],
        )

    def test_shared_root_config_stays_separate_when_multiple_features_are_dirty(self) -> None:
        repo_root = self.init_repo(
            {
                "src/auth/login.ts": "export const login = () => 'old';\n",
                "src/payments/charge.ts": "export const charge = () => 'old';\n",
                "package.json": json.dumps({"name": "demo", "version": "1.0.0"}, indent=2) + "\n",
                "pnpm-lock.yaml": "lockfileVersion: '9.0'\n",
            }
        )
        self.write_files(
            repo_root,
            {
                "src/auth/login.ts": "export const login = () => 'new-auth';\n",
                "src/payments/charge.ts": "export const charge = () => 'new-payments';\n",
                "package.json": json.dumps({"name": "demo", "version": "1.1.0"}, indent=2) + "\n",
                "pnpm-lock.yaml": "lockfileVersion: '9.1'\n",
            },
        )

        payload = self.run_cli(repo_root)

        self.assertEqual(len(payload["batches"]), 3)
        shared_batch = payload["batches"][2]
        self.assertEqual(shared_batch["kind"], "config")
        self.assertEqual(shared_batch["label"], "shared config")
        self.assertIn("Shared config", shared_batch["cautions"][0])
        self.assertTrue(payload["global_cautions"])
        self.assertTrue(shared_batch["quality_gate_plan"]["narrow_commands"])

    def test_reports_partial_staging_as_global_and_batch_caution(self) -> None:
        repo_root = self.init_repo(
            {
                "src/auth/login.ts": "export const login = () => 'old';\n",
            }
        )
        self.write_files(
            repo_root,
            {
                "src/auth/login.ts": "export const login = () => 'new';\n",
            },
        )
        self.assertEqual(self.git(repo_root, "add", "src/auth/login.ts").returncode, 0)
        self.write_files(
            repo_root,
            {
                "src/auth/login.ts": "export const login = () => 'newer';\n",
            },
        )

        payload = self.run_cli(repo_root)

        self.assertEqual(payload["git_state"]["partial_count"], 1)
        self.assertTrue(payload["global_cautions"])
        self.assertTrue(payload["batches"][0]["cautions"])

    def test_docs_only_repo_falls_back_to_diff_check(self) -> None:
        repo_root = self.init_repo(
            {
                "docs/guide.md": "# Guide\n",
            }
        )
        self.write_files(
            repo_root,
            {
                "docs/guide.md": "# Guide\n\nMore docs.\n",
            },
        )

        payload = self.run_cli(repo_root)

        self.assertEqual(payload["quality_gate_commands"][0]["command"], "git diff --check")
        self.assertEqual(payload["batches"][0]["kind"], "docs")
        self.assertEqual(
            payload["batches"][0]["quality_gate_plan"]["narrow_commands"],
            ["git diff --check"],
        )


if __name__ == "__main__":
    unittest.main()

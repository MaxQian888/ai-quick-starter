from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path
from uuid import uuid4

WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
PYTHON = WORKSPACE_ROOT / ".uv-python" / "cpython-3.11.15-windows-x86_64-none" / "python.exe"
SCRIPT = WORKSPACE_ROOT / "project-prompt-optimizer" / "scripts" / "summarize_project_context.py"
TMP_ROOT = WORKSPACE_ROOT / "project-prompt-optimizer" / ".tmp-tests"
TMP_ROOT.mkdir(parents=True, exist_ok=True)


class SummarizeProjectContextTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cleanup: list[Path] = []

    def tearDown(self) -> None:
        for path in reversed(self.cleanup):
            shutil.rmtree(path, ignore_errors=True)

    def make_repo(self) -> Path:
        repo = TMP_ROOT / f"repo-{uuid4().hex}"
        repo.mkdir(parents=True, exist_ok=False)
        self.cleanup.append(repo)

        (repo / "apps" / "web").mkdir(parents=True)
        (repo / "tests").mkdir(parents=True)
        (repo / "docs").mkdir(parents=True)
        (repo / "package.json").write_text(
            json.dumps({"name": "demo", "scripts": {"lint": "eslint .", "test": "vitest"}}),
            encoding="utf-8",
        )
        (repo / "docs" / "readme.md").write_text("# docs", encoding="utf-8")
        (repo / "apps" / "web" / "main.ts").write_text("console.log('ok')", encoding="utf-8")
        return repo

    def run_cli(self, repo: Path, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(PYTHON), str(SCRIPT), "--root", str(repo), *extra],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_json_summary_contains_core_signals(self) -> None:
        repo = self.make_repo()
        result = self.run_cli(repo)
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertIn("stack_markers", payload)
        self.assertIn("candidate_source_roots", payload)
        self.assertIn("validation_clues", payload)
        self.assertIn("notable_docs", payload)
        self.assertTrue(payload["stacks"])

    def test_markdown_output_renders_sections(self) -> None:
        repo = self.make_repo()
        result = self.run_cli(repo, "--format", "markdown")
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("## Stacks", result.stdout)
        self.assertIn("## Validation Clues", result.stdout)

    def test_skips_cache_directories_by_default(self) -> None:
        repo = self.make_repo()
        (repo / ".uv-cache-local" / "noise").mkdir(parents=True, exist_ok=True)
        (repo / ".uv-cache-local" / "noise" / "x.py").write_text("print('noise')", encoding="utf-8")
        (repo / ".codex-uv-cache" / "noise").mkdir(parents=True, exist_ok=True)
        (repo / ".codex-uv-cache" / "noise" / "y.py").write_text("print('noise')", encoding="utf-8")

        result = self.run_cli(repo)
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = json.loads(result.stdout)

        self.assertNotIn(".uv-cache-local", payload["top_level_dirs"])
        self.assertNotIn(".codex-uv-cache", payload["top_level_dirs"])

    def test_include_filters_and_max_depth_narrow_scanned_files(self) -> None:
        repo = self.make_repo()
        (repo / "packages" / "ui").mkdir(parents=True, exist_ok=True)
        (repo / "packages" / "ui" / "button.tsx").write_text("export const Button = () => null;", encoding="utf-8")
        (repo / "packages" / "ui" / "nested").mkdir(parents=True, exist_ok=True)
        (repo / "packages" / "ui" / "nested" / "deep.tsx").write_text("export const Deep = () => null;", encoding="utf-8")

        result = self.run_cli(repo, "--include", "packages/ui", "--max-depth", "1")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["include_filters"], ["packages/ui"])
        self.assertEqual(payload["scanned_file_count"], 1)
        self.assertEqual(payload["candidate_source_roots"], ["apps", "packages", "tests", "docs"])

    def test_invalid_root_returns_non_zero(self) -> None:
        missing = TMP_ROOT / f"missing-{uuid4().hex}"

        result = self.run_cli(missing)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Invalid root path", result.stderr or result.stdout)


if __name__ == "__main__":
    unittest.main()

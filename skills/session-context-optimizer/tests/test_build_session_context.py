from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "build_session_context.py"


class BuildSessionContextTests(unittest.TestCase):
    def make_repo(self, files: dict[str, str]) -> Path:
        repo_root = Path(tempfile.mkdtemp(prefix="session-context-optimizer-"))
        for relative_path, content in files.items():
            file_path = repo_root / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
        return repo_root

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        command = [sys.executable, str(SCRIPT), *args]
        return subprocess.run(command, capture_output=True, text=True, check=False)

    def load_payload(self, stdout: str) -> dict[str, object]:
        return json.loads(stdout)

    def test_detects_candidate_skill_modules(self) -> None:
        repo_root = self.make_repo(
            {
                "good-skill/SKILL.md": "---\nname: good-skill\ndescription: test\n---\n",
                "good-skill/agents/openai.yaml": "interface:\n  display_name: Good Skill\n",
                "good-skill/scripts/tool.py": "print('x')\n",
                "good-skill/tests/test_tool.py": "pass\n",
            }
        )

        result = self.run_cli("--root", str(repo_root))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        self.assertEqual(payload["candidate_count"], 1)
        self.assertEqual(payload["ranking_mode"], "structure-only")
        self.assertEqual(payload["candidates"][0]["path"], "good-skill")
        self.assertTrue(payload["candidates"][0]["signals"]["has_skill_md"])
        self.assertTrue(payload["candidates"][0]["signals"]["has_openai_yaml"])

    def test_skips_tmp_and_node_modules_by_default(self) -> None:
        repo_root = self.make_repo(
            {
                "_tmp_bad/SKILL.md": "---\nname: tmp-bad\ndescription: tmp\n---\n",
                "node_modules/fake-skill/SKILL.md": "---\nname: fake-skill\ndescription: fake\n---\n",
                "real-skill/SKILL.md": "---\nname: real-skill\ndescription: real\n---\n",
            }
        )

        result = self.run_cli("--root", str(repo_root))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        paths = [item["path"] for item in payload["candidates"]]
        self.assertIn("real-skill", paths)
        self.assertNotIn("_tmp_bad", paths)
        self.assertNotIn("node_modules/fake-skill", paths)
        skipped = {item["path"] for item in payload["skipped"]}
        self.assertIn("_tmp_bad", skipped)
        self.assertIn("node_modules", skipped)

    def test_include_and_exclude_filters_narrow_results(self) -> None:
        repo_root = self.make_repo(
            {
                "alpha-skill/SKILL.md": "---\nname: alpha-skill\ndescription: alpha\n---\n",
                "beta-skill/SKILL.md": "---\nname: beta-skill\ndescription: beta\n---\n",
            }
        )

        result = self.run_cli(
            "--root",
            str(repo_root),
            "--include",
            "alpha",
            "--exclude",
            "beta",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        self.assertEqual([item["path"] for item in payload["candidates"]], ["alpha-skill"])

    def test_limit_caps_candidate_output(self) -> None:
        repo_root = self.make_repo(
            {
                "alpha-skill/SKILL.md": "---\nname: alpha-skill\ndescription: alpha\n---\n",
                "beta-skill/SKILL.md": "---\nname: beta-skill\ndescription: beta\n---\n",
            }
        )

        result = self.run_cli("--root", str(repo_root), "--limit", "1")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        self.assertEqual(payload["candidate_count"], 1)
        self.assertEqual(len(payload["candidates"]), 1)

    def test_prefers_candidates_with_stronger_structure_signals(self) -> None:
        repo_root = self.make_repo(
            {
                "minimal-skill/SKILL.md": "---\nname: minimal-skill\ndescription: minimal\n---\n",
                "strong-skill/SKILL.md": "---\nname: strong-skill\ndescription: strong\n---\n",
                "strong-skill/agents/openai.yaml": "interface:\n  display_name: Strong Skill\n",
                "strong-skill/references/guide.md": "# Guide\n",
                "strong-skill/scripts/tool.py": "print('x')\n",
                "strong-skill/tests/test_tool.py": "pass\n",
            }
        )

        result = self.run_cli("--root", str(repo_root), "--limit", "1")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        self.assertEqual(payload["candidates"][0]["path"], "strong-skill")
        self.assertGreater(payload["candidates"][0]["signal_count"], 1)
        self.assertEqual(payload["ranking_mode"], "structure-only")

    def test_task_relevance_promotes_context_focused_skill(self) -> None:
        repo_root = self.make_repo(
            {
                "generic-skill/SKILL.md": "---\nname: generic-skill\ndescription: Build workflow docs for repository tasks.\n---\n",
                "generic-skill/agents/openai.yaml": "interface:\n  display_name: Generic Skill\n",
                "generic-skill/references/workflow.md": "# Workflow\n",
                "generic-skill/scripts/tool.py": "print('x')\n",
                "generic-skill/tests/test_tool.py": "pass\n",
                "context-skill/SKILL.md": "---\nname: context-skill\ndescription: Improve session context and planning guidance for repository work.\n---\n",
                "context-skill/agents/openai.yaml": "interface:\n  display_name: Context Skill\n",
                "context-skill/references/context-pack.md": "# Context Pack\n",
                "context-skill/scripts/context_scan.py": "print('x')\n",
                "context-skill/tests/test_context.py": "pass\n",
            }
        )

        result = self.run_cli(
            "--root",
            str(repo_root),
            "--task",
            "improve session context for planning",
            "--limit",
            "1",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        self.assertEqual(payload["ranking_mode"], "structure-plus-task")
        self.assertEqual(payload["task"], "improve session context for planning")
        self.assertEqual(payload["candidates"][0]["path"], "context-skill")
        self.assertGreater(payload["candidates"][0]["task_score"], 0)

    def test_task_mode_reports_matched_terms_and_reason(self) -> None:
        repo_root = self.make_repo(
            {
                "context-skill/SKILL.md": "---\nname: context-skill\ndescription: Improve session context and planning guidance.\n---\n",
                "context-skill/references/context-pack.md": "# Context Pack\n",
            }
        )

        result = self.run_cli(
            "--root",
            str(repo_root),
            "--task",
            "improve session context for planning",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        candidate = payload["candidates"][0]
        self.assertIn("context", candidate["matched_terms"])
        self.assertTrue(candidate["why_recommended"])
        self.assertIn("context", candidate["why_recommended"].lower())

    def test_ignores_non_skill_directories_even_if_they_have_scripts(self) -> None:
        repo_root = self.make_repo(
            {
                "not-a-skill/scripts/tool.py": "print('x')\n",
                "not-a-skill/tests/test_tool.py": "pass\n",
            }
        )

        result = self.run_cli("--root", str(repo_root))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        self.assertEqual(payload["candidate_count"], 0)
        self.assertEqual(payload["candidates"], [])

    def test_markdown_output_contains_candidate_summary_sections(self) -> None:
        repo_root = self.make_repo(
            {
                "alpha-skill/SKILL.md": "---\nname: alpha-skill\ndescription: alpha\n---\n",
                "alpha-skill/references/guide.md": "# Guide\n",
            }
        )

        result = self.run_cli("--root", str(repo_root), "--format", "markdown")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("# Session Context Candidates", result.stdout)
        self.assertIn("alpha-skill", result.stdout)
        self.assertIn("## Skipped Paths", result.stdout)

    def test_markdown_reports_scores_and_reason_in_task_mode(self) -> None:
        repo_root = self.make_repo(
            {
                "context-skill/SKILL.md": "---\nname: context-skill\ndescription: Improve session context and planning guidance.\n---\n",
                "context-skill/scripts/context_scan.py": "print('x')\n",
            }
        )

        result = self.run_cli(
            "--root",
            str(repo_root),
            "--format",
            "markdown",
            "--task",
            "improve session context for planning",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("ranking mode: structure-plus-task", result.stdout.lower())
        self.assertIn("final", result.stdout.lower())
        self.assertIn("why:", result.stdout.lower())
        self.assertIn("context-skill", result.stdout)


if __name__ == "__main__":
    unittest.main()

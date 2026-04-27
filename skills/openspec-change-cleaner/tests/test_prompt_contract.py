from __future__ import annotations

import re
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
SKILL_MD = SKILL_ROOT / "SKILL.md"
OPENAI_YAML = SKILL_ROOT / "agents" / "openai.yaml"


class OpenSpecChangeCleanerPromptContractTests(unittest.TestCase):
    def test_frontmatter_description_stays_trigger_focused(self) -> None:
        content = SKILL_MD.read_text(encoding="utf-8")

        match = re.search(
            r"^---\s+name:\s+openspec-change-cleaner\s+description:\s+(.+?)\s+---",
            content,
            re.DOTALL,
        )
        self.assertIsNotNone(match, "Could not locate SKILL.md frontmatter description")
        description = " ".join(match.group(1).split())

        self.assertTrue(description.startswith("Use when"))
        self.assertIn("openspec", description.lower())
        self.assertIn("archive", description.lower())
        self.assertIn("latest implementation", description.lower())

        forbidden_workflow_phrases = [
            "run the audit script",
            "update the task file",
            "write the cleanup report",
            "rerun validate",
        ]
        for phrase in forbidden_workflow_phrases:
            self.assertNotIn(phrase, description.lower())

    def test_openai_default_prompt_mentions_skill_and_cleanup_goal(self) -> None:
        content = OPENAI_YAML.read_text(encoding="utf-8")

        self.assertIn('display_name: "OpenSpec Change Cleaner"', content)
        self.assertIn('short_description: "Audit and reconcile stale OpenSpec changes"', content)
        self.assertIn("$openspec-change-cleaner", content)
        self.assertIn("latest implementation", content.lower())
        self.assertIn("archive", content.lower())

    def test_skill_body_mentions_reconcile_command_and_auto_archive_boundary(self) -> None:
        content = SKILL_MD.read_text(encoding="utf-8")

        self.assertIn("reconcile_change_artifacts.py", content)
        self.assertIn("--archive-when-ready", content)
        self.assertIn("Do not delete archive history", content)


if __name__ == "__main__":
    unittest.main()

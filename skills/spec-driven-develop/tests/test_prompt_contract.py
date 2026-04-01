from __future__ import annotations

import re
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
SKILL_MD = SKILL_ROOT / "SKILL.md"
OPENAI_YAML = SKILL_ROOT / "agents" / "openai.yaml"


class SpecDrivenDevelopPromptContractTests(unittest.TestCase):
    def test_frontmatter_description_stays_trigger_focused(self) -> None:
        content = SKILL_MD.read_text(encoding="utf-8")

        match = re.search(
            r"^---\s+name:\s+spec-driven-develop\s+description:\s+(.+?)\s+---",
            content,
            re.DOTALL,
        )
        self.assertIsNotNone(match, "Could not locate SKILL.md frontmatter description")
        description = " ".join(match.group(1).split())

        self.assertTrue(description.startswith("Use when"))
        self.assertIn("rewrite", description.lower())
        self.assertIn("migration", description.lower())
        self.assertIn("docs/progress/MASTER.md", description)

        # Keep the description on triggering conditions, not workflow narration.
        forbidden_workflow_phrases = [
            "confirm the requested",
            "inspect the real project surface",
            "break the work into named phases",
            "create or refresh",
            "hand off",
        ]
        for phrase in forbidden_workflow_phrases:
            self.assertNotIn(phrase, description.lower())

    def test_openai_default_prompt_mentions_skill_and_pre_implementation_boundary(self) -> None:
        content = OPENAI_YAML.read_text(encoding="utf-8")

        self.assertIn('display_name: "Spec-Driven Develop"', content)
        self.assertIn('short_description: "Plan and track large transformation work"', content)
        self.assertIn("$spec-driven-develop", content)
        self.assertIn("progress documents", content.lower())
        self.assertRegex(content.lower(), r"before (coding|implementation)")


if __name__ == "__main__":
    unittest.main()

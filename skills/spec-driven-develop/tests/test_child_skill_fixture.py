from __future__ import annotations

import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
DOC_TEMPLATES = SKILL_ROOT / "references" / "doc-templates.md"
SAMPLE_SKILL = SKILL_ROOT / "assets" / "examples" / "sample-child-skill" / "SKILL.md"
SAMPLE_OPENAI = SKILL_ROOT / "assets" / "examples" / "sample-child-skill" / "agents" / "openai.yaml"


class SpecDrivenDevelopChildSkillFixtureTests(unittest.TestCase):
    def test_doc_templates_include_sub_skill_template_section(self) -> None:
        content = DOC_TEMPLATES.read_text(encoding="utf-8")

        self.assertIn("## Sub-Skill Template", content)
        self.assertIn("Cross-conversation continuity protocol", content)
        self.assertIn("Progress update instructions", content)
        self.assertIn("Parallel Execution Protocol", content)
        self.assertIn("cleanup trigger", content.lower())

    def test_sample_child_skill_fixture_exists_and_preserves_handoff_contract(self) -> None:
        self.assertTrue(SAMPLE_SKILL.exists(), msg=f"missing sample child skill: {SAMPLE_SKILL}")
        self.assertTrue(SAMPLE_OPENAI.exists(), msg=f"missing sample child metadata: {SAMPLE_OPENAI}")

        skill = SAMPLE_SKILL.read_text(encoding="utf-8")
        meta = SAMPLE_OPENAI.read_text(encoding="utf-8")

        self.assertIn("name: sample-migration-dev", skill)
        self.assertIn("description: Use when", skill)
        self.assertIn("docs/progress/MASTER.md", skill)
        self.assertIn("phase file", skill.lower())
        self.assertIn("main thread", skill.lower())
        self.assertIn("reconcile `MASTER.md`", skill)
        self.assertIn("cleanup", skill.lower())
        self.assertIn("Parallel Execution", skill)
        self.assertIn("$sample-migration-dev", meta)


if __name__ == "__main__":
    unittest.main()

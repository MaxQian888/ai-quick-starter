import unittest
from pathlib import Path


class SkillContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.skill_root = Path(__file__).resolve().parents[1]

    def test_module_exposes_expected_navigation_files(self) -> None:
        expected_paths = [
            self.skill_root / "SKILL.md",
            self.skill_root / "CLAUDE.md",
            self.skill_root / "agents" / "openai.yaml",
            self.skill_root / "references" / "workflow-phases.md",
            self.skill_root / "references" / "progress-tracking.md",
            self.skill_root / "references" / "sub-skill-generation.md",
            self.skill_root / "references" / "parallel-execution.md",
            self.skill_root / "references" / "doc-templates.md",
            self.skill_root / "scripts" / "bootstrap_progress_docs.py",
            self.skill_root / "scripts" / "export_progress.py",
        ]
        missing = [str(path) for path in expected_paths if not path.exists()]
        self.assertEqual(missing, [], f"Missing module files: {missing}")

    def test_claude_doc_has_expected_sections(self) -> None:
        claude_path = self.skill_root / "CLAUDE.md"
        content = claude_path.read_text(encoding="utf-8")

        self.assertIn("# CLAUDE.md", content)
        self.assertIn("## Purpose", content)
        self.assertIn("## Module Map", content)
        self.assertIn("## Entry Points", content)
        self.assertIn("## Main Interface", content)
        self.assertIn("## Output Contract", content)
        self.assertIn("## Important Constraints", content)
        self.assertIn("## Related Guides", content)


if __name__ == "__main__":
    unittest.main()

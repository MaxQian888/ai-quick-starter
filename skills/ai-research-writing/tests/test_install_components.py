from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = SKILL_ROOT / "scripts" / "install_components.py"
SPEC = importlib.util.spec_from_file_location("ai_research_writing_install", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class InstallComponentsTests(unittest.TestCase):
    def test_builds_plan_for_known_components(self) -> None:
        plan = MODULE.build_install_plan(["openskills", "humanizer", "docx"])

        self.assertEqual(plan["requested"], ["openskills", "humanizer", "docx"])
        self.assertGreaterEqual(len(plan["commands"]), 3)
        joined = "\n".join(plan["commands"])
        self.assertIn("npx openskills --version", joined)
        self.assertIn("blader/humanizer", joined)
        self.assertIn("anthropics/skills", joined)

    def test_all_expands_to_curated_component_set(self) -> None:
        plan = MODULE.build_install_plan(["all"])

        self.assertIn("20-ml-paper-writing", plan["resolved_components"])
        self.assertIn("canvas-design", plan["resolved_components"])
        self.assertIn("doc-coauthoring", plan["resolved_components"])
        self.assertIn("docx", plan["resolved_components"])
        self.assertIn("humanizer", plan["resolved_components"])

    def test_unknown_component_raises_clear_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown component"):
            MODULE.build_install_plan(["not-real"])


if __name__ == "__main__":
    unittest.main()

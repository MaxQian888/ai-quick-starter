import importlib.util
import sys
import unittest
from pathlib import Path


def load_module(module_name: str, relative_script_path: str):
    script_path = Path(__file__).resolve().parents[1] / relative_script_path
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


exporter = load_module("export_progress_fixture", "scripts/export_progress.py")

SKILL_ROOT = Path(__file__).resolve().parent.parent
PROGRESS_DIR = SKILL_ROOT / "assets" / "examples" / "sample-progress" / "docs" / "progress"
MASTER = PROGRESS_DIR / "MASTER.md"
PHASE_ONE = PROGRESS_DIR / "phase-1-project-analysis.md"
PHASE_TWO = PROGRESS_DIR / "phase-2-execution-prep.md"
CHILD_SKILL = SKILL_ROOT / "assets" / "examples" / "sample-child-skill" / "SKILL.md"


class ResumeFixtureTests(unittest.TestCase):
    def test_sample_progress_fixture_exists(self) -> None:
        for path in (MASTER, PHASE_ONE, PHASE_TWO):
            self.assertTrue(path.exists(), msg=f"missing sample progress fixture file: {path}")

    def test_exporter_parses_sample_progress_fixture(self) -> None:
        payload = exporter.export_progress(PROGRESS_DIR)

        self.assertEqual(payload["master"]["task_name"], "Sample Migration")
        self.assertEqual(payload["master"]["current_phase"], "Phase 2 - Execution Prep")
        self.assertEqual(payload["master"]["completed_tasks"], 2)
        self.assertEqual(payload["master"]["total_tasks"], 3)
        self.assertEqual(len(payload["phases"]), 2)
        self.assertEqual(payload["phases"][0]["tasks"][0]["id"], "T1.1")
        self.assertTrue(payload["phases"][0]["tasks"][0]["done"])
        self.assertEqual(payload["phases"][1]["tasks"][0]["id"], "T2.1")
        self.assertFalse(payload["phases"][1]["tasks"][0]["done"])

    def test_sample_child_skill_matches_resume_fixture_contract(self) -> None:
        skill = CHILD_SKILL.read_text(encoding="utf-8")
        phase_two = PHASE_TWO.read_text(encoding="utf-8")

        self.assertIn("Read `docs/progress/MASTER.md` first.", skill)
        self.assertIn("active phase", skill.lower())
        self.assertIn("phase file", skill.lower())
        self.assertIn("Execution Prep", phase_two)
        self.assertIn("T2.1", phase_two)


if __name__ == "__main__":
    unittest.main()

from pathlib import Path
import unittest

SKILL_ROOT = Path(__file__).resolve().parents[1]

class SkillContractTests(unittest.TestCase):
    def test_scripts_take_screenshot_ps1_exists(self) -> None:
        path = SKILL_ROOT / "scripts/take_screenshot.ps1"
        self.assertTrue(path.exists(), f"Missing required file: {path}")
        self.assertGreater(path.stat().st_size, 0, f"File is empty: {path}")

    def test_scripts_take_screenshot_py_exists(self) -> None:
        path = SKILL_ROOT / "scripts/take_screenshot.py"
        self.assertTrue(path.exists(), f"Missing required file: {path}")
        self.assertGreater(path.stat().st_size, 0, f"File is empty: {path}")


if __name__ == '__main__':
    unittest.main()

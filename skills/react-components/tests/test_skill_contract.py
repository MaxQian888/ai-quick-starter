from pathlib import Path
import unittest

SKILL_ROOT = Path(__file__).resolve().parents[1]

class SkillContractTests(unittest.TestCase):
    def test_scripts_fetch_stitch_sh_exists(self) -> None:
        path = SKILL_ROOT / "scripts/fetch-stitch.sh"
        self.assertTrue(path.exists(), f"Missing required file: {path}")
        self.assertGreater(path.stat().st_size, 0, f"File is empty: {path}")

    def test_scripts_fetch_stitch_ps1_exists(self) -> None:
        path = SKILL_ROOT / "scripts/fetch-stitch.ps1"
        self.assertTrue(path.exists(), f"Missing required file: {path}")
        self.assertGreater(path.stat().st_size, 0, f"File is empty: {path}")

    def test_scripts_fetch_stitch_py_exists(self) -> None:
        path = SKILL_ROOT / "scripts/fetch-stitch.py"
        self.assertTrue(path.exists(), f"Missing required file: {path}")
        self.assertGreater(path.stat().st_size, 0, f"File is empty: {path}")

    def test_scripts_validate_js_exists(self) -> None:
        path = SKILL_ROOT / "scripts/validate.js"
        self.assertTrue(path.exists(), f"Missing required file: {path}")
        self.assertGreater(path.stat().st_size, 0, f"File is empty: {path}")


if __name__ == '__main__':
    unittest.main()

from pathlib import Path
import unittest

SKILL_ROOT = Path(__file__).resolve().parents[1]

class SkillContractTests(unittest.TestCase):
    def test_scripts_download_stitch_asset_sh_exists(self) -> None:
        path = SKILL_ROOT / "scripts/download-stitch-asset.sh"
        self.assertTrue(path.exists(), f"Missing required file: {path}")
        self.assertGreater(path.stat().st_size, 0, f"File is empty: {path}")

    def test_scripts_download_stitch_asset_ps1_exists(self) -> None:
        path = SKILL_ROOT / "scripts/download-stitch-asset.ps1"
        self.assertTrue(path.exists(), f"Missing required file: {path}")
        self.assertGreater(path.stat().st_size, 0, f"File is empty: {path}")

    def test_scripts_download_stitch_asset_py_exists(self) -> None:
        path = SKILL_ROOT / "scripts/download-stitch-asset.py"
        self.assertTrue(path.exists(), f"Missing required file: {path}")
        self.assertGreater(path.stat().st_size, 0, f"File is empty: {path}")


if __name__ == '__main__':
    unittest.main()

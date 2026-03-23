import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "scan_project_context.py"
SPEC = importlib.util.spec_from_file_location("scan_project_context", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ScanProjectContextTests(unittest.TestCase):
    def test_skip_directory_heuristics(self) -> None:
        self.assertTrue(MODULE.should_skip_directory("node_modules"))
        self.assertTrue(MODULE.should_skip_directory(".tmp-cache"))
        self.assertFalse(MODULE.should_skip_directory("agents-team-builder"))

    def test_build_report_detects_skill_and_skips_temp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            skill = root / "example-skill"
            skill.mkdir()
            (skill / "SKILL.md").write_text("---\nname: example-skill\ndescription: test\n---\n")
            (skill / "agents").mkdir()
            (skill / "agents" / "openai.yaml").write_text("interface:\n")
            (root / "_tmp_validate").mkdir()

            report = MODULE.build_report(root, max_modules=5)

            module_names = [item["name"] for item in report["suggested_modules"]]
            skipped_names = [item["name"] for item in report["skipped_directories"]]

            self.assertIn("docs", module_names)
            self.assertIn("example-skill", module_names)
            self.assertIn("_tmp_validate", skipped_names)

    def test_cli_writes_json_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            output = root / "out" / "report.json"

            subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--root", str(root), "--json-out", str(output)],
                check=True,
            )

            loaded = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(loaded["total_top_level_directories"], 1)
            self.assertEqual(loaded["total_top_level_files"], 0)


if __name__ == "__main__":
    unittest.main()


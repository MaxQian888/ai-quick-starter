import importlib.util
import json
import shutil
import sys
import tempfile
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


bootstrap = load_module("bootstrap_progress_docs", "scripts/bootstrap_progress_docs.py")
exporter = load_module("export_progress", "scripts/export_progress.py")


class ExportProgressTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="spec-driven-export-"))
        phase_file = self.tmpdir / "phases.json"
        phase_file.write_text(
            json.dumps(
                {
                    "phases": [
                        {
                            "name": "Project Analysis",
                            "tasks": [
                                "Inventory entrypoints",
                                {"text": "Record migration risks", "priority": "P0"},
                            ],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        bootstrap.create_progress_docs(
            output_root=self.tmpdir,
            task_name="Rewrite",
            task_summary="Plan the migration.",
            phase_file=phase_file,
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir)

    def test_exports_generated_progress_docs(self) -> None:
        progress_dir = self.tmpdir / "docs" / "progress"
        phase_path = progress_dir / "phase-1-project-analysis.md"
        phase_text = phase_path.read_text(encoding="utf-8").replace(
            "- [ ] T1.1 [P1] Inventory entrypoints",
            "- [x] T1.1 [P1] Inventory entrypoints",
        )
        phase_path.write_text(phase_text, encoding="utf-8")

        payload = exporter.export_progress(progress_dir)

        self.assertEqual(payload["master"]["task_name"], "Rewrite")
        self.assertEqual(len(payload["phases"]), 1)
        self.assertEqual(payload["phases"][0]["tasks"][0]["id"], "T1.1")
        self.assertTrue(payload["phases"][0]["tasks"][0]["done"])
        self.assertEqual(payload["phases"][0]["tasks"][1]["priority"], "P0")

    def test_parse_master_requires_expected_header(self) -> None:
        with self.assertRaises(ValueError):
            exporter.parse_master("## Not a valid master file")


if __name__ == "__main__":
    unittest.main()

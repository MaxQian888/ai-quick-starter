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


class BootstrapProgressDocsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="spec-driven-bootstrap-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir)

    def write_phase_file(self, payload: dict) -> Path:
        phase_path = self.tmpdir / "phases.json"
        phase_path.write_text(json.dumps(payload), encoding="utf-8")
        return phase_path

    def test_creates_master_and_phase_files_from_json(self) -> None:
        phase_file = self.write_phase_file(
            {
                "phases": [
                    {
                        "name": "Project Analysis",
                        "summary": "Map the current state.",
                        "tasks": [
                            "Inventory entrypoints",
                            {"text": "Record migration risks", "priority": "P0"},
                        ],
                    },
                    {
                        "name": "Execution Prep",
                        "tasks": ["Create execution skill"],
                        "verification": "Progress docs and child skill path reviewed",
                    },
                ]
            }
        )

        result = bootstrap.create_progress_docs(
            output_root=self.tmpdir,
            task_name="Rust Migration",
            task_summary="Prepare the rewrite before coding.",
            phase_file=phase_file,
        )

        master_path = Path(result["master_path"])
        phase_one = self.tmpdir / "docs" / "progress" / "phase-1-project-analysis.md"
        self.assertTrue(master_path.exists())
        self.assertTrue(phase_one.exists())

        master_text = master_path.read_text(encoding="utf-8")
        phase_text = phase_one.read_text(encoding="utf-8")
        self.assertIn("# Rust Migration — Progress Tracker", master_text)
        self.assertIn("Phase 1: Project Analysis (0/2 tasks)", master_text)
        self.assertIn("- [ ] T1.1 [P1] Inventory entrypoints", phase_text)
        self.assertIn("- [ ] T1.2 [P0] Record migration risks", phase_text)

    def test_refuses_to_overwrite_without_flag(self) -> None:
        phase_file = self.write_phase_file(
            {"phases": [{"name": "Phase One", "tasks": ["Task A"]}]}
        )

        bootstrap.create_progress_docs(
            output_root=self.tmpdir,
            task_name="Initial Task",
            task_summary="Bootstrap once.",
            phase_file=phase_file,
        )

        with self.assertRaises(FileExistsError):
            bootstrap.create_progress_docs(
                output_root=self.tmpdir,
                task_name="Initial Task",
                task_summary="Bootstrap twice.",
                phase_file=phase_file,
            )


if __name__ == "__main__":
    unittest.main()

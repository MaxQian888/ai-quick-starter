import importlib.util
import re
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


bootstrap = load_module("bootstrap_round_trip", "scripts/bootstrap_progress_docs.py")

SKILL_ROOT = Path(__file__).resolve().parent.parent
ROUND_TRIP_ROOT = SKILL_ROOT / "assets" / "examples" / "sample-bootstrap"
PHASES_JSON = ROUND_TRIP_ROOT / "phases.json"
FIXTURE_PROGRESS = ROUND_TRIP_ROOT / "docs" / "progress"


def normalize_generated_text(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"\[\d{4}-\d{2}-\d{2}\] Progress docs initialized\.", "[DATE] <INIT>", text)
    return text.strip()


class RoundTripFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="spec-driven-roundtrip-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir)

    def test_round_trip_fixture_files_exist(self) -> None:
        expected = [
            PHASES_JSON,
            FIXTURE_PROGRESS / "MASTER.md",
            FIXTURE_PROGRESS / "phase-1-project-analysis.md",
            FIXTURE_PROGRESS / "phase-2-execution-prep.md",
        ]
        for path in expected:
            self.assertTrue(path.exists(), msg=f"missing round-trip fixture file: {path}")

    def test_bootstrap_output_matches_checked_in_round_trip_fixture(self) -> None:
        result = bootstrap.create_progress_docs(
            output_root=self.tmpdir,
            task_name="Sample Migration",
            task_summary="Create initial progress docs for the sample migration.",
            phase_file=PHASES_JSON,
        )

        generated_master = Path(result["master_path"]).read_text(encoding="utf-8")
        fixture_master = (FIXTURE_PROGRESS / "MASTER.md").read_text(encoding="utf-8")
        self.assertEqual(normalize_generated_text(generated_master), normalize_generated_text(fixture_master))

        for filename in ("phase-1-project-analysis.md", "phase-2-execution-prep.md"):
            generated = (self.tmpdir / "docs" / "progress" / filename).read_text(encoding="utf-8")
            fixture = (FIXTURE_PROGRESS / filename).read_text(encoding="utf-8")
            self.assertEqual(normalize_generated_text(generated), normalize_generated_text(fixture))


if __name__ == "__main__":
    unittest.main()

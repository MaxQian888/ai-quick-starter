import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_coverage_threshold.py"
SPEC = importlib.util.spec_from_file_location("check_coverage_threshold", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class CheckCoverageThresholdTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="coverage-threshold-"))
        self.addCleanup(lambda: shutil.rmtree(self.temp_dir, ignore_errors=True))

    def write_summary(self, payload: dict) -> Path:
        coverage_dir = self.temp_dir / "coverage"
        coverage_dir.mkdir(parents=True, exist_ok=True)
        path = coverage_dir / "coverage-summary.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_parse_summary_json_extracts_metric_percentages(self) -> None:
        path = self.write_summary(
            {
                "total": {
                    "lines": {"pct": 91},
                    "statements": {"pct": 90},
                    "functions": {"pct": 89},
                    "branches": {"pct": 88},
                }
            }
        )

        metrics = MODULE.parse_summary_json(path)

        self.assertEqual(metrics["lines"], 91.0)
        self.assertEqual(metrics["branches"], 88.0)

    def test_parse_summary_json_accepts_string_pct(self) -> None:
        path = self.write_summary(
            {"total": {"lines": {"pct": "91.5"}, "branches": {"pct": "ignored-bad"}}}
        )
        metrics = MODULE.parse_summary_json(path)
        self.assertEqual(metrics["lines"], 91.5)
        self.assertNotIn("branches", metrics)

    def test_parse_lcov_aggregates_across_files(self) -> None:
        lcov_path = self.temp_dir / "coverage" / "lcov.info"
        lcov_path.parent.mkdir(parents=True, exist_ok=True)
        lcov_path.write_text(
            textwrap.dedent(
                """\
                SF:src/a.ts
                LF:10
                LH:9
                FNF:2
                FNH:1
                BRF:4
                BRH:3
                end_of_record
                SF:src/b.ts
                LF:10
                LH:8
                FNF:2
                FNH:2
                BRF:0
                BRH:0
                end_of_record
                """
            ),
            encoding="utf-8",
        )
        metrics = MODULE.parse_lcov(lcov_path)
        self.assertAlmostEqual(metrics["lines"], 85.0)
        self.assertAlmostEqual(metrics["functions"], 75.0)
        self.assertAlmostEqual(metrics["branches"], 75.0)

    def test_cli_fails_when_metric_is_below_threshold(self) -> None:
        self.write_summary(
            {
                "total": {
                    "lines": {"pct": 92},
                    "statements": {"pct": 91},
                    "functions": {"pct": 70},
                    "branches": {"pct": 85},
                }
            }
        )

        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--root",
                str(self.temp_dir),
                "--threshold",
                "80",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 1)
        self.assertIn("below_threshold: functions=70.00%", completed.stdout)

    def test_per_file_offenders_lists_failing_files(self) -> None:
        summary_path = self.write_summary(
            {
                "total": {
                    "lines": {"pct": 95},
                    "branches": {"pct": 60},
                    "functions": {"pct": 90},
                    "statements": {"pct": 95},
                },
                "src/clean.ts": {
                    "branches": {"pct": 95},
                },
                "src/messy.ts": {
                    "branches": {"pct": 40},
                },
                "src/awful.ts": {
                    "branches": {"pct": 10},
                },
            }
        )

        offenders = MODULE.find_per_file_offenders(
            summary_path, threshold=80, metrics=["branches"], limit=10
        )

        # Worst-first ordering, only files actually below threshold.
        self.assertEqual(
            offenders,
            [
                ("src/awful.ts", "branches", 10.0),
                ("src/messy.ts", "branches", 40.0),
            ],
        )

    def test_cli_per_file_flag_prints_offenders(self) -> None:
        self.write_summary(
            {
                "total": {
                    "lines": {"pct": 95},
                    "branches": {"pct": 60},
                    "functions": {"pct": 90},
                    "statements": {"pct": 95},
                },
                "src/messy.ts": {"branches": {"pct": 40}},
            }
        )

        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--root",
                str(self.temp_dir),
                "--threshold",
                "80",
                "--per-file",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 1)
        self.assertIn("per_file_offenders", completed.stdout)
        self.assertIn("src/messy.ts: branches=40.00%", completed.stdout)


if __name__ == "__main__":
    unittest.main()

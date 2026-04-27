import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_ROOT / "scripts" / "build-vega-lite-stub.js"


class BuildVegaLiteStubTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="vega-lite-stub-"))
        self.addCleanup(lambda: shutil.rmtree(self.temp_dir, ignore_errors=True))

    def test_builds_stub_spec_from_config(self) -> None:
        config_path = self.temp_dir / "config.json"
        output_path = self.temp_dir / "spec.json"
        config_path.write_text(
            json.dumps(
                {
                    "title": "Quarterly Revenue",
                    "mark": "bar",
                    "data": {"url": "data.csv"},
                    "encoding": {
                        "x": {"field": "quarter", "type": "ordinal"},
                        "y": {"field": "revenue", "type": "quantitative"},
                    },
                }
            ),
            encoding="utf-8",
        )

        result = subprocess.run(
            ["node", str(SCRIPT_PATH), "--config", str(config_path), "--out", str(output_path)],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(output_path.exists())
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["mark"], "bar")
        self.assertEqual(payload["encoding"]["x"]["field"], "quarter")
        self.assertEqual(payload["encoding"]["y"]["field"], "revenue")

    def test_writes_spec_to_stdout_when_out_is_omitted(self) -> None:
        config_path = self.temp_dir / "stdout-config.json"
        config_path.write_text(
            json.dumps(
                {
                    "title": "Traffic Source Breakdown",
                    "mark": "arc",
                    "data": {"url": "traffic.csv"},
                    "encoding": {
                        "theta": {"field": "visits", "type": "quantitative"},
                        "color": {"field": "source", "type": "nominal"},
                    },
                    "transform": [{"filter": "datum.visits > 0"}],
                }
            ),
            encoding="utf-8",
        )

        result = subprocess.run(
            ["node", str(SCRIPT_PATH), "--config", str(config_path)],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["mark"], "arc")
        self.assertEqual(payload["transform"][0]["filter"], "datum.visits > 0")
        self.assertEqual(payload["encoding"]["color"]["field"], "source")

    def test_invalid_config_returns_non_zero_and_usage(self) -> None:
        config_path = self.temp_dir / "bad-config.json"
        config_path.write_text(json.dumps(["not-an-object"]), encoding="utf-8")

        result = subprocess.run(
            ["node", str(SCRIPT_PATH), "--config", str(config_path)],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Config root must be a JSON object.", result.stderr)
        self.assertIn("Usage:", result.stderr)

    def test_preserves_inline_data_values_arrays(self) -> None:
        config_path = self.temp_dir / "inline-values.json"
        config_path.write_text(
            json.dumps(
                {
                    "mark": "line",
                    "data": {
                        "values": [
                            {"day": "Mon", "visits": 12},
                            {"day": "Tue", "visits": 18},
                        ]
                    },
                    "encoding": {
                        "x": {"field": "day", "type": "ordinal"},
                        "y": {"field": "visits", "type": "quantitative"},
                    },
                }
            ),
            encoding="utf-8",
        )

        result = subprocess.run(
            ["node", str(SCRIPT_PATH), "--config", str(config_path)],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["data"]["values"][0]["day"], "Mon")
        self.assertEqual(payload["data"]["values"][1]["visits"], 18)


if __name__ == "__main__":
    unittest.main()

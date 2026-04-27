from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "audit_logging_surface.py"
MODULE_SPEC = importlib.util.spec_from_file_location("audit_logging_surface", SCRIPT)
MODULE = importlib.util.module_from_spec(MODULE_SPEC)
assert MODULE_SPEC and MODULE_SPEC.loader
sys.modules[MODULE_SPEC.name] = MODULE
MODULE_SPEC.loader.exec_module(MODULE)


class AuditLoggingSurfaceTests(unittest.TestCase):
    def make_tree(self, files: dict[str, str]) -> Path:
        root = Path(tempfile.mkdtemp(prefix="guarded-log-editor-"))
        for relative_path, content in files.items():
            file_path = root / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")
        return root

    def test_detects_pino_and_level_counts(self) -> None:
        root = self.make_tree(
            {
                "src/service.ts": """
                    import pino from "pino";

                    const logger = pino();

                    export function runTask(taskId: string) {
                      logger.info({ taskId }, "task started");
                      logger.debug({ taskId }, "task detail");
                      logger.error({ taskId }, "task failed");
                    }
                """,
            }
        )

        payload = MODULE.analyze_target(root, root / "src")

        self.assertEqual(payload["selected_system"]["name"], "pino")
        self.assertEqual(payload["summary"]["level_totals"]["info"], 1)
        self.assertEqual(payload["summary"]["level_totals"]["debug"], 1)
        self.assertEqual(payload["summary"]["level_totals"]["error"], 1)
        self.assertEqual(payload["file_findings"][0]["call_count"], 3)
        self.assertEqual(payload["safe_fix_plan"][0]["operation"], "edit-existing-logs")

    def test_detects_python_logging_and_warn_error_levels(self) -> None:
        root = self.make_tree(
            {
                "worker/job.py": """
                    import logging

                    logger = logging.getLogger(__name__)

                    def run(job_id: str) -> None:
                        logger.warning("job delayed: %s", job_id)
                        try:
                            raise RuntimeError("boom")
                        except RuntimeError:
                            logger.exception("job failed: %s", job_id)
                """,
            }
        )

        payload = MODULE.analyze_target(root, root / "worker")

        self.assertEqual(payload["selected_system"]["name"], "python-logging")
        self.assertEqual(payload["summary"]["level_totals"]["warn"], 1)
        self.assertEqual(payload["summary"]["level_totals"]["error"], 1)

    def test_flags_high_density_info_heavy_files(self) -> None:
        root = self.make_tree(
            {
                "feature/handler.ts": """
                    import { logger } from "@/lib/logger";

                    export function handle(id: string) {
                      logger.info({ id }, "start");
                      logger.info({ id }, "step 1");
                      logger.info({ id }, "step 2");
                      logger.info({ id }, "step 3");
                      logger.info({ id }, "step 4");
                      logger.info({ id }, "step 5");
                      logger.info({ id }, "step 6");
                      logger.info({ id }, "step 7");
                    }
                """,
            }
        )

        payload = MODULE.analyze_target(root, root / "feature")
        file_payload = payload["file_findings"][0]

        self.assertEqual(payload["selected_system"]["name"], "custom-wrapper")
        self.assertIn("high-density", file_payload["needs_review"])
        self.assertIn("info-heavy", file_payload["needs_review"])
        self.assertIn(
            "Do not add more info/debug logs to high-density files before removing duplicates.",
            payload["forbidden_actions"],
        )

    def test_marks_unknown_scope_low_confidence(self) -> None:
        root = self.make_tree(
            {
                "pkg/helper.ts": """
                    export function pickLabel(value: string) {
                      return value.trim();
                    }
                """,
            }
        )

        payload = MODULE.analyze_target(root, root / "pkg")

        self.assertEqual(payload["selected_system"]["confidence"], "low")
        self.assertEqual(payload["file_findings"][0]["status"], "no-logs")
        self.assertFalse(payload["safe_fix_plan"])
        self.assertIn(
            "Do not add new logs until the shared logger entrypoint or adjacent files are inspected manually.",
            payload["forbidden_actions"],
        )

    def test_cli_json_output(self) -> None:
        root = self.make_tree(
            {
                "pkg/main.go": """
                    package pkg

                    import "log/slog"

                    func Run(id string) {
                        slog.Info("running", "id", id)
                    }
                """,
            }
        )

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--root",
                str(root),
                "--target",
                str(root / "pkg"),
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["selected_system"]["name"], "go-slog")
        self.assertEqual(payload["summary"]["level_totals"]["info"], 1)


if __name__ == "__main__":
    unittest.main()

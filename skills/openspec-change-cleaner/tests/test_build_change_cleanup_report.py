from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


def load_module(module_name: str, relative_script_path: str):
    script_path = Path(__file__).resolve().parents[1] / relative_script_path
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


cleanup_report = load_module("openspec_change_cleanup_report", "scripts/build_change_cleanup_report.py")


class FakeCli:
    def __init__(
        self,
        *,
        changes: list[dict[str, object]],
        show_map: dict[str, dict[str, object]],
        status_map: dict[str, dict[str, object]],
        validate_map: dict[str, dict[str, object]],
    ) -> None:
        self._changes = changes
        self._show_map = show_map
        self._status_map = status_map
        self._validate_map = validate_map

    def list_changes(self) -> list[dict[str, object]]:
        return self._changes

    def show_change(self, change_name: str) -> dict[str, object]:
        return self._show_map[change_name]

    def status(self, change_name: str) -> dict[str, object]:
        return self._status_map[change_name]

    def validate(self, change_name: str) -> dict[str, object]:
        return self._validate_map[change_name]


class BuildChangeCleanupReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="openspec-change-cleaner-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir)

    def make_file(self, relative_path: str, content: str) -> None:
        file_path = self.tmpdir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

    def test_active_change_without_deltas_is_flagged_for_artifact_repair(self) -> None:
        self.make_file("openspec/changes/stale-change/proposal.md", "## Why\n\nNeed a fix.\n")

        cli = FakeCli(
            changes=[
                {
                    "name": "stale-change",
                    "completedTasks": 0,
                    "totalTasks": 0,
                    "status": "no-tasks",
                    "lastModified": "2026-04-01T00:00:00.000Z",
                }
            ],
            show_map={"stale-change": {"id": "stale-change", "deltaCount": 0, "deltas": []}},
            status_map={
                "stale-change": {
                    "changeName": "stale-change",
                    "isComplete": False,
                    "applyRequires": ["tasks"],
                    "artifacts": [
                        {"id": "proposal", "status": "done"},
                        {"id": "design", "status": "ready"},
                        {"id": "specs", "status": "ready"},
                        {"id": "tasks", "status": "blocked", "missingDeps": ["design", "specs"]},
                    ],
                }
            },
            validate_map={
                "stale-change": {
                    "items": [
                        {
                            "id": "stale-change",
                            "type": "change",
                            "valid": False,
                            "issues": [
                                {
                                    "level": "ERROR",
                                    "message": "Change must have at least one delta.",
                                }
                            ],
                        }
                    ]
                }
            },
        )

        report = cleanup_report.build_cleanup_report(
            repo_root=self.tmpdir,
            cli=cli,
            include_archive=False,
        )

        self.assertEqual(report["active_changes"][0]["assessment"]["classification"], "repair-artifacts")
        reasons = "\n".join(report["active_changes"][0]["assessment"]["reasons"])
        self.assertIn("delta", reasons.lower())
        self.assertIn("validation", reasons.lower())
        self.assertIn("stale-change", report["summary"]["repair_candidates"])

    def test_completed_change_is_ready_for_verify_or_archive(self) -> None:
        self.make_file(
            "openspec/changes/ready-change/tasks.md",
            "- [x] Confirm spec updates\n- [x] Verify implementation\n",
        )

        cli = FakeCli(
            changes=[
                {
                    "name": "ready-change",
                    "completedTasks": 2,
                    "totalTasks": 2,
                    "status": "complete",
                    "lastModified": "2026-04-01T00:00:00.000Z",
                }
            ],
            show_map={
                "ready-change": {
                    "id": "ready-change",
                    "deltaCount": 1,
                    "deltas": [{"spec": "cleanup", "type": "MODIFIED"}],
                }
            },
            status_map={
                "ready-change": {
                    "changeName": "ready-change",
                    "isComplete": True,
                    "applyRequires": [],
                    "artifacts": [
                        {"id": "proposal", "status": "done"},
                        {"id": "design", "status": "done"},
                        {"id": "specs", "status": "done"},
                        {"id": "tasks", "status": "done"},
                    ],
                }
            },
            validate_map={
                "ready-change": {
                    "items": [{"id": "ready-change", "type": "change", "valid": True, "issues": []}]
                }
            },
        )

        report = cleanup_report.build_cleanup_report(
            repo_root=self.tmpdir,
            cli=cli,
            include_archive=False,
        )

        self.assertEqual(
            report["active_changes"][0]["assessment"]["classification"],
            "ready-for-verify-or-archive",
        )
        self.assertIn("ready-change", report["summary"]["ready_candidates"])

    def test_archive_placeholder_folder_becomes_safe_cleanup_candidate(self) -> None:
        self.make_file(
            "openspec/changes/archive/empty-archive/proposal.md",
            "# Placeholder\n\nTODO: replace me.\n",
        )
        self.make_file(
            "openspec/changes/archive/empty-archive/.openspec.yaml",
            "schema: spec-driven\n",
        )

        cli = FakeCli(changes=[], show_map={}, status_map={}, validate_map={})

        report = cleanup_report.build_cleanup_report(
            repo_root=self.tmpdir,
            cli=cli,
            include_archive=True,
        )

        self.assertEqual(len(report["archive_changes"]), 1)
        archive_entry = report["archive_changes"][0]
        self.assertEqual(archive_entry["assessment"]["classification"], "safe-cleanup-candidate")
        self.assertIn("empty-archive", report["summary"]["safe_cleanup_candidates"])

    def test_markdown_renderer_mentions_active_and_archive_sections(self) -> None:
        report = {
            "repo_root": str(self.tmpdir),
            "active_changes": [
                {
                    "name": "demo-change",
                    "assessment": {
                        "classification": "repair-artifacts",
                        "reasons": ["No deltas were found."],
                    },
                    "task_file": {"total": 0, "completed": 0},
                }
            ],
            "archive_changes": [
                {
                    "name": "old-change",
                    "assessment": {
                        "classification": "safe-cleanup-candidate",
                        "reasons": ["Only placeholder content remains."],
                    }
                }
            ],
            "summary": {
                "repair_candidates": ["demo-change"],
                "ready_candidates": [],
                "safe_cleanup_candidates": ["old-change"],
            },
        }

        markdown = cleanup_report.render_markdown(report)

        self.assertIn("## Active Changes", markdown)
        self.assertIn("## Archive Review", markdown)
        self.assertIn("demo-change", markdown)
        self.assertIn("old-change", markdown)

    @patch("openspec_change_cleanup_report.shutil.which")
    def test_resolves_full_openspec_shim_path_before_subprocess(self, which_mock) -> None:
        which_mock.side_effect = lambda name: {
            "openspec": r"C:\Users\qwdma\AppData\Roaming\npm\openspec.cmd",
        }.get(name)

        resolved = cleanup_report.resolve_executable_path("openspec")

        self.assertEqual(resolved, r"C:\Users\qwdma\AppData\Roaming\npm\openspec.cmd")


if __name__ == "__main__":
    unittest.main()

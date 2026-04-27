from __future__ import annotations

import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW_REF = SKILL_ROOT / "references" / "current-workflow.md"
CLEANUP_REF = SKILL_ROOT / "references" / "cleanup-rules.md"
REFRESH_REF = SKILL_ROOT / "references" / "artifact-refresh.md"


class OpenSpecChangeCleanerReferenceContractTests(unittest.TestCase):
    def test_workflow_reference_covers_current_cli_surface(self) -> None:
        workflow = WORKFLOW_REF.read_text(encoding="utf-8")

        self.assertIn("OpenSpec 1.2.0", workflow)
        self.assertIn("openspec list --json", workflow)
        self.assertIn("openspec show", workflow)
        self.assertIn("openspec status --change", workflow)
        self.assertIn("openspec archive", workflow)

    def test_cleanup_rules_stay_conservative_about_archive_history(self) -> None:
        cleanup = CLEANUP_REF.read_text(encoding="utf-8")

        self.assertIn("safe-cleanup-candidate", cleanup)
        self.assertIn("keep-history", cleanup)
        self.assertIn("Never delete archive history on the first pass", cleanup)
        self.assertIn("placeholder", cleanup.lower())

    def test_artifact_refresh_reference_covers_task_and_validation_loop(self) -> None:
        refresh = REFRESH_REF.read_text(encoding="utf-8")

        self.assertIn("proposal.md", refresh)
        self.assertIn("design.md", refresh)
        self.assertIn("tasks.md", refresh)
        self.assertIn("openspec validate", refresh)
        self.assertIn("latest implementation", refresh.lower())
        self.assertIn("reconcile_change_artifacts.py", refresh)
        self.assertIn("archive", refresh.lower())


if __name__ == "__main__":
    unittest.main()

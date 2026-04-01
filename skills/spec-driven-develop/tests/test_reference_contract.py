from __future__ import annotations

import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW_REF = SKILL_ROOT / "references" / "workflow-phases.md"
PROGRESS_REF = SKILL_ROOT / "references" / "progress-tracking.md"
SUB_SKILL_REF = SKILL_ROOT / "references" / "sub-skill-generation.md"
PARALLEL_REF = SKILL_ROOT / "references" / "parallel-execution.md"


class SpecDrivenDevelopReferenceContractTests(unittest.TestCase):
    def test_workflow_and_progress_refs_cover_native_task_mirroring(self) -> None:
        workflow = WORKFLOW_REF.read_text(encoding="utf-8")
        progress = PROGRESS_REF.read_text(encoding="utf-8")

        self.assertIn("TodoWrite", workflow)
        self.assertIn("native task", workflow.lower())
        self.assertIn("P0=high", workflow)
        self.assertIn("P1=medium", workflow)
        self.assertIn("P2=low", workflow)
        self.assertIn("If no native task tool is available", workflow)

        self.assertIn("native task tools", progress.lower())
        self.assertIn("in-session visibility", progress.lower())
        self.assertIn("source of truth", progress.lower())
        self.assertIn("P0", progress)
        self.assertIn("P1", progress)
        self.assertIn("P2", progress)

    def test_sub_skill_and_parallel_refs_preserve_execution_boundaries(self) -> None:
        sub_skill = SUB_SKILL_REF.read_text(encoding="utf-8")
        parallel = PARALLEL_REF.read_text(encoding="utf-8")

        self.assertIn("read `docs/progress/MASTER.md` first", sub_skill)
        self.assertIn("verification boundaries", sub_skill.lower())
        self.assertIn("cleanup trigger", sub_skill.lower())
        self.assertIn("generic", sub_skill.lower())

        self.assertIn("write scopes", parallel.lower())
        self.assertIn("merge point", parallel.lower())
        self.assertIn("main thread", parallel.lower())
        self.assertIn("MASTER.md", parallel)


if __name__ == "__main__":
    unittest.main()

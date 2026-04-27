from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = SKILL_ROOT / "scripts" / "select_workflow.py"
SPEC = importlib.util.spec_from_file_location("ai_research_writing_select", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class SelectWorkflowTests(unittest.TestCase):
    def test_routes_cn_to_en_latex_request(self) -> None:
        result = MODULE.select_workflow("请把下面中文草稿翻译成英文论文段落，并保留 LaTeX 公式。")

        self.assertEqual(result["workflow_id"], "cn-to-en")
        self.assertEqual(result["category"], "prompt")
        self.assertIn("中转英", result["matched_sections"])
        self.assertIn("references/cache/upstream-section-index.json", result["references"])

    def test_routes_reviewer_style_request(self) -> None:
        result = MODULE.select_workflow("请从 reviewer 视角审视这篇论文，找出致命问题。")

        self.assertEqual(result["workflow_id"], "reviewer-audit")
        self.assertIn("20-ml-paper-writing", result["related_components"])
        self.assertIn("论文整体以 Reviewer 视角进行审视", result["matched_sections"])

    def test_routes_component_setup_request(self) -> None:
        result = MODULE.select_workflow("帮我装好 openskills、humanizer、docx 这些论文写作组件。")

        self.assertEqual(result["workflow_id"], "skills-setup")
        self.assertEqual(result["category"], "installation")
        self.assertIn("openskills", result["related_components"])
        self.assertIn("humanizer", result["related_components"])
        self.assertIn("docx", result["related_components"])

    def test_falls_back_to_general_writing_route(self) -> None:
        result = MODULE.select_workflow("帮我处理一个论文写作任务，但我还没确定具体是润色还是审稿。")

        self.assertEqual(result["workflow_id"], "general-academic-writing")
        self.assertTrue(result["matched_sections"])


if __name__ == "__main__":
    unittest.main()

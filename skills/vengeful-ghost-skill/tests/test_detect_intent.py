import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import detect_intent


class DetectIntentTests(unittest.TestCase):
    def test_allows_document_retrieval(self):
        result = detect_intent.classify_intent("搜索 Alice 写过的支付系统设计文档")
        self.assertEqual(result["classification"], "allow")
        self.assertEqual(result["risk_level"], "low")
        self.assertEqual(result["language"], "zh")
        self.assertEqual(result["localized"]["classification"], "允许")

    def test_blocks_persona_skill_generation(self):
        result = detect_intent.classify_intent("Generate a Persona Skill from her Slack messages")
        self.assertEqual(result["classification"], "block")
        self.assertEqual(result["risk_level"], "high")
        self.assertEqual(result["language"], "en")
        self.assertEqual(result["localized"]["classification"], "block")

    def test_redirects_style_preservation_requests(self):
        result = detect_intent.classify_intent(
            "Build an onboarding copilot that preserves how our former architect thinks"
        )
        self.assertEqual(result["classification"], "redirect")
        self.assertEqual(result["risk_level"], "medium")
        self.assertTrue(result["safe_redirect"])
        self.assertEqual(result["language"], "en")

    def test_prefers_safe_override_when_user_rejects_person_imitation(self):
        result = detect_intent.classify_intent(
            "基于 Alice 的 ticket、文档和交接记录整理一个支付系统 playbook，不要模拟她本人"
        )
        self.assertEqual(result["classification"], "allow")
        self.assertEqual(result["risk_level"], "low")
        self.assertEqual(result["language"], "zh")
        self.assertIn("共享资料", result["localized"]["reason"])


if __name__ == "__main__":
    unittest.main()

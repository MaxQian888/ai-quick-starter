from __future__ import annotations

import re
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent


def read_text(relative_path: str) -> str:
    return (SKILL_ROOT / relative_path).read_text(encoding="utf-8")


class WaveOrchestrationSkillTests(unittest.TestCase):
    def test_required_files_exist(self) -> None:
        required_paths = [
            SKILL_ROOT / "SKILL.md",
            SKILL_ROOT / "references" / "patterns.md",
            SKILL_ROOT / "references" / "codex-adaptation.md",
            SKILL_ROOT / "agents" / "openai.yaml",
        ]

        for path in required_paths:
            self.assertTrue(path.exists(), msg=f"missing required skill file: {path}")

    def test_frontmatter_uses_supported_fields(self) -> None:
        content = read_text("SKILL.md")
        match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        self.assertIsNotNone(match, msg="SKILL.md frontmatter is missing")

        keys = []
        for line in match.group(1).splitlines():
            if ":" not in line:
                continue
            key = line.split(":", 1)[0].strip()
            if key:
                keys.append(key)

        self.assertEqual(keys, ["name", "description"])
        self.assertIn("name: wave-orchestration", match.group(1))

    def test_skill_mentions_codex_dispatch_rules(self) -> None:
        content = read_text("SKILL.md")
        self.assertIn("spawn_agent", content)
        self.assertIn("multi_tool_use.parallel", content)
        self.assertIn("close_agent", content)

        codex_notes = read_text("references/codex-adaptation.md")
        self.assertIn("send_input", codex_notes)
        self.assertIn("wait_agent", codex_notes)
        self.assertIn("critical path", codex_notes)

    def test_openai_metadata_is_present(self) -> None:
        content = read_text("agents/openai.yaml")
        self.assertIn('display_name: "Wave Orchestration"', content)
        self.assertIn("short_description:", content)
        self.assertIn("default_prompt:", content)


if __name__ == "__main__":
    unittest.main()

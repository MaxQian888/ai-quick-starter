from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = SKILL_ROOT / "scripts" / "sync_upstream_reference.py"
SPEC = importlib.util.spec_from_file_location("ai_research_writing_sync", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


SAMPLE_MARKDOWN = """# Part I: 写作 Prompt 集合
## 中转英
text
## 英转中
text
# Part II: 论文写作相关的 Agent-Skills
## Skills 的配置
text
"""

FENCED_MARKDOWN = """# Part I: 写作 Prompt 集合
## 中转英
```markdown
# Role
# Task
```
## 英转中
"""


class SyncUpstreamReferenceTests(unittest.TestCase):
    def test_extract_section_index(self) -> None:
        sections = MODULE.extract_section_index(SAMPLE_MARKDOWN)

        self.assertEqual(sections[0]["title"], "Part I: 写作 Prompt 集合")
        self.assertEqual(sections[1]["title"], "中转英")
        self.assertEqual(sections[2]["title"], "英转中")
        self.assertEqual(sections[3]["title"], "Part II: 论文写作相关的 Agent-Skills")
        self.assertEqual(sections[4]["title"], "Skills 的配置")

    def test_extract_section_index_ignores_fenced_code_headings(self) -> None:
        sections = MODULE.extract_section_index(FENCED_MARKDOWN)

        self.assertEqual([item["title"] for item in sections], ["Part I: 写作 Prompt 集合", "中转英", "英转中"])

    def test_write_outputs_creates_expected_files(self) -> None:
        temp_dir = Path(tempfile.mkdtemp(prefix="ai-research-writing-"))
        readme_path = temp_dir / "upstream.md"
        index_path = temp_dir / "index.json"

        MODULE.write_outputs(SAMPLE_MARKDOWN, readme_path, index_path)

        self.assertEqual(readme_path.read_text(encoding="utf-8"), SAMPLE_MARKDOWN)
        index_payload = json.loads(index_path.read_text(encoding="utf-8"))
        self.assertEqual(index_payload["source_url"], MODULE.DEFAULT_UPSTREAM_URL)
        self.assertEqual(index_payload["sections"][0]["title"], "Part I: 写作 Prompt 集合")


if __name__ == "__main__":
    unittest.main()

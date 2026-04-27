import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "fetch_ai_news.py"
SPEC = importlib.util.spec_from_file_location("fetch_ai_news", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class FetchAiNewsTests(unittest.TestCase):
    def test_load_sources_normalizes_region_and_urls(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ai-news-") as temp_dir:
            path = Path(temp_dir) / "sources.json"
            path.write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "id": "ai-test",
                                "name": "AI Test",
                                "region": "GLOBAL",
                                "urls": ["https://example.com/ai.xml"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            sources = MODULE.load_sources(path)

            self.assertEqual(sources[0]["region"], "global")
            self.assertEqual(sources[0]["urls"], ["https://example.com/ai.xml"])

    def test_parse_keywords_and_normalize_link(self) -> None:
        self.assertEqual(MODULE.parse_keywords("agent, open-source, , inference"), ["agent", "open-source", "inference"])
        self.assertEqual(
            MODULE.normalize_link("https://example.com/ai?utm_source=rss&id=2#frag"),
            "https://example.com/ai?id=2",
        )

    def test_to_markdown_renders_failed_sources_and_items(self) -> None:
        payload = {
            "generated_at_utc": "2026-04-08T00:00:00Z",
            "request": {"region": "all", "hours": 48, "keywords": ["agent"]},
            "source_stats": {"total_sources": 2, "ok_sources": 1, "failed_sources": 1},
            "failed_sources": [
                {
                    "source_id": "down",
                    "source_name": "Down Feed",
                    "attempted_urls": ["https://down.example.com/rss"],
                    "error": "connection refused",
                }
            ],
            "source_counts": {"AI Test": 1},
            "total_items": 1,
            "items": [
                {
                    "title": "Agent platform update",
                    "link": "https://example.com/agent",
                    "source_name": "AI Test",
                    "source_id": "ai-test",
                    "published_utc": "2026-04-07T10:00:00Z",
                    "published_raw": "Mon, 07 Apr 2026 10:00:00 GMT",
                    "region": "global",
                    "summary": "New agent tooling shipped this week.",
                }
            ],
        }

        rendered = MODULE.to_markdown(payload)

        self.assertIn("- Failed sources:", rendered)
        self.assertIn("[Agent platform update](https://example.com/agent)", rendered)
        self.assertIn("Summary: New agent tooling shipped this week.", rendered)


if __name__ == "__main__":
    unittest.main()

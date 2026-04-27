import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "fetch_market_signals.py"
SPEC = importlib.util.spec_from_file_location("fetch_market_signals", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class FetchMarketSignalsTests(unittest.TestCase):
    def test_normalize_link_removes_tracking_params_and_fragment(self) -> None:
        raw = "https://example.com/article?utm_source=rss&id=42&fbclid=abc#section"

        normalized = MODULE.normalize_link(raw)

        self.assertEqual(normalized, "https://example.com/article?id=42")

    def test_detect_signal_type_prefers_keyword_match(self) -> None:
        signal_type = MODULE.detect_signal_type(
            "Startup announces Series A funding round",
            "The company raised fresh capital to expand in Europe.",
        )

        self.assertEqual(signal_type, "funding")

    def test_to_markdown_renders_failed_tasks_and_items(self) -> None:
        payload = {
            "generated_at_utc": "2026-04-08T00:00:00Z",
            "request": {
                "queries": ["robotics market"],
                "feeds": [],
                "lookback_days": 30,
                "max_per_query": 10,
                "max_items": 20,
                "hl": "en-US",
                "gl": "US",
                "dedupe_by": "link",
            },
            "stats": {"tasks_total": 2, "tasks_ok": 1, "tasks_failed": 1},
            "failed_tasks": [
                {
                    "label": "custom-feed",
                    "kind": "feed",
                    "url": "https://feeds.example.com/rss",
                    "error": "timeout",
                }
            ],
            "signal_counts": {"funding": 1},
            "total_items": 1,
            "items": [
                {
                    "title": "Robotics startup raises funding",
                    "link": "https://example.com/robotics",
                    "source_name": "example.com",
                    "published_utc": "2026-04-07T12:00:00Z",
                    "published_raw": "Mon, 07 Apr 2026 12:00:00 GMT",
                    "signal_type": "funding",
                    "query": "robotics market",
                    "input_label": "robotics market",
                    "summary": "Fresh capital suggests stronger category momentum.",
                }
            ],
        }

        rendered = MODULE.to_markdown(payload)

        self.assertIn("# Market Signal Scan (2026-04-08T00:00:00Z)", rendered)
        self.assertIn("## Failed Inputs", rendered)
        self.assertIn("[Robotics startup raises funding](https://example.com/robotics)", rendered)
        self.assertIn("Why it matters: Fresh capital suggests stronger category momentum.", rendered)

    def test_parse_feed_supports_rss_and_atom_documents(self) -> None:
        rss = b"""
        <rss><channel>
          <item>
            <title>RSS Title</title>
            <link>https://example.com/rss</link>
            <pubDate>Mon, 07 Apr 2026 01:00:00 GMT</pubDate>
            <description>RSS summary</description>
          </item>
        </channel></rss>
        """
        atom = b"""
        <feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <title>Atom Title</title>
            <link rel="alternate" href="https://example.com/atom"/>
            <updated>2026-04-07T01:00:00Z</updated>
            <summary>Atom summary</summary>
          </entry>
        </feed>
        """

        rss_rows = MODULE.parse_feed(rss)
        atom_rows = MODULE.parse_feed(atom)

        self.assertEqual(rss_rows[0]["title"], "RSS Title")
        self.assertEqual(rss_rows[0]["link"], "https://example.com/rss")
        self.assertEqual(atom_rows[0]["title"], "Atom Title")
        self.assertEqual(atom_rows[0]["link"], "https://example.com/atom")

    def test_dedupe_items_can_dedupe_by_title_when_links_differ(self) -> None:
        items = [
            {"title": "Same Headline", "link": "https://example.com/a"},
            {"title": "Same Headline", "link": "https://example.com/b"},
            {"title": "Different Headline", "link": "https://example.com/c"},
        ]

        deduped = MODULE.dedupe_items(items, strategy="title")

        self.assertEqual(len(deduped), 2)
        self.assertEqual(deduped[0]["title"], "Same Headline")
        self.assertEqual(deduped[1]["title"], "Different Headline")

    def test_fetch_task_returns_error_payload_when_feed_request_fails(self) -> None:
        task = MODULE.FetchTask(
            label="custom-feed",
            kind="feed",
            url="https://feeds.example.com/rss.xml",
            query=None,
        )

        with mock.patch.object(MODULE, "fetch_url", side_effect=RuntimeError("boom")):
            result = MODULE.fetch_task(task, timeout_seconds=1.0)

        self.assertEqual(result.label, "custom-feed")
        self.assertEqual(result.items, [])
        self.assertIn("unexpected error", result.error or "")


if __name__ == "__main__":
    unittest.main()

import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "fetch_daily_news.py"
SPEC = importlib.util.spec_from_file_location("fetch_daily_news", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class FetchDailyNewsTests(unittest.TestCase):
    def test_load_sources_returns_sources_and_presets(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daily-news-") as temp_dir:
            path = Path(temp_dir) / "sources.json"
            path.write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "id": "cn-test",
                                "name": "CN Test",
                                "region": "cn",
                                "category": "policy",
                                "country": "cn",
                                "language": "zh",
                                "tier": "core",
                                "urls": ["https://example.com/rss.xml"],
                            }
                        ],
                        "presets": {"all-core": ["cn-test"]},
                    }
                ),
                encoding="utf-8",
            )

            sources, presets = MODULE.load_sources(path)

            self.assertEqual(sources[0]["id"], "cn-test")
            self.assertEqual(sources[0]["region"], "cn")
            self.assertEqual(presets["all-core"], ["cn-test"])

    def test_normalize_link_removes_tracking_query_parameters(self) -> None:
        raw = "https://example.com/a?utm_source=rss&id=1&spm=foo#frag"
        self.assertEqual(MODULE.normalize_link(raw), "https://example.com/a?id=1")

    def test_to_markdown_includes_failed_sources_and_top_items(self) -> None:
        payload = {
            "generated_at_utc": "2026-04-08T00:00:00Z",
            "request": {
                "presets": ["all-core"],
                "hours": 24,
                "region": "all",
                "categories": [],
                "countries": [],
                "languages": [],
                "tiers": [],
            },
            "source_stats": {"total_sources": 2, "ok_sources": 1, "failed_sources": 1},
            "failed_sources": [
                {
                    "source_id": "broken",
                    "source_name": "Broken Feed",
                    "attempted_urls": ["https://broken.example.com/rss"],
                    "error": "timeout",
                }
            ],
            "source_counts": {"CN Test": 1},
            "total_items": 1,
            "items": [
                {
                    "title": "Policy update",
                    "link": "https://example.com/policy",
                    "source_name": "CN Test",
                    "published_utc": "2026-04-07T01:00:00Z",
                    "published_raw": "Mon, 07 Apr 2026 01:00:00 GMT",
                    "region": "cn",
                    "category": "policy",
                    "country": "cn",
                    "language": "zh",
                    "tier": "core",
                    "summary": "Key changes in the latest circular.",
                }
            ],
        }

        rendered = MODULE.to_markdown(payload)

        self.assertIn("- Failed sources (first 15):", rendered)
        self.assertIn("[Policy update](https://example.com/policy)", rendered)
        self.assertIn("Summary: Key changes in the latest circular.", rendered)

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

    def test_filter_item_applies_time_and_keyword_and_dimension_filters(self) -> None:
        item = {
            "title": "AI policy briefing",
            "summary": "China releases new AI rules",
            "published_ts": datetime.now(tz=timezone.utc).timestamp(),
            "category": "policy",
            "country": "cn",
            "language": "zh",
            "tier": "core",
        }

        self.assertTrue(
            MODULE.filter_item(
                item,
                keywords=["ai"],
                earliest_utc=datetime.now(tz=timezone.utc) - timedelta(hours=1),
                categories={"policy"},
                countries={"cn"},
                languages={"zh"},
                tiers={"core"},
            )
        )

        self.assertFalse(
            MODULE.filter_item(
                item,
                keywords=["finance"],
                earliest_utc=datetime.now(tz=timezone.utc) - timedelta(hours=1),
                categories={"policy"},
                countries={"cn"},
                languages={"zh"},
                tiers={"core"},
            )
        )

    def test_fetch_source_returns_error_payload_when_all_urls_fail(self) -> None:
        source = {
            "id": "broken-feed",
            "name": "Broken Feed",
            "region": "global",
            "category": "general",
            "country": "us",
            "language": "en",
            "tier": "extended",
            "urls": ["https://broken.example.com/rss.xml"],
        }

        with mock.patch.object(MODULE, "fetch_url", side_effect=RuntimeError("boom")):
            result = MODULE.fetch_source(source, timeout_seconds=1.0)

        self.assertEqual(result.source_id, "broken-feed")
        self.assertEqual(result.items, [])
        self.assertIn("boom", result.error or "")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = SKILL_ROOT / "scripts" / "fetch.py"
SPEC = importlib.util.spec_from_file_location("fetch_skill_main", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

YOUTUBE_VIDEO_HTML = """
<html>
<head>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "VideoObject",
  "name": "Example YouTube Video",
  "description": "Example YouTube description",
  "uploadDate": "2024-01-02",
  "thumbnailUrl": ["https://img.youtube.com/example.jpg"],
  "duration": "PT3M5S",
  "author": {
    "@type": "Person",
    "name": "Example Channel",
    "url": "https://www.youtube.com/@example"
  }
}
</script>
<script>
var ytInitialPlayerResponse = {
  "videoDetails": {
    "videoId": "abc123",
    "title": "Example YouTube Video",
    "shortDescription": "Example YouTube description",
    "author": "Example Channel",
    "channelId": "chan123",
    "viewCount": "12345",
    "lengthSeconds": "185",
    "keywords": ["ai", "video"],
    "thumbnail": {"thumbnails": [{"url": "https://img.youtube.com/example.jpg"}]}
  },
  "microformat": {
    "playerMicroformatRenderer": {
      "publishDate": "2024-01-02",
      "ownerProfileUrl": "https://www.youtube.com/@example"
    }
  }
};
</script>
</head>
</html>
"""

YOUTUBE_CHANNEL_HTML = """
<html>
<head>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "Example Channel",
  "description": "Channel description",
  "url": "https://www.youtube.com/@example",
  "image": "https://img.youtube.com/channel.jpg"
}
</script>
<script>
var ytInitialData = {
  "header": {
    "c4TabbedHeaderRenderer": {
      "subscriberCountText": {"simpleText": "10K subscribers"}
    }
  },
  "contents": {
    "twoColumnBrowseResultsRenderer": {
      "tabs": [{
        "tabRenderer": {
          "content": {
            "sectionListRenderer": {
              "contents": [{
                "itemSectionRenderer": {
                  "contents": [{
                    "gridRenderer": {
                      "items": [
                        {"gridVideoRenderer": {"title": {"simpleText": "Latest 1"}, "videoId": "vid1", "publishedTimeText": {"simpleText": "1 day ago"}}},
                        {"gridVideoRenderer": {"title": {"simpleText": "Latest 2"}, "videoId": "vid2", "publishedTimeText": {"simpleText": "2 days ago"}}}
                      ]
                    }
                  }]
                }
              }]
            }
          }
        }
      }]
    }
  }
};
</script>
</head>
</html>
"""

YOUTUBE_PLAYLIST_HTML = """
<html>
<head>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "name": "Example Playlist",
  "description": "Playlist description",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "url": "https://www.youtube.com/watch?v=one", "name": "Item One"},
    {"@type": "ListItem", "position": 2, "url": "https://www.youtube.com/watch?v=two", "name": "Item Two"}
  ]
}
</script>
<script>
var ytInitialData = {
  "sidebar": {
    "playlistSidebarRenderer": {
      "items": [{
        "playlistSidebarPrimaryInfoRenderer": {
          "title": {"runs": [{"text": "Example Playlist"}]},
          "stats": [{"runs": [{"text": "2 videos"}]}]
        }
      }]
    }
  },
  "contents": {
    "twoColumnBrowseResultsRenderer": {
      "tabs": [{
        "tabRenderer": {
          "content": {
            "sectionListRenderer": {
              "contents": [{
                "itemSectionRenderer": {
                  "contents": [{
                    "playlistVideoListRenderer": {
                      "contents": [
                        {"playlistVideoRenderer": {"title": {"runs": [{"text": "Item One"}]}, "videoId": "one", "lengthText": {"simpleText": "1:11"}}},
                        {"playlistVideoRenderer": {"title": {"runs": [{"text": "Item Two"}]}, "videoId": "two", "lengthText": {"simpleText": "2:22"}}}
                      ]
                    }
                  }]
                }
              }]
            }
          }
        }
      }]
    }
  }
};
</script>
</head>
</html>
"""

BILIBILI_VIDEO_HTML = """
<html>
<head>
<script>
window.__INITIAL_STATE__ = {
  "videoData": {
    "bvid": "BV1xx411c7mD",
    "title": "Example Bilibili Video",
    "desc": "Example bilibili description",
    "pic": "https://i0.hdslb.com/example.jpg",
    "pubdate": 1700000000,
    "duration": 321,
    "owner": {"name": "Example UP", "mid": 42},
    "stat": {"view": 54321, "like": 1200}
  },
  "tags": [{"tag_name": "tech"}, {"tag_name": "demo"}]
};
</script>
</head>
</html>
"""

BILIBILI_SPACE_HTML = """
<html>
<head>
<script>
window.__INITIAL_STATE__ = {
  "card": {
    "card": {
      "name": "Example UP",
      "mid": "42",
      "face": "https://i0.hdslb.com/face.jpg",
      "fans": 8888,
      "sign": "UP description"
    }
  },
  "archive": {
    "list": [{
      "bvid": "BV1A",
      "title": "Latest BV1A",
      "description": "Desc A",
      "play": 100,
      "created": 1700000001
    }, {
      "bvid": "BV1B",
      "title": "Latest BV1B",
      "description": "Desc B",
      "play": 200,
      "created": 1700000002
    }]
  }
};
</script>
</head>
</html>
"""

BILIBILI_COLLECTION_HTML = """
<html>
<head>
<script>
window.__INITIAL_STATE__ = {
  "mediaListInfo": {
    "id": "col-1",
    "title": "Example Collection",
    "intro": "Collection intro",
    "upper": {"name": "Example UP"}
  },
  "mediaListResponse": {
    "list": [{
      "bv_id": "BVCOL1",
      "title": "Collection Item 1",
      "duration": 99
    }, {
      "bv_id": "BVCOL2",
      "title": "Collection Item 2",
      "duration": 199
    }]
  }
};
</script>
</head>
</html>
"""

BILIBILI_VIDEO_API = {
    "code": 0,
    "message": "OK",
    "data": {
        "bvid": "BV1xx411c7mD",
        "title": "Example Bilibili Video API",
        "desc": "Video description",
        "pic": "https://i0.hdslb.com/example.jpg",
        "pubdate": 1700000000,
        "duration": 321,
        "owner": {"mid": 42, "name": "Example UP"},
        "stat": {"view": 54321, "like": 1200},
        "tname": "科技"
    },
}

BILIBILI_CARD_API = {
    "code": 0,
    "message": "OK",
    "data": {
        "card": {
            "mid": "42",
            "name": "Example UP",
            "face": "https://i0.hdslb.com/face.jpg",
            "sign": "UP description",
            "fans": 8888,
        },
        "archive_count": 43,
        "follower": 8888,
    },
}

BILIBILI_ARC_SEARCH_API = {
    "code": 0,
    "message": "OK",
    "data": {
        "list": {
            "vlist": [
                {"bvid": "BV1A", "title": "Latest BV1A", "length": "04:20", "created": 1700000001, "author": "Example UP"},
                {"bvid": "BV1B", "title": "Latest BV1B", "length": "05:30", "created": 1700000002, "author": "Example UP"},
            ]
        }
    },
}

BILIBILI_TOP_ARC_API = {
    "code": 0,
    "message": "OK",
    "data": {
        "aid": 349,
        "bvid": "BVTOP1",
        "title": "Pinned BVTOP1",
        "duration": 84,
        "pubdate": 1700000003,
        "owner": {"name": "Example UP"},
    },
}

BILIBILI_COLLECTION_API = {
    "code": 0,
    "message": "OK",
    "data": {
        "archives": [
            {"bvid": "BVCOL1", "title": "Collection Item 1", "duration": 99, "pubdate": 1700000101},
            {"bvid": "BVCOL2", "title": "Collection Item 2", "duration": 199, "pubdate": 1700000102},
        ],
        "meta": {
            "season_id": 57445,
            "title": "Example Collection API",
            "name": "Example Collection API",
            "description": "Collection intro",
            "mid": 42,
            "total": 2,
        },
    },
}

BILIBILI_PLAYINFO_HTML = """
<html>
<head>
<script>
window.__playinfo__={"code":0,"message":"OK","ttl":1,"data":{"dash":{"duration":217,"minBufferTime":1.5,"video":[{"id":80,"baseUrl":"https://cdn.example.com/video-1080.m4s","backupUrl":["https://backup.example.com/video-1080.m4s"],"bandwidth":2500000,"mimeType":"video/mp4","codecs":"avc1.640032","width":1920,"height":1080},{"id":64,"baseUrl":"https://cdn.example.com/video-720.m4s","bandwidth":1500000,"mimeType":"video/mp4","codecs":"avc1.64001F","width":1280,"height":720}],"audio":[{"id":30280,"baseUrl":"https://cdn.example.com/audio-high.m4s","bandwidth":192000,"mimeType":"audio/mp4","codecs":"mp4a.40.2"},{"id":30216,"baseUrl":"https://cdn.example.com/audio-low.m4s","bandwidth":64000,"mimeType":"audio/mp4","codecs":"mp4a.40.2"}]}}};
</script>
</head>
</html>
"""


class FetchSkillPackageTests(unittest.TestCase):
    def test_required_skill_files_exist(self) -> None:
        required_paths = [
            SKILL_ROOT / "SKILL.md",
            SKILL_ROOT / "agents" / "openai.yaml",
            SKILL_ROOT / "references" / "backend-selection.md",
            SKILL_ROOT / "references" / "safety-and-operations.md",
            SKILL_ROOT / "scripts" / "fetch.py",
            SKILL_ROOT / "tests" / "test_fetch.py",
        ]

        for path in required_paths:
            self.assertTrue(path.exists(), msg=f"missing required skill file: {path}")

        self.assertFalse((SKILL_ROOT / "README.md").exists(), msg="README.md should not exist in the standardized skill package")
        self.assertFalse((SKILL_ROOT / "program.md").exists(), msg="program.md should be folded into references/")


class FetchScriptTests(unittest.TestCase):
    def test_detect_platform_target_identifies_video_platform_urls(self) -> None:
        self.assertEqual(MODULE.detect_platform_target("https://www.youtube.com/watch?v=abc123"), "youtube-video")
        self.assertEqual(MODULE.detect_platform_target("https://www.youtube.com/@example"), "youtube-channel")
        self.assertEqual(MODULE.detect_platform_target("https://www.youtube.com/playlist?list=PL123"), "youtube-playlist")
        self.assertEqual(MODULE.detect_platform_target("https://www.bilibili.com/video/BV1xx411c7mD"), "bilibili-video")
        self.assertEqual(MODULE.detect_platform_target("https://space.bilibili.com/42"), "bilibili-space")
        self.assertEqual(
            MODULE.detect_platform_target("https://space.bilibili.com/42/channel/collectiondetail?sid=99"),
            "bilibili-collection",
        )

    def test_parser_supports_batch_and_safety_options(self) -> None:
        parser = MODULE.build_parser()

        args = parser.parse_args(
            [
                "--batch",
                "urls.txt",
                "--output-dir",
                "out",
                "--continue-on-error",
                "--wespy-path",
                "C:/tools/WeSpy",
                "--allow-wespy-import",
                "--stdin",
                "--manifest",
                "manifest.json",
                "--jobs",
                "4",
                "--retry",
                "2",
                "--retry-delay",
                "0.1",
                "--cache-dir",
                "cache",
                "--resume",
                "--rate-limit-ms",
                "50",
                "--results-file",
                "results.jsonl",
                "--download-media",
                "--download-dir",
                "downloads",
                "--ffmpeg-path",
                "C:/tools/ffmpeg.exe",
            ]
        )

        self.assertEqual(args.batch, "urls.txt")
        self.assertEqual(args.output_dir, "out")
        self.assertTrue(args.continue_on_error)
        self.assertEqual(args.wespy_path, "C:/tools/WeSpy")
        self.assertTrue(args.allow_wespy_import)
        self.assertTrue(args.stdin)
        self.assertEqual(args.manifest, "manifest.json")
        self.assertEqual(args.jobs, 4)
        self.assertEqual(args.retry, 2)
        self.assertEqual(args.retry_delay, 0.1)
        self.assertEqual(args.cache_dir, "cache")
        self.assertTrue(args.resume)
        self.assertEqual(args.rate_limit_ms, 50)
        self.assertEqual(args.results_file, "results.jsonl")
        self.assertTrue(args.download_media)
        self.assertEqual(args.download_dir, "downloads")
        self.assertEqual(args.ffmpeg_path, "C:/tools/ffmpeg.exe")

    def test_validate_args_rejects_non_positive_limit(self) -> None:
        parser = MODULE.build_parser()
        args = parser.parse_args(["--user", "openai", "--limit", "0"])

        with self.assertRaises(ValueError):
            MODULE.validate_args(args)

    def test_collect_input_urls_reads_batch_and_stdin(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fetch-skill-main-") as temp_dir:
            batch_path = Path(temp_dir) / "urls.txt"
            batch_path.write_text(
                "# comment\nhttps://example.com/a\n\nhttps://example.com/b\n",
                encoding="utf-8",
            )

            args = argparse.Namespace(
                url="https://example.com/root",
                batch=str(batch_path),
                stdin=True,
                user=None,
            )

            urls = MODULE.collect_input_urls(args, stdin_text="https://example.com/c\nhttps://example.com/b\n")

        self.assertEqual(
            urls,
            [
                "https://example.com/root",
                "https://example.com/a",
                "https://example.com/b",
                "https://example.com/c",
            ],
        )

    def test_http_get_decompresses_gzip_payloads(self) -> None:
        compressed = gzip.compress(b'window.__playinfo__={"code":0}')

        class FakeResponse:
            headers = {"Content-Encoding": "gzip"}

            def read(self) -> bytes:
                return compressed

            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, exc_type, exc, tb) -> bool:
                return False

        with mock.patch.object(MODULE.urllib.request, "urlopen", return_value=FakeResponse()):
            content = MODULE.http_get("https://example.com/test")

        self.assertIn("__playinfo__", content)

    def test_load_manifest_tasks_supports_metadata_and_enabled_flag(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fetch-skill-main-") as temp_dir:
            manifest_path = Path(temp_dir) / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    [
                        {
                            "url": "https://example.com/a",
                            "mode": "web",
                            "output_name": "a-custom.md",
                            "tags": ["news", "a"],
                            "enabled": True,
                        },
                        {
                            "url": "https://example.com/b",
                            "enabled": False,
                        },
                    ]
                ),
                encoding="utf-8",
            )

            tasks = MODULE.load_manifest_tasks(str(manifest_path))

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["url"], "https://example.com/a")
        self.assertEqual(tasks[0]["mode"], "web")
        self.assertEqual(tasks[0]["output_name"], "a-custom.md")
        self.assertEqual(tasks[0]["tags"], ["news", "a"])

    def test_parse_youtube_video_html_returns_structured_metadata(self) -> None:
        payload = MODULE.parse_youtube_html(
            YOUTUBE_VIDEO_HTML,
            "https://www.youtube.com/watch?v=abc123",
            limit=5,
        )

        self.assertEqual(payload["platform"], "youtube")
        self.assertEqual(payload["entity_type"], "video")
        self.assertEqual(payload["id"], "abc123")
        self.assertEqual(payload["title"], "Example YouTube Video")
        self.assertEqual(payload["author_name"], "Example Channel")
        self.assertEqual(payload["view_count"], 12345)
        self.assertEqual(payload["duration"], "185")
        self.assertEqual(payload["tags"], ["ai", "video"])

    def test_parse_youtube_playlist_and_channel_limit_items(self) -> None:
        playlist_payload = MODULE.parse_youtube_html(
            YOUTUBE_PLAYLIST_HTML,
            "https://www.youtube.com/playlist?list=PL123",
            limit=1,
        )
        channel_payload = MODULE.parse_youtube_html(
            YOUTUBE_CHANNEL_HTML,
            "https://www.youtube.com/@example",
            limit=1,
        )

        self.assertEqual(playlist_payload["entity_type"], "playlist")
        self.assertEqual(len(playlist_payload["items"]), 1)
        self.assertEqual(playlist_payload["items"][0]["title"], "Item One")
        self.assertEqual(channel_payload["entity_type"], "channel")
        self.assertEqual(len(channel_payload["items"]), 1)
        self.assertEqual(channel_payload["items"][0]["title"], "Latest 1")

    def test_parse_bilibili_video_space_and_collection_html(self) -> None:
        video_payload = MODULE.parse_bilibili_html(
            BILIBILI_VIDEO_HTML,
            "https://www.bilibili.com/video/BV1xx411c7mD",
            limit=5,
        )
        space_payload = MODULE.parse_bilibili_html(
            BILIBILI_SPACE_HTML,
            "https://space.bilibili.com/42",
            limit=1,
        )
        collection_payload = MODULE.parse_bilibili_html(
            BILIBILI_COLLECTION_HTML,
            "https://space.bilibili.com/42/channel/collectiondetail?sid=99",
            limit=1,
        )

        self.assertEqual(video_payload["entity_type"], "video")
        self.assertEqual(video_payload["title"], "Example Bilibili Video")
        self.assertEqual(video_payload["author_name"], "Example UP")
        self.assertEqual(space_payload["entity_type"], "channel")
        self.assertEqual(len(space_payload["items"]), 1)
        self.assertEqual(collection_payload["entity_type"], "playlist")
        self.assertEqual(len(collection_payload["items"]), 1)

    def test_parse_bilibili_api_payloads_return_real_entities(self) -> None:
        video_payload = MODULE.parse_bilibili_video_api(BILIBILI_VIDEO_API, "https://www.bilibili.com/video/BV1xx411c7mD")
        space_payload = MODULE.parse_bilibili_space_api(
            BILIBILI_CARD_API,
            BILIBILI_ARC_SEARCH_API,
            "https://space.bilibili.com/42",
            limit=1,
        )
        collection_payload = MODULE.parse_bilibili_collection_api(
            BILIBILI_COLLECTION_API,
            "https://space.bilibili.com/42/channel/collectiondetail?sid=57445",
            limit=1,
        )

        self.assertEqual(video_payload["entity_type"], "video")
        self.assertEqual(video_payload["title"], "Example Bilibili Video API")
        self.assertEqual(space_payload["entity_type"], "channel")
        self.assertEqual(space_payload["author_name"], "Example UP")
        self.assertEqual(len(space_payload["items"]), 1)
        self.assertEqual(collection_payload["entity_type"], "playlist")
        self.assertEqual(collection_payload["title"], "Example Collection API")
        self.assertEqual(len(collection_payload["items"]), 1)

    def test_parse_bilibili_playinfo_extracts_dash_streams(self) -> None:
        playinfo = MODULE.parse_bilibili_playinfo(BILIBILI_PLAYINFO_HTML)

        dash = playinfo["data"]["dash"]
        self.assertEqual(len(dash["video"]), 2)
        self.assertEqual(dash["video"][0]["height"], 1080)
        self.assertEqual(dash["audio"][0]["bandwidth"], 192000)

    def test_build_bilibili_download_plan_prefers_highest_quality_streams(self) -> None:
        metadata = MODULE.parse_bilibili_video_api(
            BILIBILI_VIDEO_API,
            "https://www.bilibili.com/video/BV1xx411c7mD",
        )
        playinfo = MODULE.parse_bilibili_playinfo(BILIBILI_PLAYINFO_HTML)

        plan = MODULE.build_bilibili_download_plan(
            metadata,
            playinfo,
            "https://www.bilibili.com/video/BV1xx411c7mD",
        )

        self.assertEqual(plan["video_url"], "https://cdn.example.com/video-1080.m4s")
        self.assertEqual(plan["audio_url"], "https://cdn.example.com/audio-high.m4s")
        self.assertTrue(plan["bundle_name"].startswith("bilibili-bv1xx411c7md-"))
        self.assertTrue(plan["video_filename"].endswith(".video.mp4"))
        self.assertTrue(plan["audio_filename"].endswith(".audio.m4a"))

    def test_download_bilibili_media_bundle_writes_streams_and_info_files(self) -> None:
        metadata = MODULE.parse_bilibili_video_api(
            BILIBILI_VIDEO_API,
            "https://www.bilibili.com/video/BV1xx411c7mD",
        )

        with tempfile.TemporaryDirectory(prefix="fetch-skill-main-") as temp_dir:
            output_dir = Path(temp_dir) / "downloads"
            calls: list[tuple[str, str, str]] = []

            def fake_downloader(url: str, destination: Path, headers: dict[str, str], timeout: int) -> None:
                calls.append((url, destination.name, headers.get("Referer", "")))
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(f"downloaded from {url}".encode("utf-8"))

            result = MODULE.download_bilibili_media_bundle(
                "https://www.bilibili.com/video/BV1xx411c7mD",
                metadata,
                output_dir,
                timeout=30,
                page_getter=lambda url, timeout=30: BILIBILI_PLAYINFO_HTML,
                binary_downloader=fake_downloader,
                ffmpeg_path="",
                verbose=False,
            )

            bundle_dir = Path(result["bundle_dir"])
            info_payload = json.loads((bundle_dir / "info.json").read_text(encoding="utf-8"))
            self.assertEqual(len(calls), 2)
            self.assertTrue((bundle_dir / result["video_filename"]).exists())
            self.assertTrue((bundle_dir / result["audio_filename"]).exists())
            self.assertTrue((bundle_dir / "info.json").exists())
            self.assertTrue((bundle_dir / "info.md").exists())
            self.assertEqual(info_payload["downloads"]["merge_status"], "not-requested")
            self.assertEqual(info_payload["downloads"]["video_path"], str(bundle_dir / result["video_filename"]))
            self.assertEqual(info_payload["downloads"]["audio_path"], str(bundle_dir / result["audio_filename"]))

    def test_parse_bilibili_space_api_falls_back_to_top_arc(self) -> None:
        payload = MODULE.parse_bilibili_space_api(
            BILIBILI_CARD_API,
            {"code": -799, "message": "rate limited"},
            "https://space.bilibili.com/42",
            limit=1,
            top_arc_payload=BILIBILI_TOP_ARC_API,
        )

        self.assertEqual(payload["entity_type"], "channel")
        self.assertEqual(len(payload["items"]), 1)
        self.assertEqual(payload["items"][0]["title"], "Pinned BVTOP1")

    def test_fetch_media_platform_falls_back_to_web_fetcher(self) -> None:
        args = argparse.Namespace(timeout=30, verbose=False, text_only=False, limit=5, no_jina=False)

        payload = MODULE.fetch_video_platform(
            "https://www.youtube.com/watch?v=abc123",
            args,
            html_getter=lambda url, timeout=30: "<html>broken</html>",
            web_fetcher=lambda url, timeout=30, skip_jina=False, verbose=True: "fallback-content",
        )

        self.assertEqual(payload, "fallback-content")

    def test_fetch_media_platform_uses_bilibili_api_before_html_fallback(self) -> None:
        args = argparse.Namespace(timeout=30, verbose=False, text_only=False, limit=1, no_jina=False, pretty=False)
        api_calls: list[str] = []

        def fake_api_getter(url: str, timeout: int = 30, referer: str = "") -> object:
            api_calls.append(url)
            if "x/web-interface/view" in url:
                return BILIBILI_VIDEO_API
            raise AssertionError(f"unexpected api url: {url}")

        payload = MODULE.fetch_video_platform(
            "https://www.bilibili.com/video/BV1xx411c7mD",
            args,
            api_getter=fake_api_getter,
            html_getter=lambda url, timeout=30: (_ for _ in ()).throw(AssertionError("html getter should not run")),
            web_fetcher=lambda url, timeout=30, skip_jina=False, verbose=True: "fallback-content",
        )

        parsed = json.loads(payload)
        self.assertEqual(parsed["platform"], "bilibili")
        self.assertEqual(parsed["entity_type"], "video")
        self.assertTrue(any("x/web-interface/view" in item for item in api_calls))

    def test_resolve_wespy_path_never_clones_or_installs(self) -> None:
        with mock.patch.object(MODULE, "subprocess") as mocked_subprocess:
            mocked_subprocess.run.side_effect = AssertionError("should not spawn subprocesses")

            resolved = MODULE.resolve_wespy_path(
                explicit_path="C:/missing/WeSpy",
                allow_import=False,
                env={},
                verbose=False,
            )

        self.assertIsNone(resolved)

    def test_run_batch_continues_on_error_and_writes_safe_outputs(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fetch-skill-main-") as temp_dir:
            output_dir = Path(temp_dir) / "artifacts"
            args = argparse.Namespace(
                mode="auto",
                no_jina=False,
                timeout=30,
                verbose=False,
                output_dir=str(output_dir),
                continue_on_error=True,
                pretty=False,
                text_only=False,
            )

            def fake_fetch(url: str, parsed_args: argparse.Namespace) -> str:
                if "fail" in url:
                    raise RuntimeError("boom")
                return f"content for {url}"

            results = MODULE.run_batch(
                [
                    "https://example.com/ok",
                    "https://example.com/fail",
                    "https://example.com/../../escape",
                ],
                args,
                fetcher=fake_fetch,
            )

            self.assertEqual(len(results), 3)
            self.assertTrue(results[0]["ok"])
            self.assertFalse(results[1]["ok"])
            self.assertTrue(results[2]["ok"])

            written_files = sorted(path.name for path in output_dir.iterdir())
            self.assertEqual(
                written_files,
                [
                    "001-example-com-ok.md",
                    "003-example-com-escape.md",
                    "batch-summary.json",
                    "results.jsonl",
                ],
            )

            summary = json.loads((output_dir / "batch-summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary[1]["error"], "boom")

    def test_run_batch_raises_on_first_error_when_continue_disabled(self) -> None:
        args = argparse.Namespace(
            output_dir=None,
            continue_on_error=False,
            verbose=False,
        )

        def fake_fetch(url: str, parsed_args: argparse.Namespace) -> str:
            raise RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            MODULE.run_batch(["https://example.com/fail"], args, fetcher=fake_fetch)

    def test_execute_tasks_retries_uses_cache_and_writes_results_log(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fetch-skill-main-") as temp_dir:
            temp_root = Path(temp_dir)
            output_dir = temp_root / "out"
            cache_dir = temp_root / "cache"
            results_file = temp_root / "results.jsonl"
            args = argparse.Namespace(
                mode="auto",
                no_jina=False,
                timeout=30,
                verbose=False,
                output_dir=str(output_dir),
                continue_on_error=True,
                pretty=False,
                text_only=False,
                cache_dir=str(cache_dir),
                retry=1,
                retry_delay=0.0,
                jobs=1,
                rate_limit_ms=0,
                resume=False,
                results_file=str(results_file),
            )
            calls: dict[str, int] = {}

            def flaky_fetch(url: str, parsed_args: argparse.Namespace) -> str:
                calls[url] = calls.get(url, 0) + 1
                if calls[url] == 1:
                    raise RuntimeError("transient")
                return f"content for {url}"

            tasks = [
                {"id": "task-a", "url": "https://example.com/a", "mode": "web", "output_name": "a.md"},
            ]
            first_results = MODULE.execute_batch_tasks(tasks, args, fetcher=flaky_fetch)
            second_results = MODULE.execute_batch_tasks(tasks, args, fetcher=flaky_fetch)
            log_lines = results_file.read_text(encoding="utf-8").strip().splitlines()

        self.assertEqual(calls["https://example.com/a"], 2)
        self.assertTrue(first_results[0]["ok"])
        self.assertFalse(first_results[0]["from_cache"])
        self.assertTrue(second_results[0]["ok"])
        self.assertTrue(second_results[0]["from_cache"])
        self.assertEqual(first_results[0]["output_path"], str(output_dir / "a.md"))
        self.assertEqual(len(log_lines), 2)

    def test_execute_tasks_resume_skips_previously_successful_entries(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fetch-skill-main-") as temp_dir:
            temp_root = Path(temp_dir)
            output_dir = temp_root / "out"
            results_file = temp_root / "results.jsonl"
            results_file.write_text(
                json.dumps(
                    {
                        "id": "task-a",
                        "url": "https://example.com/a",
                        "ok": True,
                        "output_path": str(output_dir / "a.md"),
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            args = argparse.Namespace(
                mode="auto",
                no_jina=False,
                timeout=30,
                verbose=False,
                output_dir=str(output_dir),
                continue_on_error=True,
                pretty=False,
                text_only=False,
                cache_dir=None,
                retry=0,
                retry_delay=0.0,
                jobs=1,
                rate_limit_ms=0,
                resume=True,
                results_file=str(results_file),
            )

            def should_not_run(url: str, parsed_args: argparse.Namespace) -> str:
                raise AssertionError("resume should skip completed task")

            results = MODULE.execute_batch_tasks(
                [{"id": "task-a", "url": "https://example.com/a", "mode": "web", "output_name": "a.md"}],
                args,
                fetcher=should_not_run,
            )

        self.assertTrue(results[0]["ok"])
        self.assertTrue(results[0]["resumed"])


if __name__ == "__main__":
    unittest.main()

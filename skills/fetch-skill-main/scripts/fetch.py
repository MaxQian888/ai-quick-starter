#!/usr/bin/env python3
"""Unified content fetcher with a stdlib-first core and explicit optional integrations."""

from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

FXTWITTER_API = "https://api.fxtwitter.com"
CAMOFOX_DEFAULT_PORT = 9377

_RE_TWITTER = re.compile(r"https?://(www\.)?(twitter|x)\.com/", re.I)
_RE_TWEET = re.compile(r"https?://(www\.)?(twitter|x)\.com/\w+/status/(\d+)", re.I)
_RE_ARTICLE = re.compile(r"https?://(www\.)?(twitter|x)\.com/i/(article|web/article)/(\d+)", re.I)
_RE_WECHAT = re.compile(r"https?://mp\.weixin\.qq\.com/", re.I)
_RE_YOUTUBE_WATCH = re.compile(r"https?://(www\.)?(youtube\.com/watch|youtu\.be/|m\.youtube\.com/watch)", re.I)
_RE_YOUTUBE_PLAYLIST = re.compile(r"https?://(www\.)?(youtube|m\.youtube)\.com/playlist", re.I)
_RE_YOUTUBE_CHANNEL = re.compile(r"https?://(www\.)?(youtube|m\.youtube)\.com/(@|channel/|c/|user/)", re.I)
_RE_BILIBILI_VIDEO = re.compile(r"https?://(www\.)?bilibili\.com/video/", re.I)
_RE_BILIBILI_SPACE = re.compile(r"https?://space\.bilibili\.com/\d+/?$", re.I)
_RE_BILIBILI_COLLECTION = re.compile(r"https?://(www\.)?bilibili\.com/list/|https?://space\.bilibili\.com/\d+/channel/collectiondetail", re.I)
_RE_TAG = re.compile(r"<[^>]+>")
_RE_SAFE_FILENAME = re.compile(r"[^a-z0-9]+")
_RE_LD_JSON = re.compile(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', re.I | re.S)
_RE_BILIBILI_ERROR_PAGE = re.compile(r"错误号[:：]\\s*412|请求被拒绝|出错啦!", re.I)

_BILIBILI_WBI_MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52,
]


def log(msg: str, verbose: bool) -> None:
    if verbose:
        print(msg, file=sys.stderr)


def http_get(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 30) -> str:
    merged_headers = {
        "User-Agent": UA,
        "Accept-Encoding": "gzip, deflate",
    }
    if headers:
        merged_headers.update(headers)
    request = urllib.request.Request(url, headers=merged_headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read()
        content_encoding = str(response.headers.get("Content-Encoding", "")).lower()
        if "gzip" in content_encoding:
            payload = gzip.decompress(payload)
        elif "deflate" in content_encoding:
            payload = zlib.decompress(payload)
        return payload.decode("utf-8", errors="replace")


def http_json(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 30) -> Any:
    return json.loads(http_get(url, headers=headers, timeout=timeout))


def http_json_bilibili(url: str, timeout: int = 30, referer: str = "https://www.bilibili.com/") -> Any:
    return http_json(url, headers={"Referer": referer}, timeout=timeout)


def http_html_bilibili(url: str, timeout: int = 30) -> str:
    return http_get(
        url,
        headers={
            "Referer": "https://www.bilibili.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
        timeout=timeout,
    )


def http_download_file(url: str, destination: Path, headers: Optional[Dict[str, str]] = None, timeout: int = 60) -> None:
    merged_headers = {"User-Agent": UA}
    if headers:
        merged_headers.update(headers)
    request = urllib.request.Request(url, headers=merged_headers)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(request, timeout=timeout) as response, destination.open("wb") as handle:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)


def _apply_inline_styles(text: str, ranges: List[Dict[str, Any]]) -> str:
    if not ranges:
        return text
    chars = list(text)
    opens: Dict[int, List[str]] = {}
    closes: Dict[int, List[str]] = {}
    for item in sorted(ranges, key=lambda candidate: candidate.get("offset", 0)):
        style = item.get("style", "")
        start = item.get("offset", 0)
        length = item.get("length", 0)
        end = start + length
        tag = "**" if style == "Bold" else ("*" if style == "Italic" else "")
        if not tag:
            continue
        opens.setdefault(start, []).append(tag)
        closes.setdefault(end, []).insert(0, tag)
    rendered: List[str] = []
    for index, character in enumerate(chars):
        rendered.extend(opens.get(index, []))
        rendered.append(character)
        rendered.extend(closes.get(index, []))
    rendered.extend(closes.get(len(chars), []))
    return "".join(rendered)


def _draftjs_to_md(article: Dict[str, Any]) -> str:
    content = article.get("content", {})
    blocks = content.get("blocks", [])
    entity_list = content.get("entityMap", [])
    media_entities = article.get("media_entities", [])

    entity_map: Dict[str, Dict[str, Any]] = {}
    for entity in entity_list:
        entity_map[str(entity.get("key", ""))] = entity.get("value", {})

    media_lookup: Dict[str, str] = {}
    for media_entity in media_entities:
        media_id = str(media_entity.get("media_id", ""))
        original_url = media_entity.get("media_info", {}).get("original_img_url", "")
        if media_id and original_url:
            media_lookup[media_id] = original_url

    title = article.get("title", "")
    lines = [f"# {title}", ""] if title else []

    for block in blocks:
        block_type = block.get("type", "unstyled")
        text = block.get("text", "")
        ranges = block.get("inlineStyleRanges", [])
        entity_ranges = block.get("entityRanges", [])

        if block_type == "atomic":
            for entity_range in entity_ranges:
                entity_key = str(entity_range.get("key", ""))
                entity_value = entity_map.get(entity_key, {})
                entity_data = entity_value.get("data", {})
                caption = entity_data.get("caption", "")
                for item in entity_data.get("mediaItems", []):
                    media_id = str(item.get("mediaId", ""))
                    image_url = media_lookup.get(media_id, "")
                    if image_url:
                        lines.append(f"\n![{caption or 'image'}]({image_url})\n")
            continue

        styled = _apply_inline_styles(text, ranges)
        if block_type == "header-one":
            lines.append(f"# {styled}")
        elif block_type == "header-two":
            lines.append(f"\n## {styled}")
        elif block_type == "header-three":
            lines.append(f"\n### {styled}")
        elif block_type == "unordered-list-item":
            lines.append(f"- {styled}")
        elif block_type == "ordered-list-item":
            lines.append(f"1. {styled}")
        elif block_type == "blockquote":
            lines.append(f"> {styled}")
        elif block_type == "code-block":
            lines.append(f"```\n{text}\n```")
        else:
            lines.append(styled if styled.strip() else "")

    return "\n".join(lines)


def _strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", _RE_TAG.sub("", text or "")).strip()


def _slugify(value: str) -> str:
    cleaned = _RE_SAFE_FILENAME.sub("-", value.lower()).strip("-")
    return cleaned or "item"


def validate_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Unsupported URL: {url}")
    return url


def _coerce_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        digits = re.sub(r"[^\d]", "", value)
        return int(digits) if digits else None
    return None


def _extract_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if isinstance(value.get("simpleText"), str):
            return value["simpleText"]
        if isinstance(value.get("text"), str):
            return value["text"]
        if isinstance(value.get("runs"), list):
            return "".join(_extract_text(item) for item in value["runs"])
    if isinstance(value, list):
        return "".join(_extract_text(item) for item in value)
    return ""


def _recursive_find_renderers(node: Any, key: str) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    if isinstance(node, dict):
        for current_key, value in node.items():
            if current_key == key and isinstance(value, dict):
                results.append(value)
            results.extend(_recursive_find_renderers(value, key))
    elif isinstance(node, list):
        for item in node:
            results.extend(_recursive_find_renderers(item, key))
    return results


def _extract_json_object_after_marker(text: str, marker: str) -> Optional[Any]:
    index = text.find(marker)
    if index < 0:
        return None
    start = -1
    for position in range(index + len(marker), len(text)):
        if text[position] in "{[":
            start = position
            break
    if start < 0:
        return None
    opening = text[start]
    closing = "}" if opening == "{" else "]"
    depth = 0
    in_string = False
    escaping = False
    for position in range(start, len(text)):
        character = text[position]
        if in_string:
            if escaping:
                escaping = False
            elif character == "\\":
                escaping = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
            continue
        if character == opening:
            depth += 1
        elif character == closing:
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : position + 1])
                except json.JSONDecodeError:
                    return None
    return None


def _extract_json_ld_blocks(html: str) -> List[Any]:
    blocks: List[Any] = []
    for match in _RE_LD_JSON.finditer(html):
        raw = match.group(1).strip()
        if not raw:
            continue
        try:
            blocks.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return blocks


def _find_first_json_ld(blocks: Sequence[Any], schema_type: str) -> Optional[Dict[str, Any]]:
    for block in blocks:
        if isinstance(block, dict) and block.get("@type") == schema_type:
            return block
    return None


def _bilibili_extract_mid(url: str) -> Optional[int]:
    parsed = urllib.parse.urlparse(url)
    if "space.bilibili.com" not in parsed.netloc:
        return None
    parts = [part for part in parsed.path.split("/") if part]
    if not parts:
        return None
    return _coerce_int(parts[0])


def _bilibili_extract_season_id(url: str) -> Optional[int]:
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)
    for key in ("sid", "season_id"):
        value = params.get(key, [""])[0]
        resolved = _coerce_int(value)
        if resolved:
            return resolved
    return None


def _bilibili_build_wbi_key(img_url: str, sub_url: str) -> str:
    img_key = img_url.rsplit("/", 1)[-1].split(".")[0]
    sub_key = sub_url.rsplit("/", 1)[-1].split(".")[0]
    origin = img_key + sub_key
    return "".join(origin[index] for index in _BILIBILI_WBI_MIXIN_KEY_ENC_TAB)[:32]


def _bilibili_sign_wbi_params(params: Mapping[str, Any], img_url: str, sub_url: str, timestamp: Optional[int] = None) -> Dict[str, str]:
    signed_params = {key: "".join(ch for ch in str(value) if ch not in "!'()*") for key, value in params.items()}
    signed_params["wts"] = str(timestamp or int(time.time()))
    ordered = dict(sorted(signed_params.items()))
    query = urllib.parse.urlencode(ordered)
    mixin_key = _bilibili_build_wbi_key(img_url, sub_url)
    ordered["w_rid"] = hashlib.md5((query + mixin_key).encode("utf-8")).hexdigest()
    return ordered


def _dedupe_keep_order(items: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    ordered: List[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def read_url_lines(text: str) -> List[str]:
    urls: List[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(validate_url(line))
    return urls


def collect_input_urls(args: argparse.Namespace, stdin_text: Optional[str] = None) -> List[str]:
    urls: List[str] = []
    if getattr(args, "url", None):
        urls.append(validate_url(args.url))

    if getattr(args, "batch", None):
        batch_path = Path(args.batch)
        batch_text = batch_path.read_text(encoding="utf-8")
        urls.extend(read_url_lines(batch_text))

    if getattr(args, "stdin", False):
        incoming = stdin_text if stdin_text is not None else sys.stdin.read()
        urls.extend(read_url_lines(incoming))

    return _dedupe_keep_order(urls)


def _stable_task_id(url: str, mode: str, output_name: str = "", tags: Optional[Sequence[str]] = None) -> str:
    raw = json.dumps(
        {
            "url": url,
            "mode": mode,
            "output_name": output_name,
            "tags": list(tags or []),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def load_manifest_tasks(manifest_path: str) -> List[Dict[str, Any]]:
    path = Path(manifest_path)
    payload = path.read_text(encoding="utf-8").strip()
    if not payload:
        return []

    if path.suffix.lower() == ".jsonl":
        raw_items = [json.loads(line) for line in payload.splitlines() if line.strip()]
    else:
        decoded = json.loads(payload)
        raw_items = decoded if isinstance(decoded, list) else decoded.get("tasks", [])

    tasks: List[Dict[str, Any]] = []
    for index, item in enumerate(raw_items, start=1):
        if not item.get("enabled", True):
            continue
        url = validate_url(item["url"])
        mode = item.get("mode", "auto")
        output_name = item.get("output_name")
        tags = list(item.get("tags", []))
        tasks.append(
            {
                "id": item.get("id") or _stable_task_id(url, mode, output_name or "", tags),
                "url": url,
                "mode": mode,
                "output_name": output_name,
                "tags": tags,
                "source": "manifest",
                "index": index,
            }
        )
    return tasks


def build_batch_tasks(args: argparse.Namespace, stdin_text: Optional[str] = None) -> List[Dict[str, Any]]:
    tasks: List[Dict[str, Any]] = []
    urls = collect_input_urls(args, stdin_text=stdin_text)
    for index, url in enumerate(urls, start=1):
        mode = args.mode if args.mode != "auto" else detect_mode(url)
        tasks.append(
            {
                "id": _stable_task_id(url, mode),
                "url": url,
                "mode": mode,
                "output_name": None,
                "tags": [],
                "source": "input",
                "index": index,
            }
        )

    if getattr(args, "manifest", None):
        tasks.extend(load_manifest_tasks(args.manifest))

    seen: set[str] = set()
    unique_tasks: List[Dict[str, Any]] = []
    for task in tasks:
        if task["id"] in seen:
            continue
        seen.add(task["id"])
        unique_tasks.append(task)
    return unique_tasks


def validate_args(args: argparse.Namespace) -> None:
    if args.limit <= 0:
        raise ValueError("--limit must be a positive integer")
    if args.timeout <= 0:
        raise ValueError("--timeout must be a positive integer")
    if getattr(args, "jobs", 1) <= 0:
        raise ValueError("--jobs must be a positive integer")
    if getattr(args, "retry", 0) < 0:
        raise ValueError("--retry must be zero or greater")
    if getattr(args, "retry_delay", 0.0) < 0:
        raise ValueError("--retry-delay must be zero or greater")
    if getattr(args, "rate_limit_ms", 0) < 0:
        raise ValueError("--rate-limit-ms must be zero or greater")
    if args.output and getattr(args, "output_dir", None):
        raise ValueError("--output and --output-dir cannot be used together")
    if args.output and (getattr(args, "batch", None) or getattr(args, "stdin", False)):
        raise ValueError("--output is only supported for single URL mode")
    if getattr(args, "download_dir", None) and not getattr(args, "download_media", False):
        raise ValueError("--download-dir requires --download-media")
    if getattr(args, "ffmpeg_path", None) and not getattr(args, "download_media", False):
        raise ValueError("--ffmpeg-path requires --download-media")
    if args.user and (getattr(args, "batch", None) or getattr(args, "stdin", False)):
        raise ValueError("--user cannot be combined with --batch or --stdin")
    if not any([getattr(args, "url", None), args.user, getattr(args, "batch", None), getattr(args, "stdin", False), getattr(args, "manifest", None)]):
        raise ValueError("provide a URL, --user USERNAME, --batch FILE, --manifest FILE, or --stdin")


def detect_mode(url: str) -> str:
    if _RE_TWITTER.search(url):
        return "twitter"
    if _RE_WECHAT.search(url):
        return "wechat"
    return "web"


def detect_platform_target(url: str) -> Optional[str]:
    if _RE_YOUTUBE_PLAYLIST.search(url):
        return "youtube-playlist"
    if _RE_YOUTUBE_CHANNEL.search(url):
        return "youtube-channel"
    if _RE_YOUTUBE_WATCH.search(url):
        return "youtube-video"
    if _RE_BILIBILI_COLLECTION.search(url):
        return "bilibili-collection"
    if _RE_BILIBILI_SPACE.search(url):
        return "bilibili-space"
    if _RE_BILIBILI_VIDEO.search(url):
        return "bilibili-video"
    return None


def _youtube_video_id(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if "youtu.be" in parsed.netloc:
        return parsed.path.strip("/").split("/")[0]
    return urllib.parse.parse_qs(parsed.query).get("v", [""])[0]


def _youtube_playlist_id(url: str) -> str:
    return urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get("list", [""])[0]


def _bilibili_id_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    path_parts = [part for part in parsed.path.split("/") if part]
    return path_parts[-1] if path_parts else ""


def parse_youtube_html(html: str, url: str, limit: int) -> Dict[str, Any]:
    target = detect_platform_target(url)
    json_ld_blocks = _extract_json_ld_blocks(html)
    player_response = _extract_json_object_after_marker(html, "ytInitialPlayerResponse")
    initial_data = _extract_json_object_after_marker(html, "ytInitialData")

    if target == "youtube-video":
        video_ld = _find_first_json_ld(json_ld_blocks, "VideoObject") or {}
        video_details = (player_response or {}).get("videoDetails", {})
        microformat = (player_response or {}).get("microformat", {}).get("playerMicroformatRenderer", {})
        thumbnails = ((video_details.get("thumbnail") or {}).get("thumbnails") or [])
        thumbnail_url = (thumbnails[-1] or {}).get("url") if thumbnails else ""
        author_url = microformat.get("ownerProfileUrl") or ((video_ld.get("author") or {}).get("url", ""))
        title = video_details.get("title") or video_ld.get("name", "")
        if not title:
            raise RuntimeError("Missing YouTube video metadata")
        return {
            "platform": "youtube",
            "entity_type": "video",
            "id": video_details.get("videoId") or _youtube_video_id(url),
            "url": url,
            "title": title,
            "description": video_details.get("shortDescription") or video_ld.get("description", ""),
            "author_name": video_details.get("author") or ((video_ld.get("author") or {}).get("name", "")),
            "author_url": author_url,
            "published_at": microformat.get("publishDate") or video_ld.get("uploadDate", ""),
            "duration": str(video_details.get("lengthSeconds") or video_ld.get("duration", "")),
            "view_count": _coerce_int(video_details.get("viewCount")),
            "like_count": None,
            "thumbnail_url": thumbnail_url or ((video_ld.get("thumbnailUrl") or [""])[0]),
            "tags": list(video_details.get("keywords") or []),
            "items": [],
        }

    if target == "youtube-channel":
        channel_ld = _find_first_json_ld(json_ld_blocks, "Person") or _find_first_json_ld(json_ld_blocks, "Organization") or {}
        header = (initial_data or {}).get("header", {}).get("c4TabbedHeaderRenderer", {})
        videos = _recursive_find_renderers(initial_data or {}, "gridVideoRenderer")[:limit]
        if not channel_ld and not videos:
            raise RuntimeError("Missing YouTube channel metadata")
        items = [
            {
                "title": _extract_text(item.get("title")),
                "url": f"https://www.youtube.com/watch?v={item.get('videoId', '')}",
                "author_name": channel_ld.get("name", ""),
                "published_at": _extract_text(item.get("publishedTimeText")),
                "duration": _extract_text(item.get("thumbnailOverlays")),
            }
            for item in videos
            if item.get("videoId")
        ]
        return {
            "platform": "youtube",
            "entity_type": "channel",
            "id": _bilibili_id_from_url(url) or url.rstrip("/").split("/")[-1],
            "url": url,
            "title": channel_ld.get("name", ""),
            "description": channel_ld.get("description", ""),
            "author_name": channel_ld.get("name", ""),
            "author_url": channel_ld.get("url", url),
            "published_at": "",
            "duration": None,
            "view_count": None,
            "like_count": None,
            "follower_count": _extract_text(header.get("subscriberCountText")),
            "thumbnail_url": channel_ld.get("image", ""),
            "tags": [],
            "items": items,
        }

    if target == "youtube-playlist":
        playlist_ld = _find_first_json_ld(json_ld_blocks, "ItemList") or {}
        primary_info = (((initial_data or {}).get("sidebar") or {}).get("playlistSidebarRenderer") or {}).get("items", [])
        title = ""
        item_count = None
        if primary_info:
            primary_renderer = primary_info[0].get("playlistSidebarPrimaryInfoRenderer", {})
            title = _extract_text(primary_renderer.get("title"))
            stats = primary_renderer.get("stats") or []
            item_count = _coerce_int(_extract_text(stats[0]) if stats else None)
        renderers = _recursive_find_renderers(initial_data or {}, "playlistVideoRenderer")[:limit]
        items = [
            {
                "title": _extract_text(item.get("title")),
                "url": f"https://www.youtube.com/watch?v={item.get('videoId', '')}",
                "author_name": "",
                "published_at": "",
                "duration": _extract_text(item.get("lengthText")),
            }
            for item in renderers
            if item.get("videoId")
        ]
        if not items:
            items = [
                {
                    "title": item.get("name", ""),
                    "url": item.get("url", ""),
                    "author_name": "",
                    "published_at": "",
                    "duration": "",
                }
                for item in (playlist_ld.get("itemListElement") or [])[:limit]
            ]
        if not items and not playlist_ld and not title:
            raise RuntimeError("Missing YouTube playlist metadata")
        return {
            "platform": "youtube",
            "entity_type": "playlist",
            "id": _youtube_playlist_id(url),
            "url": url,
            "title": title or playlist_ld.get("name", ""),
            "description": playlist_ld.get("description", ""),
            "author_name": "",
            "author_url": "",
            "published_at": "",
            "duration": None,
            "view_count": None,
            "like_count": None,
            "item_count": item_count or len(items),
            "thumbnail_url": "",
            "tags": [],
            "items": items[:limit],
        }

    raise RuntimeError("Unsupported YouTube entity")


def parse_bilibili_html(html: str, url: str, limit: int) -> Dict[str, Any]:
    target = detect_platform_target(url)
    if _RE_BILIBILI_ERROR_PAGE.search(html):
        raise RuntimeError("Bilibili returned an anti-crawler or error page")
    state = _extract_json_object_after_marker(html, "window.__INITIAL_STATE__") or _extract_json_object_after_marker(html, "__INITIAL_STATE__")
    if not isinstance(state, dict):
        raise RuntimeError("Missing Bilibili initial state")

    if target == "bilibili-video":
        video_data = state.get("videoData", {})
        owner = video_data.get("owner", {})
        stat = video_data.get("stat", {})
        if not video_data.get("title"):
            raise RuntimeError("Missing Bilibili video metadata")
        return {
            "platform": "bilibili",
            "entity_type": "video",
            "id": video_data.get("bvid") or _bilibili_id_from_url(url),
            "url": url,
            "title": video_data.get("title", ""),
            "description": video_data.get("desc", ""),
            "author_name": owner.get("name", ""),
            "author_url": f"https://space.bilibili.com/{owner.get('mid', '')}" if owner.get("mid") else "",
            "published_at": video_data.get("pubdate"),
            "duration": str(video_data.get("duration", "")),
            "view_count": _coerce_int(stat.get("view")),
            "like_count": _coerce_int(stat.get("like")),
            "thumbnail_url": video_data.get("pic", ""),
            "tags": [item.get("tag_name", "") for item in (state.get("tags") or []) if item.get("tag_name")],
            "items": [],
        }

    if target == "bilibili-space":
        card = ((state.get("card") or {}).get("card") or {})
        archive_items = (((state.get("archive") or {}).get("list")) or [])[:limit]
        if not card:
            raise RuntimeError("Missing Bilibili space metadata")
        return {
            "platform": "bilibili",
            "entity_type": "channel",
            "id": str(card.get("mid", _bilibili_id_from_url(url))),
            "url": url,
            "title": card.get("name", ""),
            "description": card.get("sign", ""),
            "author_name": card.get("name", ""),
            "author_url": url,
            "published_at": "",
            "duration": None,
            "view_count": None,
            "like_count": None,
            "follower_count": _coerce_int(card.get("fans")),
            "thumbnail_url": card.get("face", ""),
            "tags": [],
            "items": [
                {
                    "title": item.get("title", ""),
                    "url": f"https://www.bilibili.com/video/{item.get('bvid', '')}",
                    "author_name": card.get("name", ""),
                    "published_at": item.get("created"),
                    "duration": item.get("length") or "",
                }
                for item in archive_items
                if item.get("bvid")
            ],
        }

    if target == "bilibili-collection":
        info = state.get("mediaListInfo", {})
        items = ((state.get("mediaListResponse") or {}).get("list") or [])[:limit]
        if not info and not items:
            raise RuntimeError("Missing Bilibili collection metadata")
        return {
            "platform": "bilibili",
            "entity_type": "playlist",
            "id": str(info.get("id", _bilibili_id_from_url(url))),
            "url": url,
            "title": info.get("title", ""),
            "description": info.get("intro", ""),
            "author_name": ((info.get("upper") or {}).get("name", "")),
            "author_url": "",
            "published_at": "",
            "duration": None,
            "view_count": None,
            "like_count": None,
            "item_count": len(items),
            "thumbnail_url": "",
            "tags": [],
            "items": [
                {
                    "title": item.get("title", ""),
                    "url": f"https://www.bilibili.com/video/{item.get('bv_id', '')}",
                    "author_name": ((info.get("upper") or {}).get("name", "")),
                    "published_at": item.get("pubtime", ""),
                    "duration": str(item.get("duration", "")),
                }
                for item in items
                if item.get("bv_id")
            ],
        }

    raise RuntimeError("Unsupported Bilibili entity")


def parse_bilibili_video_api(payload: Mapping[str, Any], url: str) -> Dict[str, Any]:
    if payload.get("code") != 0:
        raise RuntimeError(f"Bilibili video API failed: {payload.get('message', 'unknown error')}")
    data = payload.get("data", {})
    owner = data.get("owner", {})
    stat = data.get("stat", {})
    return {
        "platform": "bilibili",
        "entity_type": "video",
        "id": data.get("bvid") or _bilibili_id_from_url(url),
        "url": url,
        "title": data.get("title", ""),
        "description": data.get("desc", ""),
        "author_name": owner.get("name", ""),
        "author_url": f"https://space.bilibili.com/{owner.get('mid', '')}" if owner.get("mid") else "",
        "published_at": data.get("pubdate"),
        "duration": str(data.get("duration", "")),
        "view_count": _coerce_int(stat.get("view")),
        "like_count": _coerce_int(stat.get("like")),
        "thumbnail_url": data.get("pic", ""),
        "tags": [data.get("tname")] if data.get("tname") else [],
        "items": [],
    }


def parse_bilibili_playinfo(html: str) -> Dict[str, Any]:
    playinfo = (
        _extract_json_object_after_marker(html, "window.__playinfo__=")
        or _extract_json_object_after_marker(html, "window.__playinfo__ =")
        or _extract_json_object_after_marker(html, "__playinfo__=")
    )
    if not isinstance(playinfo, dict):
        raise RuntimeError("Missing Bilibili playinfo")
    dash = ((playinfo.get("data") or {}).get("dash")) or {}
    if not dash.get("video") or not dash.get("audio"):
        raise RuntimeError("Missing Bilibili DASH streams in playinfo")
    return playinfo


def _bilibili_stream_url(stream: Mapping[str, Any]) -> str:
    direct = stream.get("baseUrl") or stream.get("base_url")
    if isinstance(direct, str) and direct:
        return direct
    for key in ("backupUrl", "backup_url"):
        candidates = stream.get(key) or []
        if isinstance(candidates, list):
            for item in candidates:
                if isinstance(item, str) and item:
                    return item
    return ""


def _bilibili_pick_best_stream(streams: Sequence[Mapping[str, Any]], kind: str) -> Mapping[str, Any]:
    available = [stream for stream in streams if _bilibili_stream_url(stream)]
    if not available:
        raise RuntimeError(f"Missing Bilibili {kind} stream URLs")

    def sort_key(stream: Mapping[str, Any]) -> Tuple[int, int, int, int]:
        return (
            _coerce_int(stream.get("height")) or 0,
            _coerce_int(stream.get("width")) or 0,
            _coerce_int(stream.get("bandwidth")) or 0,
            _coerce_int(stream.get("id")) or 0,
        )

    return max(available, key=sort_key)


def _bilibili_stream_extension(stream: Mapping[str, Any], kind: str) -> str:
    mime_type = str(stream.get("mimeType") or stream.get("mime_type") or "").lower()
    if kind == "video":
        if "webm" in mime_type:
            return "webm"
        return "mp4"
    if "webm" in mime_type:
        return "weba"
    return "m4a"


def _bilibili_bundle_name(metadata: Mapping[str, Any]) -> str:
    bvid = _slugify(str(metadata.get("id") or "video"))
    title = _slugify(str(metadata.get("title") or ""))[:80]
    if title:
        return f"bilibili-{bvid}-{title}"
    return f"bilibili-{bvid}"


def build_bilibili_download_plan(metadata: Mapping[str, Any], playinfo: Mapping[str, Any], url: str) -> Dict[str, Any]:
    dash = ((playinfo.get("data") or {}).get("dash")) or {}
    video_stream = _bilibili_pick_best_stream(dash.get("video") or [], kind="video")
    audio_stream = _bilibili_pick_best_stream(dash.get("audio") or [], kind="audio")
    bundle_name = _bilibili_bundle_name(metadata)
    video_extension = _bilibili_stream_extension(video_stream, kind="video")
    audio_extension = _bilibili_stream_extension(audio_stream, kind="audio")
    return {
        "bundle_name": bundle_name,
        "video_url": _bilibili_stream_url(video_stream),
        "audio_url": _bilibili_stream_url(audio_stream),
        "video_stream": dict(video_stream),
        "audio_stream": dict(audio_stream),
        "video_filename": f"{bundle_name}.video.{video_extension}",
        "audio_filename": f"{bundle_name}.audio.{audio_extension}",
        "merged_filename": f"{bundle_name}.merged.mp4",
        "referer": url,
    }


def _resolve_ffmpeg_path(explicit_path: Optional[str]) -> Optional[str]:
    if explicit_path == "":
        return None
    if explicit_path:
        candidate = Path(explicit_path)
        if candidate.exists():
            return str(candidate)
        return None
    located = shutil.which("ffmpeg")
    return located or None


def _merge_bilibili_streams(
    ffmpeg_path: str,
    video_path: Path,
    audio_path: Path,
    merged_path: Path,
    verbose: bool,
) -> None:
    command = [
        ffmpeg_path,
        "-y",
        "-i",
        str(video_path),
        "-i",
        str(audio_path),
        "-c",
        "copy",
        str(merged_path),
    ]
    log(f"[bilibili] merging with ffmpeg -> {merged_path}", verbose)
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        raise RuntimeError(stderr or "ffmpeg merge failed")


def download_bilibili_media_bundle(
    url: str,
    metadata: Mapping[str, Any],
    download_dir: Path,
    timeout: int = 30,
    page_getter: Callable[..., str] = http_html_bilibili,
    binary_downloader: Callable[[str, Path, Dict[str, str], int], None] = http_download_file,
    ffmpeg_path: Optional[str] = None,
    verbose: bool = True,
) -> Dict[str, Any]:
    html = page_getter(url, timeout=timeout)
    playinfo = parse_bilibili_playinfo(html)
    plan = build_bilibili_download_plan(metadata, playinfo, url)
    bundle_dir = download_dir / plan["bundle_name"]
    bundle_dir.mkdir(parents=True, exist_ok=True)

    request_headers = {"Referer": url}
    video_path = bundle_dir / plan["video_filename"]
    audio_path = bundle_dir / plan["audio_filename"]

    log(f"[bilibili] downloading video stream -> {video_path.name}", verbose)
    binary_downloader(plan["video_url"], video_path, request_headers, timeout)
    log(f"[bilibili] downloading audio stream -> {audio_path.name}", verbose)
    binary_downloader(plan["audio_url"], audio_path, request_headers, timeout)

    resolved_ffmpeg = _resolve_ffmpeg_path(ffmpeg_path)
    merged_path = bundle_dir / plan["merged_filename"]
    merge_status = "not-requested" if ffmpeg_path == "" else "ffmpeg-not-found"
    merge_error = ""
    if resolved_ffmpeg:
        try:
            _merge_bilibili_streams(resolved_ffmpeg, video_path, audio_path, merged_path, verbose=verbose)
            merge_status = "merged"
        except Exception as exc:  # noqa: BLE001
            merge_status = "merge-failed"
            merge_error = str(exc)
            log(f"[bilibili] ffmpeg merge failed: {exc}", verbose)

    info_payload = dict(metadata)
    info_payload["downloads"] = {
        "bundle_dir": str(bundle_dir.resolve()),
        "video_path": str(video_path.resolve()),
        "audio_path": str(audio_path.resolve()),
        "merged_path": str(merged_path.resolve()) if merge_status == "merged" else "",
        "merge_status": merge_status,
        "merge_error": merge_error,
        "video_stream": {
            "id": plan["video_stream"].get("id"),
            "bandwidth": plan["video_stream"].get("bandwidth"),
            "width": plan["video_stream"].get("width"),
            "height": plan["video_stream"].get("height"),
            "codecs": plan["video_stream"].get("codecs"),
        },
        "audio_stream": {
            "id": plan["audio_stream"].get("id"),
            "bandwidth": plan["audio_stream"].get("bandwidth"),
            "codecs": plan["audio_stream"].get("codecs"),
        },
        "video_source_url": plan["video_url"],
        "audio_source_url": plan["audio_url"],
    }
    info_json_path = bundle_dir / "info.json"
    info_md_path = bundle_dir / "info.md"
    write_text_output(info_json_path, json.dumps(info_payload, ensure_ascii=False, indent=2))
    markdown_lines = [
        render_video_platform_text(info_payload),
        "",
        "## Downloads",
        "",
        f"- Bundle Dir: {bundle_dir.resolve()}",
        f"- Video: {video_path.resolve()}",
        f"- Audio: {audio_path.resolve()}",
        f"- Merge Status: {merge_status}",
    ]
    if merge_status == "merged":
        markdown_lines.append(f"- Merged: {merged_path.resolve()}")
    elif merge_error:
        markdown_lines.append(f"- Merge Error: {merge_error}")
    write_text_output(info_md_path, "\n".join(markdown_lines).strip() + "\n")
    return {
        **plan,
        "bundle_dir": str(bundle_dir.resolve()),
        "video_path": str(video_path.resolve()),
        "audio_path": str(audio_path.resolve()),
        "merged_path": str(merged_path.resolve()) if merge_status == "merged" else "",
        "merge_status": merge_status,
        "merge_error": merge_error,
        "info_json_path": str(info_json_path.resolve()),
        "info_md_path": str(info_md_path.resolve()),
    }


def parse_bilibili_space_api(
    card_payload: Mapping[str, Any],
    arc_payload: Optional[Mapping[str, Any]],
    url: str,
    limit: int,
    top_arc_payload: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    if card_payload.get("code") != 0:
        raise RuntimeError(f"Bilibili card API failed: {card_payload.get('message', 'unknown error')}")
    card_data = card_payload.get("data", {})
    card = card_data.get("card", {})
    items: List[Dict[str, Any]] = []
    if arc_payload and arc_payload.get("code") == 0:
        vlist = (((arc_payload.get("data") or {}).get("list") or {}).get("vlist") or [])[:limit]
        items = [
            {
                "title": item.get("title", ""),
                "url": f"https://www.bilibili.com/video/{item.get('bvid', '')}",
                "author_name": item.get("author", card.get("name", "")),
                "published_at": item.get("created"),
                "duration": item.get("length", ""),
            }
            for item in vlist
            if item.get("bvid")
        ]
    elif top_arc_payload and top_arc_payload.get("code") == 0 and (top_arc_payload.get("data") or {}).get("bvid"):
        top_arc = top_arc_payload.get("data") or {}
        items = [
            {
                "title": top_arc.get("title", ""),
                "url": f"https://www.bilibili.com/video/{top_arc.get('bvid', '')}",
                "author_name": ((top_arc.get("owner") or {}).get("name", card.get("name", ""))),
                "published_at": top_arc.get("pubdate"),
                "duration": str(top_arc.get("duration", "")),
            }
        ]
    return {
        "platform": "bilibili",
        "entity_type": "channel",
        "id": str(card.get("mid", _bilibili_extract_mid(url) or "")),
        "url": url,
        "title": card.get("name", ""),
        "description": card.get("sign", "") or card_data.get("archive_count", ""),
        "author_name": card.get("name", ""),
        "author_url": url,
        "published_at": "",
        "duration": None,
        "view_count": None,
        "like_count": _coerce_int(card_data.get("like_num")),
        "follower_count": _coerce_int(card_data.get("follower") or card.get("fans")),
        "thumbnail_url": card.get("face", ""),
        "tags": [],
        "items": items,
    }


def parse_bilibili_collection_api(payload: Mapping[str, Any], url: str, limit: int) -> Dict[str, Any]:
    if payload.get("code") != 0:
        raise RuntimeError(f"Bilibili collection API failed: {payload.get('message', 'unknown error')}")
    data = payload.get("data", {})
    meta = data.get("meta", {})
    archives = (data.get("archives") or [])[:limit]
    return {
        "platform": "bilibili",
        "entity_type": "playlist",
        "id": str(meta.get("season_id", _bilibili_extract_season_id(url) or "")),
        "url": url,
        "title": meta.get("title") or meta.get("name", ""),
        "description": meta.get("description", ""),
        "author_name": "",
        "author_url": f"https://space.bilibili.com/{meta.get('mid', '')}" if meta.get("mid") else "",
        "published_at": meta.get("ptime"),
        "duration": None,
        "view_count": None,
        "like_count": None,
        "item_count": _coerce_int(meta.get("total")) or len(archives),
        "thumbnail_url": meta.get("cover", ""),
        "tags": [],
        "items": [
            {
                "title": item.get("title", ""),
                "url": f"https://www.bilibili.com/video/{item.get('bvid', '')}",
                "author_name": "",
                "published_at": item.get("pubdate") or item.get("ctime"),
                "duration": str(item.get("duration", "")),
            }
            for item in archives
            if item.get("bvid")
        ],
    }


def _bilibili_wbi_nav(api_getter: Callable[..., Any], timeout: int) -> Mapping[str, Any]:
    payload = api_getter("https://api.bilibili.com/x/web-interface/nav", timeout=timeout, referer="https://www.bilibili.com/")
    if payload.get("data", {}).get("wbi_img"):
        return payload
    raise RuntimeError(f"Bilibili nav API failed: {payload.get('message', 'unknown error')}")


def fetch_bilibili_platform(
    url: str,
    args: argparse.Namespace,
    api_getter: Callable[..., Any] = http_json_bilibili,
    html_getter: Callable[..., str] = http_get,
    web_fetcher: Optional[Callable[..., str]] = None,
) -> str:
    target = detect_platform_target(url)
    fallback = web_fetcher or fetch_web

    try:
        if target == "bilibili-video":
            parsed = urllib.parse.urlparse(url)
            qs = urllib.parse.parse_qs(parsed.query)
            bvid = _bilibili_id_from_url(url)
            aid = _coerce_int(qs.get("aid", [""])[0])
            if bvid and bvid.lower().startswith("av"):
                aid = _coerce_int(bvid[2:])
                bvid = ""
            api_url = (
                f"https://api.bilibili.com/x/web-interface/view?bvid={urllib.parse.quote(bvid)}"
                if bvid and not aid
                else f"https://api.bilibili.com/x/web-interface/view?aid={aid}"
            )
            payload = parse_bilibili_video_api(api_getter(api_url, timeout=args.timeout, referer=url), url)
            if getattr(args, "download_media", False):
                download_root = Path(getattr(args, "download_dir", None) or getattr(args, "output_dir", None) or "downloads")
                payload = dict(payload)
                payload["downloads"] = download_bilibili_media_bundle(
                    url,
                    payload,
                    download_root,
                    timeout=args.timeout,
                    ffmpeg_path=getattr(args, "ffmpeg_path", None),
                    verbose=getattr(args, "verbose", True),
                )
        elif target == "bilibili-space":
            mid = _bilibili_extract_mid(url)
            if not mid:
                raise RuntimeError("Missing Bilibili mid")
            card_payload = api_getter(f"https://api.bilibili.com/x/web-interface/card?mid={mid}", timeout=args.timeout, referer=url)
            nav_payload = _bilibili_wbi_nav(api_getter, timeout=args.timeout)
            wbi = (nav_payload.get("data") or {}).get("wbi_img", {})
            signed_params = _bilibili_sign_wbi_params(
                {"mid": mid, "pn": 1, "ps": args.limit, "order": "pubdate"},
                wbi.get("img_url", ""),
                wbi.get("sub_url", ""),
            )
            arc_url = "https://api.bilibili.com/x/space/wbi/arc/search?" + urllib.parse.urlencode(signed_params)
            arc_payload = api_getter(arc_url, timeout=args.timeout, referer=url)
            top_arc_payload = None
            if arc_payload.get("code") != 0:
                try:
                    top_arc_payload = api_getter(f"https://api.bilibili.com/x/space/top/arc?vmid={mid}", timeout=args.timeout, referer=url)
                except Exception:  # noqa: BLE001
                    top_arc_payload = None
            payload = parse_bilibili_space_api(card_payload, arc_payload, url, args.limit, top_arc_payload=top_arc_payload)
        elif target == "bilibili-collection":
            mid = _bilibili_extract_mid(url)
            season_id = _bilibili_extract_season_id(url)
            if not mid or not season_id:
                raise RuntimeError("Missing Bilibili collection identifiers")
            collection_url = (
                "https://api.bilibili.com/x/polymer/web-space/seasons_archives_list?"
                + urllib.parse.urlencode({"mid": mid, "season_id": season_id, "page_num": 1, "page_size": args.limit})
            )
            payload = parse_bilibili_collection_api(api_getter(collection_url, timeout=args.timeout, referer=url), url, args.limit)
        else:
            html = html_getter(url, timeout=args.timeout)
            payload = parse_bilibili_html(html, url, limit=args.limit)

        if getattr(args, "text_only", False):
            return render_video_platform_text(payload)
        return json.dumps(payload, ensure_ascii=False, indent=2 if getattr(args, "pretty", False) else None)
    except Exception as exc:  # noqa: BLE001
        log(f"[bilibili] structured/API fetch failed: {exc}", getattr(args, "verbose", True))
        return fallback(url, timeout=args.timeout, skip_jina=getattr(args, "no_jina", False), verbose=getattr(args, "verbose", True))


def render_video_platform_text(payload: Mapping[str, Any]) -> str:
    lines = [f"# {payload.get('title', '')}", ""]
    meta = []
    if payload.get("platform"):
        meta.append(f"Platform: {payload['platform']}")
    if payload.get("entity_type"):
        meta.append(f"Type: {payload['entity_type']}")
    if payload.get("author_name"):
        meta.append(f"Author: {payload['author_name']}")
    if payload.get("published_at"):
        meta.append(f"Published: {payload['published_at']}")
    if payload.get("duration"):
        meta.append(f"Duration: {payload['duration']}")
    if payload.get("view_count") is not None:
        meta.append(f"Views: {payload['view_count']}")
    if meta:
        lines.extend(meta)
        lines.append("")
    if payload.get("description"):
        lines.append(str(payload["description"]))
        lines.append("")
    items = payload.get("items") or []
    if items:
        lines.append("## Items")
        lines.append("")
        for index, item in enumerate(items, start=1):
            lines.append(f"{index}. {item.get('title', '')}")
            if item.get("url"):
                lines.append(f"   {item['url']}")
            if item.get("duration"):
                lines.append(f"   duration: {item['duration']}")
        lines.append("")
    downloads = payload.get("downloads") or {}
    if downloads:
        lines.append("## Downloads")
        lines.append("")
        if downloads.get("bundle_dir"):
            lines.append(f"Bundle Dir: {downloads['bundle_dir']}")
        if downloads.get("video_path"):
            lines.append(f"Video: {downloads['video_path']}")
        if downloads.get("audio_path"):
            lines.append(f"Audio: {downloads['audio_path']}")
        if downloads.get("merged_path"):
            lines.append(f"Merged: {downloads['merged_path']}")
        if downloads.get("merge_status"):
            lines.append(f"Merge Status: {downloads['merge_status']}")
        lines.append("")
    return "\n".join(lines).strip()


def fetch_video_platform(
    url: str,
    args: argparse.Namespace,
    api_getter: Callable[..., Any] = http_json_bilibili,
    html_getter: Callable[..., str] = http_get,
    web_fetcher: Optional[Callable[..., str]] = None,
) -> str:
    target = detect_platform_target(url)
    if not target:
        raise RuntimeError("Unsupported video platform URL")
    try:
        if target.startswith("youtube-"):
            html = html_getter(url, timeout=args.timeout)
            payload = parse_youtube_html(html, url, limit=args.limit)
        elif target.startswith("bilibili-"):
            return fetch_bilibili_platform(url, args, api_getter=api_getter, html_getter=html_getter, web_fetcher=web_fetcher)
        else:
            html = html_getter(url, timeout=args.timeout)
            payload = parse_bilibili_html(html, url, limit=args.limit)
        if getattr(args, "text_only", False):
            return render_video_platform_text(payload)
        return json.dumps(payload, ensure_ascii=False, indent=2 if getattr(args, "pretty", False) else None)
    except Exception as exc:  # noqa: BLE001
        log(f"[video-platform] structured parse failed: {exc}", getattr(args, "verbose", True))
        fallback = web_fetcher or fetch_web
        return fallback(url, timeout=args.timeout, skip_jina=getattr(args, "no_jina", False), verbose=getattr(args, "verbose", True))


def fetch_web(url: str, timeout: int = 30, skip_jina: bool = False, verbose: bool = True) -> str:
    strategies: List[Tuple[str, str, Optional[Dict[str, str]]]] = []
    if not skip_jina:
        strategies.append(("Jina Reader", f"https://r.jina.ai/{url}", {"Accept": "text/markdown"}))
    strategies.extend(
        [
            ("defuddle.md", f"https://defuddle.md/{url}", None),
            ("markdown.new", f"https://markdown.new/{url}", None),
            ("Raw HTML", url, None),
        ]
    )
    failures: List[str] = []
    for name, fetch_url, headers in strategies:
        try:
            log(f"[web/{name}] fetching...", verbose)
            content = http_get(fetch_url, headers=headers, timeout=timeout)
            log(f"[web/{name}] ok ({len(content)} chars)", verbose)
            return content
        except Exception as exc:  # noqa: BLE001
            log(f"[web/{name}] failed: {exc}", verbose)
            failures.append(f"{name}: {exc}")
    raise RuntimeError("All web strategies failed:\n  " + "\n  ".join(failures))


def _camofox_rpc(method: str, params: Dict[str, Any], port: int, timeout: int = 60) -> Any:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    request = urllib.request.Request(
        f"http://localhost:{port}/api",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def _camofox_ok(port: int) -> bool:
    try:
        _camofox_rpc("ping", {}, port=port, timeout=3)
        return True
    except Exception:  # noqa: BLE001
        return False


def _camofox_snapshot(url: str, port: int, timeout: int, verbose: bool) -> str:
    session_key = f"fetch-{int(time.time())}"
    log(f"[Camofox] opening {url}", verbose)
    response = _camofox_rpc("openTab", {"url": url, "sessionKey": session_key}, port=port, timeout=timeout)
    tab_id = response.get("result", {}).get("tabId", "")
    try:
        time.sleep(4)
        snapshot_response = _camofox_rpc(
            "getSnapshot",
            {"tabId": tab_id, "sessionKey": session_key},
            port=port,
            timeout=timeout,
        )
        snapshot = snapshot_response.get("result", {}).get("snapshot", "")
        log(f"[Camofox] snapshot {len(snapshot)} chars", verbose)
        return snapshot
    finally:
        try:
            _camofox_rpc("closeTab", {"tabId": tab_id, "sessionKey": session_key}, port=port, timeout=10)
        except Exception:  # noqa: BLE001
            pass


def _fetch_nitter_timeline(username: str, limit: int, timeout: int, pretty: bool, text_only: bool, verbose: bool) -> str:
    rss_url = f"https://nitter.net/{username}/rss"
    log(f"[twitter/rss] {rss_url}", verbose)
    payload = http_get(rss_url, timeout=timeout)
    root = ET.fromstring(payload)
    items = []
    for item in root.findall("./channel/item")[:limit]:
        items.append(
            {
                "title": item.findtext("title", default=""),
                "link": item.findtext("link", default=""),
                "published_at": item.findtext("pubDate", default=""),
                "summary": _strip_html(item.findtext("description", default="")),
            }
        )
    if not items:
        raise RuntimeError(f"No RSS timeline items found for @{username}")
    if text_only:
        lines: List[str] = [f"# @{username} timeline", ""]
        for index, item in enumerate(items, start=1):
            lines.extend(
                [
                    f"## {index}. {item['title']}",
                    item["published_at"],
                    item["link"],
                    "",
                    item["summary"],
                    "",
                ]
            )
        return "\n".join(lines).strip()
    return json.dumps(
        {"type": "timeline", "user": username, "items": items},
        ensure_ascii=False,
        indent=2 if pretty else None,
    )


def fetch_twitter(url: str, args: argparse.Namespace) -> str:
    verbose = args.verbose
    port = args.port
    timeout = args.timeout
    pretty = args.pretty
    text_only = args.text_only

    def dump_json(obj: Any) -> str:
        return json.dumps(obj, ensure_ascii=False, indent=2 if pretty else None)

    if args.user:
        username = args.user.lstrip("@")
        try:
            return _fetch_nitter_timeline(username, args.limit, timeout, pretty, text_only, verbose)
        except Exception as exc:  # noqa: BLE001
            log(f"[twitter/rss] failed: {exc}", verbose)
        if not _camofox_ok(port):
            raise RuntimeError(f"User timeline requires Nitter RSS or Camofox on port {port}.")
        nitter_url = f"https://nitter.net/{username}"
        snapshot = _camofox_snapshot(nitter_url, port, timeout, verbose)
        return snapshot if text_only else dump_json({"type": "timeline", "user": username, "snapshot": snapshot, "limit": args.limit})

    if _RE_ARTICLE.search(url):
        if not _camofox_ok(port):
            raise RuntimeError(f"X Articles require Camofox on port {port}.")
        snapshot = _camofox_snapshot(url, port, timeout, verbose)
        return snapshot if text_only else dump_json({"type": "article", "url": url, "content": snapshot})

    tweet_match = _RE_TWEET.search(url)
    if tweet_match:
        tweet_id = tweet_match.group(3)
        username_match = re.search(r"\.com/([^/]+)/status/", url, re.I)
        username = username_match.group(1) if username_match else "_"
        data: Any = None
        for api_path in [f"/{username}/status/{tweet_id}", f"/status/{tweet_id}"]:
            try:
                api_url = f"{FXTWITTER_API}{api_path}"
                log(f"[twitter/FxTwitter] {api_url}", verbose)
                data = http_json(api_url, timeout=timeout)
                break
            except urllib.error.HTTPError as exc:
                if exc.code != 404:
                    raise
        if data is None:
            log("[twitter/FxTwitter] 404, falling back to web fetch", verbose)
            return fetch_web(url, timeout=timeout, verbose=verbose)

        tweet = data.get("tweet", {})
        article = tweet.get("article")
        if article:
            markdown = _draftjs_to_md(article)
            if text_only:
                author = tweet.get("author", {}).get("name", "")
                handle = tweet.get("author", {}).get("screen_name", "")
                created = tweet.get("created_at", "")
                header = f"> **{author}** (@{handle})  {created}\n\n---\n\n"
                return header + markdown
            return markdown

        if text_only:
            author = tweet.get("author", {}).get("name", "")
            handle = tweet.get("author", {}).get("screen_name", "")
            body = tweet.get("text", "")
            created = tweet.get("created_at", "")
            likes = tweet.get("likes", 0)
            views = tweet.get("views", 0)
            retweets = tweet.get("retweets", 0)
            bookmarks = tweet.get("bookmarks", 0)
            lines = [
                f"**{author}** (@{handle})  {created}",
                "",
                body,
                "",
                f"❤️ {likes}  👁 {views}  🔁 {retweets}  🔖 {bookmarks}",
            ]
            media = tweet.get("media") or {}
            for item in (media.get("photos") or []) + (media.get("videos") or []):
                source = item.get("url") or item.get("thumbnail_url", "")
                if source:
                    lines.append(f"\n![]({source})")
            quote = tweet.get("quote")
            if quote:
                lines.extend(
                    [
                        "",
                        "---",
                        "Quoted:",
                        "",
                        f"> **{quote.get('author', {}).get('name', '')}**: {quote.get('text', '')}",
                    ]
                )
            return "\n".join(lines)
        return dump_json(data)

    if args.replies:
        if not _camofox_ok(port):
            raise RuntimeError(f"Reply fetching requires Camofox on port {port}.")
        nitter_url = re.sub(r"https?://(www\.)?(twitter|x)\.com", "https://nitter.net", url)
        snapshot = _camofox_snapshot(nitter_url, port, timeout, verbose)
        return snapshot if text_only else dump_json({"type": "replies", "url": url, "snapshot": snapshot, "limit": args.limit})

    log("[twitter] no specific pattern matched, using web fallback", verbose)
    return fetch_web(url, timeout=timeout, verbose=verbose)


def _unwrap_captcha_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if "wappoc_appmsgcaptcha" in parsed.path:
        target = urllib.parse.parse_qs(parsed.query).get("target_url", [""])[0]
        if target:
            return target
    return url


def resolve_wespy_path(
    explicit_path: Optional[str],
    allow_import: bool,
    env: Optional[Mapping[str, str]] = None,
    verbose: bool = True,
) -> Optional[str]:
    runtime_env = env or os.environ
    candidates: List[Path] = []
    if explicit_path:
        candidates.append(Path(explicit_path))
    env_candidate = runtime_env.get("WESPY_PATH")
    if env_candidate:
        candidates.append(Path(env_candidate))

    for candidate in candidates:
        marker = candidate / "wespy" / "main.py"
        if marker.exists():
            return str(candidate)
        log(f"[wespy] invalid path: {candidate}", verbose)

    if allow_import:
        return "__IMPORT_ONLY__"
    return None


def _fetch_via_wespy(
    url: str,
    verbose: bool = True,
    wespy_path: Optional[str] = None,
    allow_import: bool = False,
    env: Optional[Mapping[str, str]] = None,
) -> str:
    resolved = resolve_wespy_path(wespy_path, allow_import, env=env, verbose=verbose)
    if not resolved:
        raise RuntimeError("WeSpy not configured")
    if resolved != "__IMPORT_ONLY__" and resolved not in sys.path:
        sys.path.insert(0, resolved)

    try:
        from wespy.main import ArticleFetcher  # type: ignore
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"WeSpy import failed: {exc}") from exc

    fetcher = ArticleFetcher()
    output_dir = tempfile.gettempdir()
    log(f"[wespy] fetching {url}", verbose)
    article_info = fetcher._fetch_wechat_article(  # type: ignore[attr-defined]
        url,
        output_dir=output_dir,
        save_html=False,
        save_json=False,
        save_markdown=False,
    )
    if not article_info:
        raise RuntimeError("WeSpy returned no article data")

    title = article_info.get("title", "")
    author = article_info.get("author", "")
    published_at = article_info.get("publish_time", "")
    content_html = article_info.get("content_html", "")
    markdown_body = fetcher._convert_to_markdown(content_html) if content_html else ""  # type: ignore[attr-defined]
    return "\n".join(
        [
            f"# {title}",
            "",
            f"**作者**: {author}",
            f"**发布时间**: {published_at}",
            f"**原文链接**: {url}",
            "",
            "---",
            "",
            markdown_body,
        ]
    )


def fetch_wechat(url: str, args: argparse.Namespace) -> str:
    verbose = args.verbose
    timeout = args.timeout
    api_base = getattr(args, "wechat_api", None) or os.environ.get("WECHAT_API_URL", "")

    try:
        return _fetch_via_wespy(
            url,
            verbose=verbose,
            wespy_path=getattr(args, "wespy_path", None),
            allow_import=getattr(args, "allow_wespy_import", False),
        )
    except Exception as exc:  # noqa: BLE001
        log(f"[wechat/wespy] skipped or failed: {exc}", verbose)

    if api_base:
        try:
            endpoint = api_base.rstrip("/") + "/api/article?url=" + urllib.parse.quote(url, safe="")
            log(f"[wechat/exporter] {endpoint}", verbose)
            data = http_json(endpoint, timeout=timeout)
            content = (
                data.get("markdown")
                or data.get("content")
                or data.get("html")
                or json.dumps(data, ensure_ascii=False, indent=2)
            )
            log(f"[wechat/exporter] ok ({len(content)} chars)", verbose)
            return content
        except Exception as exc:  # noqa: BLE001
            log(f"[wechat/exporter] failed: {exc}", verbose)

    try:
        log("[wechat/Jina] fetching...", verbose)
        content = http_get(f"https://r.jina.ai/{url}", headers={"Accept": "text/markdown"}, timeout=timeout)
        log(f"[wechat/Jina] ok ({len(content)} chars)", verbose)
        return content
    except Exception as exc:  # noqa: BLE001
        log(f"[wechat/Jina] failed: {exc}", verbose)

    try:
        log("[wechat/defuddle] fetching...", verbose)
        content = http_get(f"https://defuddle.md/{url}", timeout=timeout)
        log(f"[wechat/defuddle] ok ({len(content)} chars)", verbose)
        return content
    except Exception as exc:  # noqa: BLE001
        log(f"[wechat/defuddle] failed: {exc}", verbose)

    log("[wechat/raw] fetching...", verbose)
    return http_get(url, timeout=timeout)


def fetch(url: str, args: argparse.Namespace) -> str:
    unwrapped = _unwrap_captcha_url(url)
    if unwrapped != url:
        log(f"[fetch] captcha URL unwrapped -> {unwrapped}", args.verbose)
        url = unwrapped

    platform_target = detect_platform_target(url)
    if platform_target:
        log(f"[fetch] video-platform={platform_target} url={url}", args.verbose)
        return fetch_video_platform(url, args)

    mode = args.mode if args.mode != "auto" else detect_mode(url)
    log(f"[fetch] mode={mode} url={url}", args.verbose)

    if mode == "twitter":
        return fetch_twitter(url, args)
    if mode == "wechat":
        return fetch_wechat(url, args)
    return fetch_web(url, timeout=args.timeout, skip_jina=args.no_jina, verbose=args.verbose)


def build_output_file_name(index: int, url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    parts = [_slugify(parsed.netloc.replace("www.", ""))]
    for segment in parsed.path.split("/"):
        normalized = segment.strip()
        if not normalized or normalized in {".", ".."}:
            continue
        parts.append(_slugify(normalized))
    stem = "-".join(part for part in parts if part)
    return f"{index:03d}-{stem or 'item'}.md"


def write_text_output(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _results_file_path(args: argparse.Namespace) -> Optional[Path]:
    if getattr(args, "results_file", None):
        return Path(args.results_file)
    if getattr(args, "output_dir", None):
        return Path(args.output_dir) / "results.jsonl"
    return None


def _load_previous_results(path: Optional[Path]) -> Dict[str, Dict[str, Any]]:
    if path is None or not path.exists():
        return {}
    loaded: Dict[str, Dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        loaded[record["id"]] = record
    return loaded


def _append_result_record(path: Optional[Path], record: Dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _cache_key(task: Mapping[str, Any], args: argparse.Namespace) -> str:
    raw = json.dumps(
        {
            "url": task["url"],
            "mode": task.get("mode", "auto"),
            "output_name": task.get("output_name"),
            "text_only": getattr(args, "text_only", False),
            "pretty": getattr(args, "pretty", False),
            "no_jina": getattr(args, "no_jina", False),
            "limit": getattr(args, "limit", 50),
            "replies": getattr(args, "replies", False),
            "download_media": getattr(args, "download_media", False),
            "download_dir": getattr(args, "download_dir", None),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _read_cached_content(task: Mapping[str, Any], args: argparse.Namespace) -> Optional[str]:
    if getattr(args, "download_media", False):
        return None
    cache_dir = getattr(args, "cache_dir", None)
    if not cache_dir:
        return None
    cache_path = Path(cache_dir) / f"{_cache_key(task, args)}.json"
    if not cache_path.exists():
        return None
    payload = json.loads(cache_path.read_text(encoding="utf-8"))
    return payload.get("content")


def _write_cached_content(task: Mapping[str, Any], args: argparse.Namespace, content: str) -> None:
    if getattr(args, "download_media", False):
        return
    cache_dir = getattr(args, "cache_dir", None)
    if not cache_dir:
        return
    cache_path = Path(cache_dir) / f"{_cache_key(task, args)}.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps({"url": task["url"], "mode": task.get("mode"), "content": content}, ensure_ascii=False),
        encoding="utf-8",
    )


def _task_output_path(task: Mapping[str, Any], index: int, args: argparse.Namespace) -> Optional[Path]:
    if not getattr(args, "output_dir", None):
        return None
    output_dir = Path(args.output_dir)
    output_name = task.get("output_name")
    if output_name:
        return output_dir / Path(output_name).name
    return output_dir / build_output_file_name(index, task["url"])


def _task_args(args: argparse.Namespace, task: Mapping[str, Any]) -> argparse.Namespace:
    task_args = argparse.Namespace(**vars(args))
    task_mode = task.get("mode") or args.mode
    if task_mode and task_mode != "auto":
        task_args.mode = task_mode
    return task_args


def _run_with_retry(
    task: Mapping[str, Any],
    args: argparse.Namespace,
    fetcher: Callable[[str, argparse.Namespace], str],
) -> Tuple[str, int]:
    attempts = 0
    max_attempts = max(1, getattr(args, "retry", 0) + 1)
    while True:
        attempts += 1
        try:
            return fetcher(task["url"], _task_args(args, task)), attempts
        except Exception:  # noqa: BLE001
            if attempts >= max_attempts:
                raise
            delay = getattr(args, "retry_delay", 0.0)
            if delay > 0:
                time.sleep(delay)


def _domain_key(url: str) -> str:
    return urllib.parse.urlparse(url).netloc.lower()


def execute_batch_tasks(
    tasks: Sequence[Dict[str, Any]],
    args: argparse.Namespace,
    fetcher: Callable[[str, argparse.Namespace], str] = fetch,
) -> List[Dict[str, Any]]:
    results_path = _results_file_path(args)
    previous_results = _load_previous_results(results_path)
    output_dir = Path(args.output_dir) if getattr(args, "output_dir", None) else None
    rate_limit_ms = getattr(args, "rate_limit_ms", 0)
    domain_lock = threading.Lock()
    last_domain_run: Dict[str, float] = {}

    def process(index_and_task: Tuple[int, Dict[str, Any]]) -> Dict[str, Any]:
        index, task = index_and_task
        output_path = _task_output_path(task, index, args)
        previous = previous_results.get(task["id"])
        if getattr(args, "resume", False) and previous and previous.get("ok"):
            resumed = dict(previous)
            resumed["resumed"] = True
            resumed.setdefault("from_cache", False)
            _append_result_record(results_path, resumed)
            return resumed

        cached_content = _read_cached_content(task, args)
        if cached_content is not None:
            result: Dict[str, Any] = {
                "id": task["id"],
                "url": task["url"],
                "ok": True,
                "mode": task.get("mode", "auto"),
                "from_cache": True,
                "resumed": False,
                "attempts": 0,
            }
            if output_path is not None:
                write_text_output(output_path, cached_content)
                result["output_path"] = str(output_path)
            else:
                result["content"] = cached_content
            _append_result_record(results_path, result)
            return result

        if rate_limit_ms > 0:
            domain = _domain_key(task["url"])
            with domain_lock:
                now = time.monotonic()
                earliest = last_domain_run.get(domain, 0.0) + (rate_limit_ms / 1000.0)
                if earliest > now:
                    time.sleep(earliest - now)
                last_domain_run[domain] = time.monotonic()

        try:
            content, attempts = _run_with_retry(task, args, fetcher)
            _write_cached_content(task, args, content)
            result = {
                "id": task["id"],
                "url": task["url"],
                "ok": True,
                "mode": task.get("mode", "auto"),
                "from_cache": False,
                "resumed": False,
                "attempts": attempts,
            }
            if output_path is not None:
                write_text_output(output_path, content)
                result["output_path"] = str(output_path)
            else:
                result["content"] = content
        except Exception as exc:  # noqa: BLE001
            result = {
                "id": task["id"],
                "url": task["url"],
                "ok": False,
                "mode": task.get("mode", "auto"),
                "from_cache": False,
                "resumed": False,
                "error": str(exc),
            }
            if not getattr(args, "continue_on_error", False):
                _append_result_record(results_path, result)
                raise
        _append_result_record(results_path, result)
        return result

    indexed_tasks = list(enumerate(tasks, start=1))
    if getattr(args, "jobs", 1) <= 1:
        results = [process(item) for item in indexed_tasks]
    else:
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as executor:
            futures = [executor.submit(process, item) for item in indexed_tasks]
            for future in futures:
                results.append(future.result())

    if output_dir is not None:
        write_text_output(output_dir / "batch-summary.json", json.dumps(results, ensure_ascii=False, indent=2))
    return results


def run_batch(
    urls: Sequence[str],
    args: argparse.Namespace,
    fetcher: Callable[[str, argparse.Namespace], str] = fetch,
) -> List[Dict[str, Any]]:
    tasks = []
    for index, url in enumerate(urls, start=1):
        current_mode = getattr(args, "mode", "auto")
        mode = current_mode if current_mode != "auto" else detect_mode(url)
        tasks.append({"id": _stable_task_id(url, mode), "url": url, "mode": mode, "output_name": None, "tags": [], "index": index})
    return execute_batch_tasks(tasks, args, fetcher=fetcher)


def render_batch_stdout(results: Sequence[Dict[str, Any]]) -> str:
    rendered: List[str] = []
    for item in results:
        rendered.append(f"## {item['url']}")
        rendered.append("")
        if item["ok"]:
            rendered.append(item.get("content", f"Saved to {item.get('output_path', '(no file)')}"))
        else:
            rendered.append(f"ERROR: {item['error']}")
        rendered.append("")
    return "\n".join(rendered).strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unified content fetcher: web / X/Twitter / WeChat")
    parser.add_argument("url", nargs="?", help="URL to fetch")
    parser.add_argument("-o", "--output", help="Save single-output content to file")
    parser.add_argument("--output-dir", help="Directory for batch output files")
    parser.add_argument("-m", "--mode", choices=["auto", "web", "twitter", "wechat"], default="auto", help="Force mode (default: auto-detect)")
    parser.add_argument("--batch", help="Read newline-delimited URLs from a file")
    parser.add_argument("--manifest", help="Read task definitions from a JSON or JSONL manifest file")
    parser.add_argument("--stdin", action="store_true", help="Read newline-delimited URLs from stdin")
    parser.add_argument("--continue-on-error", action="store_true", help="Keep processing batch URLs when one item fails")
    parser.add_argument("--jobs", type=int, default=1, help="Number of concurrent batch workers (default 1)")
    parser.add_argument("--retry", type=int, default=0, help="Retry failed batch items this many extra times")
    parser.add_argument("--retry-delay", type=float, default=0.0, help="Delay in seconds between retries")
    parser.add_argument("--cache-dir", help="Directory for cached batch responses")
    parser.add_argument("--resume", action="store_true", help="Skip tasks already marked successful in the results log")
    parser.add_argument("--rate-limit-ms", type=int, default=0, help="Minimum delay per domain between batch fetches")
    parser.add_argument("--results-file", help="Path to a JSONL results log for batch execution")
    parser.add_argument("--download-media", action="store_true", help="Download public Bilibili video/audio streams for single video pages")
    parser.add_argument("--download-dir", help="Directory for downloaded media bundles")
    parser.add_argument("--ffmpeg-path", help="Optional ffmpeg binary for merging downloaded Bilibili DASH streams")
    parser.add_argument("--no-jina", action="store_true", help="Skip Jina Reader")
    parser.add_argument("-r", "--replies", action="store_true", help="Fetch tweet replies (needs Camofox)")
    parser.add_argument("--user", metavar="USERNAME", help="Fetch user timeline")
    parser.add_argument("--limit", type=int, default=50, help="Maximum items for timeline-like fetches (default 50)")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    parser.add_argument("-t", "--text-only", action="store_true", help="Human-readable output instead of JSON")
    parser.add_argument("--port", type=int, default=CAMOFOX_DEFAULT_PORT, help=f"Camofox port (default {CAMOFOX_DEFAULT_PORT})")
    parser.add_argument("--lang", choices=["zh", "en"], default="zh")
    parser.add_argument("--wechat-api", metavar="URL", help="wechat-article-exporter base URL (or set WECHAT_API_URL env)")
    parser.add_argument("--wespy-path", metavar="PATH", help="Explicit local WeSpy checkout path")
    parser.add_argument("--allow-wespy-import", action="store_true", help="Allow importing WeSpy from the current Python environment")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout seconds (default 30)")
    parser.add_argument("-v", "--verbose", action="store_true", default=True)
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress progress messages")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.quiet:
        args.verbose = False

    try:
        validate_args(args)
        urls = collect_input_urls(args)
        if args.user and not urls:
            urls = [validate_url(f"https://x.com/{args.user.lstrip('@')}")]
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        if len(urls) == 1 and not args.batch and not args.stdin and not args.manifest:
            content = fetch(urls[0], args)
            if args.output:
                write_text_output(Path(args.output), content)
                log(f"Saved to {args.output}", args.verbose)
            else:
                print(content)
            return

        tasks = build_batch_tasks(args)
        results = execute_batch_tasks(tasks, args)
        if args.output_dir:
            print(json.dumps(results, ensure_ascii=False, indent=2 if args.pretty else None))
        else:
            print(render_batch_stdout(results))
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

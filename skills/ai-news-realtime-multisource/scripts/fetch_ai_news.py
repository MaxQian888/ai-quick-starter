#!/usr/bin/env python3
"""Fetch latest AI news from multiple domestic and global feeds."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_MAX_WORKERS = 10
DEFAULT_LOOKBACK_HOURS = 72.0
USER_AGENT = "Mozilla/5.0 (compatible; ai-news-realtime-multisource/1.0)"
IGNORED_QUERY_KEYS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
    "spm",
}


@dataclass
class SourceResult:
    source_id: str
    source_name: str
    region: str
    attempted_urls: list[str]
    items: list[dict[str, Any]]
    error: str | None


def load_sources(path: Path) -> list[dict[str, Any]]:
    content = path.read_text(encoding="utf-8")
    raw = json.loads(content)
    if not isinstance(raw, dict) or not isinstance(raw.get("sources"), list):
        raise ValueError("sources file must be a JSON object containing a 'sources' list")
    sources: list[dict[str, Any]] = []
    for source in raw["sources"]:
        if not isinstance(source, dict):
            continue
        source_id = str(source.get("id", "")).strip()
        name = str(source.get("name", "")).strip()
        region = str(source.get("region", "global")).strip().lower()
        urls = source.get("urls")
        if urls is None and source.get("url"):
            urls = [source["url"]]
        if not source_id or not name or not isinstance(urls, list):
            continue
        normalized_urls = [str(url).strip() for url in urls if str(url).strip()]
        if not normalized_urls:
            continue
        sources.append(
            {
                "id": source_id,
                "name": name,
                "region": region if region in {"cn", "global"} else "global",
                "urls": normalized_urls,
            }
        )
    return sources


def local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def joined_text(node: ET.Element) -> str:
    parts = [part.strip() for part in node.itertext() if part and part.strip()]
    return " ".join(parts)


def first_child_text(node: ET.Element, candidates: Iterable[str]) -> str:
    names = set(candidates)
    for child in node:
        if local_name(child.tag) in names:
            text = joined_text(child)
            if text:
                return text
    return ""


def atom_entry_link(entry: ET.Element) -> str:
    fallback = ""
    for child in entry:
        if local_name(child.tag) != "link":
            continue
        href = child.attrib.get("href", "").strip()
        if not href:
            continue
        rel = child.attrib.get("rel", "alternate").strip().lower()
        if rel in {"", "alternate"}:
            return href
        if not fallback:
            fallback = href
    return fallback


def clean_text(value: str) -> str:
    text = unescape(value or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_datetime(value: str) -> datetime | None:
    raw = (value or "").strip()
    if not raw:
        return None

    candidate = raw
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(candidate)
    except ValueError:
        dt = None

    if dt is None:
        try:
            dt = parsedate_to_datetime(raw)
        except (TypeError, ValueError):
            dt = None

    if dt is None:
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def normalize_link(link: str) -> str:
    raw = (link or "").strip()
    if not raw:
        return ""

    parsed = urlparse(raw)
    if parsed.scheme in {"http", "https"}:
        filtered_query = [
            (k, v)
            for k, v in parse_qsl(parsed.query, keep_blank_values=True)
            if k.lower() not in IGNORED_QUERY_KEYS
        ]
        parsed = parsed._replace(query=urlencode(filtered_query, doseq=True), fragment="")
        raw = urlunparse(parsed)

    return raw.rstrip("/")


def parse_rss(root: ET.Element) -> list[dict[str, str]]:
    channel = None
    for child in root:
        if local_name(child.tag).lower() == "channel":
            channel = child
            break
    container = channel or root

    rows: list[dict[str, str]] = []
    for child in container:
        if local_name(child.tag).lower() != "item":
            continue

        title = first_child_text(child, ["title"])
        link = first_child_text(child, ["link", "guid"])
        published = first_child_text(child, ["pubDate", "date", "published", "updated"])
        summary = first_child_text(child, ["description", "summary", "encoded", "content"])

        rows.append(
            {
                "title": clean_text(title),
                "link": clean_text(link),
                "published": clean_text(published),
                "summary": clean_text(summary),
            }
        )

    return rows


def parse_atom(root: ET.Element) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for entry in root:
        if local_name(entry.tag).lower() != "entry":
            continue

        title = first_child_text(entry, ["title"])
        link = atom_entry_link(entry)
        published = first_child_text(entry, ["published", "updated"])
        summary = first_child_text(entry, ["summary", "content"])

        rows.append(
            {
                "title": clean_text(title),
                "link": clean_text(link),
                "published": clean_text(published),
                "summary": clean_text(summary),
            }
        )

    return rows


def parse_feed(raw_xml: bytes) -> list[dict[str, str]]:
    root = ET.fromstring(raw_xml)
    root_name = local_name(root.tag).lower()

    if root_name == "feed":
        return parse_atom(root)
    if root_name in {"rss", "rdf", "rdf:rdf"}:
        return parse_rss(root)

    for child in root:
        if local_name(child.tag).lower() == "channel":
            return parse_rss(root)

    raise ValueError(f"unsupported feed root: {root.tag}")


def fetch_url(url: str, timeout_seconds: float) -> bytes:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        },
    )
    with urlopen(request, timeout=timeout_seconds) as response:  # nosec B310
        return response.read()


def fetch_source(source: dict[str, Any], timeout_seconds: float) -> SourceResult:
    source_id = source["id"]
    source_name = source["name"]
    region = source["region"]

    attempted: list[str] = []
    errors: list[str] = []

    for url in source["urls"]:
        attempted.append(url)
        try:
            raw = fetch_url(url, timeout_seconds)
            parsed_items = parse_feed(raw)
            if not parsed_items:
                errors.append(f"{url}: parsed zero items")
                continue

            normalized_items: list[dict[str, Any]] = []
            for item in parsed_items:
                published_dt = parse_datetime(item.get("published", ""))
                normalized_items.append(
                    {
                        "title": item.get("title") or "(untitled)",
                        "link": normalize_link(item.get("link", "")),
                        "published_raw": item.get("published", ""),
                        "published_utc": (
                            published_dt.isoformat().replace("+00:00", "Z") if published_dt else None
                        ),
                        "published_ts": published_dt.timestamp() if published_dt else None,
                        "summary": item.get("summary") or "",
                        "source_id": source_id,
                        "source_name": source_name,
                        "region": region,
                    }
                )

            return SourceResult(
                source_id=source_id,
                source_name=source_name,
                region=region,
                attempted_urls=attempted,
                items=normalized_items,
                error=None,
            )
        except (HTTPError, URLError, ET.ParseError, ValueError, TimeoutError) as exc:
            errors.append(f"{url}: {exc}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{url}: unexpected error: {exc}")

    return SourceResult(
        source_id=source_id,
        source_name=source_name,
        region=region,
        attempted_urls=attempted,
        items=[],
        error=" | ".join(errors) if errors else "all source URLs failed",
    )


def parse_keywords(raw_keywords: str) -> list[str]:
    if not raw_keywords.strip():
        return []
    return [token.strip().lower() for token in raw_keywords.split(",") if token.strip()]


def filter_item(
    item: dict[str, Any],
    keywords: list[str],
    earliest_utc: datetime | None,
) -> bool:
    if earliest_utc:
        ts = item.get("published_ts")
        if ts is not None and datetime.fromtimestamp(ts, tz=timezone.utc) < earliest_utc:
            return False

    if keywords:
        searchable = f"{item.get('title', '')}\n{item.get('summary', '')}".lower()
        if not any(keyword in searchable for keyword in keywords):
            return False

    return True


def dedupe_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []

    for item in items:
        link = item.get("link") or ""
        title = (item.get("title") or "").strip().lower()
        key = f"link::{link}" if link else f"title::{title}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    return deduped


def sort_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(items, key=lambda x: (x.get("published_ts") is not None, x.get("published_ts") or 0), reverse=True)


def to_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# AI News Snapshot ({payload['generated_at_utc']})")
    lines.append(
        "- Sources queried: "
        f"{payload['source_stats']['total_sources']} "
        f"(ok {payload['source_stats']['ok_sources']}, failed {payload['source_stats']['failed_sources']})"
    )
    lines.append(f"- Items returned: {payload['total_items']}")

    if payload["failed_sources"]:
        lines.append("- Failed sources:")
        for failure in payload["failed_sources"]:
            lines.append(f"  - {failure['source_name']}: {failure['error']}")

    lines.append("")
    lines.append("## Latest Items")
    if not payload["items"]:
        lines.append("No items matched the current filters.")
        return "\n".join(lines)

    for idx, item in enumerate(payload["items"], start=1):
        title = item.get("title") or "(untitled)"
        link = item.get("link") or ""
        published = item.get("published_utc") or item.get("published_raw") or "unknown"
        source = item.get("source_name") or item.get("source_id")
        region = item.get("region") or "unknown"

        if link:
            lines.append(f"{idx}. [{title}]({link})")
        else:
            lines.append(f"{idx}. {title}")
        lines.append(f"   Source: {source} ({region})")
        lines.append(f"   Published: {published}")

        summary = (item.get("summary") or "").strip()
        if summary:
            if len(summary) > 240:
                summary = summary[:237].rstrip() + "..."
            lines.append(f"   Summary: {summary}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def parse_extra_sources(raw_entries: list[str]) -> list[dict[str, Any]]:
    parsed: list[dict[str, Any]] = []

    for index, raw in enumerate(raw_entries, start=1):
        parts = [part.strip() for part in raw.split("|")]
        if len(parts) == 1:
            name = f"extra-{index}"
            region = "global"
            url = parts[0]
        elif len(parts) == 2:
            name = parts[0] or f"extra-{index}"
            region = "global"
            url = parts[1]
        else:
            name = parts[0] or f"extra-{index}"
            region = parts[1].lower() if parts[1] else "global"
            url = "|".join(parts[2:]).strip()

        if not url:
            continue

        parsed.append(
            {
                "id": f"extra-{index}",
                "name": name,
                "region": region if region in {"cn", "global"} else "global",
                "urls": [url],
            }
        )

    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch latest AI news from multiple domestic and global sources",
    )
    parser.add_argument(
        "--sources-file",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "references" / "sources.json",
        help="JSON file that contains the default source list",
    )
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="Extra source using 'URL' or 'NAME|URL' or 'NAME|REGION|URL'",
    )
    parser.add_argument(
        "--region",
        choices=["all", "cn", "global"],
        default="all",
        help="Filter by source region",
    )
    parser.add_argument(
        "--keywords",
        default="",
        help="Comma-separated keywords to filter titles and summaries",
    )
    parser.add_argument(
        "--hours",
        type=float,
        default=DEFAULT_LOOKBACK_HOURS,
        help="Look-back window in hours (<=0 disables time filtering)",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=40,
        help="Maximum total items in the final result",
    )
    parser.add_argument(
        "--max-per-source",
        type=int,
        default=8,
        help="Maximum number of items retained per source before global merge",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="HTTP timeout per request (seconds)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_MAX_WORKERS,
        help="Number of concurrent source fetch workers",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output file path (stdout is always used)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        sources = load_sources(args.sources_file)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to load sources file: {exc}", file=sys.stderr)
        return 2

    extra_sources = parse_extra_sources(args.source)
    sources.extend(extra_sources)

    if args.region != "all":
        sources = [source for source in sources if source["region"] == args.region]

    if not sources:
        print("No sources selected after applying filters.", file=sys.stderr)
        return 2

    keywords = parse_keywords(args.keywords)
    earliest_utc = None
    if args.hours > 0:
        earliest_utc = datetime.now(tz=timezone.utc) - timedelta(hours=args.hours)

    workers = max(1, min(args.workers, len(sources)))
    timeout_seconds = max(1.0, args.timeout)

    results: list[SourceResult] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        future_to_source = {
            pool.submit(fetch_source, source, timeout_seconds): source for source in sources
        }
        for future in concurrent.futures.as_completed(future_to_source):
            results.append(future.result())

    items_by_source: dict[str, list[dict[str, Any]]] = {}
    failed_sources: list[dict[str, str]] = []

    for result in results:
        if result.error:
            failed_sources.append(
                {
                    "source_id": result.source_id,
                    "source_name": result.source_name,
                    "region": result.region,
                    "error": result.error,
                }
            )
            continue

        filtered = [
            item
            for item in result.items
            if filter_item(item, keywords=keywords, earliest_utc=earliest_utc)
        ]
        sorted_filtered = sort_items(filtered)
        items_by_source[result.source_id] = sorted_filtered[: max(1, args.max_per_source)]

    merged_items: list[dict[str, Any]] = []
    for source_items in items_by_source.values():
        merged_items.extend(source_items)

    merged_items = dedupe_items(sort_items(merged_items))
    merged_items = merged_items[: max(1, args.max_items)]

    for item in merged_items:
        item.pop("published_ts", None)

    payload: dict[str, Any] = {
        "generated_at_utc": datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z"),
        "request": {
            "region": args.region,
            "keywords": keywords,
            "hours": args.hours,
            "max_items": args.max_items,
            "max_per_source": args.max_per_source,
            "sources_file": str(args.sources_file),
            "extra_source_count": len(extra_sources),
        },
        "source_stats": {
            "total_sources": len(sources),
            "ok_sources": len(items_by_source),
            "failed_sources": len(failed_sources),
        },
        "failed_sources": failed_sources,
        "total_items": len(merged_items),
        "items": merged_items,
    }

    if args.format == "json":
        rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    else:
        rendered = to_markdown(payload)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")

    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

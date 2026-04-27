#!/usr/bin/env python3
"""Fetch market-research signals from Google News RSS and optional feed URLs."""

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
from urllib.parse import parse_qsl, quote_plus, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

USER_AGENT = "Mozilla/5.0 (compatible; market-research-skill/1.0)"
DEFAULT_TIMEOUT_SECONDS = 12.0
DEFAULT_WORKERS = 8
IGNORED_QUERY_KEYS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
}

SIGNAL_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("funding", ("funding", "raised", "series a", "series b", "series c", "financing", "融资", "投融资")),
    ("pricing", ("pricing", "price", "subscription", "discount", "涨价", "降价", "定价")),
    ("product-launch", ("launch", "released", "rollout", "announced", "推出", "发布", "上线")),
    ("partnership", ("partnership", "collaboration", "alliance", "合作", "签约")),
    ("regulation", ("regulation", "policy", "compliance", "监管", "政策", "合规")),
    ("talent", ("hiring", "recruitment", "layoff", "裁员", "招聘", "人才")),
]


@dataclass
class FetchTask:
    label: str
    kind: str
    url: str
    query: str | None = None


@dataclass
class FetchResult:
    label: str
    kind: str
    url: str
    query: str | None
    items: list[dict[str, Any]]
    error: str | None


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def joined_text(node: ET.Element) -> str:
    return " ".join(part.strip() for part in node.itertext() if part and part.strip()).strip()


def first_child_text(node: ET.Element, names: Iterable[str]) -> str:
    expected = {name.lower() for name in names}
    for child in node:
        if local_name(child.tag).lower() in expected:
            text = joined_text(child)
            if text:
                return text
    return ""


def atom_entry_link(entry: ET.Element) -> str:
    fallback = ""
    for child in entry:
        if local_name(child.tag).lower() != "link":
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

    candidate = raw[:-1] + "+00:00" if raw.endswith("Z") else raw

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


def parse_rss(root: ET.Element) -> list[dict[str, str]]:
    channel = None
    for child in root:
        if local_name(child.tag).lower() == "channel":
            channel = child
            break
    container = channel if channel is not None else root

    rows: list[dict[str, str]] = []
    for child in container:
        if local_name(child.tag).lower() != "item":
            continue
        rows.append(
            {
                "title": clean_text(first_child_text(child, ["title"])),
                "link": clean_text(first_child_text(child, ["link", "guid"])),
                "published": clean_text(first_child_text(child, ["pubDate", "date", "published", "updated"])),
                "summary": clean_text(first_child_text(child, ["description", "summary", "content", "encoded"])),
                "source": clean_text(first_child_text(child, ["source"])),
            }
        )
    return rows


def parse_atom(root: ET.Element) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for entry in root:
        if local_name(entry.tag).lower() != "entry":
            continue
        rows.append(
            {
                "title": clean_text(first_child_text(entry, ["title"])),
                "link": clean_text(atom_entry_link(entry)),
                "published": clean_text(first_child_text(entry, ["published", "updated"])),
                "summary": clean_text(first_child_text(entry, ["summary", "content"])),
                "source": "",
            }
        )
    return rows


def parse_feed(raw_xml: bytes) -> list[dict[str, str]]:
    root = ET.fromstring(raw_xml)
    root_name = local_name(root.tag).lower()

    if root_name == "feed":
        return parse_atom(root)
    if root_name in {"rss", "rdf"}:
        return parse_rss(root)

    for child in root:
        if local_name(child.tag).lower() == "channel":
            return parse_rss(root)

    raise ValueError(f"unsupported feed root: {root.tag}")


def build_google_news_url(query: str, lookback_days: float, hl: str, gl: str) -> str:
    normalized = query.strip()
    if lookback_days > 0:
        normalized = f"{normalized} when:{int(round(lookback_days))}d".strip()

    lang = hl.split("-", 1)[0].lower() if "-" in hl else hl.lower()
    encoded_query = quote_plus(normalized)
    return f"https://news.google.com/rss/search?q={encoded_query}&hl={hl}&gl={gl}&ceid={gl}:{lang}"


def normalize_link(link: str) -> str:
    raw = (link or "").strip()
    if not raw:
        return ""

    parsed = urlparse(raw)
    if parsed.scheme in {"http", "https"}:
        filtered = [
            (key, value)
            for key, value in parse_qsl(parsed.query, keep_blank_values=True)
            if key.lower() not in IGNORED_QUERY_KEYS
        ]
        parsed = parsed._replace(query=urlencode(filtered, doseq=True), fragment="")
        raw = urlunparse(parsed)

    return raw.rstrip("/")


def detect_signal_type(title: str, summary: str) -> str:
    blob = f"{title}\n{summary}".lower()
    for signal_type, keywords in SIGNAL_RULES:
        if any(keyword in blob for keyword in keywords):
            return signal_type
    return "general"


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


def host_or_default(url: str, fallback: str = "unknown-source") -> str:
    hostname = urlparse(url).netloc.strip().lower()
    return hostname or fallback


def fetch_task(task: FetchTask, timeout_seconds: float) -> FetchResult:
    try:
        raw = fetch_url(task.url, timeout_seconds)
        parsed_rows = parse_feed(raw)
        items: list[dict[str, Any]] = []
        for row in parsed_rows:
            title = row.get("title", "").strip() or "(untitled)"
            link = normalize_link(row.get("link", ""))
            published_raw = row.get("published", "").strip()
            published_dt = parse_datetime(published_raw)
            source_name = row.get("source", "").strip() or host_or_default(link, host_or_default(task.url))
            summary = row.get("summary", "").strip()

            items.append(
                {
                    "input_kind": task.kind,
                    "input_label": task.label,
                    "query": task.query,
                    "title": title,
                    "link": link,
                    "published_raw": published_raw,
                    "published_utc": (
                        published_dt.isoformat().replace("+00:00", "Z") if published_dt else None
                    ),
                    "published_ts": published_dt.timestamp() if published_dt else None,
                    "source_name": source_name,
                    "source_url": task.url,
                    "signal_type": detect_signal_type(title, summary),
                    "summary": summary,
                }
            )

        return FetchResult(
            label=task.label,
            kind=task.kind,
            url=task.url,
            query=task.query,
            items=items,
            error=None,
        )
    except (HTTPError, URLError, TimeoutError, ET.ParseError, ValueError) as exc:
        return FetchResult(
            label=task.label,
            kind=task.kind,
            url=task.url,
            query=task.query,
            items=[],
            error=str(exc),
        )
    except Exception as exc:  # noqa: BLE001
        return FetchResult(
            label=task.label,
            kind=task.kind,
            url=task.url,
            query=task.query,
            items=[],
            error=f"unexpected error: {exc}",
        )


def dedupe_items(items: list[dict[str, Any]], strategy: str) -> list[dict[str, Any]]:
    seen: set[str] = set()
    output: list[dict[str, Any]] = []

    for item in items:
        if strategy == "title":
            key = f"title::{(item.get('title') or '').strip().lower()}"
        else:
            link = (item.get("link") or "").strip().lower()
            if link:
                key = f"link::{link}"
            else:
                key = f"title::{(item.get('title') or '').strip().lower()}"

        if key in seen:
            continue
        seen.add(key)
        output.append(item)

    return output


def sort_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: (item.get("published_ts") is not None, item.get("published_ts") or 0.0),
        reverse=True,
    )


def trim_summary(summary: str, limit: int = 280) -> str:
    normalized = re.sub(r"\s+", " ", summary or "").strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def to_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    request = payload["request"]
    stats = payload["stats"]

    lines.append(f"# Market Signal Scan ({payload['generated_at_utc']})")
    lines.append(f"- Inputs: {stats['tasks_total']} (ok {stats['tasks_ok']}, failed {stats['tasks_failed']})")
    lines.append(f"- Queries: {', '.join(request['queries']) if request['queries'] else 'none'}")
    lines.append(f"- Lookback days: {request['lookback_days']}")
    lines.append(f"- Returned items: {payload['total_items']}")

    signal_counts = payload.get("signal_counts", {})
    if signal_counts:
        lines.append("")
        lines.append("## Signal Mix")
        for signal_type, count in signal_counts.items():
            lines.append(f"- {signal_type}: {count}")

    failed_tasks = payload.get("failed_tasks", [])
    if failed_tasks:
        lines.append("")
        lines.append("## Failed Inputs")
        for entry in failed_tasks:
            lines.append(f"- {entry['label']} ({entry['url']}): {entry['error']}")

    lines.append("")
    lines.append("## Top Signals")
    items = payload["items"]
    if not items:
        lines.append("No items matched current filters.")
        return "\n".join(lines) + "\n"

    for idx, item in enumerate(items, start=1):
        title = item.get("title", "(untitled)")
        link = item.get("link", "")
        source_name = item.get("source_name", "unknown-source")
        published = item.get("published_utc") or item.get("published_raw") or "unknown"
        signal_type = item.get("signal_type", "general")
        query = item.get("query") or item.get("input_label") or "n/a"
        summary = trim_summary(item.get("summary", ""))

        if link:
            lines.append(f"{idx}. [{title}]({link})")
        else:
            lines.append(f"{idx}. {title}")
        lines.append(f"   - Query/Input: {query}")
        lines.append(f"   - Signal type: {signal_type}")
        lines.append(f"   - Source: {source_name}")
        lines.append(f"   - Published: {published}")
        if summary:
            lines.append(f"   - Why it matters: {summary}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch market signals from Google News RSS and custom feeds")
    parser.add_argument("--query", action="append", default=[], help="Search query (repeatable)")
    parser.add_argument("--feed", action="append", default=[], help="Custom RSS/Atom feed URL (repeatable)")
    parser.add_argument("--lookback-days", type=float, default=30.0, help="Lookback window in days (<=0 disables)")
    parser.add_argument("--max-per-query", type=int, default=20, help="Maximum items kept per input task")
    parser.add_argument("--max-items", type=int, default=100, help="Maximum total returned items after merge")
    parser.add_argument("--hl", default="en-US", help="Google News language locale (for query mode)")
    parser.add_argument("--gl", default="US", help="Google News country code (for query mode)")
    parser.add_argument("--dedupe-by", choices=["link", "title"], default="link", help="Deduplication strategy")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="Concurrent fetch workers")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS, help="HTTP timeout seconds")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format")
    parser.add_argument("--output", type=Path, default=None, help="Optional output file path")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    queries = [value.strip() for value in args.query if value and value.strip()]
    feeds = [value.strip() for value in args.feed if value and value.strip()]

    if not queries and not feeds:
        parser.error("provide at least one --query or --feed")

    tasks: list[FetchTask] = []
    for query in queries:
        tasks.append(
            FetchTask(
                label=query,
                kind="query",
                query=query,
                url=build_google_news_url(query=query, lookback_days=args.lookback_days, hl=args.hl, gl=args.gl),
            )
        )
    for feed_url in feeds:
        tasks.append(FetchTask(label=host_or_default(feed_url, "custom-feed"), kind="feed", query=None, url=feed_url))

    workers = max(1, min(args.workers, len(tasks)))
    timeout_seconds = max(1.0, args.timeout)
    max_per_query = max(1, args.max_per_query)
    max_items = max(1, args.max_items)

    results: list[FetchResult] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch_task, task, timeout_seconds): task for task in tasks}
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    earliest_utc = None
    if args.lookback_days > 0:
        earliest_utc = datetime.now(tz=timezone.utc) - timedelta(days=args.lookback_days)

    failed_tasks: list[dict[str, str]] = []
    merged_items: list[dict[str, Any]] = []

    for result in results:
        if result.error:
            failed_tasks.append({"label": result.label, "kind": result.kind, "url": result.url, "error": result.error})
            continue

        filtered: list[dict[str, Any]] = []
        for item in result.items:
            published_ts = item.get("published_ts")
            if earliest_utc and published_ts is not None:
                published_dt = datetime.fromtimestamp(float(published_ts), tz=timezone.utc)
                if published_dt < earliest_utc:
                    continue
            filtered.append(item)

        merged_items.extend(sort_items(filtered)[:max_per_query])

    merged_items = sort_items(merged_items)
    merged_items = dedupe_items(merged_items, strategy=args.dedupe_by)
    merged_items = merged_items[:max_items]

    signal_counts: dict[str, int] = {}
    for item in merged_items:
        signal_type = str(item.get("signal_type", "general"))
        signal_counts[signal_type] = signal_counts.get(signal_type, 0) + 1

    for item in merged_items:
        item.pop("published_ts", None)

    payload: dict[str, Any] = {
        "generated_at_utc": datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z"),
        "request": {
            "queries": queries,
            "feeds": feeds,
            "lookback_days": args.lookback_days,
            "max_per_query": max_per_query,
            "max_items": max_items,
            "hl": args.hl,
            "gl": args.gl,
            "dedupe_by": args.dedupe_by,
        },
        "stats": {
            "tasks_total": len(tasks),
            "tasks_ok": len(tasks) - len(failed_tasks),
            "tasks_failed": len(failed_tasks),
        },
        "failed_tasks": failed_tasks,
        "signal_counts": dict(sorted(signal_counts.items(), key=lambda pair: pair[1], reverse=True)),
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

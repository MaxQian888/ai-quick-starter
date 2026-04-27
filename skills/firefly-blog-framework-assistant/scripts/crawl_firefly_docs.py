from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen


BLOCK_TAGS = {
    "article",
    "aside",
    "blockquote",
    "br",
    "code",
    "div",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "li",
    "main",
    "ol",
    "p",
    "pre",
    "section",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "ul",
}

SKIP_TAGS = {"script", "style", "noscript", "svg"}
ALLOWED_HTML_EXTENSIONS = {"", ".html"}


def normalize_href(base_url: str, href: str) -> str:
    raw = (href or "").strip()
    if not raw:
        return ""
    lowered = raw.lower()
    if lowered.startswith("javascript:") or lowered.startswith("mailto:"):
        return ""

    absolute = urljoin(base_url, raw)
    parsed = urlparse(absolute)
    if parsed.scheme not in {"http", "https"}:
        return ""

    normalized = parsed._replace(query="", fragment="")
    return urlunparse(normalized)


def is_doc_page_url(url: str, allowed_host: str, path_prefix: str) -> bool:
    parsed = urlparse(url)
    if not parsed.netloc:
        return False
    if parsed.netloc.lower() != allowed_host.lower():
        return False
    if not parsed.path.startswith(path_prefix):
        return False

    path = parsed.path
    if path.endswith("/"):
        return True

    suffix = Path(path).suffix.lower()
    return suffix in ALLOWED_HTML_EXTENSIONS


def url_to_relative_doc_path(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path or "/"
    if path.endswith("/"):
        path = f"{path}index"
    if path.endswith(".html"):
        path = path[: -len(".html")]
    normalized = path.lstrip("/") or "index"
    return normalized


class _LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        for name, value in attrs:
            if name == "href" and value:
                self.links.add(value)
                return


class _MainTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._main_depth = 0
        self._article_depth = 0
        self._skip_depth = 0
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "main":
            self._main_depth += 1
            self._chunks.append("\n")
            return

        if tag == "article" and self._main_depth <= 0:
            self._article_depth += 1
            self._chunks.append("\n")
            return

        if self._main_depth <= 0 and self._article_depth <= 0:
            return

        if tag in SKIP_TAGS:
            self._skip_depth += 1
            return

        if self._skip_depth == 0 and tag in BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag == "main" and self._main_depth > 0:
            self._main_depth -= 1
            self._chunks.append("\n")
            return

        if tag == "article" and self._article_depth > 0 and self._main_depth <= 0:
            self._article_depth -= 1
            self._chunks.append("\n")
            return

        if self._main_depth <= 0 and self._article_depth <= 0:
            return

        if tag in SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
            return

        if self._skip_depth == 0 and tag in BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if (self._main_depth <= 0 and self._article_depth <= 0) or self._skip_depth > 0:
            return
        text = data.strip()
        if text:
            self._chunks.append(text)
            self._chunks.append(" ")

    def text(self) -> str:
        return "".join(self._chunks)


def _normalize_text(raw: str) -> str:
    value = unescape(raw)
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def extract_main_text(html: str) -> str:
    parser = _MainTextExtractor()
    parser.feed(html)
    parser.close()
    primary = _normalize_text(parser.text())
    if primary:
        return primary

    # Fallback for unexpected page structure.
    body_match = re.search(r"<body[^>]*>(.*?)</body>", html, flags=re.IGNORECASE | re.DOTALL)
    body = body_match.group(1) if body_match else html
    body = re.sub(r"<script[\s\S]*?</script>", " ", body, flags=re.IGNORECASE)
    body = re.sub(r"<style[\s\S]*?</style>", " ", body, flags=re.IGNORECASE)
    body = re.sub(r"<[^>]+>", " ", body)
    return _normalize_text(body)


def extract_links(html: str, base_url: str) -> set[str]:
    parser = _LinkExtractor()
    parser.feed(html)
    parser.close()

    normalized: set[str] = set()
    for href in parser.links:
        full = normalize_href(base_url, href)
        if full:
            normalized.add(full)
    return normalized


def extract_title(html: str) -> str:
    match = re.search(r"<title>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    value = re.sub(r"\s+", " ", unescape(match.group(1))).strip()
    return value


def fetch_html(url: str, timeout_seconds: int) -> str:
    request = Request(
        url=url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        },
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        data = response.read()
    return data.decode("utf-8", errors="replace")


def _markdown_document(url: str, title: str, content: str) -> str:
    label = title or url
    generated_at = datetime.now(timezone.utc).isoformat()
    return (
        f"# {label}\n\n"
        f"- Source URL: {url}\n"
        f"- Crawled At (UTC): {generated_at}\n\n"
        f"## Extracted Content\n\n"
        f"{content}\n"
    )


@dataclass(frozen=True)
class CrawlConfig:
    start_url: str
    output_dir: Path
    host: str
    path_prefix: str
    timeout_seconds: int
    max_pages: int
    delay_ms: int


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _write_text(path: Path, content: str) -> None:
    _ensure_parent(path)
    path.write_text(content, encoding="utf-8")


def _render_catalog(start_url: str, pages: Iterable[dict[str, object]]) -> str:
    rows = ["# Firefly Docs Catalog", "", f"- Start URL: {start_url}", ""]
    for item in pages:
        rows.append(
            f"- [{item['title']}]({item['url']}) -> `{item['md_path']}`"
        )
    rows.append("")
    return "\n".join(rows)


def crawl_docs(config: CrawlConfig) -> dict[str, object]:
    queue: list[tuple[str, str]] = [(config.start_url, "seed")]
    queued: set[str] = {config.start_url}
    visited: set[str] = set()
    pages: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []

    while queue and len(visited) < config.max_pages:
        url, source = queue.pop(0)
        queued.discard(url)
        if url in visited:
            continue
        if not is_doc_page_url(url, config.host, config.path_prefix):
            continue

        try:
            html = fetch_html(url, timeout_seconds=config.timeout_seconds)
        except Exception as exc:  # noqa: BLE001
            errors.append({"url": url, "error": str(exc)})
            visited.add(url)
            continue

        title = extract_title(html)
        content = extract_main_text(html)
        relative = url_to_relative_doc_path(url)
        md_rel = f"pages/{relative}.md"
        raw_rel = f"raw/{relative}.html"
        md_path = config.output_dir / md_rel
        raw_path = config.output_dir / raw_rel

        _write_text(raw_path, html)
        _write_text(md_path, _markdown_document(url, title, content))

        page_entry = {
            "url": url,
            "title": title or relative,
            "source": source,
            "md_path": md_rel.replace("\\", "/"),
            "raw_path": raw_rel.replace("\\", "/"),
            "content_char_count": len(content),
        }
        pages.append(page_entry)
        visited.add(url)

        for link in sorted(extract_links(html, url)):
            if not is_doc_page_url(link, config.host, config.path_prefix):
                continue
            if link in visited or link in queued:
                continue
            queue.append((link, url))
            queued.add(link)

        if config.delay_ms > 0:
            time.sleep(config.delay_ms / 1000)

    pages.sort(key=lambda item: str(item["url"]))

    index_payload: dict[str, object] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "start_url": config.start_url,
        "host": config.host,
        "path_prefix": config.path_prefix,
        "page_count": len(pages),
        "max_pages": config.max_pages,
        "pages": pages,
        "errors": errors,
    }

    _write_text(config.output_dir / "index.json", json.dumps(index_payload, ensure_ascii=False, indent=2))
    _write_text(config.output_dir / "catalog.md", _render_catalog(config.start_url, pages))

    return index_payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crawl Firefly docs and export comprehensive references.")
    parser.add_argument(
        "--start-url",
        default="https://docs-firefly.cuteleaf.cn/en/guide/getting-started.html",
        help="Seed documentation URL.",
    )
    parser.add_argument(
        "--output-dir",
        default="references/firefly-docs",
        help="Output directory for crawled references.",
    )
    parser.add_argument(
        "--path-prefix",
        default="/en/",
        help="Only crawl URLs whose path starts with this prefix.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=30,
        help="Per-request timeout in seconds.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=500,
        help="Maximum number of pages to crawl.",
    )
    parser.add_argument(
        "--delay-ms",
        type=int,
        default=0,
        help="Delay between requests in milliseconds.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print crawl summary as JSON.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    start_url = normalize_href(args.start_url, args.start_url)
    if not start_url:
        raise SystemExit("Invalid --start-url value.")

    parsed = urlparse(start_url)
    config = CrawlConfig(
        start_url=start_url,
        output_dir=Path(args.output_dir).resolve(),
        host=parsed.netloc,
        path_prefix=args.path_prefix,
        timeout_seconds=args.timeout_seconds,
        max_pages=args.max_pages,
        delay_ms=args.delay_ms,
    )

    result = crawl_docs(config)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Crawled {result['page_count']} pages into {config.output_dir}")
        if result["errors"]:
            print(f"Encountered {len(result['errors'])} fetch errors. See index.json for details.")


if __name__ == "__main__":
    main()

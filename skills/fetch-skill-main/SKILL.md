---
name: fetch-skill-main
description: |
  Use this skill whenever you need to fetch readable content from URLs, scrape web pages, extract metadata from videos or social media,
  download articles, or process links in batch. Make sure to use this skill whenever the user mentions fetching, scraping, crawling,
  downloading content, extracting YouTube/Bilibili/X/WeChat data, or saving web pages locally. Also trigger for requests like
  "get this page", "download these links", "what's in this URL", "extract video info", or any batch content-gathering task.
  Covers synonyms such as crawl, scrape, pull, retrieve, archive, and mirror.
---

# Fetch Skill Main

Use the CLI in `scripts/fetch.py` as the primary interface. Keep the core path stdlib-first and treat optional integrations as explicit opt-in helpers rather than hidden side effects.

## Adaptive Detection

Before fetching, detect the content type and environment:

1. **Content type**: general web page, X/Twitter post, WeChat article, YouTube video/channel/playlist, or Bilibili video.
2. **Output needs**: readable Markdown-like text (`--text-only`) or structured JSON for downstream tooling.
3. **Scale**: single URL vs batch (`--batch`, `--manifest`, `--stdin`).
4. **Environment**: check for `WESPY_PATH`, Camofox, or `wechat-article-exporter` before relying on them.
5. **Local tools**: verify `ffmpeg` exists before requesting merged media output.

## Workflow

1. Identify whether the input is a general web page, an X/Twitter URL, a WeChat article, or a supported YouTube/Bilibili page.
2. Run `python scripts/fetch.py <url>` for one URL, or use `--batch`, `--manifest`, or `--stdin` for multi-URL work.
3. Prefer `--text-only` when the user wants readable Markdown-like output. Keep JSON output when downstream tooling needs structured data.
4. Use `--output` for one result or `--output-dir` for batch mode. In batch mode, expect `batch-summary.json` plus `results.jsonl`.
5. Only enable WeSpy via `--wespy-path`, `WESPY_PATH`, or `--allow-wespy-import` when the environment is already prepared.
6. Use `--cache-dir`, `--resume`, `--retry`, `--jobs`, and `--rate-limit-ms` when the user needs repeatable large-batch fetching rather than a one-off scrape.
7. Prefer default JSON output for YouTube/Bilibili when the user needs structured metadata, and `--text-only` when the user wants a readable digest.
8. For Bilibili, prefer the built-in public API path over HTML parsing whenever the script can resolve a stable endpoint.
9. Use `--download-media --download-dir <dir>` for public Bilibili single-video pages when the user needs local media files plus metadata.
10. Add `--ffmpeg-path <path>` only when a local ffmpeg binary already exists and merged output is required.
11. Report which backend succeeded and any remaining unverified live integrations.

## Examples

**Single article fetch:**
```bash
python scripts/fetch.py https://example.com/article --text-only --output article.md
```

**Batch video metadata extraction:**
```bash
python scripts/fetch.py --batch urls.txt --output-dir ./results --json
```

## Guardrails

- Do not auto-install dependencies or clone repositories.
- Do not assume local services such as Camofox or `wechat-article-exporter` are available; detect and fall back.
- Do not store credentials or mutate browser/tooling state just to fetch content.
- Keep progress on stderr and fetched content on stdout when possible.
- Keep Bilibili media download opt-in only; never turn public metadata fetch into an implicit media download.

## References

- Read `references/backend-selection.md` for the routing and fallback order.
- Read `references/safety-and-operations.md` before changing integrations, batch output, or WeSpy handling.

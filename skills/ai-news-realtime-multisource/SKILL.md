---
name: ai-news-realtime-multisource
description: Real-time aggregation of latest AI news from multiple Chinese and global sources. Use when users ask for latest AI news/updates/intel, cross-region AI trend tracking, daily brief generation, or structured multi-source AI updates. Supports concurrent RSS/Atom fetching, source fallback, deduplication, keyword filtering, and latest-first ranking.
---

# AI News Realtime Multisource

## Overview

Fetch and rank the latest AI news from multiple domestic (`cn`) and global (`global`) sources.
Use the bundled script for repeatable, machine-readable results.

## Run Workflow

1. Run the fetch script.

```bash
uv run --python 3.11 scripts/fetch_ai_news.py --format markdown
```

2. Filter by region when the request is region-specific.

```bash
# China only
uv run --python 3.11 scripts/fetch_ai_news.py --region cn --hours 48 --format markdown

# Global only
uv run --python 3.11 scripts/fetch_ai_news.py --region global --hours 48 --format markdown
```

3. Apply keywords when users care about a topic slice.

```bash
uv run --python 3.11 scripts/fetch_ai_news.py --keywords "agent,open-source,inference" --hours 24 --max-items 30 --format markdown
```

4. Export JSON when downstream summarization or automation is needed.

```bash
uv run --python 3.11 scripts/fetch_ai_news.py --format json --output outputs/ai_news_snapshot.json
```

## Source Management

- Edit `references/sources.json` to add or remove feeds.
- Keep each source as one object with: `id`, `name`, `region`, `urls`.
- Set `region` to `cn` or `global`.
- Provide multiple `urls` for one source to implement fallback endpoints.

Example source entry:

```json
{
  "id": "example-ai-media",
  "name": "Example AI Media",
  "region": "global",
  "urls": [
    "https://example.com/ai/rss.xml",
    "https://backup.example.com/feed"
  ]
}
```

## Output Contract

Returned items are sorted newest first and deduplicated by canonicalized link/title.
Each item includes:

- `title`
- `link`
- `published_raw`
- `published_utc`
- `summary`
- `source_id`
- `source_name`
- `region`

The script also reports:

- source success/failure counts
- per-source errors when a feed is unavailable

## Reliability Rules

- Continue when some sources fail; keep partial successful results.
- Prefer `--hours` between `24` and `72` for near-real-time briefings.
- Use `--max-per-source` to avoid one source flooding the result set.
- Use `--source "NAME|REGION|URL"` for temporary ad-hoc feeds without editing files.


---
name: daily-news-multisource-brief
description: Use whenever aggregating daily news, building morning or evening briefings, creating news roundups or digests, monitoring policy/business/technology topics across regions, or collecting multi-source current events with source attribution. Make sure to use this skill for RSS-based news aggregation, cross-region trend tracking, media monitoring, newsletter compilation, or any request involving structured news briefs with timestamps and links. Also triggers for daily briefing automation, news deduplication, or failure-tolerant fetching from China and global sources.
---

# Daily News Multisource Brief

Use bundled script to fetch multi-source news, then produce a structured daily brief.

## Adaptive Detection

Before fetching, scan the workspace to adapt sources and output format:

1. Detect runtime environment:
   - Look for `pyproject.toml`, `requirements.txt`, or `.python-version` to confirm Python availability.
   - Check for `uv` in PATH; fallback to `python` or `python3` if missing.
2. Detect existing source configuration:
   - Read `references/sources.json` to see maintained presets and source tiers.
   - Check for custom source overrides or local additions.
3. Detect output preferences:
   - Look for existing brief files (`.md`, `.json`) to infer preferred format.
   - Check for `outputs/` or `briefs/` directories for default save locations.

## Quick Start

1. Fetch a fast high-trust daily snapshot (core sources only).

```bash
uv run --python 3.11 scripts/fetch_daily_news.py --preset all-core --hours 24 --max-items 80 --format markdown
```

2. Fetch official-direct snapshot (prefer official/mainstream direct RSS, less aggregation).

```bash
uv run --python 3.11 scripts/fetch_daily_news.py --preset all-official --hours 24 --max-items 120 --format markdown
```

3. Fetch broad coverage snapshot (core + extended + community where available).

```bash
uv run --python 3.11 scripts/fetch_daily_news.py --preset all-expanded --hours 24 --max-items 150 --format markdown
```

4. Export JSON for downstream structured summarization.

```bash
uv run --python 3.11 scripts/fetch_daily_news.py --preset all-expanded --hours 24 --format json --output outputs/daily_news.json
```

## Workflow

1. **Pick a preset** from `references/sources.json`.
   - `cn-core`: domestic core coverage.
   - `global-core`: international core coverage.
   - `all-core`: fast balanced CN + global core.
   - `all-official`: official/mainstream direct-feed preferred mode.
   - `all-expanded`: maximum obtainable coverage from maintained list.

2. **Apply scoped filters** when users ask for narrower slices.

```bash
# example: global technology + markets in English
uv run --python 3.11 scripts/fetch_daily_news.py --preset all-expanded --region global --category technology,markets --language en --hours 24
```

3. **Add temporary ad-hoc source** when the user names a specific site.

```bash
# format: NAME|REGION|CATEGORY|COUNTRY|LANGUAGE|TIER|URL
uv run --python 3.11 scripts/fetch_daily_news.py --preset all-core --source "ExampleWire|global|world|us|en|extended|https://example.com/rss.xml"
```

4. **Produce final report** grouped by `CN` and `Global`, then by topic.
   - Include headline, link, source name, publish time.
   - Keep major items first: policy, macro economy, markets, technology, society.
   - Highlight cross-source consensus and source conflicts separately.

## Source Governance

- Edit `references/sources.json` to maintain source definitions and presets.
- Keep each source object fields:
  - `id`, `name`, `region`, `category`, `country`, `language`, `tier`, `urls`.
- Add at least one fallback URL for fragile endpoints when possible.
- Keep `tier=core` for official/high-trust sources.
- Keep `tier=community` for social aggregation sources and treat as lower confidence.

## Output Rules

- Preserve source links for every item.
- Keep time in UTC field returned by script (`published_utc`) when available.
- Report failed sources to make coverage gaps explicit.
- State clearly that coverage is "obtainable sources in configured list", not absolute full internet.

## Examples

### Example 1: Morning Briefing

**Input:** "Give me today's tech and market news."

**Output:**
- Fetched with `--preset all-core --category technology,markets --hours 24`.
- Grouped by region (CN, Global), then by topic.
- Headlines with links, source names, and publish times.

### Example 2: Policy Monitoring

**Input:** "Track policy news from the last 48 hours."

**Output:**
- Fetched with `--preset all-official --category policy --hours 48`.
- Prioritized official sources.
- Cross-source consensus highlighted where multiple sources report the same policy.

## References

- Source inventory and presets: `references/sources.json`
- Coverage and maintenance playbook: `references/coverage-playbook.md`
- Fetcher script: `scripts/fetch_daily_news.py`

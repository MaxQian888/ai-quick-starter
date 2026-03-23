# Daily Coverage Playbook

## Source Tiering

- `core`: official wires, major newspapers, official institutions.
- `extended`: useful but sometimes unstable or narrower feeds.
- `community`: social/community aggregations, useful for signal discovery.

## Recommended Daily Modes

- Fast mode:
  - `--preset all-core --hours 24`
  - Use for routine morning/evening brief.
- Official mode:
  - `--preset all-official --hours 24`
  - Use when you prefer official/mainstream direct RSS and lower aggregator dependency.
- Full mode:
  - `--preset all-expanded --hours 24`
  - Use for comprehensive daily wrap-up.
- Low-noise mode:
  - `--preset all-expanded --tier core,extended`
  - Exclude community sources for higher confidence.

## Category Vocabulary

- `general`
- `politics`
- `world`
- `business`
- `finance`
- `markets`
- `technology`
- `science`
- `health`
- `policy`
- `energy`

Use only these values in `references/sources.json` to keep filtering predictable.

## Add-Source Checklist

1. Confirm feed is RSS/Atom and returns parseable XML.
2. Assign one `region`: `cn` or `global`.
3. Assign one category from category vocabulary.
4. Use lowercase country/language codes (`cn`, `us`, `en`, `zh`).
5. Set tier with bias to caution:
   - official/media institution -> `core` or `extended`
   - social aggregation -> `community`
6. Add backup URL when available.
7. Validate by running:

```bash
uv run --python 3.11 scripts/fetch_daily_news.py --source-id <new-source-id> --hours 72 --max-items 5
```

## Known Limits

- Some feeds are geo-blocked, rate-limited, or intermittently unavailable.
- Paywalled media may publish only partial RSS data.
- "All sources" means all configured and reachable sources, not exhaustive web crawl.

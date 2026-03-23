# Python Component Split Plan

- Target module: `daily-news-multisource-brief/scripts/fetch_daily_news.py`
- Target package: `daily-news-multisource-brief/scripts/fetch_daily_news_parts`
- Architecture style: `package`
- Style reason: No strong architecture markers found; defaulting to package style

## Proposed File Layout

- `daily-news-multisource-brief/scripts/fetch_daily_news_parts/config.py`
  - constant `DEFAULT_TIMEOUT_SECONDS` (line 22, bucket config)
  - constant `DEFAULT_MAX_WORKERS` (line 23, bucket config)
  - constant `DEFAULT_LOOKBACK_HOURS` (line 24, bucket config)
  - constant `USER_AGENT` (line 25, bucket config)
  - constant `IGNORED_QUERY_KEYS` (line 26, bucket config)
- `daily-news-multisource-brief/scripts/fetch_daily_news_parts/core.py`
  - class `SourceResult` (line 39, bucket domain)
- `daily-news-multisource-brief/scripts/fetch_daily_news_parts/operations.py`
  - function `build_parser` (line 536, bucket commands)
- `daily-news-multisource-brief/scripts/fetch_daily_news_parts/queries.py`
  - function `load_sources` (line 52, bucket queries)
  - function `fetch_url` (line 262, bucket queries)
  - function `fetch_source` (line 274, bucket queries)
- `daily-news-multisource-brief/scripts/fetch_daily_news_parts/services.py`
  - function `local_name` (line 103, bucket services)
  - function `joined_text` (line 109, bucket services)
  - function `first_child_text` (line 114, bucket services)
  - function `atom_entry_link` (line 124, bucket services)
  - function `clean_text` (line 140, bucket services)
  - function `filter_item` (line 359, bucket services)
  - function `dedupe_items` (line 390, bucket services)
  - function `sort_items` (line 406, bucket services)
  - function `to_markdown` (line 410, bucket services)
  - function `main` (line 634, bucket services)
- `daily-news-multisource-brief/scripts/fetch_daily_news_parts/validators.py`
  - function `parse_datetime` (line 147, bucket validators)
  - function `normalize_link` (line 175, bucket validators)
  - function `parse_rss` (line 193, bucket validators)
  - function `parse_atom` (line 223, bucket validators)
  - function `parse_feed` (line 246, bucket validators)
  - function `parse_csv_tokens` (line 349, bucket validators)
  - function `parse_keywords` (line 353, bucket validators)
  - function `parse_extra_sources` (line 469, bucket validators)

## Migration Steps

1. Create target package and placeholder files.
2. Move symbols file-by-file, keeping signatures stable.
3. Add thin compatibility shim in original module that re-exports public API.
4. Run unit/integration tests after each moved group to isolate regressions.
5. Update imports in callers in small batches and remove shim when fully migrated.

## Imported Modules Snapshot

- `__future__`
- `argparse`
- `concurrent.futures`
- `dataclasses`
- `datetime`
- `email.utils`
- `html`
- `json`
- `pathlib`
- `re`
- `sys`
- `typing`
- `urllib.error`
- `urllib.parse`
- `urllib.request`
- `xml.etree.ElementTree`

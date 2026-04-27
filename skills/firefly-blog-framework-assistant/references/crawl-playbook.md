# Firefly Crawl Playbook

This skill includes a reproducible crawler for refreshing full documentation references.

## Script

- Path: `scripts/crawl_firefly_docs.py`
- Entry command:

```bash
python scripts/crawl_firefly_docs.py \
  --start-url https://docs-firefly.cuteleaf.cn/ \
  --path-prefix / \
  --output-dir references/firefly-docs \
  --json
```

## Output Contract

The crawler always writes these files:

- `references/firefly-docs/index.json`
  - canonical crawl metadata
  - full page list with URL/title/source and local file paths
  - per-page extracted character count
  - fetch errors array
- `references/firefly-docs/catalog.md`
  - readable list of all crawled pages
- `references/firefly-docs/pages/**/*.md`
  - cleaned text snapshots for fast loading into context
- `references/firefly-docs/raw/**/*.html`
  - raw HTML snapshots for fallback verification

## Verification Checklist

Run after each crawl:

1. `index.json.page_count` is non-zero and close to expected doc size.
2. `errors` array is empty.
3. `pages/` file count equals `raw/` file count.
4. `catalog.md` contains both `/en/guide/` and `/zh/guide/` sections for full-site crawl.
5. Spot-check one high-traffic page:
   - `pages/en/guide/site.md`
   - `pages/zh/guide/site.md`

## Narrow Scope Crawl

Use path prefixes to crawl only one locale:

- English only: `--path-prefix /en/ --start-url https://docs-firefly.cuteleaf.cn/en/guide/getting-started.html`
- Chinese only: `--path-prefix /zh/ --start-url https://docs-firefly.cuteleaf.cn/zh/guide/getting-started.html`

## Operational Notes

- Use `--max-pages` to cap breadth in exploratory runs.
- Use `--delay-ms` if the docs host starts rate-limiting requests.
- Keep UTF-8 output; do not down-convert encodings.

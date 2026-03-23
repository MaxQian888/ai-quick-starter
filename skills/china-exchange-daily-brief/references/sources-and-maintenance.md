# Data Sources and Maintenance

## Source Map

- `SSE` (上海证券交易所)
  - List URL: `https://www.sse.com.cn/aboutus/mediacenter/hotandd/`
  - Parser: `parseSseList`
  - Expected pattern: `<dd><span>YYYY-MM-DD</span><a href="..." title="...">`

- `SZSE` (深圳证券交易所)
  - List URL: `https://www.szse.cn/aboutus/trends/news/`
  - Parser: `parseSzseList`
  - Expected pattern: list items with inline JS variables:
    - `var curHref = './tYYYYMMDD_*.html'`
    - `var curTitle = '...'`

- `HKEX` (香港交易所)
  - List URL: `https://www.hkex.com.hk/News/News-Release?sc_lang=zh-CN`
  - Parser: `parseHkexList`
  - Expected pattern: anchors containing `/News/News-Release/...`
  - Date extraction: URL date code first, then nearby context fallback

- `BSE` (北京证券交易所, optional)
  - List URL: `https://www.bse.cn/important_news`
  - Parser: `parseBseList`
  - Risk: official WAF can return `403` in some environments

## Item Enrichment Rules

- Detail page text extraction:
  - Prefer meta descriptions (`description`, `og:description`, `twitter:description`)
  - Fallback to `<p>` paragraphs
  - Final fallback to cleaned full-page text

- Image extraction:
  - Prefer `og:image`, then `twitter:image`
  - Fallback to first suitable `<img src=...>`
  - Reject common non-content assets (`logo`, `icon`, `qrcode`, etc.)
  - Final fallback to exchange logo

## Date Policy

- Default target date: `Asia/Shanghai` current day.
- If same-day items exist: output same-day items.
- If none:
  - `--strict-date`: output none for that exchange.
  - default mode: fallback to latest available items.

## Common Failure Modes

- `403 Forbidden` / anti-bot:
  - Keep partial output for remaining exchanges.
  - Mark exchange status as failed with explicit reason.
  - For BSE, prefer keeping it optional unless environment is verified.

- Site DOM changes:
  - Update only parser functions in `scripts/fetch_exchange_daily_brief.mjs`.
  - Keep output contract unchanged to avoid breaking downstream consumers.

- Slow responses / timeout:
  - Increase `--timeout-ms` for unstable networks.
  - Avoid unbounded retries; keep deterministic single-pass behavior.

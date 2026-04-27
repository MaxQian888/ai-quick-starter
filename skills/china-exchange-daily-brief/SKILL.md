---
name: china-exchange-daily-brief
description: >
  Make sure to use this skill whenever the user asks for China stock exchange news,
  SSE/SZSE/HKEX updates, market bulletins, exchange daily briefs, or same-day
  official exchange announcements. Also trigger for Chinese financial market summaries,
  regulatory updates, listing notices, or exchange-level market reports. Covers
  synonyms like "Shanghai Stock Exchange news," "Shenzhen exchange updates,"
  "Hong Kong exchange brief," "China market bulletin," "exchange announcements,"
  and "stock market daily." Use it even when the user only mentions "China stocks"
  or "what's new from the exchanges today."
---

# China Exchange Daily Brief

## Overview

Generate an exchange-level daily brief from official exchange websites.
Return per-item title, date, short summary, source link, and image URL.

## Adaptive Detection

Before collecting, detect the user's scope and constraints:

- Determine the target date: today in `Asia/Shanghai` by default, or a specific date.
- Identify required exchanges: `SSE`, `SZSE`, `HKEX` are defaults; add `BSE` only when requested.
- Check for network constraints: some environments hit WAF blocks on `BSE`.
- Choose output format: `markdown` for human review, `json` for downstream systems.

## Workflow

1. Confirm date and coverage.
   - Default date: current day in `Asia/Shanghai`.
   - Default coverage: `SSE`, `SZSE`, `HKEX`.
   - Add `BSE` only when needed (`--include-bse`) because some environments hit official WAF blocks.

2. Run the collector script.
   - Basic:
   ```bash
   node scripts/fetch_exchange_daily_brief.mjs
   ```
   - Strict same-day only:
   ```bash
   node scripts/fetch_exchange_daily_brief.mjs --strict-date
   ```
   - Specific date and write markdown:
   ```bash
   node scripts/fetch_exchange_daily_brief.mjs --date 2026-03-10 --output report.md
   ```
   - JSON output for downstream systems:
   ```bash
   node scripts/fetch_exchange_daily_brief.mjs --format json --output report.json
   ```

3. Validate output completeness.
   - Ensure each exchange has a status line (success, partial, or failed).
   - Ensure each item has summary, source link, and image.
   - Keep partial output when a single exchange fails.

4. Prepare final user-facing brief.
   - Always show an absolute date in the title (`YYYY-MM-DD`).
   - Group results by exchange.
   - Keep explicit failure notes; do not hide errors.

## Output Contract

- Header: `China Exchange Daily Brief (YYYY-MM-DD)`
- Per exchange:
  - list source URL
  - status with reason
  - item list
- Per item:
  - title
  - date
  - summary
  - source link
  - image

## Reliability Notes

- `BSE` can return `403` due anti-crawler/WAF in some networks.
- If page structure changes, update parser functions in `scripts/fetch_exchange_daily_brief.mjs`.
- Keep official-source links; do not replace with third-party reposts.

## Examples

**Today's brief (default exchanges):**
```bash
node scripts/fetch_exchange_daily_brief.mjs --output brief.md
```

**Specific date with BSE included:**
```bash
node scripts/fetch_exchange_daily_brief.mjs --date 2026-04-20 --include-bse --output report.md
```

## Script

Core script: `scripts/fetch_exchange_daily_brief.mjs`

Supported flags:
- `--date YYYY-MM-DD`
- `--max-items N`
- `--strict-date`
- `--include-bse`
- `--format markdown|json`
- `--output PATH`
- `--timeout-ms N`
